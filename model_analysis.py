"""
File Name: model_analysis.py

Outline: Data visualization
1. Draw Network diagram: Fig4

Developer: Tanmoy Das
Date: Dec 2022
"""

# import libraries
import pandas as pd
import custom_functions
from matplotlib import collections as mc
import matplotlib.pyplot as plt
import folium


# %% Network Diagram
def draw_network_diagram(DistanceMax, NumberStMax, spill_df, station_df, ResponseTimeT, coverage_percentage,
                         assignment3, cover_1s, select_1s, amountSt_groupby, m, Wi, ArcticLand, ArcticWater):

    # plot the line segments, indicent points, and base station points of the final network
    fig, ax = plt.subplots()

    ArcticLandPlot = ArcticLand.plot(ax=ax, color="seashell", alpha=.5)  # ax=ax,
    ArcticWaterPlot = ArcticWater.plot(ax=ax, color="lightskyblue", alpha=.5)


    unique_stations = assignment3['Station no.'].unique()

    for ust in range(len(unique_stations)):
        d1 = assignment3.loc[assignment3['Station no.'] == unique_stations[ust]].reset_index()
        new_list = []
        for r in range(d1.shape[0]):
            new_list.append([(d1.Spill_Longitude[r], d1.Spill_Latitude[r]), (d1.St_Longitude[r], d1.St_Latitude[r])])
        lc = mc.LineCollection(new_list, colors=f'C{ust + 1}',
                               alpha=.9, lw=1.5)  # alpha = (ust/len(unique_stations)), colors=ust,
        ax.add_collection(lc)

    #
    x_max = max(spill_df[spill_df['Spill #'].isin([item[0] for item in cover_1s.index])]['Resource needed'])
    x_min = min(spill_df[spill_df['Spill #'].isin([item[0] for item in cover_1s.index])]['Resource needed'])
    x1_max = max(spill_df[~spill_df['Spill #'].isin([item[0] for item in cover_1s.index])]['Resource needed'])
    x1_min = min(spill_df[~spill_df['Spill #'].isin([item[0] for item in cover_1s.index])]['Resource needed'])

    # Spill related nodes
    # Points of covered spills
    spillC = plt.scatter(data=spill_df[spill_df['Spill #'].isin([item[0] for item in cover_1s.index])],
                         x='Spill_Longitude', y='Spill_Latitude',
                         s=((
                                spill_df[spill_df['Spill #'].isin([item[0] for item in cover_1s.index])][
                                    'Resource needed'])
                            - x_min) * 400 / (x_max - x_min),
                         c='black', alpha=0.2)
    # Points of un-covered spills
    spillUnC = plt.scatter(data=spill_df[~spill_df['Spill #'].isin([item[0] for item in cover_1s.index])],
                           x='Spill_Longitude', y='Spill_Latitude',
                           s=((spill_df[~spill_df['Spill #'].isin([item[0] for item in cover_1s.index])][
                               'Resource needed'])
                              - x1_min) * 400 / (x1_max - x1_min),
                           facecolors='none', edgecolors='black', alpha=.5)

    # Stations related nodes and edges
    # Green Square showing stations
    st = plt.scatter(data=station_df[station_df['Station no.'].isin(select_1s.index.tolist())],
                     x='St_Longitude', y='St_Latitude', marker='s',
                     alpha=0.9,
                     zorder=2,
                     s=120,
                     c='green')

    # Showing station number as text
    selected_supply_stations = station_df[
        station_df['Station no.'].isin(select_1s.index.tolist())].reset_index()

    #for i in range(selected_supply_stations.shape[0]):
    #    plt.text(x=selected_supply_stations.St_Longitude[i] + 2.5, y=selected_supply_stations.St_Latitude[i] - .25,
    #             s=selected_supply_stations.loc[:, 'Station no.'][i] + 1,
    #             fontdict=dict(color='red', size=9))

    # Small purple squares to show non-selected stations
    #stUns = plt.scatter(data=station_df[~station_df['Station no.'].isin(select_1s.index.tolist())],
    #                    x='St_Longitude', y='St_Latitude', marker='s', alpha=.25, c='blue')

    # legends of all shapes in this figure
    plt.legend((spillC, spillUnC, st),  # , stUns
               ('Oil Spill covered', 'Oil Spill uncovered', 'Stations selected'),  # ,'Stations not selected
               ncol=1, handlelength=5, borderpad=.5, markerscale=.4,
               fontsize=7, loc='lower left'
               )
    ax.set_xlim([-140, -60])
    ax.set_ylim([50, 80])
    plt.axis('off')
    # plt.xticks([])
    # plt.yticks([])

    #plt.xlabel('Longitude')
    #plt.ylabel('Latitude')

    plt.show()
    fig.savefig(
        f'Outputs/{m} {len(spill_df)}spills {NumberStMax}NumberSt_max {DistanceMax}Distance_max {coverage_percentage}%coverage.png'
    , transparent=True)  #
