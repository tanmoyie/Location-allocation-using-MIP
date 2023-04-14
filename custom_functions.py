"""
File Name: custom_functions.py
All the custom functions related to data processing and optimizaiton modeling are written here
& called as module in main.py script
Function list
1. Compute Distance
2. Compute Pairings
3. Normalize
4. Extract Coordinate
5. Calculate Sensitivity

"""
# Compute distance
import math
import pandas as pd
from shapely.geometry import Point
import shapely
import geopandas as gpd


def compute_distance(loc1, loc2):
    dx = loc1[0] - loc2[0]
    dy = loc1[1] - loc2[1]
    return math.sqrt(dx * dx + dy * dy)


def compute_pairing(coordinates_spill, coordinates_st, DistanceMax):
    pairings = {(c, f): compute_distance(coordinates_spill[c], coordinates_st[f])
                for c in range(len(coordinates_spill))
                for f in range(len(coordinates_st))
                if compute_distance(tuple(coordinates_spill[c]), tuple(coordinates_st[f])) < DistanceMax}
    return pairings


def normalize():
    return 0


def compute_TimeR(pairings, spill_data):
    TimeR = pairings
    rank1 = spill_data[['1st Ranking']]
    for i in range(len(rank1)):
        if rank1[i] == "MCR":
            TimeR[i, :] = pairings[i, :]  # pairings values = distance
        elif rank1[i] == "CDU" or "ISB":
            TimeR[i, :] = pairings[i, :] / 10
    return TimeR


# Extract coordinates in right format
def extract_coordinate(data):
    # location of demands
    coordinates_in = data[['Coordinates']]  # .values.tolist()
    # preprocessing (what exactly?)
    temp_df2 = coordinates_in.Coordinates.str.split(",", expand=True, )
    temp_df2['Extracted_1'] = temp_df2[0].str.extract('([-+]?\d*\.?\d+)')
    temp_df2['Extracted_2'] = temp_df2[1].str.extract('([-+]?\d*\.?\d+)')
    temp_df2["Extracted_1"] = pd.to_numeric(temp_df2["Extracted_1"], downcast="float")
    temp_df2["Extracted_2"] = pd.to_numeric(temp_df2["Extracted_2"], downcast="float")
    # Getting coordinates of stations in a format needed for Folium MAP
    coordinates = temp_df2[['Extracted_1', 'Extracted_2']].values.tolist()
    return coordinates

# Extract coordinates in right format
def extract_spill_coordinate(data):
    # location of demands
    coordinates_in = data[['Coordinates']]  # .values.tolist()
    # preprocessing (what exactly?)
    temp_df2 = coordinates_in.Coordinates.str.split(",", expand=True, )
    temp_df2['Extracted_1'] = temp_df2[0].str.extract('([-+]?\d*\.?\d+)')
    temp_df2['Extracted_2'] = temp_df2[1].str.extract('([-+]?\d*\.?\d+)')
    temp_df2["Extracted_1"] = pd.to_numeric(temp_df2["Extracted_1"], downcast="float")
    temp_df2["Extracted_2"] = pd.to_numeric(temp_df2["Extracted_2"], downcast="float")
    # Getting coordinates of stations in a format needed for Folium MAP
    coordinates = temp_df2[['Extracted_1', 'Extracted_2']].values.tolist()
    coordinates_dict = {}
    for i in range(len(coordinates)):
        coordinates_dict[data.reset_index().at[i, 'Spill #']] = coordinates[i]
    return coordinates, coordinates_dict


# Extract coordinates in right format
def extract_station_coordinate(data):
    # location of demands
    coordinates_in = data[['Coordinates']]  # .values.tolist()
    # preprocessing (what exactly?)
    temp_df2 = coordinates_in.Coordinates.str.split(",", expand=True, )
    temp_df2['Extracted_1'] = temp_df2[0].str.extract('([-+]?\d*\.?\d+)')
    temp_df2['Extracted_2'] = temp_df2[1].str.extract('([-+]?\d*\.?\d+)')
    temp_df2["Extracted_1"] = pd.to_numeric(temp_df2["Extracted_1"], downcast="float")
    temp_df2["Extracted_2"] = pd.to_numeric(temp_df2["Extracted_2"], downcast="float")
    # Getting coordinates of stations in a format needed for Folium MAP
    coordinates = temp_df2[['Extracted_1', 'Extracted_2']].values.tolist()
    coordinates_dict = {}
    for i in range(len(coordinates)):
        coordinates_dict[data.reset_index().at[i, 'Station #']] = coordinates[i]
    return coordinates, coordinates_dict


"""
def swapPositions(lis, pos1, pos2):
    temp = lis[pos1] #++
    lis[pos1] = lis[pos2]
    lis[pos2] = temp
    return lis
"""


def calculate_sensitivity(coordinates_spill, sensitivity_dataR):
    G_series = sensitivity_dataR.geometry.map(lambda polygon: shapely.ops.transform(lambda x, y: (y, x), polygon))
    sensitivity_data = gpd.GeoDataFrame(geometry=gpd.GeoSeries(G_series))
    sensitivity_data['Sensitivity'] = sensitivity_dataR[['Sensitivit']]

    Sensitivity = []
    for i in range(len(coordinates_spill)):
        # Coordinate of spill zone i
        # demand_i_coord = swapPositions(coordinates_spill[i], 0, 1)
        # print(i)
        spill_zone_i = Point(
            coordinates_spill[i])  # demand_i_coord  coordinates_spill[i] # need to work on NAN in dataset
        # list comprehension to determine which sensitive area this spill belongs
        spill_zone_contains = [sensitivity_data.loc[g, 'geometry'].contains(spill_zone_i) for g in
                               range(len(sensitivity_data))]
        # print(spill_zone_contains)
        # Calculate sensitivity value of spill zone i
        try:
            SN_within1 = sensitivity_data.loc[spill_zone_contains.index(True), 'Sensitivity']  # +++
        except:
            SN_within1 = 0
        # Create a circle around spill zone i
        spill_zone_larger = spill_zone_i.buffer(10)  # 10 is fine??
        # Find all intersecting neighborhood of sensitive areas of spill zone i
        spill_zone_within_neighbor = [spill_zone_larger.intersects(sensitivity_data.loc[j, 'geometry'])
                                      for j in range(len(sensitivity_data))]
        index_neighbor = [nei for nei in range(len(spill_zone_within_neighbor)) if
                          spill_zone_within_neighbor[nei] == True]
        # Calculate total sensitivity value of neighborhood
        SN_neighbor = sum(sensitivity_data.loc[index_neighbor, 'Sensitivity'])
        # Total sensitivity value of spill i
        sensitivity_i = 10 * SN_within1 + SN_neighbor
        Sensitivity.append(sensitivity_i)
    return Sensitivity


# %%
"""
# Converting units for km, knot
Dalplex = [44.63521075008297, -63.59257743952542];
Home = [44.63571446821034, -63.58029358022154]
# 980meters according to Google map
distance_googleMap = 0.98 # kilometer
distance_computeDistance = custom_functions.compute_distance(Dalplex, Home)

to_kms = (distance_googleMap / distance_computeDistance)

# 1 unit = 80 kms


# 11 km in 1 hours
# 1280 km in 116 hours

ResponseTimeT = 16
ResponseTimeT_inHours = (ResponseTimeT*80)/11
"""


# response time: ()

def convert_to_kms(unit):
    return 0


def convert_to_hrs():
    return 0


def extract_cluster_coordinates():
    return 0
