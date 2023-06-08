import pandas as pd
from random import randint, random
import numpy as np
from matplotlib import pyplot as plt

class SolarPV(object):
    

    csv_input_file = "../reinforcement-learning-based-smart-grid/data/Load_Consumption.csv"
    # test_file = "../reinforcement-learning-based-smart-grid/data/Load_Consumption.csv"
    # test_file = "../reinforcement-learning-based-smart-grid/data/Load_Consumption_25.csv"
    # test_file = "../reinforcement-learning-based-smart-grid/data/test-2.csv"

    THRESHOLD = 5
    

    def __init__(self):

        df = pd.read_csv(self.csv_input_file)
        self.pvGeneration = df[df.columns[4]].tolist()

        self.pvGeneration = SolarPV.pv_reshape(self, self.pvGeneration)
        #SolarPV.pv_graph(self, self.pvGeneration)

    def get_pvGeneration(self):
        return self.pvGeneration
    
    def generate_pv(self, upper_bound, lower_bound):
        return random()*(upper_bound - lower_bound) + lower_bound
    
    def pv_reshape(self, pv_data):
        temp_arr = np.zeros(12*(len(pv_data)))
        temp_diff = 0.0
        j = 0
        for i in range(0,len(temp_arr)-2):
            if i % 12 == 0:
                try:
                    #print(temp_diff)
                    if j > 8700:
                        #print(i, j)
                        #print(demands[j])
                        None
                        
                    temp_diff = self.generate_pv(max(pv_data[j+1],pv_data[j]), min(pv_data[j+1],pv_data[j]))
                    temp_arr[i] = pv_data[j]
                    

                    j += 1
                    
                except:
                    #print('Invalid Index!')
                    None
            else:
                temp_arr[i] = temp_arr[int(i/12)] + self.generate_pv(max(temp_diff,0), min(temp_diff,0))

        #print(temp_arr.shape)
        return temp_arr
    
    def pv_graph(self, pv_data):
        plt.plot(pv_data, 'g', linewidth=1.0)
        plt.show()
        None