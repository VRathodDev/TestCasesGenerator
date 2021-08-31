import json
import os
import random
import subprocess
from shutil import copytree, copy, move, rmtree
import xml.etree.ElementTree as ET
from InputReader import assure, InputReader, m_ModifiedMDEFLocation, m_CompareTwoRevisions, P4USER, P4_ROOT, P4PORT, \
    P4CLIENT, getEnvVariableValue

# Global Variables
m_TouchStoneAssets = ['Touchstone.exe', 'sbicudt58_64.dll', 'sbicuuc58d_64.dll']
m_TouchStone = 'Touchstone.exe'
m_TouchStoneOutput = 'TouchStoneOutput'
m_DeleteFolder = '.ignore'
m_OutputFolder = 'Output'
m_EnvsFolder = 'Envs'
m_TestEnv = 'TestEnv.xml'
m_TestSuite = 'TestSuite.xml'
m_TestFilesExtension = '.xml'
m_TestSets = 'TestSets'
m_ResultSets = 'ResultSets'
TOUCHSTONE_DIR = getEnvVariableValue('TOUCHSTONE_DIR')
m_Integration = 'Integration'
m_SP = 'SP'
m_SQL = 'SQL'
SQL_SELECT_ALL = 'SQL_SELECT_ALL'
SQL_PASSDOWN = 'SQL_PASSDOWN'
SQL_SP = 'SQL_SP'
SQL_AND_OR = 'SQL_AND_OR'
SQL_FUNCTION_1TABLE = 'SQL_FUNCTION_1TABLE'
SQL_GROUP_BY = 'SQL_GROUP_BY'
SQL_IN_BETWEEN = 'SQL_IN_BETWEEN'
SQL_LIKE = 'SQL_LIKE'
SQL_ORDER_BY = 'SQL_ORDER_BY'
SQL_SELECT_TOP = 'SQL_SELECT_TOP'


def _checkFilesInDir(in_dir_path: str, in_files: list):
    """
    Checks whether given files are present or not in the specified Directory
    :param in_dir_path: The specified Directory path
    :param in_files: List of files to check
    :return: Returns True if all the given files are present in the specified directory else False
    """
    if os.path.exists(in_dir_path) and os.path.isdir(in_dir_path):
        if in_files is not None and len(in_files) > 0 and all(map(lambda x: x in os.listdir(in_dir_path), in_files)):
            return True
    return False


def _copyFilesInDir(in_src_dir_path: str, in_dest_dir_path: str, in_files: list):
    """
    Copies given files in the specified Directory
    :param in_src_dir_path: The specified Source Directory path
    :param in_dest_dir_path: The specified Destination Directory path
    :param in_files: List of files to copy
    :return: Return True if succeeded else False
    """
    if os.path.exists(in_src_dir_path) and os.path.isdir(in_src_dir_path) and os.path.exists(
            in_dest_dir_path) and os.path.isdir(in_dest_dir_path):
        try:
            [copy(os.path.join(in_src_dir_path, file_name), in_dest_dir_path) for file_name in in_files]
            return True
        except FileNotFoundError as e:
            print(e)
            return False
    else:
        return False


class MDEF:
    # MDEF Variables
    m_StoredProcedures = 'StoredProcedures'
    m_Tables = 'Tables'
    m_TableName = 'TableName'
    m_Name = 'Name'
    m_Column = 'Column'
    m_Columns = 'Columns'
    m_MetaData = 'Metadata'
    m_SQLType = 'SQLType'
    m_APIAccesses = ['ReadAPI', 'CreateAPI', 'UpdateAPI', 'DeleteAPI']
    m_APIAccess = 'APIAccess'
    m_ColumnRequirements = 'ColumnRequirements'
    m_VirtualTables = 'VirtualTables'
    m_ResultTable = 'ResultTable'
    m_ParentColumn = 'ParentColumn'
    m_Passdownable = 'Passdownable'

    def __init__(self, in_filepath: str = None, with_columns: bool = False, in_file_content: dict = None):
        if in_filepath is not None:
            if len(in_filepath) > 0 and os.path.exists(in_filepath):
                with open(in_filepath, 'r') as file:
                    self.inMDEFPath = in_filepath
                    self.inMDEFContent = json.load(file)
                    self.inTableNames = dict()
                    self.inVirtualTableNames = list()
                    self.inMDEFStoredProcedures = self.parseStoredProcedures(with_columns)
                    self.inTables = self.parseTables(with_columns)
            else:
                raise FileNotFoundError(f"{in_filepath} is an invalid location")
        else:
            if in_file_content is not None:
                self.inMDEFPath = None
                self.inMDEFContent = in_file_content
                self.inTableNames = dict()
                self.inVirtualTableNames = list()
                self.inMDEFStoredProcedures = self.parseStoredProcedures(with_columns)
                self.inTables = self.parseTables(with_columns)
            else:
                raise ValueError(f"Invalid MDEF Content provided")

    def findDifference(self, in_mdef):
        """
        Finds the difference in Tables and Stored Procedures with respect to passed MDEF Content
        :param in_mdef: Another MDEF Instance to compare in order to find the difference between both
        :return: Returns the difference between both files in the form of MDEF Instance
        """
        if in_mdef is None:
            return None
        mdef_diff = dict()
        # Compare Stored Procedures
        if len(self.inMDEFStoredProcedures) > 0 and len(in_mdef.inMDEFStoredProcedures) > 0:
            mdef_diff[MDEF.m_StoredProcedures] = list()
            index = 0
            for stored_proc_name in self.inMDEFStoredProcedures:
                if stored_proc_name not in in_mdef.inMDEFStoredProcedures:
                    mdef_diff[MDEF.m_StoredProcedures].append(self.inMDEFContent[MDEF.m_StoredProcedures][index])
                index += 1

        # Compare Tables
        if len(self.inTables) > 0 and len(in_mdef.inTables) > 0:
            mdef_diff[MDEF.m_Tables] = list()
            index = 0
            for table in self.inMDEFContent[MDEF.m_Tables]:
                if assure(table, MDEF.m_TableName) not in in_mdef.inTableNames:
                    mdef_diff[MDEF.m_Tables].append(self.inMDEFContent[MDEF.m_Tables][index])
                index += 1

        return mdef_diff if len(mdef_diff[MDEF.m_Tables]) > 0 and len(mdef_diff[MDEF.m_StoredProcedures]) > 0 else None

    def parseStoredProcedures(self, with_columns: bool = False):
        if assure(self.inMDEFContent, MDEF.m_StoredProcedures, True) and len(
                self.inMDEFContent[MDEF.m_StoredProcedures]) > 0:
            mdef_stored_procedures = list()
            if with_columns:
                for stored_proc in self.inMDEFContent[MDEF.m_StoredProcedures]:
                    columns = list()
                    if assure(stored_proc, MDEF.m_ResultTable):
                        for column in assure(stored_proc[MDEF.m_ResultTable], MDEF.m_Columns):
                            columns.append({
                                assure(column, MDEF.m_Name): assure(column[MDEF.m_MetaData], MDEF.m_SQLType) if assure(
                                    column, MDEF.m_MetaData) else None
                            })
                        mdef_stored_procedures.append({
                            assure(stored_proc, MDEF.m_Name): columns
                        })
            else:
                for stored_proc in self.inMDEFContent[MDEF.m_StoredProcedures]:
                    mdef_stored_procedures.append(assure(stored_proc, MDEF.m_Name))
            return mdef_stored_procedures

    def parseTables(self, with_column: bool = False):
        if assure(self.inMDEFContent, MDEF.m_Tables) and len(self.inMDEFContent[MDEF.m_Tables]) > 0:
            mdef_tables = list()
            for table in self.inMDEFContent[MDEF.m_Tables]:
                if assure(table, MDEF.m_TableName) in mdef_tables:
                    raise Exception(
                        f"Error: {self.inMDEFPath} contains more than one table with name {table[MDEF.m_TableName]}")
                else:
                    columns = dict()
                    passdownable_columns = list()
                    if with_column:
                        if len(assure(table, MDEF.m_Columns)) > 0:
                            for column in table[MDEF.m_Columns]:
                                if assure(column, MDEF.m_Passdownable):
                                    passdownable_columns.append(assure(column, MDEF.m_Name))
                                columns[assure(column, MDEF.m_Name)] = assure(column[MDEF.m_MetaData], MDEF.m_SQLType) \
                                    if assure(column, MDEF.m_MetaData) else None
                    if assure(table, MDEF.m_APIAccess):
                        api_accesses = list()
                        for api_access in table[MDEF.m_APIAccess]:
                            if api_access in MDEF.m_APIAccesses:
                                columns_req = assure(table[MDEF.m_APIAccess][api_access], MDEF.m_ColumnRequirements,
                                                     True)
                                api_accesses.append({
                                    api_access: columns_req if columns_req else []
                                })
                        mdef_tables.append({
                            MDEF.m_Name: table[MDEF.m_TableName],
                            MDEF.m_Columns: columns,
                            MDEF.m_APIAccess: api_accesses
                        })
                        self.inTableNames[table[MDEF.m_TableName]] = passdownable_columns \
                            if len(passdownable_columns) > 0 else None
                    self.parseVirtualTables(table, mdef_tables, with_column)
            return mdef_tables

    def parseVirtualTables(self, in_table: dict, in_mdef_tables: list, with_column: bool = False):
        if assure(in_table, MDEF.m_VirtualTables, True) and len(in_table[MDEF.m_VirtualTables]) > 0:
            for virtual_table in in_table[MDEF.m_VirtualTables]:
                if assure(virtual_table, MDEF.m_TableName) in in_mdef_tables:
                    raise Exception(
                        f"Error: {self.inMDEFPath} contains more than one table with name {virtual_table[MDEF.m_TableName]}")
                else:
                    columns = dict()
                    if with_column and len(assure(virtual_table, MDEF.m_Columns)) > 0:
                        for column in virtual_table[MDEF.m_Columns]:
                            if MDEF.m_ParentColumn in column:
                                col_index = 0
                                for in_table_column, in_table_column_type in in_mdef_tables[-1][MDEF.m_Columns].items():
                                    if col_index == int(column[MDEF.m_ParentColumn]):
                                        columns[in_table_column] = in_table_column_type
                                        break
                                    col_index += 1
                            else:
                                columns[assure(column, MDEF.m_Name)] = assure(column[MDEF.m_MetaData], MDEF.m_SQLType) \
                                    if assure(column, MDEF.m_MetaData) else None
                    in_mdef_tables.append({
                        MDEF.m_Name: virtual_table[MDEF.m_TableName],
                        MDEF.m_Columns: columns,
                        'Virtual': True
                    })
                    self.inVirtualTableNames.append(virtual_table[MDEF.m_TableName])
                    self.parseVirtualTables(virtual_table, in_mdef_tables, with_column)


class TestWriter:

    @staticmethod
    def writeTestEnv(in_test_env_loc: str, in_conn_str: str):
        """
        Prepares the Test Env File at the specified location
        :param in_test_env_loc: Location to write Test Environment File
        :param in_conn_str: Connection String
        :return: Returns True if written successfully else False
        """
        if os.path.exists(in_test_env_loc):
            if len(in_conn_str) > 0:
                with open(os.path.join(in_test_env_loc, m_TestEnv), 'w') as file:
                    file.write('<?xml version="1.0" encoding="utf-8"?>\n')
                    file.write('<TestEnvironment>\n')
                    file.write(f"\t<ConnectionString>{in_conn_str}</ConnectionString>\n")
                    file.write('\t<_Monitor>\n')
                    file.write('\t\t<GenerateResults>true</GenerateResults>\n')
                    file.write('\t\t<timeout>20</timeout>\n')
                    file.write('\t\t<maxConsecutiveTimeout>15</maxConsecutiveTimeout>\n')
                    file.write('\t\t<maxAccumulatedTimeout>50</maxAccumulatedTimeout>\n')
                    file.write('\t</_Monitor>\n')
                    file.write('\t<SqlWcharEncoding>UTF-32</SqlWcharEncoding>\n')
                    file.write('</TestEnvironment>')
                return True
            else:
                print('Error: Empty Connection String passed')
                return False
        else:
            print('Error: Incorrect Test Env Location')
            return False

    @staticmethod
    def writeTestSuites(in_required_testsuites: dict):
        """
        Prepares Testsuite Folders and writes `TestSuite.xml` within the folder
        :param in_required_testsuites: A Dictionary having Testsuite as a key and list of test-sets as value
        :return: Returns True if written successfully else False
        """
        output_folder_loc = os.path.abspath(m_OutputFolder)
        if os.path.exists(output_folder_loc):
            for test_suite, test_sets in in_required_testsuites.items():
                with open(os.path.join(os.path.join(output_folder_loc, test_suite), m_TestSuite), 'w') as file:
                    file.write('<TestSuite Name="SQL Test">\n')
                    for test_set in test_sets:
                        file.write(
                            f"\t<TestSet Name=\"{test_set}\" SetFile=\"{test_suite}/TestSets/{test_set}{m_TestFilesExtension}\">\n")
                        file.write('\t\t<!--\n')
                        file.write('\t\t<Exclusion StartID="6" EndID="6">Exclusion reason</Exclusion>\n')
                        file.write('\t\t<Ignorable StartID="6" EndID="6">Ignorable reason</Ignorable>\n')
                        file.write('\t\t-->\n')
                        file.write('\t</TestSet>\n')
                    file.write('\t<GenerateResults>true</GenerateResults>\n')
                    file.write(f"\t<BaselineDirectory>{test_suite}\\ResultSets</BaselineDirectory>\n")
                    file.write('</TestSuite>')
            return True
        else:
            print('Error: Incorrect Test Suite Location')
            return False

    @staticmethod
    def writeTestSets(in_required_testsuites: dict, in_mdef_diff: MDEF, only_select_all: bool = False,
                      in_table_column_values: dict = None):
        """
        Prepares required TestSets for given Testsuites
        :param in_table_column_values: Table Column Values Mapping
        :param only_select_all: A Flag to only generate test sets for SQL_SELECT_ALL
        :param in_mdef_diff: MDEF Instance
        :param in_required_testsuites: A Dictionary having Testsuite as a key and list of test-sets as value
        :return: Returns True if written successfully else False
        """
        if len(in_required_testsuites) > 0:
            if not only_select_all and (in_table_column_values is None or len(in_table_column_values) == 0):
                print('Error: Tables Column Values Map must be provided in order to generate Test Cases other than '
                      '`SQL_SELECT_ALL`')
                return False
            else:
                had_failure = False
                for test_suite, test_sets in in_required_testsuites.items():
                    for test_set, starting_id in test_sets.items():
                        if test_set == SQL_SELECT_ALL and only_select_all:
                            return TestWriter.writeSelectAllTestSets(test_suite, in_mdef_diff, starting_id)
                        # elif test_set == SQL_PASSDOWN:
                        #     had_failure = not TestWriter.writeSQLPassdownTestsets(test_suite, in_mdef_diff,
                        #                                                           in_table_column_values, starting_id)
                        elif test_set == SQL_SELECT_TOP:
                            had_failure = not TestWriter.writeSQLSelectTopTestsets(test_suite,
                                                                                   in_table_column_values, starting_id)
                        elif test_set == SQL_AND_OR:
                            had_failure = not TestWriter.writeSQLAndOrTestsets(test_suite,
                                                                               in_table_column_values, starting_id)
                        elif test_set == SQL_ORDER_BY:
                            had_failure = not TestWriter.writeSQLOrderByTestsets(test_suite,
                                                                                 in_table_column_values, starting_id)
                        if had_failure:
                            print(f"Error: Generation of {test_set} for {test_suite} failed")
                            break
                return not had_failure
        else:
            print('Error: No Test-Suites selected to prepare')
            return False

    @staticmethod
    def writeSelectAllTestSets(in_test_suite: str, in_mdef_diff: MDEF, in_starting_id: int = 1):
        """
        Prepares Test Set for SQL_SELECT_All
        :param in_starting_id: Starting Id of the test-set to write testcases further
        :param in_test_suite: Name of associated Testsuite
        :param in_mdef_diff: Difference of MDEFs as MDEF Instance
        :return: Returns True if all `SQL_SELECT_All` generated successfully else False
        """
        if len(in_test_suite) == 0 or in_mdef_diff is None:
            print('Error: Invalid Parameters')
            return False
        else:
            queries = list()
            for table in in_mdef_diff.inTables:
                queries.append(f"SELECT * FROM {table[MDEF.m_Name]}")
            return TestWriter._prepareTestSet(in_test_suite, SQL_SELECT_ALL, queries, in_starting_id)

    @staticmethod
    def writeSQLPassdownTestsets(in_test_suite: str, in_mdef_diff: MDEF, in_table_column_values: dict,
                                 in_starting_id: int = 1):
        """
        Prepares Test Set for SQL_PASSDOWN
        :param in_table_column_values: Key Value Pair Containing Table Name & Column Value Map
        :param in_starting_id: Starting Id of the test-set to write testcases further
        :param in_test_suite: Name of associated Testsuite
        :param in_mdef_diff: Difference of MDEFs as MDEF Instance
        :return: Returns True if all `SQL_PASSDOWN` generated successfully else False
        """
        if len(in_test_suite) == 0 or in_mdef_diff is None or in_table_column_values is None:
            print('Error: Invalid Parameters')
            return False
        else:
            queries = list()
            table_index, found_table = 0, False
            for table_name, passdownable_columns in in_mdef_diff.inTableNames.items():
                table_index += 1
                if passdownable_columns is None:
                    continue
                table = in_mdef_diff.inTables[table_index - 1]
                for column_name in passdownable_columns:
                    if table_name == table[MDEF.m_Name] and column_name in table[MDEF.m_Columns]:
                        found_table = True
                        for column_value in in_table_column_values[table_name][column_name]:
                            if column_value is not None and len(column_value) > 0:
                                if table[MDEF.m_Columns][column_name] in ['SQL_VARCHAR', 'SQL_LONGVARCHAR']:
                                    queries.append(
                                        f"SELECT * FROM {table_name} WHERE {column_name} = \'{column_value}\'")
                                else:
                                    queries.append(f"SELECT * FROM {table_name} WHERE {column_name} = {column_value}")
                                break
            return TestWriter._prepareTestSet(in_test_suite, SQL_PASSDOWN, queries, in_starting_id)

    @staticmethod
    def writeSQLSelectTopTestsets(in_test_suite: str, in_table_column_values: dict,
                                  in_starting_id: int = 1):
        if len(in_test_suite) > 0 and in_table_column_values is not None:
            queries = list()
            for table_name, columns in in_table_column_values.items():
                row_count = max(list(map(len, columns.values())))
                if row_count > 0:
                    for column_name in columns:
                        if random.randint(0, 50) % 2 == 0:
                            queries.append(f"SELECT TOP {row_count % 25} * FROM {table_name} ORDER BY {column_name}")
                        else:
                            queries.append(f"SELECT TOP {row_count % 25} {column_name} FROM {table_name} ORDER BY {column_name}")
                        break
                else:
                    print(f"Error: Columns for {table_name} could not be parsed correctly from the Resultsets")
                    return False
            return TestWriter._prepareTestSet(in_test_suite, SQL_SELECT_TOP, queries, in_starting_id)
        else:
            print('Error: Invalid Parameters')
            return False

    @staticmethod
    def writeSQLAndOrTestsets(in_test_suite: str, in_table_column_values: dict,
                              in_starting_id: int = 1):
        if len(in_test_suite) > 0 and in_table_column_values is not None:
            queries = list()
            index = 0
            for table_name, columns in in_table_column_values.items():
                queryCompleted = True
                if len(columns) > 0:
                    query = f"SELECT * FROM {table_name} WHERE "
                    for column_name, column_values in columns.items():
                        if len(column_values) >= 2:
                            query += f"{column_name}={column_values[0]} "
                            queryCompleted = not queryCompleted
                            if queryCompleted:
                                queries.append(query)
                                break
                            else:
                                if index % 2 == 0:
                                    query += 'AND '
                                else:
                                    query += 'OR '
                    index += 1
            return TestWriter._prepareTestSet(in_test_suite, SQL_AND_OR, queries, in_starting_id)
        else:
            print('Error: Invalid Parameters')
            return False

    @staticmethod
    def writeSQLOrderByTestsets(in_test_suite: str, in_table_column_values: dict,
                              in_starting_id: int = 1):
        if len(in_test_suite) > 0 and in_table_column_values is not None:
            queries = list()
            for table_name, columns in in_table_column_values.items():
                columns_len = len(columns)
                required_col_index = random.randrange(0, (columns_len % 10) - 1) if columns_len % 10 == 0 else 0
                index = 0
                if columns_len > 0:
                    for column_name, column_values in columns.items():
                        if required_col_index == index:
                            if random.randint(0, 5) % 2 == 0:
                                queries.append(f"SELECT * FROM {table_name} ORDER BY {column_name}")
                            else:
                                queries.append(f"SELECT {column_name} FROM {table_name} ORDER BY {column_name}")
                        index += 1
            return TestWriter._prepareTestSet(in_test_suite, SQL_ORDER_BY, queries, in_starting_id)
        else:
            print('Error: Invalid Parameters')
            return False

    @staticmethod
    def _prepareTestSet(in_testsuite: str, in_testset: str, in_queries: list, in_starting_id: int = 1):
        """
        Prepares a new Testset file for given queries
        :param in_testsuite: Name of the Test Suite
        :param in_testset: Name of the Test Set
        :param in_queries: List of queries
        :param in_starting_id: Starting Id for the testcases
        :return: Returns True if Testset written successfully else False
        """
        if in_testsuite is not None and len(in_testsuite) > 0 and in_testset is not None and len(in_testset) > 0:
            test_set_path = os.path.abspath(os.path.join(os.path.join(m_OutputFolder, in_testsuite), m_TestSets))
            if os.path.exists(test_set_path):
                with open(os.path.join(test_set_path, in_testset + m_TestFilesExtension), 'w') as file:
                    file.write(f"<TestSet Name=\"{in_testset}\" JavaClass=\"com.simba.testframework.testcases"
                               f".jdbc.resultvalidation.SqlTester\" dotNetClass=\"SqlTester\">\n")
                    for query in in_queries:
                        file.write(
                            f"\t<Test Name=\"SQL_QUERY\" JavaMethod=\"testSqlQuery\" dotNetMethod=\"TestSqlQuery\" ID=\"{in_starting_id}\">\n")
                        file.write(f"\t\t<SQL><![CDATA[{query}]]></SQL>\n")
                        file.write('\t\t<ValidateColumns>True</ValidateColumns>\n')
                        file.write('\t\t<ValidateNumericExactly>True</ValidateNumericExactly>\n')
                        file.write('\t</Test>\n')
                        in_starting_id += 1
                    file.write('</TestSet>')
                return True
            else:
                print(f"Error: Path {test_set_path} doesn't exist")
                return False


class PerforceUtility:
    def __init__(self):
        try:
            self.inP4User = assure(dict(os.environ), P4USER)
            self.inP4CLIENT = assure(dict(os.environ), P4CLIENT)
            self.inP4ROOT = assure(dict(os.environ), P4_ROOT)
        except:
            print(f"Environment Variables for Perforce are not set correctly")

    @staticmethod
    def getRevision(in_file_path: str, in_revision: int = None):
        """
        Gets a file from Perforce with the latest revision if revision not specified
        :param in_file_path: Path of the file to get revision
        :param in_revision: Revision Number of a file to get
        :return: Returns the Absolute Path of the File if downloaded successfully
        """
        if os.path.exists(in_file_path):
            in_file_name = os.path.splitext(os.path.basename(os.path.abspath(in_file_path)))[0]
            in_file_extension = os.path.splitext(os.path.basename(os.path.abspath(in_file_path)))[1]
            out_file_name = None
            if in_revision is not None:
                out_file_name = f"{in_file_name}_{in_revision}{in_file_extension}"
                subprocess.call(
                    f"p4.exe print -o {m_DeleteFolder}\\{out_file_name} {os.path.abspath(in_file_path)}#{in_revision}")
            else:
                out_file_name = f"{in_file_name}_Head{in_file_extension}"
                subprocess.call(f"p4.exe print -o {m_DeleteFolder}\\{out_file_name} {os.path.abspath(in_file_path)}")
            return os.path.abspath(f"{m_DeleteFolder}/{out_file_name}")
        else:
            raise FileNotFoundError(f"{in_file_path} is an invalid location")

    @staticmethod
    def getLatestRevisionNumber(in_file_path: str):
        """
        Finds the latest revision number of the file
        :param in_file_path: Path of the file to get latest revision number
        :return: Returns latest revision number of the specified file
        """
        if os.path.exists(in_file_path):
            output = subprocess.check_output(f"p4.exe files {os.path.abspath(in_file_path)}").decode().split(' - ')[0]
            file_name = os.path.basename(os.path.abspath(in_file_path))
            index = output.find(file_name + '#') + len(file_name) + 1
            return int(output[index:])
        else:
            raise FileNotFoundError(f"{in_file_path} is an invalid location")


class TestSetGenerator:
    def __init__(self, in_filepath):
        self.inputFile = InputReader(in_filepath)
        self.inMDEFToGenerateTests = None

    def run(self):
        required_testsuites = self.inputFile.getRequiredTestSuites()
        if self.setupTestFolders(required_testsuites):
            mdef_diff = self.findMDEFDifference()
            if mdef_diff is not None:
                if TestWriter.writeTestSets(required_testsuites, mdef_diff, only_select_all=True):
                    if True or ResultSetGenerator.executeTestSuite(m_Integration, SQL_SELECT_ALL):
                        table_column_values = ResultSetGenerator.parseResultSets(mdef_diff,
                                                                                 required_testsuites[m_Integration][
                                                                                     SQL_SELECT_ALL])
                        if table_column_values is not None and len(table_column_values) > 0:
                            TestWriter.writeTestSets(required_testsuites, mdef_diff, False, table_column_values)

    def findMDEFDifference(self):
        mdef_diff_mode = self.inputFile.getMDEFDifferenceFindMode()
        if mdef_diff_mode == m_CompareTwoRevisions:
            latest_mdef, older_mdef = None, None
            mdef_loc = self.inputFile.getMDEFLocation()
            older_mdef_rev = self.inputFile.getOlderMDEFRevision()
            newer_mdef_rev = self.inputFile.getNewerMDEFRevision()
            if older_mdef_rev is not None and newer_mdef_rev is not None:
                older_mdef_loc = PerforceUtility.getRevision(mdef_loc, older_mdef_rev)
                older_mdef = MDEF(older_mdef_loc) if older_mdef_loc is not None else None
                newer_mdef_loc = PerforceUtility.getRevision(mdef_loc, newer_mdef_rev)
                newer_mdef = MDEF(newer_mdef_loc) if newer_mdef_loc is not None else None
                mdef_diff = newer_mdef.findDifference(older_mdef)
            else:
                latest_mdef_revision_num = PerforceUtility.getLatestRevisionNumber(mdef_loc)
                older_mdef_loc = PerforceUtility.getRevision(mdef_loc, latest_mdef_revision_num - 1)
                older_mdef = MDEF(older_mdef_loc) if older_mdef_loc is not None else None
                latest_mdef_loc = PerforceUtility.getRevision(mdef_loc)
                latest_mdef = MDEF(latest_mdef_loc) if latest_mdef_loc is not None else None
                mdef_diff = latest_mdef.findDifference(older_mdef)
            if mdef_diff is not None:
                return MDEF(in_file_content=mdef_diff, with_columns=True)
            else:
                print('No Difference found between the specified version of MDEF')
                return None
        else:
            modifed_mdef_loc = self.inputFile.getModifiedMDEFLocation()
            if modifed_mdef_loc is not None:
                if modifed_mdef_loc == self.inputFile.getMDEFLocation(in_perforce_loc=False):
                    # Try to backup the MDEF
                    raise Exception(f"Move MDEF from this {self.inputFile.getModifiedMDEFLocation()} location.")
                else:
                    latest_mdef_loc = PerforceUtility.getRevision(self.inputFile.getMDEFLocation())
                    latest_mdef = MDEF(latest_mdef_loc) if latest_mdef_loc is not None else None
                modifed_mdef = MDEF(modifed_mdef_loc)
                mdef_diff = modifed_mdef.findDifference(latest_mdef)
                if mdef_diff is not None:
                    return MDEF(in_file_content=mdef_diff, with_columns=True)
                else:
                    print('No Difference found between the specified version of MDEF')
                    return None
            else:
                raise Exception(f"{m_ModifiedMDEFLocation} is an invalid value! Provide a correct one.")

    def setupOutputFolder(self):
        """
        Makes a directory name `Output` and puts required files of TouchStone with the same by copying from the
        location environment variable TOUCHSTONE_DIR refers
        :return: Returns True if `Output` setup successfully else raises an Exception.
        """
        if m_OutputFolder in os.listdir() and os.path.exists(m_OutputFolder) and os.path.isdir(m_OutputFolder):
            return True if _checkFilesInDir(os.path.abspath(m_OutputFolder), m_TouchStoneAssets) else _copyFilesInDir(
                TOUCHSTONE_DIR, os.path.abspath(m_OutputFolder), m_TouchStoneAssets)
        else:
            try:
                os.mkdir(m_OutputFolder)
                return _copyFilesInDir(TOUCHSTONE_DIR, os.path.abspath(m_OutputFolder), m_TouchStoneAssets)
            except PermissionError as e:
                print(e)
                return False

    def setupTestFolders(self, in_required_testsuites: dict):
        """
        Prepares Envs & TestSuites' Folder
        :param in_required_testsuites: A Dictionary having Testsuite as a key and list of test-sets as value
        :return: Returns True if succeeded else False
        """
        if self.setupOutputFolder():
            output_folder_path = os.path.abspath(m_OutputFolder)
            envs_folder_path = os.path.abspath(os.path.join(output_folder_path, m_EnvsFolder))
            # if os.path.exists(envs_folder_path):
            #     rmtree(envs_folder_path)
            # os.mkdir(envs_folder_path)
            if TestWriter.writeTestEnv(envs_folder_path, self.inputFile.getConnectionString()):
                for test_suite in in_required_testsuites.keys():
                    curr_test_suite_path = os.path.abspath(os.path.join(output_folder_path, test_suite))
                    # if os.path.exists(curr_test_suite_path):
                    #     rmtree(curr_test_suite_path)
                    # os.mkdir(curr_test_suite_path)
                    # os.mkdir(os.path.join(curr_test_suite_path, m_TestSets))
                    # os.mkdir(os.path.join(curr_test_suite_path, m_ResultSets))
                return TestWriter.writeTestSuites(in_required_testsuites)
            else:
                return False
        else:
            return False


class ResultSetGenerator:
    def __init__(self, in_filepath):
        TestSetGenerator(in_filepath).run()

    def run(self):
        pass

    @staticmethod
    def executeTestSuite(in_test_suite: str, with_specific_testset: str = None):
        """
        Runs Touchstone test for given testsuite
        :param with_specific_testset: Name of test-set to run Touchstone for that particular test-set only
        :param in_test_suite: Name of the Testsuite
        :return: Returns None
        """
        if len(in_test_suite) > 0:
            touchstone_cmd = f"{m_TouchStone} -te {m_EnvsFolder}\\{m_TestEnv} -ts {in_test_suite}\\{m_TestSuite} " \
                             f"-o {in_test_suite}"
            if with_specific_testset is not None and len(with_specific_testset) > 0:
                touchstone_cmd += f" -rts {with_specific_testset}"
            with open('exec.bat', 'w') as file:
                file.write(f"cd {m_OutputFolder}\n")
                file.write(touchstone_cmd)
            subprocess.call('exec.bat')
            os.remove('exec.bat')
            return True if len(os.listdir(os.path.join(os.path.join(m_OutputFolder, m_Integration), m_ResultSets))) > 0 \
                else False
        else:
            print('Error: Invalid Testsuite Name')

    @staticmethod
    def _convertDataType(in_data: str, in_sqltype: str):
        """
        Converts given string data into provided data type
        :param in_data: Data as String to convert
        :param in_sqltype: SQLType to convert data accordingly
        :return: Returns Data with Converted data type
        """
        if in_sqltype in ['SQL_WVARCHAR', 'SQL_TYPE_TIMESTAMP', 'SQL_WLONGVARCHAR']:
            return f"\'{str(in_data)}\'"
        elif in_sqltype == 'SQL_BIT':
            return bool(in_data)
        elif in_sqltype == 'SQL_INTEGER':
            return int(in_data)
        elif in_sqltype == 'SQL_DOUBLE':
            return float(in_data)
        else:
            return f"\'{str(in_data)}\'"

    @staticmethod
    def parseResultSets(in_mdef_diff: MDEF, in_starting_id: int = 1):
        """
        Parses the Resultsets generated and maps to its relevant columns
        :param in_mdef_diff: MDEF Difference as MDEF Instance
        :param in_starting_id: Starting Testcase Id for `SQL_SELECT_ALL` Testset
        :return: Returns Table Columns Values Mapping
        """
        if in_mdef_diff is not None:
            resultsets_path = os.path.abspath(os.path.join(os.path.join(m_OutputFolder, m_Integration), m_ResultSets))
            total_resultsets = len(in_mdef_diff.inTables)
            etree = None
            table_column_values = dict()
            for test_case_id in range(in_starting_id, in_starting_id + total_resultsets):
                if os.path.exists(os.path.join(resultsets_path,
                                               f"{SQL_SELECT_ALL}-SQL_QUERY-{test_case_id}{m_TestFilesExtension}")):
                    invalid_row_desc = True
                    row_count = 0
                    with open(os.path.abspath(os.path.join(resultsets_path,
                                f"{SQL_SELECT_ALL}-SQL_QUERY-{test_case_id}{m_TestFilesExtension}"))) as file:
                        etree = ET.fromstring(file.read())
                        row_descriptions = None
                        for child in etree.iter('RowDescriptions'):
                            row_descriptions = child
                            invalid_row_desc = not invalid_row_desc
                            row_count = int(child.attrib.get('RowCount'))
                        if invalid_row_desc:
                            print('More than one RowDescriptions found in the resultset')
                            return None
                        if row_count > 0:
                            row_count %= 30
                            curr_table_name = in_mdef_diff.inTables[test_case_id - in_starting_id][MDEF.m_Name]
                            table_column_values[curr_table_name] = dict()
                            column_count = 0
                            for column in etree.iter('Column'):
                                column_count += 1
                                column_name = column[0].text
                                column_type = column[1].attrib.get('Type')
                                table_column_values[curr_table_name][column_name] = list()
                                if column_name in in_mdef_diff.inTables[test_case_id - in_starting_id][MDEF.m_Columns]:
                                    for i in range(1, row_count + 1):
                                        column_value = row_descriptions[i - 1][column_count - 1]
                                        if not assure(column_value.attrib, 'IsNull', lazy=True) and \
                                                column_value.text is not None and column_value.text != 'none' and \
                                                len(column_value.text) > 0:
                                            table_column_values[curr_table_name][column_name].append(
                                                ResultSetGenerator._convertDataType(column_value.text, column_type)
                                            )
                                else:
                                    print('Error: Column Name mismatched')
                                    return None
                            if column_count != len(in_mdef_diff.inTables[test_case_id - in_starting_id][MDEF.m_Columns]):
                                print('Error: Column Count mismatched')
                                return None
                else:
                    return None
            return table_column_values
