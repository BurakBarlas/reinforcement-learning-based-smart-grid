from Environment import Environment
from QTableAgent import QTableAgent
import time, os
import numpy as np
import pickle
from Utils import create_model_path
from constants import *


mode = 'vanilla'
num_days = 360

agent_params_dict = {
RANDOMIZE_BATTERY: True,
LEARNING_RATE : 0.1,
DISCOUNT_FACTOR : 0.95,
NUM_DUM_LOADS : 999,MODE : mode,
STATES : ['b101','d15','p10'],
MOVING_BUCKETS : True,
BALANCE_AMOUNT : 500
#CONSTANT_DEMAND = False

#PENALTY_FACTOR = 0.5
}


MODEL_PATH = create_model_path(agent_params_dict)



def setup():
    env = Environment()
    env.add_connections({0:[0]})
    env.add_dumb_loads(0,agent_params_dict[NUM_DUM_LOADS])
    env.set_environment_ready()
    env.reset(agent_params_dict[RANDOMIZE_BATTERY])
    load_agent_dict = {0:QTableAgent(env.get_load_action_space(),
                                     {LOAD_BATTERY_STATE:[0,100],LOAD_PRICE_STATE:env.get_price_bounds(0),
                                      #LOAD_MEAN_BATTERY_STATE:env.get_battery_bounds(0)[0],
                                      #LOAD_VARIANCE_BATTERY_STATE:env.get_battery_bounds(0)[1],
                                      LOAD_DEMAND_STATE:env.get_demand_bounds(0)
                                      },
                                     {LOAD_BATTERY_STATE:101, LOAD_PRICE_STATE:10,
                                      #LOAD_MEAN_BATTERY_STATE:10,
                                      #LOAD_VARIANCE_BATTERY_STATE:10,
                                      LOAD_DEMAND_STATE:15
                                     },
                                     default_action=1,
                                     discount_factor=agent_params_dict[DISCOUNT_FACTOR],
                                     moving_buckets= agent_params_dict[MOVING_BUCKETS]
                                    )}
    load_agent_dict[0].set_learning_rate(agent_params_dict[LEARNING_RATE])
    load_agent_dict[0].exploration_decay_constant = num_days/10
    return env, load_agent_dict


def train(startday=0, endday=num_days):
    start=time.time()
    total_cost = 0
    monthly_balances = []
    for day in range(startday, endday):
        
        states = []
        actions = []
        daily_balance = 0
        max_change = 0
        total_change = 0
        day_cost = 0
        max_change_state_action = []
        response = env.reset(agent_params_dict[RANDOMIZE_BATTERY])
        next_state = {LOAD_BATTERY_STATE: response[1][0][0][0],
                      LOAD_PRICE_STATE: response[1][0][0][1][-1],
                      #LOAD_MEAN_BATTERY_STATE: response[1][0][0][2],
                      #LOAD_VARIANCE_BATTERY_STATE: response[1][0][0][3],
                      LOAD_DEMAND_STATE: response[1][0][1][0]
                      }
        load_agent_dict[0].update_state(next_state)
        next_action = load_agent_dict[0].take_action()

        for step in range(env.get_max_timestep()+1):
            #for sourceID in env.source_dict.keys():
                #print('price',env.source_dict[sourceID].price_bounds.get_bounds())
            #print(env.get_current_timestep(),step)
            current_state = next_state
            current_action = next_action
            actions.append(current_action)
            response = env.step(loadActionDict={0:current_action})
            next_state = {LOAD_BATTERY_STATE: response[1][0][0][0],
                          LOAD_PRICE_STATE: response[1][0][0][1][-1],
                          #LOAD_MEAN_BATTERY_STATE: response[1][0][0][2],
                          #LOAD_VARIANCE_BATTERY_STATE: response[1][0][0][3],
                          LOAD_DEMAND_STATE: response[1][0][1][0]
                          }
            # print("cost", next_state)
            if(next_action == 0 or next_action == 1):
                day_cost += next_state[LOAD_PRICE_STATE] * next_state[LOAD_DEMAND_STATE]
            total_cost += day_cost
            states.append(current_state)
            if step%20==0:
                load_agent_dict[0].update_state(next_state, True)
            else:
                load_agent_dict[0].update_state(next_state, False)


            if mode == 'vanilla':
                change = abs(
                    load_agent_dict[0].update_qtable(
                        current_state=current_state, current_action=current_action,
                        reward= (-1)*(response[1][0][1][1])* response[1][0][1][2],#*
                               # sum(env.get_demand_bounds(0)) * response[1][0][1][1] * PENALTY_FACTOR *
                               # get_battery_reward_factor(current_action,
                               #                           current_state[LOAD_BATTERY_STATE]),
                               #                           current_state[LOAD_MEAN_BATTERY_STATE],
                               #                           current_state[LOAD_VARIANCE_BATTERY_STATE],
                               #                           load_agent_dict[0].bucket_bounds[LOAD_VARIANCE_BATTERY_STATE][1])),
                               #                           * 0.5),
                        mode=mode, next_state = next_state, #clip=[-100,100]
                    ))
                max_change = max(change, max_change) #response should be negative
                total_change += change
                next_action = load_agent_dict[0].take_action()
                #print(daily_balance)
                daily_balance += env.load_dict[0].get_daily_balance()

            elif mode == 'sarsa':
                next_action = load_agent_dict[0].take_action()
                max_change = max(abs(
                    load_agent_dict[0].update_qtable(
                        current_state=current_state, current_action=current_action,
                        reward = (-1) * (response[1][0][1][0]* response[1][0][1][1]), #+
                                 # sum(env.get_demand_bounds(0)) * response[1][0][1][1] *
                                 # get_battery_reward_factor(current_action,
                                 #                           current_state[LOAD_BATTERY_STATE],
                                 #                           current_state[LOAD_MEAN_BATTERY_STATE],
                                 #                           current_state[LOAD_VARIANCE_BATTERY_STATE],
                                 #                           load_agent_dict[0].bucket_bounds[LOAD_VARIANCE_BATTERY_STATE][1])/2),
                        next_state=next_state, next_action=next_action, mode=mode, #clip=[-25,25]  # clip the increments to a certain range
                    )), max_change)  # response should be negative


            max_change_state_action = [load_agent_dict[0].state,current_action]
        # print(day,'Ageof:',load_agent_dict[0].get_explore_rate(day),':',total_change,':',max_change,':',max_change_state_action,':',np.mean(load_agent_dict[0].qtable.max((-1))))
        # if max_change<0.001:
        #     break
        load_agent_dict[0].set_explore_rate(load_agent_dict[0].get_explore_rate(day))
        # load_agent_dict[0].set_learning_rate(load_agent_dict[0].get_learning_rate(day))
        if (day+1)%int(num_days/12)==0:
            load_agent_dict[0].update_policy()
            0.23557750793144008
            # np.save(MODEL_PATH+'/qtable_'+str(day),load_agent_dict[0].qtable)
            # np.save(MODEL_PATH+'/visitcounts_'+str(day),load_agent_dict[0].visit_counts)
            # np.save(MODEL_PATH+'/policy_'+str(day),load_agent_dict[0].policy)
            with open(MODEL_PATH+'/'+mode+'_agent_'+str(day)+'.pickle', 'wb') as f:
                pickle.dump(load_agent_dict[0], f)


        load_agent_dict[0].set_state_bounds({LOAD_BATTERY_STATE:[0,100],LOAD_PRICE_STATE:env.get_price_bounds(0),
                                      # LOAD_MEAN_BATTERY_STATE:env.get_battery_bounds(0)[0],
                                      # LOAD_VARIANCE_BATTERY_STATE:env.get_battery_bounds(0)[1],
                                      LOAD_DEMAND_STATE:env.get_demand_bounds(0)
                                                })
            # print(env.get_battery_bounds(0))
        if day-1%10==0:# and agent_params_dict[MOVING_BUCKETS]:
            load_agent_dict[0].update_bucket_bounds(moving_buckets=agent_params_dict[MOVING_BUCKETS])


    end = time.time()
    return end-start, total_cost, monthly_balances

env, load_agent_dict = setup()



timetaken, total_cost, monthly_balances = train(0, num_days)
#print(monthly_balances)