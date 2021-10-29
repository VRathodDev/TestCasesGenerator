from Generator import TestSetGenerator, ResultSetGenerator


# Global Variables
m_InputFile = 'input.json'
m_TestSetsOption = '-ts'
m_ResultSetsOption = '-rs'


class Runner:
    def run(self, in_mode):
        if in_mode == m_TestSetsOption:
            TestSetGenerator(m_InputFile).run()
        else:
            ResultSetGenerator(m_InputFile).run()


if __name__ == '__main__':
    Runner().run(m_ResultSetsOption)
    # if len(sys.argv) < 2:
    #     raise RuntimeError("Missing mode parameter.")
    # mode = sys.argv[1].lower()
    # if mode == m_TestSetsOption:
    #     runner = Runner()
    #     runner.run(m_TestSetsOption)
    # elif mode == m_ResultSetsOption:
    #     runner = Runner()
    #     runner.run(m_ResultSetsOption)
    # else:
    #     print('Invalid Operation Code')
