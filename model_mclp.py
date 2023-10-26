""" Traditional MCLP model 
Implementation of MCLP model (presented in equation [12] in the last paragraph of Section 2.2 and compared with proposed model in Section 3.2 of the paper). 

Output: Figure 9 is the output of this model.

Outline:

1. Define Decision variables
2. Add Constraints
3. Add objective functions
4. Set some gurobi parameters, & write the model
5. Solve the model
6. Write log file
7. Get some variables out of the model for further analysis

Developer: Tanmoy Das
Date: Aug 18, 2023
"""

# %% Data
# data processing libraries
import pandas as pd
from datetime import datetime, date
# optimization
import gurobipy as gp
from gurobipy import GRB
# import custom functions or classes
import custom_func
import math


# %% Model 2: MIP-2
def solve(Stations, OilSpills, ResourcesD, coordinates_st, coordinates_spill, SizeSpill, SizeSpill_n,
          Demand, Sensitivity_R, Sensitivity_n, Eff, Effectiveness_n, Availability, NumberStMax, Distance, Distance_n,
          W, QuantityMin, DistanceMax, Cf_s, CostU, Budget,
          BigM, MaxFO):
    """
    :param Stations:
    :param OilSpills:
    :param ResourcesD:
    :param coordinates_st:
    :param coordinates_spill:
    :param SizeSpill:
    :param SizeSpill_n:
    :param Demand:
    :param Sensitivity_R:
    :param Sensitivity_n:
    :param Eff:
    :param Effectiveness_n:
    :param Availability:
    :param NumberStMax:
    :param Distance:
    :param Distance_n:
    :param W:
    :param QuantityMin:
    :param DistanceMax:
    :param Cf_s:
    :param CostU:
    :param Budget:
    :param BigM:
    :param MaxFO:
    :return:
    """

    import gurobipy as gp
    from gurobipy import GRB
    from datetime import datetime, date

    w1, w2, w3, w4, w5, w6 = W[0], W[1], W[2], W[3], W[4], W[5]

    # ---------------------------------------- Set & Index -------------------------------------------------------------
    os_pair = {(o, s): custom_func.compute_distance(coordinates_spill[1][o], coordinates_st[1][s])
               for o in OilSpills
               for s in Stations
               if
               custom_func.compute_distance(tuple(coordinates_spill[1][o]), tuple(coordinates_st[1][s])) < DistanceMax}
    os_pair = tuple(os_pair.keys())

    # sr_pair (based on unique stations in pair_os )
    st_o = list(set([item[1] for item in os_pair]))
    o_st = list(set([item[0] for item in os_pair])) # unique oil spills
    print('len of OilSpills: ', len(OilSpills))
    sr_pair = []
    for s in st_o:
        for r in ResourcesD:
            sr_pair.append((s, r))
    sr_pair = tuple(sr_pair)

    osr_pair = {(o, s, r): custom_func.compute_distance(coordinates_spill[1][o], coordinates_st[1][s])
                for o in OilSpills
                for s in Stations
                for r in ResourcesD
                if
                custom_func.compute_distance(tuple(coordinates_spill[1][o]), tuple(coordinates_st[1][s])) < DistanceMax}
    osr_pair = tuple(osr_pair.keys())

    print('--------------MIP-moo--------')
    model = gp.Model("MIP-moo-LAMOSCAD")
    # ---------------------------------------- Decision variable -------------------------------------------------------
    cover = model.addVars(os_pair, vtype=GRB.BINARY, name='cover')  # OilSpills
    select = model.addVars(st_o, vtype=GRB.BINARY, name='select')
    deploy = model.addVars(osr_pair, vtype=GRB.CONTINUOUS, lb=0,
                           name='deploy')  # QuantityMin Minimum quantity constraint ++

    # print('cover'); print(cover); print(''); print('select'); print(select); print(''); print('deploy'); print(deploy)

    # %% ----------------------------------------------------------------------------------------------------------------
    # ------------------------------------------------ Constraints -----------------------------------------------------

    # ---------------------------------------- Coverage constraints (cover) --------------------------------------------

    # C10: facility must be open to cover oil spill
    C_open_facility_to_cover = model.addConstrs((cover[o, s] <= select[s]
                                                 for o, s in os_pair), name='C_open_facility_to_cover')
                                                 
    C_few_facility_per_spill = model.addConstrs((cover.sum(o, '*') <= 1
                                               for o, s in os_pair), name='C_few_facility_per_spill')  
    ## Although this constraint does not exist in traditional MCLP model, without this one, each demand is assigned to multiple facilites, which we dont want.
    
    # C11: max number of facilities to be open
    C_max_facility = model.addConstr((gp.quicksum(select[s]
                                                  for s in st_o) <= NumberStMax), name='C_max_facility')
    ## == condition in this constraint will make the model infeasible, <= has the expected outcome for the given problem.

    # %% ----------------------------------------------------------------------------------------------------------------
    # ----------------------------------------------- Objective function -----------------------------------------------
    model.ModelSense = GRB.MAXIMIZE
    objective_1 = gp.quicksum((w1 * SizeSpill_n[o]) * cover[o, s]
                              for o, s in os_pair)
    model.setObjective(objective_1)

    # %% Model parameters
    # Organizing model
    # Limit how many solutions to collect
    model.setParam(GRB.Param.PoolSolutions, 1024)
    # Limit the search space by setting a gap for the worst possible solution that will be accepted
    model.setParam(GRB.Param.PoolGap, 0.80)
    # do a systematic search for the k-best solutions
    # model.setParam(GRB.Param.PoolSearchMode, 2)
    today = date.today()
    now = datetime.now()
    date_time = str(date.today().strftime("%b %d,") + datetime.now().strftime("%H%M"))
    filename = 'model (' + date_time + ')'

    # Write the model
    model.write(f'Outputs/Logfiles/model_moo.lp')
    model.Params.LogFile = f"Outputs/Logfiles/model_moo({date_time}).log"  # write the log file

    # %% Solve the model
    model.optimize()
    # Debugging model
    # model.computeIIS()
    model.write('Outputs/Logfiles/model_moo.sol')

    # %% Query number of multiple objectives, and number of solutions
    x = model.getVars()
    select_series = pd.Series(model.getAttr('X', select))
    deploy_series = pd.Series(model.getAttr('X', deploy))
    # select_series[select_series > 0.5]  # +++
    # deploy_series[deploy_series > 0.5]
    nSolutions = model.SolCount
    nObjectives = model.NumObj
    print('Problem has', nObjectives, 'objectives')
    print('Gurobi found', nSolutions, 'solutions')
    solutions = []
    for s in range(nSolutions):
        # Set which solution we will query from now on
        model.params.SolutionNumber = s

        # Print objective value of this solution in each objective
        print('Solution', s, ':', end='')

    for j in range(len(x)):
        if x[j].Xn > 0:
            print(x[j].VarName, x[j].Xn, end=' ')
            print(' ')

    # %% Output the result
    # Obtain model results & carry them outside the model scope
    model.printAttr('X')
    mvars = model.getVars()  # these values are NOT accessible outside the model scope
    names = model.getAttr('VarName', mvars)
    values = model.getAttr('X', mvars)  # X Xn https://www.gurobi.com/documentation/9.5/refman/working_with_multiple_obje.html

    objValues = []
    nSolutions = model.SolCount
    nObjectives = model.NumObj
    for s in range(nSolutions):
        # Set which solution we will query from now on
        model.params.SolutionNumber = s
        print('Solution', s, ':', end='')

    cover_series = pd.Series(model.getAttr('X', cover))
    cover_1s = cover_series[cover_series > 0.5]

    select_series = pd.Series(model.getAttr('X', select))
    select_1s = select_series[select_series > 0.5]
    # print('\nselect_1s\n', select_1s)
    deploy_series = pd.Series(model.getAttr('X', deploy))
    deploy_1s = deploy_series[deploy_series > 0.5]
    # print('\ndeploy_1s\n', deploy_1s)
    cover_series = pd.Series(model.getAttr('X', cover))
    cover_1s = cover_series[cover_series > 0.5]
    # print('\ncover_1s\n', cover_1s)

    # Saving the file
    modelStructure_output_code = python_code = logfile = model_structure = outputs = inputs = ""
    # Reading data from files
    with open('Outputs/Logfiles/model_moo.lp') as fp:
        model_structure = fp.read()
    with open('Outputs/Logfiles/model_moo.sol') as fp:
        outputs = fp.read()
    with open(f'Outputs/Logfiles/model_moo({date_time}).log') as fp:
        logfile = fp.read()
    with open('model.py') as fp:
        python_code = fp.read()
    # Merging 2 files
    # To add the data of file2
    # from next line
    modelStructure_output_code += "------------------------------- Model Structure ----------------------------------\n"
    modelStructure_output_code += model_structure
    modelStructure_output_code += "\n------------------------------- Model Outputs ----------------------------------\n"
    modelStructure_output_code += outputs
    modelStructure_output_code += "\n------------------------------- Model logfile ----------------------------------\n"
    modelStructure_output_code += logfile
    modelStructure_output_code += "\n------------------------------- Python Code ------------------------------------\n"
    modelStructure_output_code += python_code

    with open(f'Outputs/Logfiles/Structure, outputs & python code of {filename}.txt', 'w') as fp:
        fp.write(modelStructure_output_code)

    # Extract assignment variables
    sol_y = pd.Series(model.getAttr('X', cover)) #++ deploy is replaced with cover
    sol_y.name = 'Assignments'
    sol_y.index.names = ['Spill #', 'Station no.']
    assignment4 = sol_y[sol_y > 0.5].to_frame()
    assignment_name = assignment4.reset_index()
    print('assignment_name', assignment_name)

    # %%
    # organize data # need to clean this section ++
    spill_df = pd.DataFrame(coordinates_spill[1]).T.reset_index()
    spill_df.columns = ['Spill #', 'Spill_Latitude', 'Spill_Longitude']
    spill_df['Resource needed'] = pd.DataFrame(SizeSpill)  # ++ update with spill size later
    spill_df['Sensitivity'] = Sensitivity_R  # ++

    station_df = pd.DataFrame(coordinates_st[1]).T.reset_index()
    station_df.columns = ['Station no.', 'St_Latitude', 'St_Longitude']

    assignment2 = pd.merge(assignment_name[['Spill #', 'Station no.']],
                           station_df[['Station no.', 'St_Latitude', 'St_Longitude']])

    assignment3 = pd.merge(assignment2, spill_df[['Spill #', 'Spill_Latitude', 'Spill_Longitude']])
    cover_reset = cover_1s.reset_index()
    cover_reset.columns = ['Spill #', 'Station no.',  'Quantity deployed']
    assignment = pd.merge(assignment3, cover_reset)

    assignment['Distance'] = [math.sqrt((assignment.loc[i]['St_Latitude'] - assignment.loc[i]['Spill_Latitude']) ** 2 \
                                        + (assignment.loc[i]['St_Longitude'] - assignment.loc[i][
        'Spill_Longitude']) ** 2)
                              for i in assignment.index]

    # Outputs from the model +++
    # Calculate Coverage # chance later ++
    coverage_percentage = int(100 * len(cover_1s)/ len(OilSpills))  # / len(cover_series)
    # Calculate total distance travelled
    DistanceTravelled = []
    for i in range(len(assignment)):
        st_coord = (assignment[['St_Latitude', 'St_Longitude']]).iloc[i, :].values
        sp_coord = (assignment[['Spill_Latitude', 'Spill_Longitude']]).iloc[i, :].values
        aaa = DistanceTravelled.append(custom_func.compute_distance(st_coord, sp_coord))

    DistanceTravelled = sum(DistanceTravelled)*80  # 80 for convering GIS data into kilometer
    ResponseTimeM = round((DistanceTravelled / 60) / len(assignment), 2)  # len() +++ OilSpills
    print(f'Coverage Percentage: {coverage_percentage}%')
    print(f'Mean Response Time: {ResponseTimeM}')

    return model, select, deploy, mvars, names, values, objValues, \
        spill_df, station_df, cover_1s, select_1s, deploy_1s, ResponseTimeM, coverage_percentage, assignment
