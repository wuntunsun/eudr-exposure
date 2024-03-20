import streamlit as st
from streamlit_app import sidebar
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns



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

sidebar()