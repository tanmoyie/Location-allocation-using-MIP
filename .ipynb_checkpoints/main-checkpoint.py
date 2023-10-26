"""
File name: main.py
THis file will import data, call the optimization model, provide optimization result
Input data, then, run the optimization model

Outline:
1. Estimating input parameters
2.
3. Mdeling
4. Sensitivity analysis
5.

Developer: Tanmoy Das
Date: Dec 2022
"""
# %%
globals().clear()  # Clear previous workspace
# import library
import pandas as pd
import geopandas as gpd
import custom_functions, data_visualization
import model_PAMIP, model_analysis
import shapely
import numpy as np
from sklearn.cluster import MiniBatchKMeans


# import data
spill_data = pd.read_excel('Inputs/data_PAMIP.xlsx', sheet_name='spills', header=0).copy()
station_data = pd.read_excel('Inputs/data_PAMIP.xlsx', sheet_name='stations', header=0).copy()
sensitivity_dataR = gpd.read_file('Inputs/ArcGIS_data/Sensitivity_data5.shp').copy()
# %% Input parameters of the model
# ++ think what is same across all model and scenes , move them at the top+++
# pre-determined inputs
NumberStMax = 5
DistanceMax = 10  # 5


coordinates_spill = custom_functions.extract_coordinate(spill_data)
coordinates_st = custom_functions.extract_coordinate(station_data)
num_customers = len(coordinates_spill)
num_facilities = len(coordinates_st)

# ++ convert 10 into km using google map (for reporting, not related to modeling in this code)
coor1 = (63.31720065616187, -90.65327442130385)
coor2 = (61.99735832040513, -92.36804572739923)
custom_functions.compute_distance(coor1, coor2)


#%%
pairings = {(c, f): custom_functions.compute_distance(coordinates_spill[c], coordinates_st[f])
            for c in range(num_customers)
            for f in range(num_facilities)
            if custom_functions.compute_distance(tuple(coordinates_spill[c]), tuple(coordinates_st[f])) < DistanceMax}


print("Number of viable pairings: {0}".format(len(pairings.keys())))

# Weights and scaling
# W = [1, 2000, 1]
max_spill_size = max(spill_data['Spill size'])
max_sensitivity = max(sensitivity_dataR['Sensitivit'])
max_timeR = pairings[max(pairings, key=pairings.get )]
min_spill_size = min(spill_data['Spill size'])
min_sensitivity = min(sensitivity_dataR['Sensitivit'])
min_timeR = pairings[min(pairings, key=pairings.get )]

# x* = (x-x_min)/(x_max - x_min)

#Demand = list(spill_data['Resource needed']).copy()

SizeSpill_R = list(spill_data['Spill size']).copy()
Sensitivity_R = custom_functions.calculate_sensitivity(coordinates_spill, sensitivity_dataR)
TimeR_R = pairings.copy()  # compute_TimeR +++

#%% Normalize terms in objective function
SizeSpill = []; Sensitivity = []; TimeR = []
SizeSpill = [((SizeSpill_R[i]-min_spill_size)/(max_spill_size-min_spill_size)) for i in range(len(SizeSpill_R))]
Sensitivity = [((Sensitivity_R[i]-min_sensitivity)/(max_sensitivity-min_sensitivity)) for i in range(len(Sensitivity_R))]

# TimeR = {((list(TimeR_R.values())[i]-min_timeR)/(max_timeR-min_timeR)) for i in range(len(TimeR_R))}
TimeR_Scaled = [((list(TimeR_R.values())[i]-min_timeR)/(max_timeR-min_timeR)) for i in range(len(TimeR_R))]
keysD = TimeR_R.keys()
TimeR = {}
for i in range(len(keysD)):
    TimeR[list(keysD)[i]] = TimeR_Scaled[i]
# %% Predictive Analytics
# Tradeoff curve for number of stations
# ----------------------------------------------------------------------------------------------------------------------
NumberStMax_list = [1,2,3,4 ,5,6,7,8,9,10]
W1 = [[0.1, 0.2, 0.7], [0.8, 0.1, 0.1]] # from model configuration table
Tradeoff_output = []
for i in range(len(NumberStMax_list)):
    Wi = W1[1]
    NumberStMax = NumberStMax_list[i]
    m = 'm1' # m2
    model, cover, select, amount, mvars, names, values, \
               cover_1s, select_1s, amountSt_groupby, coverage_percentage, \
               ResponseTimeT, assignment3, spill_df, station_df,  \
                sol_y, assignment, assignment2, assignment_name= model_PAMIP.solve(Wi, coordinates_st, coordinates_spill,
                                               pairings, SizeSpill, Sensitivity, TimeR, NumberStMax, m, spill_data)

    Tradeoff_output.append([NumberStMax, coverage_percentage, int(ResponseTimeT*80)/11])

Tradeoff_Output_df = pd.DataFrame(Tradeoff_output)
Tradeoff_Output_df.columns = ['NumberStMax', 'Coverage %', 'Response time (in hours)']
Tradeoff_Output_df.to_csv('Outputs/Tradeoff_Output_df.csv')

#%% Draw the tradeoff line graph
NumberStMax_data = pd.read_csv('Outputs/Tradeoff_Output_df.csv').copy()
selected = 5
data_visualization.draw_tradeoff_plot(NumberStMax_data, selected)




#%% Model configurations and solutions table
# ----------------------------------------------------------------------------------------------------------------------
# Comparing models with different weight vectors
import random
values = [.1, .2, .3, .4, .5, .6, .7, .8]
Wd = []
for i in range(1000):
    w1 = random.choice(values); w2 = random.choice(values); w3 = random.choice(values)
    if w1+w2+w3 == 1.0:
        Wd.append([w1, w2, w3])
# drop duplication values from list W
W_Set = set(tuple(element) for element in Wd)
W0 = [list(t) for t in set(tuple(element) for element in W_Set)]

W = [W0[i] for i in range(10)]

#%%
m = 'm2'
model_output = []
# Draw Network Diagram
for i in range(5):
    Wi = W[i]
    model, cover, select, amount, mvars, names, values, \
    cover_1s, select_1s, amountSt_groupby, coverage_percentage, \
    ResponseTimeT, assignment3, spill_df, station_df, \
    sol_y, assignment, assignment2, assignment_name = model_PAMIP.solve(Wi, coordinates_st, coordinates_spill,
                                                                        pairings, SizeSpill, Sensitivity, TimeR,
                                                                        NumberStMax, m, spill_data)

    print(f'coverage_percentage: {coverage_percentage}, i: {i}')
    model_output.append([Wi, model.ObjVal, coverage_percentage, int(ResponseTimeT*80)/11])
    print('-------------------------------------------------------------')
Model_Output = pd.DataFrame(model_output)
Model_Output.columns = ['Weights', 'Objective Value', 'Coverage %', 'Response time (in hours)']
Model_Output.to_csv('Outputs/Model_Output.csv')

# %% Draw Network Diagram
# ----------------------------------------------------------------------------------------------------------------------
# Examine model results
# Sensitivity analysis

W1 = [[0.1, 0.2, 0.7], [0.8, 0.1, 0.1]] # from model configuration table
for i in range(2):
    Wi = W1[i]
    m = 'm2' # m2
    model, cover, select, amount, mvars, names, values, \
               cover_1s, select_1s, amountSt_groupby, coverage_percentage, \
               ResponseTimeT, assignment3, spill_df, station_df,  \
                sol_y, assignment, assignment2, assignment_name= model_PAMIP.solve(Wi, coordinates_st, coordinates_spill,
                                               pairings, SizeSpill, Sensitivity, TimeR, NumberStMax, m, spill_data)

    model_analysis.draw_network_diagram(DistanceMax, NumberStMax, spill_df, station_df, ResponseTimeT, coverage_percentage,
                                        assignment3, cover_1s, select_1s, amountSt_groupby, m, Wi)

#%%
# Feb 20
import folium
gdb1 = gpd.read_file('C:/Users/tanmo/Downloads/lpr_000b21f_e/lpr_000b21f_e.gdb')
gdb1.plot()
# Draw empty map +++
# map_shipping_spill = folium.Map(location=spill_coordinates.iloc[0], zoom_start=4, min_zoom=2.5, max_zoom=7)
# Draw the Shipping route
# map_shipping_spill.choropleth(geo_data="Inputs/ArcGIS_data/Shipping_and_Hydrography.geojson")

# save this map as transparent .svg of jpg file , then import it as .svg file to matplotlib
#+++
#%% Data Scene 2
#%% Clustering
# ----------------------------------------------------------------------------------------------------------------------
# %%
globals().clear()  # Clear previous workspace
# import library
import pandas as pd
import geopandas as gpd
import custom_functions, data_visualization
import model_PAMIP, model_analysis
import shapely
import numpy as np
from sklearn.cluster import MiniBatchKMeans


# import data
spill_data = pd.read_excel('Inputs/data_PAMIP.xlsx', sheet_name='spills', header=0).copy()
station_data = pd.read_excel('Inputs/data_PAMIP.xlsx', sheet_name='stations', header=0).copy()
sensitivity_dataR = gpd.read_file('Inputs/ArcGIS_data/Sensitivity_data5.shp').copy()
# %% Input parameters of the model
# ++ think what is same accross all model and scenes , move them at the top+++
# pre-determined inputs
NumberStMax = 5
DistanceMax = 10 # 5

coordinates_spill = custom_functions.extract_coordinate(spill_data)
coordinates_st = custom_functions.extract_coordinate(station_data)
num_customers = len(coordinates_spill)
num_facilities = len(coordinates_st)

import numpy as np
# Import excel file (containing 10k records)
spill_data_10000 = pd.read_excel('Inputs/Spill_info_4000.xlsx', header=0).copy()
# randomly select 2k records
spill_data_scene2 = spill_data_10000.sample(n=2000)
spill_size = spill_data_scene2[['Spill size']]

coordinates_spill = custom_functions.extract_coordinate(spill_data_scene2)
# Cluster them into 50 cluster
num_clusters = 50
kmeans = MiniBatchKMeans(n_clusters=num_clusters, init_size=3*num_clusters,
                         ).fit(coordinates_spill)
memberships = list(kmeans.labels_)
centroids = list(kmeans.cluster_centers_) # Center point for each cluster
weights = list(np.histogram(memberships, bins=num_clusters)[0]) # Number of customers in each cluster
print('First cluster center:', centroids[0])
print('Weights for first 10 clusters:', weights[:10])

# Draw
icon_size_list = []
# Draw the oil spills
for point_spill in range(0, len(coordinates_spill)):
    icon_size = int((spill_size.iloc[point_spill, 0]/spill_size.max())*20)
    icon_size_list.append(icon_size)

data_visualization.draw_cluster(icon_size_list, coordinates_spill, memberships, centroids)

#%% Apply optimization model
# Input parameters
coordinates_spill = kmeans.cluster_centers_.tolist()
pairings = custom_functions.compute_pairing(coordinates_spill, coordinates_st, DistanceMax)
Size_DS1 = list(spill_data_scene2['Spill size']).copy()


#%%
cluster_index = {}
for j in range(len(centroids)):
    cluster_index[j] = [i for i, x in enumerate(memberships) if x == j]
SizeSpill_Rc = [sum([e for i, e in enumerate(Size_DS1) if i in cluster_index[ii]]) for ii in range(len(cluster_index))]
Sensitivity_Rc = custom_functions.calculate_sensitivity(coordinates_spill, sensitivity_dataR)
TimeRc = pairings.copy()

max_spill_size = max(SizeSpill_Rc)
min_spill_size = min(SizeSpill_Rc)

max_sensitivity = max(Sensitivity_Rc)
min_sensitivity = min(Sensitivity_Rc)

max_timeR = pairings[max(pairings, key=pairings.get )]
min_timeR = pairings[min(pairings, key=pairings.get )]

SizeSpill = []; Sensitivity = []; TimeR = [];
SizeSpill = [((SizeSpill_Rc[i]-min_spill_size)/(max_spill_size-min_spill_size)) for i in range(len(SizeSpill_Rc))]
Sensitivity = [((Sensitivity_Rc[i]-min_sensitivity)/(max_sensitivity-min_sensitivity)) for i in range(len(Sensitivity_Rc))]

# TimeR = {((list(TimeR_R.values())[i]-min_timeR)/(max_timeR-min_timeR)) for i in range(len(TimeR_R))}
TimeR_Scaled = [((list(TimeRc.values())[i]-min_timeR)/(max_timeR-min_timeR)) for i in range(len(TimeRc))]
keysD = TimeRc.keys()
TimeR = {}
for i in range(len(keysD)):
    TimeR[list(keysD)[i]] = TimeR_Scaled[i]



m = 'm2'
spill_data = spill_data_scene2


#%%
# Solve the model
W1 = W #[[0.1, 0.2, 0.7], [0.2, 0.7, 0.1]] # from model configuration table
for i in range(10):
    Wi = W1[i]
    m = 'm2' # m2
    model, cover, select, amount, mvars, names, values, \
               cover_1s, select_1s, amountSt_groupby, coverage_percentage, \
               ResponseTimeT, assignment3, spill_df, station_df,  \
                sol_y, assignment, assignment2, assignment_name= model_PAMIP.solve(Wi, coordinates_st, coordinates_spill,
                                               pairings, SizeSpill, Sensitivity, TimeR, NumberStMax, m, spill_data_scene2)

    model_analysis.draw_network_diagram(DistanceMax, NumberStMax, spill_df, station_df, ResponseTimeT, coverage_percentage,
                                        assignment3, cover_1s, select_1s, amountSt_groupby, m, Wi)
