import streamlit as st
import pydeck as pdk
import folium
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
import os
from os.path import isfile, join

from typing import Tuple, Optional, List

# Constants
MIN_LAT, MAX_LAT, MIN_LON, MAX_LON = -90, 90, -180, 180
DATA_PATH = 'data'
GEOLOCATION_COLUMNS = ['latitude', 'longitude']
ASSET_COLUMNS = ['uid_gem', 'sector_main', 'country', 'capacity_first', 'owner_name', 'asset_name']
OBSERVATION_COLUMNS = ['defo_total', 't_m3', 't_m2', 't_m1', 't_0', 't_1', 't_2', 't_3', 'around_3', 'around_5', 'forward_3', 'past_3']

#maps, sumstat, risk = st.tabs(["🌍 Map ", "📈 Summary statistics ", "💵 Risk index "])

@st.cache_data # will hash on function arguments...
def read_dataframe_from_csv(path, separator) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(path, sep = separator)
    except:
        return None

def update_data(df: pd.DataFrame, path: str, state = st.session_state):
    if all(column in df.columns for column in GEOLOCATION_COLUMNS):
        st.toast(f'The file {path} contains geolocation data...')
        filtered_data = df[(df['latitude'] >= state.lat_range[0]) & (df['latitude'] <= state.lat_range[1]) & 
                        (df['longitude'] >= state.lon_range[0]) & (df['longitude'] <= state.lon_range[1])].copy()
        # TODO: remove mock_defor...?
        filtered_data['mock_defor'] = np.random.rand(len(filtered_data))
        state.geolocation_data = filtered_data
        #state.map_layer.data = state.geolocation_data.head(30)
        if all(column in state.geolocation_data.columns for column in ASSET_COLUMNS):
            st.toast(f'The file {path} contains asset data...')
            state.asset_data = state.geolocation_data
            if all(column in state.asset_data.columns for column in OBSERVATION_COLUMNS):
                st.toast(f'The file {path} contains observation data...')
                state.observation_data = state.asset_data

def file_changed(state = st.session_state): # state: SessionStateProxy

    if state.geolocation_file is None: return

    path = join(DATA_PATH, state.geolocation_file)
    df = read_dataframe_from_csv(path, separator='\t')
    if not df is None:
        update_data(df, path, state)

def latitude_changed(state = st.session_state):

    if geolocation_file(state) is None: return

    path = join(DATA_PATH, state.geolocation_file)
    df = read_dataframe_from_csv(path, separator='\t')
    if not df is None:
        update_data(df, path, state)

def longitude_changed(state = st.session_state):

    if geolocation_file(state) is None: return

    path = join(DATA_PATH, state.geolocation_file)
    df = read_dataframe_from_csv(path, separator='\t')
    if not df is None:
        update_data(df, path, state)

def geography_changed(state = st.session_state):

    if geolocation_file(state) is None: return

    path = join(DATA_PATH, state.geolocation_file)
    df = read_dataframe_from_csv(path, separator='\t')
    if not df is None:
        update_data(df, path, state)

def geolocation_file_index(state = st.session_state) -> Optional[int]:
    try:
        return state.csv_data_files.index(state.geolocation_file)
    except: # AttributeError, ValueError...
        return None
    
def geolocation_file(state = st.session_state) -> Optional[str]:
    return None if 'geolocation_file' not in state else state.geolocation_file

def sidebar(state = st.session_state):
    with st.sidebar:
        with st.form(key='geography'):

            st.title("🌍 Pick a geography 🌍")            

            st.selectbox("Select a file for analysis", 
                        state.csv_data_files, 
                        placeholder="Select file...",
                        index=geolocation_file_index(),
                        key='geolocation_file')
            
            print(f'lat_range sidebar {state.lat_range}')

            st.slider("Latitude range (North-South)", 
                    MIN_LAT, MAX_LAT, state.lat_range,
                    step =10, 
                    key='lat_range')

            st.slider("Longitude range (East-West)", 
                    MIN_LON, MAX_LON, state.lon_range, 
                    step =10, 
                    key= 'lon_range')
            
            _ = st.form_submit_button('Apply',
                on_click=geography_changed)