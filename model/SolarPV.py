import pandas as pd


class SolarPV(object):
    

    csv_input_file = "../reinforcement-learning-based-smart-grid/data/Load_Consumption.csv"
    # test_file = "../reinforcement-learning-based-smart-grid/data/Load_Consumption.csv"
    test_file = "../reinforcement-learning-based-smart-grid/data/Load_Consumption_25.csv"
    # test_file = "../reinforcement-learning-based-smart-grid/data/test-2.csv"

    THRESHOLD = 5
    

    def __init__(self):

        df = pd.read_csv(self.test_file)
        self.pvGeneration = df[df.columns[4]].tolist()

    def get_pvGeneration(self):
        return self.pvGeneration