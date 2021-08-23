import json
import os

# Global Variable
m_ConnectionString = 'ConnectionString'
m_DifferenceFindMode = 'DifferenceFindMode'
m_CompareTwoRevisions = 'CompareTwoRevisions'
m_ModifiedMDEFLocation = 'ModifiedMDEFLocation'
m_PerforceLocation = 'PerforceLocation'
m_MDEFLocation = 'MDEFLocation'
m_TestDefinitionsLocation = 'TestDefinitionsLocation'
m_TestSuite = 'TestSuite'
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

# Perfoce Variables
P4_ROOT = 'P4_ROOT'
P4USER = 'P4USER'
P4CLIENT = 'P4CLIENT'
P4PORT = 'P4PORT'


def assure(in_param: dict, in_arg: str, lazy: bool = False):
    if in_param is not None and in_arg in in_param and in_param[in_arg] is not None:
        return in_param[in_arg]
    else:
        if lazy:
            return False
        else:
            raise Exception(f"Invalid Expression: {in_param}[{in_arg}]")


def getEnvVariableValue(in_varname: str):
    return assure(dict(os.environ), in_varname)


class InputReader:
    def __init__(self, in_filepath: str):
        if os.path.exists(in_filepath):
            with open(in_filepath, 'r') as file:
                in_file = json.load(file)
            self.inConnectionString = assure(in_file, m_ConnectionString)
            if assure(in_file, m_DifferenceFindMode):
                if assure(in_file[m_DifferenceFindMode], m_CompareTwoRevisions) and \
                        (len(in_file[m_DifferenceFindMode][m_CompareTwoRevisions]) == 2 or
                         len(in_file[m_DifferenceFindMode][m_CompareTwoRevisions]) == 0):
                    self.inDifferenceFindMode = m_CompareTwoRevisions
                    if in_file[m_DifferenceFindMode][m_CompareTwoRevisions][0] < in_file[m_DifferenceFindMode][m_CompareTwoRevisions][1]:
                        self.inOlderMDEFVersion = in_file[m_DifferenceFindMode][m_CompareTwoRevisions][0]
                        self.inNewerMDEFVersion = in_file[m_DifferenceFindMode][m_CompareTwoRevisions][1]
                    elif in_file[m_DifferenceFindMode][m_CompareTwoRevisions][0] > in_file[m_DifferenceFindMode][m_CompareTwoRevisions][1]:
                        self.inOlderMDEFVersion = in_file[m_DifferenceFindMode][m_CompareTwoRevisions][1]
                        self.inNewerMDEFVersion = in_file[m_DifferenceFindMode][m_CompareTwoRevisions][0]
                    else:
                        raise Exception('Error: Invalid Values for `CompareTwoRevisions`. MDEF Revision Numbers must '
                                        'be different.')
                elif assure(in_file[m_DifferenceFindMode], m_ModifiedMDEFLocation) and \
                        len(in_file[m_DifferenceFindMode][m_ModifiedMDEFLocation]) > 0:
                    self.inDifferenceFindMode = m_ModifiedMDEFLocation
                    if os.path.exists(in_file[m_DifferenceFindMode][m_ModifiedMDEFLocation]):
                        self.inModifiedMDEFLocation = in_file[m_DifferenceFindMode][m_ModifiedMDEFLocation]
                    else:
                        raise FileNotFoundError(f"{in_file[m_DifferenceFindMode][m_ModifiedMDEFLocation]} is not a valid location for {m_ModifiedMDEFLocation}")

            if assure(in_file, m_PerforceLocation):
                if assure(in_file[m_PerforceLocation], m_MDEFLocation) and len(in_file[m_PerforceLocation][m_MDEFLocation]) > 0:
                    if os.path.exists(getEnvVariableValue(P4_ROOT) + in_file[m_PerforceLocation][m_MDEFLocation]):
                        self.inMDEFLocation = in_file[m_PerforceLocation][m_MDEFLocation]
                    else:
                        raise FileNotFoundError(f"{in_file[m_PerforceLocation][m_MDEFLocation]} is not a valid location for {m_MDEFLocation}")
                if assure(in_file[m_PerforceLocation], m_TestDefinitionsLocation) and len(in_file[m_PerforceLocation][m_TestDefinitionsLocation]) > 0:
                    if os.path.exists(getEnvVariableValue(P4_ROOT) + in_file[m_PerforceLocation][m_MDEFLocation]):
                        self.inTestDefinitionsLocation = in_file[m_PerforceLocation][m_TestDefinitionsLocation]
                    else:
                        raise FileNotFoundError(f"{in_file[m_PerforceLocation][m_TestDefinitionsLocation]} is not a valid location for {m_TestDefinitionsLocation}")

            if assure(in_file, m_TestSuite):
                self.inRequiredTestSuites = dict()
                for test_suite in in_file[m_TestSuite]:
                    required_test_sets = list()
                    for test_set, is_required in in_file[m_TestSuite][test_suite].items():
                        if is_required:
                            required_test_sets.append(test_set)
                    self.inRequiredTestSuites[test_suite] = required_test_sets
        else:
            raise FileNotFoundError(f"{in_filepath} not found")

    def getConnectionString(self):
        return self.inConnectionString

    def getOlderMDEFRevision(self):
        return self.inOlderMDEFVersion if self.inOlderMDEFVersion > 0 else None

    def getNewerMDEFRevision(self):
        return self.inNewerMDEFVersion if self.inNewerMDEFVersion > 0 else None

    def getMDEFDifferenceFindMode(self):
        return self.inDifferenceFindMode

    def getMDEFLocation(self, in_perforce_loc: bool = False):
        if in_perforce_loc:
            return self.inMDEFLocation
        else:
            return getEnvVariableValue(P4_ROOT) + self.inMDEFLocation

    def getModifiedMDEFLocation(self):
        if self.getMDEFDifferenceFindMode() == m_ModifiedMDEFLocation:
            return self.inModifiedMDEFLocation
        else:
            return None

    def getTestDefinitionLocation(self, in_perforce_loc: bool = False):
        if in_perforce_loc:
            return self.inTestDefinitionsLocation
        else:
            return getEnvVariableValue(P4_ROOT) + self.inTestDefinitionsLocation

    def getRequiredTestSuites(self):
        return self.inRequiredTestSuites
