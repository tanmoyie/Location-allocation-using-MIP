"""
File Name: data_visualization.py

Outline: Data visualization
1. Location Map: Fig1
2. Geolocation of spills: Fig2
3. Draw Tradeoff plot (Fig3a)
4. Draw cluster (Fig3b)

Developer: Tanmoy Das
Date: Dec 2022
"""

# %% Location map
import pandas as pd
import matplotlib.pyplot as plt
import folium
import geopandas as gpd
import shapely
import custom_functions
import plotly.express as px
import numpy as np
import matplotlib

# %% Fig 0: Oil Spills in Canada
data_historical_indidents = pd.read_excel('Inputs/data_location_allocation_Canadian_Arctic_Hypothetical.xlsx',
                                          sheet_name='historical spill in Canada').copy()
data_historical_indidents.columns
data_bubbleplot = data_historical_indidents[['Type', 'Year', 'Incident Reason', 'Spill Size (Tonnes)']]
data_bubbleplot.head()

# %%
# processing data
# replace some values with Misc in Type
data_bubbleplot['Type'].unique()
data_bubbleplot2 = data_bubbleplot.replace(' Fuel Barge', ' Miscellaneous', regex=True)
data_bubbleplot2 = data_bubbleplot2.replace(' Floating Production Storage and Offloading', ' Miscellaneous', regex=True)
data_bubbleplot2 = data_bubbleplot2.replace(' Tug Boat', ' Miscellaneous', regex=True)
data_bubbleplot2 = data_bubbleplot2.replace(' RORO Ferry', ' Miscellaneous', regex=True)
data_bubbleplot2 = data_bubbleplot2.replace(' Bulk Carrier', ' Miscellaneous', regex=True)

# reason cleaned
data_bubbleplot['Incident Reason'].unique()
data_bubbleplot2 = data_bubbleplot2.replace(' Leaking a ball valve', ' Leakage')
data_bubbleplot2 = data_bubbleplot2.replace(' Leaking spool piece', ' Leakage')
data_bubbleplot2 = data_bubbleplot2.replace(' Leak in a flowline', ' Leakage')
data_bubbleplot2 = data_bubbleplot2.replace(' Leakage', ' Leak')
# %%
size = data_bubbleplot2['Spill Size (Tonnes)']
arr2 = 10000*abs(np.log(size))
data_bubbleplot2['Size_log'] = arr2



# %%

fig1 = plt.figure(figsize=(14, 6), dpi=600)
fig = px.scatter(data_bubbleplot2, x="Year", y="Type",
                 # animation_frame="Month",  # animation_group="LocationIn",hover_name="LocationIn" ,
                 color="Incident Reason", size="Size_log", size_max=50)  # , range_x=[     100,100000], range_y=[25,90],

fig1.patch.set_facecolor('blue')
# fig["layout"].pop("updatemenus") # optional, drop animation buttons

fig.update_layout({'plot_bgcolor': 'rgba(0, 0, 0, 0)', 'paper_bgcolor': 'rgba(0, 0, 0, 0)'})
fig.update_layout(font = dict(family="Courier New",size=25, color="Black"))
fig.update_xaxes(linecolor ='black')
fig.update_yaxes(linecolor ='black')

fig.write_image("Outputs/incidents.png")  # install kaleido package before write_image
fig.show()

# %% Fig 1
# collect data
station_data = pd.read_excel('Inputs/data_PAMIP.xlsx', sheet_name='stations', header=0).copy()
sensivity_data5 = gpd.read_file('Inputs/ArcGIS_data/Sensitivity_data5.shp').copy().reset_index()

# process data
coordinates_ = station_data[['Coordinates']]  # .values.tolist()
resource_amount = station_data[['Resources total']]
max_resource = station_data[['Resources total']].max()

coordinates_st = custom_functions.extract_coordinate(station_data)

# Produce map
map_st = folium.Map(location=[67, -98], zoom_start=4, min_zoom=2.5, max_zoom=7)
# min_zoom and max_zoom to control quantity of zoom

# Draw Stations
for point in range(0, len(coordinates_st)):
    # showing stations
    # Custom icon
    # icon_size = int(resource_amount.loc[point].values / 2)
    icon_size = int((resource_amount.loc[point].values / max_resource) * 100)

    if icon_size > 100:
        icon_size = 100  # just to make sure homes are NOT too big
    iconStation = folium.features.CustomIcon('Outputs/station_icon.png',
                                             icon_size=(icon_size, icon_size))
    folium.Marker(coordinates_st[point], icon=iconStation).add_to(map_st)

    # showing number
    folium.Marker(location=[coordinates_st[point][0] - .9, coordinates_st[point][1]],
                  icon=folium.DivIcon(
                      icon_size=(150, 36),
                      icon_anchor=(7, 20),
                      html=f'<div style="font-size: 12pt;">{point + 1}</div>',
                  )).add_to(map_st)
    # circle for the number
    # map_st.add_child(folium.CircleMarker([72.89, -124.59+2], radius=15))
map_st
map_st.save('Outputs/response_stations.html')

# Draw sensitive area
# Set up Choropleth map
map_st_SN = map_st
map_st_SN.choropleth(
    geo_data=sensivity_data5,
    name='Choropleth',
    data=sensivity_data5,
    columns=['index', 'Sensitivit'],
    key_on="feature.properties.index",
    # range_color=(0, 14),
    fill_color='PuRd',
    #   'BuGn', 'BuPu', 'GnBu', 'OrRd', 'PuBu', 'PuBuGn', 'PuRd', 'RdPu',
    #   'YlGn', 'YlGnBu', 'YlOrBr', and 'YlOrRd'.
    # threshold_scale=myscale,
    fill_opacity=.7,
    line_opacity=.2,
    legend_name='Sensitivity',
    smooth_factor=0
)
map_st_SN.save('Outputs/map_st_SN.html')

# Draw shipping route
# map_shipping_spill = folium.Map(location=spill_coordinates.iloc[0], zoom_start=4, min_zoom=2.5, max_zoom=7)
map_st_SN_route = map_st_SN
map_st_SN_route.choropleth(geo_data="Inputs/ArcGIS_data/Shipping_and_Hydrography.geojson")
map_st_SN_route.save('Outputs/map_st_SN_route.html')

# %% Geolocation of spills: Fig2
# import data
gdf_route = gpd.read_file('Inputs/ArcGIS_data/Shipping_and_Hydrography.geojson')
spill_data = pd.read_excel('Inputs/data_PAMIP.xlsx', sheet_name='spills', header=0).copy()
# process data
spill_size = spill_data[['Spill size']]
max_spill = spill_data[['Spill size']].max()
gdf3 = gdf_route.geometry.map(lambda polygon: shapely.ops.transform(lambda x, y: (y, x), polygon))
# x & y coordinated were interchanged when loading geojson file
exploded3 = gdf3.explode()  # why
point5 = exploded3.geometry  # why
centroids223 = point5.centroid


# Geoseries point to Python List
def coord_lister(geom):
    coords = list(geom.coords)
    return coords[0]


spill_coordinates = centroids223.geometry.apply(coord_lister)

# Draw empty map
map_shipping_spill = folium.Map(location=spill_coordinates.iloc[0], zoom_start=4, min_zoom=2.5, max_zoom=7)

# Draw the Shipping route
map_shipping_spill.choropleth(geo_data="Inputs/ArcGIS_data/Shipping_and_Hydrography.geojson")
# Draw the oil spills
for point_spill in range(0, len(spill_coordinates)):
    icon_size = int((spill_size.loc[point_spill].values / max_spill) * 30)
    folium.CircleMarker(location=[spill_coordinates.iloc[point_spill][0], spill_coordinates.iloc[point_spill][1]],
                        radius=icon_size,
                        color='black', fill=True,
                        opacity=0.1,
                        fill_opacity=.5).add_to(map_shipping_spill)
map_shipping_spill.save('Outputs/oil_spills_Fig2.html')


# %%
# Tradeoff plot
def draw_tradeoff_plot(NumberStMax_data, selected):
    x = NumberStMax_data['NumberStMax']  # np.arange(0, 50, 2)
    # ['NumberStMax', 'Coverage %', 'Response time (in hours)']
    # y-axis values
    y1 = NumberStMax_data['Coverage %']
    y2 = NumberStMax_data['Response time (in hours)']

    # plotting figures by creating axes object
    # using subplots() function
    fig, ax = plt.subplots(figsize=(5, 3))
    # plt.title('Example of Two Y labels')

    # using the twinx() for creating another
    # axes object for secondary y-Axis
    ax2 = ax.twinx()
    ax.plot(x, y1, 'o--', color='g', lw=1)
    ax.scatter(x[selected - 1], y1[selected - 1], facecolors='none', edgecolors='r', lw=4)
    # ax.plot(x[3], y1[3], 'o', color='red', lw=1, facecolors='none')
    ax2.plot(x, y2, '*-', color='b', lw=0.5)

    # giving labels to the axises
    ax.set_xlabel('Number of stations', color='black')
    ax.set_ylabel('Maximal Coverage', color='g')

    ax.yaxis.label.set_color('green')
    ax.tick_params(axis='y', colors='green')
    ax2.yaxis.label.set_color('blue')
    ax2.tick_params(axis='y', colors='blue')
    # plt.annotate('local max', xy=(4, 90), xytext=(3, 1.5))
    ax.text(selected - 1, 92, f'{y1[selected - 1]}%', color='g', fontsize=8)

    # secondary y-axis label
    ax2.set_ylabel('Total distance travelled', color='b')

    # defining display layout
    plt.tight_layout()

    # show plot
    plt.show()
    plt.savefig('Outputs/Tradeoff.png')


# %% Clustering
# Draw cluster and centroids
#
def draw_cluster(coordinates_spill_df, centroids_df, memberships, ArcticLand, ArcticWater):
    fig_c, ax5b = plt.subplots(figsize=(8, 7))
    ArcticLandPlot = ArcticLand.plot(ax=ax5b, color="seashell", alpha=.5)  # ax=ax,
    ArcticWaterPlot = ArcticWater.plot(ax=ax5b, color="lightskyblue", alpha=.5)

    plt.scatter(data=coordinates_spill_df,
                x='Longitude', y='Latitude', c=memberships, alpha=0.5)  # s=size_10times,

    plt.scatter(data=centroids_df,
                x='Longitude', y='Latitude', c='red', marker='o', s=50, alpha=0.5)
    plt.scatter(data=centroids_df,
                x='Longitude', y='Latitude', c=range(len(centroids_df)), marker='*', s=20)

    ax5b.set_xlim([-140, -60])
    ax5b.set_ylim([50, 80])
    ax5b.axis('off')

    fig_c.savefig(f'Outputs/Fig5b spill_cluster_centroid2.png', transparent=True, bbox_inches='tight')
