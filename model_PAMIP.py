"""File Name: model_PAMIP.py
MIP Model formulation of PA-MIP
Purpose of this function: Build optimization model and ensure Model-data separation
Input: Weight vectors of decision variables in the objective function, sets and indices of the variables, and related input data
Output: Decision variables of the model and their attributes
Usage: This function will be called inside main.py to invoke the necessary optimization model using data in that Python code.

Developer: Tanmoy Das
Date: Dec 2022

"""
# %% Model
"""### Model Deployment
 We now determine the MIP model for the facility location problem, by defining the decision variables, constraints, and objective function. Next, we start the optimization process and Gurobi finds the plan to build facilities that minimizes total costs.
"""
# import libraries
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import custom_functions as func


def solve(W, coordinates_st, coordinates_spill, pairings, SizeSpill, Sensitivity, TimeR, NumberStMax, m, spill_data):
    # Organizing data
    w1 = W[0];
    w2 = W[1];
    w3 = W[2]
    num_facilities = len(coordinates_st);
    num_customers = len(coordinates_spill)  # rename customer

    # MIP  model formulation
    model = gp.Model('model PA-MIP')
    # Decision variables
    cover = model.addVars(pairings, vtype=GRB.BINARY, name='Cover')
    select = model.addVars(num_facilities, vtype=GRB.BINARY, name='Select')
    amount = model.addVars(pairings, vtype=GRB.CONTINUOUS, lb=0, name='Amount')
    # Objective function

    if m == 'm1':
        objective_m1 = gp.quicksum(
            (SizeSpill[c] + Sensitivity[c] - TimeR[c, f]) * cover[c, f]
            for c, f in pairings)
        print('m:', m)
        model.setObjective(objective_m1, GRB.MAXIMIZE)
    elif m == 'm2':
        objective_m1 = gp.quicksum(
            (w1 * SizeSpill[c] + w2 * Sensitivity[c] - w3 * TimeR[c, f]) * cover[c, f]
            for c, f in pairings)
        print('m:', m)
        model.setObjective(objective_m1, GRB.MAXIMIZE)
    """
    objective_m1 = gp.quicksum(
        (w1 * sc1 * Demand[c] + w2 * sc2 * Sensitivity[c] - w3 * sc3 * TimeR[c, f]) * cover[c, f]
        for c, f in pairings)
    model.setObjective(objective_m1, GRB.MAXIMIZE)
    """
    # Constraints
    c1 = model.addConstrs((cover[c, f] <= select[f] for c, f in pairings), name='c1')

    c2 = model.addConstr((gp.quicksum(select[f] for f in range(num_facilities)) == NumberStMax), name='c2')

    c3 = model.addConstrs((cover.sum(c, '*') <= 1 for c in range(num_customers)), name='c3')



    model.write('Outputs/model PA-MIP.lp')
    model.optimize()

    # %% Analyse model
    # Obtain model results & carry them outside of the model scope
    mvars = model.getVars()  # these values are NOT accessible outside of the model scope
    names = model.getAttr('VarName', mvars)
    values = model.getAttr('X', mvars)

    # def extract_ones_DV(model, cover, select, amount, spill_data):
    cover_series = pd.Series(model.getAttr('X', cover))
    cover_1s = cover_series[cover_series > 0.5]
    select_series = pd.Series(model.getAttr('X', select))
    select_1s = select_series[select_series > 0.5]

    cover_1s_df = cover_1s.reset_index()
    cover_1s_df.rename(columns={'level_0': 'Spill #', 'level_1': 'Station no.'}, inplace=True)
    # Demand_df = pd.DataFrame(spill_data[['Resource needed']]) #DS1
    Demand_df = pd.DataFrame(SizeSpill)
    Demand_df.columns=['Resource needed'] # dont need this for DS1
    Demand_df['Spill #'] = Demand_df.index

    amountSt = pd.merge(cover_1s_df, Demand_df)
    amountSt_groupby = amountSt.groupby(by="Station no.").sum()
    # normalize amount in each station
    amountSt_groupby['amountSt_display'] = 800 * amountSt_groupby['Resource needed'] / (
        amountSt_groupby['Resource needed'].max())

    # Calculate Coverage
    coverage_percentage = int(100 * len(cover_1s) / len(SizeSpill))

    # Extract assignment variables
    sol_y = pd.Series(model.getAttr('X', cover))
    sol_y.name = 'Assignments'
    sol_y.index.names = ['Spill #', 'Station no.']
    assignment = sol_y[sol_y > 0.5].to_frame()
    assignment_name = assignment.reset_index()

    # organize data
    spill_df = pd.DataFrame(coordinates_spill, columns=['Spill_Latitude', 'Spill_Longitude']).reset_index()  # only 3 columns
    # spill_df['Resource needed'] = spill_data['Resource needed'] # DS1
    spill_df['Resource needed'] = pd.DataFrame(SizeSpill)

    station_df = pd.DataFrame(coordinates_st, columns=['St_Latitude', 'St_Longitude']).reset_index()  # only 3 columns
    spill_df.rename(columns={'index': 'Spill #'}, inplace=True)
    station_df.rename(columns={'index': 'Station no.'}, inplace=True)

    assignment2 = pd.merge(assignment_name.reset_index()[['Spill #', 'Station no.']],
                           station_df[['Station no.', 'St_Latitude', 'St_Longitude']])
    #df_temp = spill_df[['Spill #', 'St_Latitude', 'St_Longitude']]
    #df_temp.rename(columns={'Extracted_1': 'Spill_Latitude', 'Extracted_2': 'Spill_Longitude'}, inplace=True)

    assignment3 = pd.merge(assignment2, spill_df[['Spill #', 'Spill_Latitude', 'Spill_Longitude']])

    # Calculate total distance travelled
    DistanceTravelled = []
    for i in range(len(assignment3)):
        st_coord = (assignment3[['St_Latitude', 'St_Longitude']]).iloc[i, :].values
        sp_coord = (assignment3[['Spill_Latitude', 'Spill_Longitude']]).iloc[i, :].values
        aaa = DistanceTravelled.append(func.compute_distance(st_coord, sp_coord))
    DistanceTravelled = sum(DistanceTravelled) # Section 4.1 response time equation ; paragraph inline
    ResponseTimeT = int(DistanceTravelled / 60)

    return model, cover, select, amount, mvars, names, values, \
           cover_1s, select_1s, amountSt_groupby, coverage_percentage, \
           ResponseTimeT, assignment3, spill_df, station_df, \
            sol_y, assignment, assignment2, assignment_name
