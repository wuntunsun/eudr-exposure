import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import os
from os.path import isfile, join

from streamlit_app import (
    DATA_PATH, 
    GEOLOCATION_COLUMNS,
    ASSET_COLUMNS,
    OBSERVATION_COLUMNS,
    MIN_LAT,
    MAX_LAT,
    MIN_LON,
    MAX_LON,
    sidebar
)
import streamlit_app

forest = '#284e13ff'

st.set_page_config(layout="wide")

# Initial session_state

if 'geolocation_file' not in st.session_state:
    st.toast('geolocation_file not set in st.session_state...')
    st.session_state.csv_data_files = [f for f in os.listdir(DATA_PATH) if isfile(join(DATA_PATH, f)) and f.endswith('.csv')]
    st.session_state.geolocation_data = pd.DataFrame(columns=GEOLOCATION_COLUMNS)
    st.session_state.asset_data = pd.DataFrame(columns=GEOLOCATION_COLUMNS + ASSET_COLUMNS + ['mock_defor'])
    st.session_state.observation_data = pd.DataFrame(columns=GEOLOCATION_COLUMNS + ASSET_COLUMNS + ['mock_defor'] + OBSERVATION_COLUMNS + ['capacity_norm'])
    st.session_state.geolocation_file = None

if 'lat_range' not in st.session_state:
    st.toast('lat_range not set in st.session_state...')
    st.session_state.lat_range = (MIN_LAT, MAX_LAT)

if 'lon_range' not in st.session_state:
    st.toast('lon_range not set in st.session_state...')
    st.session_state.lon_range = (MIN_LON, MAX_LON)

if 'st_folium_data' not in st.session_state:
    st.toast('st_folium_data not set in st.session_state...')
    lat = (st.session_state.lat_range[0] + st.session_state.lat_range[1]) / 2
    lng = (st.session_state.lon_range[0] + st.session_state.lon_range[1]) / 2
    st.session_state.center=(lat, lng)
    st.session_state.zoom=1
    st.session_state.st_folium_data={'center': {'lat': lat, 'lng': lng}, 'zoom': st.session_state.zoom}

sidebar()

st.title("Decent Exposure")