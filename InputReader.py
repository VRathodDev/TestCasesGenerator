import json
import os

# Global Variable
m_ConnectionString = 'ConnectionString'
m_DifferenceFindMode = 'DifferenceFindMode'
m_CompareLastTwoRevisions = 'CompareLastTwoRevisions'
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


def assure(in_param: dict, in_arg: str, lazy: bool = False):
    if in_param is not None and in_arg in in_param and in_param[in_arg] is not None:
        return in_param[in_arg]
    else:
        if lazy:
            return False
        else:
            raise Exception(f"Invalid Expression: {in_param}[{in_arg}]")


class InputReader:
    def __init__(self, in_filepath: str):
        if os.path.exists(in_filepath):
            with open(in_filepath, 'r') as file:
                in_file = json.load(file)
            self.inConnectionString = assure(in_file, m_ConnectionString)
            if assure(in_file, m_DifferenceFindMode):
                if assure(in_file[m_DifferenceFindMode], m_CompareLastTwoRevisions) and \
                        in_file[m_DifferenceFindMode][m_CompareLastTwoRevisions]:
                    self.inDifferenceFindMode = m_CompareLastTwoRevisions
                elif assure(in_file[m_DifferenceFindMode], m_ModifiedMDEFLocation) and \
                        len(in_file[m_DifferenceFindMode][m_ModifiedMDEFLocation]) > 0:
                    self.inDifferenceFindMode = m_ModifiedMDEFLocation
                    self.inModifiedMDEFLocation = in_file[m_DifferenceFindMode][m_ModifiedMDEFLocation]

            if assure(in_file, m_PerforceLocation):
                if assure(in_file[m_PerforceLocation], m_MDEFLocation) and len(in_file[m_PerforceLocation][m_MDEFLocation]) > 0:
                    self.inMDEFLocation = in_file[m_PerforceLocation][m_MDEFLocation]
                if assure(in_file[m_PerforceLocation], m_TestDefinitionsLocation) and len(in_file[m_PerforceLocation][m_TestDefinitionsLocation]) > 0:
                    self.inTestDefinitionsLocation = in_file[m_PerforceLocation][m_TestDefinitionsLocation]

            if assure(in_file, m_TestSuite):
                self.inRequiredTestSuites = list()
                for test_suite in in_file[m_TestSuite]:
                    required_test_sets = list()
                    for test_set, is_required in in_file[m_TestSuite][test_suite].items():
                        if is_required:
                            required_test_sets.append(test_set)
                    self.inRequiredTestSuites.append({
                        test_suite: required_test_sets
                    })
        else:
            raise FileNotFoundError(f"{in_filepath} not found")

    def getConnectionString(self):
        return self.inConnectionString

    def getMDEFDifferenceFindMode(self):
        return self.inDifferenceFindMode

    def getMDEFLocation(self):
        return self.inMDEFLocation

    def getModifiedMDEFLocation(self):
        if self.getMDEFDifferenceFindMode() == m_ModifiedMDEFLocation:
            return self.inModifiedMDEFLocation
        else:
            return None

    def getTestDefinitionLocation(self):
        return self.inTestDefinitionsLocation

    def getRequiredTestSuites(self):
        return self.inRequiredTestSuites
