import json
import os
import subprocess
from shutil import copytree, copy, move, rmtree
from InputReader import assure, InputReader, m_ModifiedMDEFLocation, m_CompareTwoRevisions, P4USER, P4_ROOT, P4PORT, P4CLIENT, getEnvVariableValue

# Global Variables
m_TouchStoneAssets = ['Touchstone.exe', 'sbicudt58_64.dll', 'sbicuuc58d_64.dll']
m_DeleteFolder = '.ignore'
m_OutputFolder = 'Output'
m_EnvsFolder = 'Envs'
m_TestEnv = 'TestEnv.xml'
m_TestSuite = 'TestSuite.xml'
m_TestFilesExtension = '.xml'
m_TestSets = 'TestSets'
m_ResultSets = 'ResultSets'
TOUCHSTONE_DIR = getEnvVariableValue('TOUCHSTONE_DIR')


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
    if os.path.exists(in_src_dir_path) and os.path.isdir(in_src_dir_path) and os.path.exists(in_dest_dir_path) and os.path.isdir(in_dest_dir_path):
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

    def __init__(self, in_filepath: str = None, with_columns: bool = False, in_file_content: dict = None):
        if in_filepath is not None:
            if len(in_filepath) > 0 and os.path.exists(in_filepath):
                with open(in_filepath, 'r') as file:
                    self.inMDEFPath = in_filepath
                    self.inMDEFContent = json.load(file)
                    self.inTableNames = list()
                    self.inVirtualTableNames = list()
                    self.inMDEFStoredProcedures = self.parseStoredProcedures(with_columns)
                    self.inTables = self.parseTables(with_columns)
            else:
                raise FileNotFoundError(f"{in_filepath} is an invalid location")
        else:
            if in_file_content is not None:
                self.inMDEFPath = None
                self.inMDEFContent = in_file_content
                self.inTableNames = list()
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
        if assure(self.inMDEFContent, MDEF.m_StoredProcedures, True) and len(self.inMDEFContent[MDEF.m_StoredProcedures]) > 0:
            mdef_stored_procedures = list()
            if with_columns:
                for stored_proc in self.inMDEFContent[MDEF.m_StoredProcedures]:
                    columns = list()
                    if assure(stored_proc, MDEF.m_ResultTable):
                        for column in assure(stored_proc[MDEF.m_ResultTable], MDEF.m_Columns):
                            columns.append({
                                assure(column, MDEF.m_Name): assure(column[MDEF.m_MetaData], MDEF.m_SQLType) if assure(column, MDEF.m_MetaData) else None
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
                    raise Exception(f"Error: {self.inMDEFPath} contains more than one table with name {table[MDEF.m_TableName]}")
                else:
                    columns = list()
                    if with_column:
                        if len(assure(table, MDEF.m_Columns)) > 0:
                            for column in table[MDEF.m_Columns]:
                                columns.append({
                                    assure(column, MDEF.m_Name): assure(column[MDEF.m_MetaData], MDEF.m_SQLType) if assure(column, MDEF.m_MetaData) else None
                                })
                    if assure(table, MDEF.m_APIAccess):
                        api_accesses = list()
                        for api_access in table[MDEF.m_APIAccess]:
                            if api_access in MDEF.m_APIAccesses:
                                columns_req = assure(table[MDEF.m_APIAccess][api_access], MDEF.m_ColumnRequirements, True)
                                api_accesses.append({
                                    api_access: columns_req if columns_req else []
                                })
                        mdef_tables.append({
                            MDEF.m_Name: table[MDEF.m_TableName],
                            MDEF.m_Columns: columns,
                            MDEF.m_APIAccess: api_accesses
                        })
                        self.inTableNames.append(table[MDEF.m_TableName])
                    self.parseVirtualTables(table, mdef_tables, with_column)
            return mdef_tables

    def parseVirtualTables(self, in_table: dict, in_mdef_tables: list, with_column: bool = False):
        if assure(in_table, MDEF.m_VirtualTables, True) and len(in_table[MDEF.m_VirtualTables]) > 0:
            for virtual_table in in_table[MDEF.m_VirtualTables]:
                if assure(virtual_table, MDEF.m_TableName) in in_mdef_tables:
                    raise Exception(f"Error: {self.inMDEFPath} contains more than one table with name {virtual_table[MDEF.m_TableName]}")
                else:
                    columns = list()
                    if with_column and len(assure(virtual_table, MDEF.m_Columns)) > 0:
                        for column in virtual_table[MDEF.m_Columns]:
                            if MDEF.m_ParentColumn not in column:
                                columns.append({
                                    assure(column, MDEF.m_Name): assure(column[MDEF.m_MetaData], MDEF.m_SQLType) if assure(column, MDEF.m_MetaData) else None
                                })
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
                        file.write(f"\t<TestSet Name=\"{test_set}\" SetFile=\"{test_suite}/TestSets/{test_set}{m_TestFilesExtension}\">\n")
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
                subprocess.call(f"p4.exe print -o {m_DeleteFolder}\\{out_file_name} {os.path.abspath(in_file_path)}#{in_revision}")
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
        if self.setupTestFolders(self.inputFile.getRequiredTestSuites()):
            mdef_diff = self.findMDEFDifference()
            if mdef_diff is not None:
                print(mdef_diff)

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
            return True if _checkFilesInDir(os.path.abspath(m_OutputFolder), m_TouchStoneAssets) else _copyFilesInDir(TOUCHSTONE_DIR, os.path.abspath(m_OutputFolder), m_TouchStoneAssets)
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
            if os.path.exists(envs_folder_path):
                rmtree(envs_folder_path)
            os.mkdir(envs_folder_path)
            if TestWriter.writeTestEnv(envs_folder_path, self.inputFile.getConnectionString()):
                for test_suite in in_required_testsuites.keys():
                    curr_test_suite_path = os.path.abspath(os.path.join(output_folder_path, test_suite))
                    if os.path.exists(curr_test_suite_path):
                        rmtree(curr_test_suite_path)
                    os.mkdir(curr_test_suite_path)
                    os.mkdir(os.path.join(curr_test_suite_path, m_TestSets))
                    os.mkdir(os.path.join(curr_test_suite_path, m_ResultSets))
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
