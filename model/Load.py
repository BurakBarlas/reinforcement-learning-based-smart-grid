from Battery import Battery
from SolarPV import SolarPV
from DemandRange import DemandRange
from Utils import normalize_timestep, get_last_k
from Bounds import Bounds
from matplotlib import pyplot as plt

from random import randint, random
import csv
import pandas as pd
import numpy as np

class Load(object):
    """
    Member Variables
        Demand ranges throughout the day (Array of DemandRange objects)
        Battery Object
        DailyDemandCurve - stores demand generated so far during the day
        LoadID
        WithAgent - boolean indicating presence of agent
    Member Functions
        Getters and Setters and Constructor
        GenerateDemandAndUpdateCurve(action)
        ResetDay()
        CalculateReward()
        Daily demand analytics and visualization functions

    Time of day -
        value from 0 to 287 (5 min intervals for 24 hours)

    Actions
        0-SB,SC
        1-SC
        2-BC
    """
    # global num_loads
    num_loads = 0
    default_timestep_size = 5.0
    action_space = [0,1,2,3]
    no_agent_action = 1
    RANDOMIZE_DEMANDS = False
 
    actionOne = 0
    actionTwo = 0
    actionThree = 0
    actionFour = 0

    csv_input_file = "../reinforcement-learning-based-smart-grid/data/Load_Consumption.csv"
    # test_file = "../reinforcement-learning-based-smart-grid/data/Load_Consumption.csv"
    test_file = "../reinforcement-learning-based-smart-grid/data/Load_Consumption_25.csv"
    # test_file = "../reinforcement-learning-based-smart-grid/data/test-2.csv"

    THRESHOLD = 5
    

    def __init__(self, demand_ranges = None, batteryParams = None, loadID = None, with_agent=False, look_ahead = 1):
        if loadID is None:
            loadID = Load.num_loads
        Load.num_loads += 1

        df = pd.read_csv(self.csv_input_file)
        demands = df[df.columns[3]].tolist()
        #print(len(demands))
        

        demands = self.demand_reshape(demands)
        print(len(demands))
        last_items = demands[-1]
        #print(last_items)
        # self.demand_graph(demands)


        #print(temp_arr[:100])
        #print(demands)

        #print(df.shape)
        #print(demands[1])

        if batteryParams is None:
            batteryParams = {}

        self.demand_ranges = []
        
        for demand_range in demands:
            self.demand_ranges.append(demand_range)
        # print("self.demand_ranges", self.demand_ranges)
        self.battery = Battery(**batteryParams)
        self.solarPV = SolarPV()
        self.demands = list()
        self.loadID = loadID
        self.with_agent = with_agent
        self.costs = list()
        self.look_ahead = look_ahead
        self.demand_bounds = Bounds()
        self.daily_balance = 0
        # self.min_demand = 999999.0
        # self.max_demand = 0.0

        # for key in params:
        #     setattr(self,key,params[key])
    def step(self, timestep, timestep_size= default_timestep_size, action=None):
        """timestep_size is in minutes"""
        # if not self.with_agent:
        #     action = Load.no_agent_action
        #print("TimeStep: ",timestep,", Action: ", action, "Costs: ",self.get_costs())
        if action is None:
            action = Load.no_agent_action

        if action not in Load.action_space:
            raise AssertionError("Not a valid action")

        timestep = normalize_timestep(timestep, timestep_size, Load.default_timestep_size)
        penalty_factor = 0

        # pvsolar to battery charge
        if action == 0:
            #checks
            self.demands.append(self.demand_ranges[timestep])
            print(self.solarPV.get_pvGeneration()[timestep])
            pv_percentage_increase = int((self.solarPV.get_pvGeneration()[timestep]/self.battery.get_battery_capacity())* 100)
            print(timestep)
            new_battery_percentage_increase = min(pv_percentage_increase, 100.0 - self.battery.get_current_battery_percentage())
            demand_usage_percentage = ((self.demands[-1]*(timestep_size/60.0))/self.battery.get_battery_capacity()) * 100.0


            self.battery.set_current_battery_percentage(self.battery.get_current_battery_percentage()+new_battery_percentage_increase)
            self.demand_bounds.update_bounds(self.demands[-1])
            # gride satma actionu bitince penaltyi degistirelim
            try:
                penalty_factor = 5 * (((pv_percentage_increase-new_battery_percentage_increase)/(pv_percentage_increase)) + ((demand_usage_percentage-new_battery_percentage_increase)/demand_usage_percentage))
            except:
                # buraya tekrar bakilabilir
                penalty_factor = 5 * (1 + ((demand_usage_percentage-new_battery_percentage_increase)/demand_usage_percentage))

            # if self.battery.current_battery_percentage >100.0- self.THRESHOLD:
            #     penalty_factor = 5 * (self.THRESHOLD + self.battery.current_battery_percentage - 100.0) / self.THRESHOLD
            self.actionOne += 1

            # return [self.demands[-1], (self.battery.get_battery_capacity() * new_battery_percentage_increase/100)*60 / timestep_size, penalty_factor]
            # Second index should be 0 because charged battery from PV
            return [self.demands[-1], 0, penalty_factor]
        # Use grid for demand  
        elif action == 1:
            self.demands.append(self.demand_ranges[timestep])
            grid_usage = ((self.demands[-1]*(timestep_size/60.0))/self.battery.get_battery_capacity()) * 100.0
            
            remained_battery_percentage = max(0, grid_usage - self.battery.get_current_battery_percentage())


            self.demand_bounds.update_bounds(self.demands[-1])
            penalty_factor = 5 *(100 - remained_battery_percentage)/100

            self.actionTwo += 1
            return [self.demands[-1], 0, penalty_factor]
            
        # discharge battery
        elif action == 2:
            #checks
            self.demands.append(self.demand_ranges[timestep])
            # print("self.demands", self.demands)
            battery_percentage_decrease = ((self.demands[-1]*(timestep_size/60.0))/self.battery.get_battery_capacity()) * 100.0
            # print("battery_percentage_decrease",battery_percentage_decrease)
            # print("min(" ,min(battery_percentage_decrease, self.battery.get_current_battery_percentage()))
            # print("self.battery.get_current_battery_percentage" ,self.battery.get_current_battery_percentage())

            new_battery_percentage_decrease = min(battery_percentage_decrease, self.battery.get_current_battery_percentage())
            # print("self.battery.get_current_battery_percentage()",self.battery.get_current_battery_percentage())
            # print("new_battery_percentage_decrease",new_battery_percentage_decrease)
            self.battery.set_current_battery_percentage(self.battery.get_current_battery_percentage() - new_battery_percentage_decrease)
            # controllable = battery_percentage_decrease* self.battery.get_battery_capacity()*60/ (timestep_size*100)
            uncontrollable = - new_battery_percentage_decrease* self.battery.get_battery_capacity()*60/ (timestep_size*100)
            self.demand_bounds.update_bounds(self.demands[-1])
            penalty_factor = 5*(battery_percentage_decrease-new_battery_percentage_decrease)/battery_percentage_decrease
            # if self.battery.current_battery_percentage < self.THRESHOLD:
            #     penalty_factor = 5 * (self.THRESHOLD - self.battery.current_battery_percentage) / self.THRESHOLD
            self.actionThree += 1

            return [self.demands[-1], uncontrollable,penalty_factor] # *2 is penalty for discharging battery to 0%
        # sell to grid
        elif action == 3:
            self.demands.append(self.demand_ranges[timestep])
            expected_battery_percentage_decrease = ((self.demands[-1]*(timestep_size/60.0))/self.battery.get_battery_capacity()) * 100.0

            real_battery_percentage_decrease = min(self.battery.get_current_battery_percentage(), expected_battery_percentage_decrease)
            uncontrollable = - real_battery_percentage_decrease* self.battery.get_battery_capacity()*60/ (timestep_size*100)

            remained_battery_percentage = max(0, self.battery.get_current_battery_percentage() - expected_battery_percentage_decrease)
             
            self.battery.set_current_battery_percentage(remained_battery_percentage)
            self.demand_bounds.update_bounds(self.demands[-1])
            penalty_factor = 5*(100-remained_battery_percentage)/100

            self.actionFour += 1

            return [self.demands[-1], uncontrollable, penalty_factor]
        else:
            raise AssertionError("I don't know why this is happening")

    # def update_demand_bounds(self, demand):
    #     if not demand <= 0:
    #         self.min_demand = min(self.min_demand, demand)
    #     self.max_demand = max(self.max_demand, demand)
    #
    # def get_demand_bounds(self):
    #     return [self.min_demand, self.max_demand]

    def get_demand_ranges(self):
        return self.demand_ranges

    def get_battery(self):
        return self.battery

    def get_demands(self):
        return self.demands

    def get_loadID(self):
        return self.loadID

    def is_with_agent(self):
        return self.with_agent

    def get_costs(self):
        return self.costs
    
    def reset_daily_balance(self):
        self.daily_balance = 100
    
    def get_daily_balance(self):
        return self.daily_balance

    def set_demand_ranges(self, demand_ranges):
        self.demand_ranges = demand_ranges

    def set_battery(self, battery):
        self.battery = battery

    def set_loadID(self, loadID):
        self.loadID = loadID

    def set_demands(self, demands):
        self.demands = demands

    def set_with_agent(self, with_agent):
        self.with_agent = with_agent

    def set_costs(self, costs):
        self.costs = costs

    # random batteriyi kullanma
    def reset_day(self, battery_reset = False):

        self.demands = get_last_k(self.demands, self.look_ahead)
        self.costs = get_last_k(self.costs, self.look_ahead)
        # print("actionOne" ,self.actionOne, "actionTwo", self.actionTwo, "actionThree", self.actionThree, "actionFour", self.actionFour)
        if battery_reset is True:
            None
            # self.battery.set_current_battery_percentage(100*random())
        elif isinstance(battery_reset,int) or isinstance(battery_reset, float):
            None
            # self.battery.set_current_battery_percentage(battery_reset)

    def set_look_ahead(self, look_ahead):
        self.look_ahead = look_ahead

    def get_look_ahead(self):
        return self.look_ahead

    def sample_action(self):
        return Load.action_space[randint(0,len(Load.action_space))]
    
    def generate_demand(self, upper_bound, lower_bound):
        return random()*(upper_bound - lower_bound) + lower_bound
    
    def demand_graph(self, demands):
        plt.plot(demands, 'g', linewidth=1.0)
        plt.show()
        None

    def demand_reshape(self, demands):
        temp_arr = np.zeros(12*(len(demands)))
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
                        
                    temp_diff = self.generate_demand(max(demands[j+1],demands[j]), min(demands[j+1],demands[j]))
                    temp_arr[i] = demands[j]
                    

                    j += 1
                    
                except:
                    #print('Invalid Index!')
                    None
            else:
                temp_arr[i] = temp_arr[int(i/12)] + self.generate_demand(max(temp_diff,0), min(temp_diff,0))


        return temp_arr