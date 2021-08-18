import json
import os
from InputReader import assure, InputReader, m_ModifiedMDEFLocation, m_CompareLastTwoRevisions

# Global Variables
m_TouchStoneAssets = ['Touchstone.exe', 'sbicudt58_64.dll', 'sbicuuc58d_64.dll']


def getEnvVariableValue(in_varname: str):
    return assure(dict(os.environ), in_varname)


class MDEF:
    def __init__(self, in_filepath: str):
        if len(in_filepath) > 0 and os.path.exists(in_filepath):
            with open(in_filepath, 'r') as file:
                self.inMDEFPath = in_filepath
                self.inMDEFContent = json.load(file)
                self.inMDEFStoredProcedures = self.parseStoredProcedures()
                self.inTables = self.parseTables()
        else:
            raise FileNotFoundError(f"{in_filepath} is an invalid location")

    def findDifference(self, in_mdef: dict):
        """
        Finds the difference in Tables and Stored Procedures with respect to passed MDEF Content
        :param in_mdef:
        :return: mdef_diff
        """
        pass

    def parseStoredProcedures(self, with_columns: bool = False):
        if assure(self.inMDEFContent, 'StoredProcedures', True) and len(self.inMDEFContent['StoredProcedures']) > 0:
            mdef_stored_procedures = list()
            if with_columns:
                for stored_proc in self.inMDEFContent['StoredProcedures']:
                    columns = list()
                    for column in assure(stored_proc, 'Columns'):
                        columns.append({
                            assure(column, 'Name'): assure(column['Metadata'], 'SQLType') if assure(column, 'Metadata') else None
                        })
                    mdef_stored_procedures.append({
                        assure(stored_proc, 'Name'): columns
                    })
            else:
                for stored_proc in self.inMDEFContent['StoredProcedures']:
                    mdef_stored_procedures.append(assure(stored_proc, 'Name'))
            return mdef_stored_procedures

    def parseTables(self, with_column: bool = False):
        if assure(self.inMDEFContent, 'Tables') and len(self.inMDEFContent['Tables']) > 0:
            mdef_tables = list()
            for table in self.inMDEFContent['Tables']:
                if assure(table, 'TableName') in mdef_tables:
                    raise Exception(f"Error: {self.inMDEFPath} contains more than one table with name {assure(table, 'TableName')}")
                else:
                    columns = list()
                    if with_column:
                        if len(assure(table, 'Columns')) > 0:
                            for column in table['Columns']:
                                columns.append({
                                    assure(column, 'Name'): assure(column['Metadata'], 'SQLType') if assure(column, 'Metadata') else None
                                })
                    if assure(table, 'APIAccess'):
                        api_accesses = list()
                        for api_access in table['APIAccess']:
                            if api_access in ['ReadAPI', 'CreateAPI', 'UpdateAPI', 'DeleteAPI']:
                                columns_req = assure(table['APIAccess'][api_access], 'ColumnRequirements', True)
                                api_accesses.append({
                                    api_access: columns_req if columns_req else []
                                })
                        mdef_tables.append({
                            table['TableName']: {
                                'Columns': columns,
                                'APIAccess': api_accesses
                            }
                        })
                    self.parseVirtualTables(table, mdef_tables, with_column)
                    # virtual_tables = self.parseVirtualTables(table, mdef_tables, with_column)
                    # if virtual_tables is not None:
                    #     mdef_tables.extend(virtual_tables)
            return mdef_tables

    def parseVirtualTables(self, in_table: dict, in_mdef_tables: list, with_column: bool = False):
        if assure(in_table, 'VirtualTables', True) and len(in_table['VirtualTables']) > 0:
            for virtual_table in in_table['VirtualTables']:
                if assure(virtual_table, 'TableName') in in_mdef_tables:
                    raise Exception(f"Error: {self.inMDEFPath} contains more than one table with name {virtual_table['TableName']}")
                else:
                    columns = list()
                    if with_column and len(assure(virtual_table, 'Columns')) > 0:
                        for column in virtual_table['Columns']:
                            columns.append({
                                assure(column, 'Name'): assure(column['Metadata'], 'SQLType') if assure(column, 'Metadata') else None
                            })
                    in_mdef_tables.append({
                        virtual_table['TableName']: {
                            'Columns': columns,
                            'Virtual': True
                        }
                    })
                    self.parseVirtualTables(virtual_table, in_mdef_tables, with_column)


class TestSetGenerator:
    def __init__(self, in_filepath):
        self.inputFile = InputReader(in_filepath)
        self.inMDEFToGenerateTests = None

    def run(self):
        self.findMDEFDifference()

    def findMDEFDifference(self):
        mdef_diff_mode = self.inputFile.getMDEFDifferenceFindMode()
        if mdef_diff_mode == m_CompareLastTwoRevisions:
            pass
        else:
            modifed_mdef_loc = self.inputFile.getModifiedMDEFLocation()
            if modifed_mdef_loc is not None:
                modifed_mdef = MDEF(modifed_mdef_loc)
            else:
                raise Exception(f"{m_ModifiedMDEFLocation} is an invalid value! Provide a correct one.")


class ResultSetGenerator:
    def __init__(self, in_filepath):
        TestSetGenerator(in_filepath).run()

    def run(self):
        pass
