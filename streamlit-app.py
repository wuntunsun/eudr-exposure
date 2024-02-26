import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
import os
from os.path import isfile, join

from typing import Tuple, Optional, List

forest = '#284e13ff'

# Constants
MIN_LAT, MAX_LAT, MIN_LON, MAX_LON = -90, 90, -180, 180
DATA_PATH = 'data'
GEOLOCATION_COLUMNS = ['latitude', 'longitude']
ASSET_COLUMNS = ['uid_gem', 'sector_main', 'country', 'capacity_first', 'owner_name', 'asset_name']
OBSERVATION_COLUMNS = ['defo_total', 't_m3', 't_m2', 't_m1', 't_0', 't_1', 't_2', 't_3', 'around_3', 'around_5', 'forward_3', 'past_3']

# Initial session_state
if 'geolocation_file' not in st.session_state:
    st.info('geolocation_file not set in st.session_state...')
    st.session_state.csv_data_files = [f for f in os.listdir(DATA_PATH) if isfile(join(DATA_PATH, f)) and f.endswith('.csv')]
    st.session_state.geolocation_data = pd.DataFrame(columns=GEOLOCATION_COLUMNS)
    st.session_state.asset_data = pd.DataFrame(columns=GEOLOCATION_COLUMNS + ASSET_COLUMNS + ['mock_defor'])
    st.session_state.observation_data = pd.DataFrame(columns=GEOLOCATION_COLUMNS + ASSET_COLUMNS + ['mock_defor'] + OBSERVATION_COLUMNS + ['capacity_norm'])

if 'map_layer' not in st.session_state:
    st.info('map_layer not set in st.session_state...')
    st.session_state.map_layer = pdk.Layer(
        "ScatterplotLayer",
        data=st.session_state.geolocation_data,
        get_position=["longitude", "latitude"],
        get_radius=10000,
        get_fill_color = [128, 0, 128, 140],
        #get_fill_color=lambda d: get_color(d["sector_main"]),
        pickable=True,
        auto_highlight=True)

if 'map_deck' not in st.session_state:
    st.info('map_deck not set in st.session_state...')
    st.session_state.map_deck = pdk.Deck(
        #map_style="mapbox://styles/mapbox/outdoors-v11",
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=(MIN_LAT + MAX_LAT) / 2,
            longitude=(MIN_LON + MAX_LON) / 2,
            zoom=2,
            pitch=0,
        ),
        layers=[st.session_state.map_layer])

st.title("Decent Exposure")
maps, sumstat, risk = st.tabs(["🌍 Map ", "📈 Summary statistics ", "💵 Risk index "])

@st.cache_data # will hash on function arguments...
def read_dataframe_from_csv(path, separator) -> Optional[pd.DataFrame]:
    st.info(f'read_dataframe_from_csv {path}')
    try:
        return pd.read_csv(path, sep = separator)
    except:
        st.error(f'The file {path} could not be read...')
        return None

def update_data(state, df: pd.DataFrame, path: str):
    if all(column in df.columns for column in GEOLOCATION_COLUMNS):
        st.info(f'The file {path} contains geolocation data...')
        filtered_data = df[(df['latitude'] >= state.lat_range[0]) & (df['latitude'] <= state.lat_range[1]) & 
                        (df['longitude'] >= state.lon_range[0]) & (df['longitude'] <= state.lon_range[1])].copy()
        # TODO: remove mock_defor...?
        filtered_data['mock_defor'] = np.random.rand(len(filtered_data))
        state.geolocation_data = filtered_data
        #state.map_layer.data = state.geolocation_data.head(30)
        if all(column in state.geolocation_data.columns for column in ASSET_COLUMNS):
            st.info(f'The file {path} contains asset data...')
            state.asset_data = state.geolocation_data
            if all(column in state.asset_data.columns for column in OBSERVATION_COLUMNS):
                st.info(f'The file {path} contains observation data...')
                state.observation_data = state.asset_data

def file_changed(state): # state: SessionStateProxy
    path = join(DATA_PATH, state.geolocation_file)
    df = read_dataframe_from_csv(path, separator='\t')
    if not df is None:
        update_data(state, df, path)

def latitude_changed(state):
    path = join(DATA_PATH, state.geolocation_file)
    df = read_dataframe_from_csv(path, separator='\t')
    if not df is None:
        update_data(state, df, path)

def longitude_changed(state):
    path = join(DATA_PATH, state.geolocation_file)
    df = read_dataframe_from_csv(path, separator='\t')
    if not df is None:
        update_data(state, df, path)

def create_map_deck(state):

    default_view = pdk.ViewState(
        latitude=(MIN_LAT + MAX_LAT) / 2,
        longitude=(MIN_LON + MAX_LON) / 2,
        zoom=2,
        pitch=0,
    )

    state.map_layer = pdk.Layer(
        "ScatterplotLayer",
        data=state.geolocation_data,
        get_position=["longitude", "latitude"],
        get_radius=1000,
        #get_fill_color = [0, 255, 0],
        #get_fill_color=lambda d: get_color(d["sector_main"]),
        pickable=True,
        auto_highlight=True)
    
    state.map_deck = pdk.Deck(
        #map_style="mapbox://styles/mapbox/outdoors-v11",
        map_style=None,
        initial_view_state=default_view,
        layers=[state.map_layer],
    )

    return state.map_deck


###############################################################
######################## SIDEBAR ##############################
###############################################################

with st.sidebar:

    st.title("🌍 Pick a geography 🌍")

    st.selectbox("Select a file for analysis", 
                 st.session_state.csv_data_files, 
                 placeholder="Select file...",
                 index = None, # avoid initial state issue with on_change...
                 key='geolocation_file',
                 on_change=file_changed,
                 args=(st.session_state,))

    #st.text(st.session_state.GEMFile)

    st.slider("Latitude range (North-South)", 
              MIN_LAT, MAX_LAT, (MIN_LAT, MAX_LAT), step =10, 
              key='lat_range',
              on_change=latitude_changed,
              args=(st.session_state,))

    st.slider("Longitude range (East-West)", 
              MIN_LON, MAX_LON, (MIN_LON, MAX_LON), step = 10, 
              key= 'lon_range',
              on_change=longitude_changed,
              args=(st.session_state,))

###############################################################
########################## MAPS ###############################
###############################################################
maps.subheader("Assets: visualized")

maps.write("In the map below, you can see the visualized location of the assets in your selected geography.")


#--------------------------------------------------------------

with maps:

    #st.info(st.session_state.geolocation_data.head(10))
    #st.map(st.session_state.geolocation_data[['latitude', 'longitude']], color = forest)

    # maps.write("WHY IS COLOR BY SECTOR IN CHART NOT WORKING OUT?!")
    # maps.write("WHY IS THE MAP NOT ZOOMING IN AUTOMATICALLY? 🥲")

    # # Sector color map
    # sector_color_map = {
    #     "wind power": [255, 0, 0],   # Red
    #     1: [0, 255, 0],   # Green
    #     2: [0, 0, 255],   # Blue
    #     3: [255, 255, 0], # Yellow
    #     4: [255, 0, 255], # Magenta
    #     5: [0, 255, 255], # Cyan    
    #     6: [128, 0, 0],   # Maroon
    #     7: [0, 128, 0],   # Green (dark)
    #     8: [0, 0, 128],   # Blue (dark)
    #     9: [128, 128, 0], # Olive
    #     10: [128, 0, 128] # Purple
    # }

    # # Function to get color based on sector
    # def get_color(sector):
    #     return sector_color_map.get(sector, [255, 128, 128]) 

    # # Function to calculate zoom level
    # def calculate_zoom_level(lat_range, lon_range):
    #     """
    #     Calculate the appropriate zoom level based on the selected latitude and longitude ranges.
    #     """
    #     # Example calculation - you may need to adjust this based on your specific requirements
    #     lat_span = lat_range[1] - lat_range[0]
    #     lon_span = lon_range[1] - lon_range[0]
    #     max_span = max(lat_span, lon_span)
    #     zoom_level = 14 - max_span  # Adjust 14 based on your preference for initial zoom level
    #     return zoom_level

    #maps.pydeck_chart(map_deck(st.session_state))

    # # Map visualization
    # st.session_state.map_layer = pdk.Layer(
    #     "ScatterplotLayer",
    #     data=st.session_state.geolocation_data,
    #     get_position=["longitude", "latitude"],
    #     get_radius=1000,
    #     #get_fill_color = [0, 255, 0],
    #     #get_fill_color=lambda d: get_color(d["sector_main"]),
    #     pickable=True,
    #     auto_highlight=True)
    
    # st.session_state.map_deck = pdk.Deck(
    #     map_style="mapbox://styles/mapbox/outdoors-v11",
    #     initial_view_state=pdk.ViewState(
    #         latitude=(MIN_LAT + MAX_LAT) / 2,
    #         longitude=(MIN_LON + MAX_LON) / 2,
    #         zoom=2,
    #         pitch=0,
    #     ),
    #     layers=[st.session_state.map_layer],
    # )

    # # Update initial view state based on slider values
    # map_view.initial_view_state.latitude = (st.session_state.lat_range[0] + st.session_state.lat_range[1]) / 2
    # map_view.initial_view_state.longitude = (st.session_state.lon_range[0] + st.session_state.lon_range[1]) / 2
    # map_view.initial_view_state.zoom = calculate_zoom_level(st.session_state.lat_range, st.session_state.lon_range)

    # TODO: Find out how to refresh rather than re-create the 
    # and keep the current viewport...
    st.pydeck_chart(create_map_deck(st.session_state))

    #--------------------------------------------------------------
    st.subheader("Sample asset")
    st.write("would sth like this be possible? how to do? would be imo interesting to go from the 'general' to the 'specific'.")
        
with sumstat:
    st.header("Data overview: assets")

    st.write("This tab displays information about the data for the selected region") 

    st.write("""First, the asset data. Below are a few graphical representation of the asset data, 
              showing informationa about the distribution of setors and subsectors of the assets, 
              capacity and number of sub-units of assets.""")
    
    country_count = st.session_state.asset_data.country.value_counts()
    st.write(country_count)

    st.write(st.session_state.observation_data.head(10))

    # ----------------- BAR CHART OF SECTORS --------------

    st.subheader("Main sectors")
    st.write("The chosen area on the map has the following distribution of sectors:")

    top_sectors = st.session_state.observation_data.groupby('sector_main').uid_gem.count().reset_index().sort_values('uid_gem')

    fig1 = plt.figure(figsize=(5, 5))

    plt.barh(top_sectors.sector_main, top_sectors.uid_gem, color = 'green')
    plt.title('Number of assets, by sector')
    plt.show()
 
    # render
    st.pyplot(fig1, use_container_width=True)

    #--------------------------------------------------------------
    st.subheader("Most represented countries")

    top_countries = st.session_state.observation_data.groupby('country').uid_gem.count().reset_index().sort_values('uid_gem').tail(10)

    fig2 = plt.figure(figsize=(5, 5))

    plt.barh(top_countries.country, top_countries.uid_gem, color = 'green')
    plt.title('Number of assets, by country')
    plt.show()
 
    # render
    st.pyplot(fig2, use_container_width=True)

    #--------------------------------------------------------------
    st.subheader("Capacity distribution")

# normalize capacity within group

    def normalize_group(sector_main):
        sector_main['capacity_norm'] = (sector_main['capacity_first'] - sector_main['capacity_first'].mean()) / sector_main['capacity_first'].std()
        return sector_main

    # Apply the function to each group
    normalized_data = st.session_state.observation_data.groupby('sector_main').apply(normalize_group).reset_index(drop = True)

    fig = plt.figure(figsize=(5, 5))
    sns.kdeplot(data = normalized_data, x = 'capacity_norm', hue = 'sector_main')
    plt.xlabel('Capacity (normalized)')
    plt.ylabel('Density')
    plt.title('Capacity (normalized), by sector')

    st.pyplot(fig, use_container_width=True)
    #--------------------------------------------------------------
    #--------------------------------------------------------------
    st.header("Deforestation")

    st.write("TBD: ")

###############################################################
###############################################################
###############################################################

with risk:

    st.header("🌲 Deforestation exposure")

    # st.write(st.session_state.observation_data.head())

    data = st.session_state.observation_data
    cols_to_show = ['country', 'latitude', 'longitude', 'sector_main', 'treecover2000']
    top_deforesters = data.sort_values('around_3', ascending= False).head(10)
    st.write(top_deforesters.head(10))

