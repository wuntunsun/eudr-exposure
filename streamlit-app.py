import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns

forest = '#284e13ff'

# get data
# @st.cache_data

df = pd.read_csv("data/assets_for_deforestation.csv", sep = "\t")

# deforestation mock values
df['mock_defor'] = np.random.rand(len(df))

st.title("Decent Exposure")
maps, pred, sumstat, risk = st.tabs(["🌍 Map ", "🌲 Deforestation prediction ", "📈 Summary statistics ", "💵 Risk index "])

# Load your asset data
@st.cache_resource
def load_data():
    # Load your asset data from a CSV file or any other source
    return pd.read_csv("data/assets_for_deforestation.csv", sep = "\t")  # Update with your file path

data = load_data()

###############################################################
######################## SIDEBAR ##############################
###############################################################

st.sidebar.title("🌍 Pick a geography 🌍")
# Sidebar sliders for latitude and longitude ranges
min_lat, max_lat, min_lon, max_lon  = -90, 90, -180, 180

lat_range = st.sidebar.slider("Latitude range (North-South)", min_lat, max_lat, (min_lat, max_lat), step =10)
lon_range = st.sidebar.slider("Longitude range (East-West)", min_lon, max_lon, (min_lon, max_lon), step = 10)

# Filter data based on selected ranges
filtered_data = data[(data['latitude'] >= lat_range[0]) & (data['latitude'] <= lat_range[1]) &
                     (data['longitude'] >= lon_range[0]) & (data['longitude'] <= lon_range[1])]



###############################################################
########################## MAPS ###############################
###############################################################
maps.subheader("Assets and deforestation: visualized")

maps.write("In the map below, you can see the visualized location of the assets in your selected geography.")


#--------------------------------------------------------------

maps.map(filtered_data[['latitude', 'longitude']], color = forest)

maps.write("WHY IS COLOR BY SECTOR IN CHART NOT WORKING OUT?!")
maps.write("WHY IS THE MAP NOT ZOOMING IN AUTOMATICALLY? 🥲")

# Sector color map
sector_color_map = {
    "wind power": [255, 0, 0],   # Red
    1: [0, 255, 0],   # Green
    2: [0, 0, 255],   # Blue
    3: [255, 255, 0], # Yellow
    4: [255, 0, 255], # Magenta
    5: [0, 255, 255], # Cyan    
    6: [128, 0, 0],   # Maroon
    7: [0, 128, 0],   # Green (dark)
    8: [0, 0, 128],   # Blue (dark)
    9: [128, 128, 0], # Olive
    10: [128, 0, 128] # Purple
}

# Function to get color based on sector
def get_color(sector):
    return sector_color_map.get(sector, [255, 128, 128]) 

# Function to calculate zoom level
def calculate_zoom_level(lat_range, lon_range):
    """
    Calculate the appropriate zoom level based on the selected latitude and longitude ranges.
    """
    # Example calculation - you may need to adjust this based on your specific requirements
    lat_span = lat_range[1] - lat_range[0]
    lon_span = lon_range[1] - lon_range[0]
    max_span = max(lat_span, lon_span)
    zoom_level = 14 - max_span  # Adjust 14 based on your preference for initial zoom level
    return zoom_level

# Map visualization
map_view = pdk.Deck(
    map_style="mapbox://styles/mapbox/outdoors-v11",
    initial_view_state=pdk.ViewState(
        latitude=(min_lat + max_lat) / 2,
        longitude=(min_lon + max_lon) / 2,
        zoom=2,
        pitch=0,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=filtered_data,
            get_position=["longitude", "latitude"],
            get_radius=1000,
            get_fill_color=lambda d: get_color(d["sector_main"]),
            pickable=True,
            auto_highlight=True,
        ),
    ],
)

# Update initial view state based on slider values
map_view.initial_view_state.latitude = (lat_range[0] + lat_range[1]) / 2
map_view.initial_view_state.longitude = (lon_range[0] + lon_range[1]) / 2
map_view.initial_view_state.zoom = calculate_zoom_level(lat_range, lon_range)

# Render the map
maps.pydeck_chart(map_view)


#--------------------------------------------------------------
maps.subheader("Sample asset")
maps.write("would sth like this be possible? how to do? would be imo interesting to go from the 'general' to the 'specific'.")
###############################################################
####################### PREDICTION ############################
###############################################################

pred.header("A tab with the results")

pred.write("NOT SURE IF NECESSARY?!")

pred.write("This sheet will have the overview of the method plus the predicted deforestation loss. ")
pred.write("TBD how exactly this will look")

pred.write("Could be: for a given geography - list of assets and owners with highest deforestation.")

option = pred.selectbox(
   "On which level would you like to see the results?",
   ("asset level", "owner level"),
   index=None,
   placeholder="Select level...",
)

dict_options = {"owner level": "owner_name", "asset level": "asset_name"}
option_var = dict_options.get(option)

if option in ["asset level", "owner level"]:

# -------------- plot highest deforesters -----------------
    pred.subheader(f"Assets in most deforested areas, on {option}:")
    plot_defor = df[['mock_defor', option_var]].sort_values('mock_defor', ascending = False).head(10)

    pred.bar_chart(data=plot_defor, x=option_var, y='mock_defor', color=forest , use_container_width=True)

    pred.subheader("Table format:")
    pred.dataframe(plot_defor.style.hide(axis="index").format(subset=['mock_defor'], precision=4))

    
    # fig = plt.figure(figsize=(5, 5))

    # plt.barh(plot_defor[option_var], plot_defor.mock_defor, color = forest)
    # plt.title(f'Highest deforestation, by {option}')
    # plt.show()

    # # # render
    # pred.pyplot(fig, use_container_width=True)

###############################################################
###############################################################
###############################################################
sumstat.header("Data overview: assets")

sumstat.write("This tab displays information about the data for the selected region") 

sumstat.write("""First, the asset data. Below are a few graphical representation of the asset data, 
              showing informationa about the distribution of setors and subsectors of the assets, 
              capacity and number of sub-units of assets.""")
sumstat.write(filtered_data.head(10))

# ----------------- BAR CHART OF SECTORS --------------

sumstat.subheader("Main sectors")
sumstat.write("The chosen area on the map has the following distribution of sectors:")

top_sectors = filtered_data.groupby('sector_main').uid_gem.count().reset_index().sort_values('uid_gem')

fig1 = plt.figure(figsize=(5, 5))

plt.barh(top_sectors.sector_main, top_sectors.uid_gem, color = 'green')
plt.title('Number of assets, by sector')
plt.show()
 
# render
sumstat.pyplot(fig1, use_container_width=True)

#--------------------------------------------------------------
sumstat.subheader("Most represented countries")

top_countries = filtered_data.groupby('country').uid_gem.count().reset_index().sort_values('uid_gem').tail(10)

fig2 = plt.figure(figsize=(5, 5))

plt.barh(top_countries.country, top_countries.uid_gem, color = 'green')
plt.title('Number of assets, by country')
plt.show()
 
# render
sumstat.pyplot(fig2, use_container_width=True)

#--------------------------------------------------------------
sumstat.subheader("Capacity distribution")

# normalize capacity within group

def normalize_group(sector_main):
    sector_main['capacity_norm'] = (sector_main['capacity_first'] - sector_main['capacity_first'].mean()) / sector_main['capacity_first'].std()
    return sector_main

# Apply the function to each group
normalized_data = filtered_data.groupby('sector_main').apply(normalize_group).reset_index(drop = True)

fig = plt.figure(figsize=(5, 5))
sns.kdeplot(data = normalized_data, x = 'capacity_norm', hue = 'sector_main')
plt.xlabel('Capacity (normalized)')
plt.ylabel('Density')
plt.title('Capacity (normalized), by sector')

sumstat.pyplot(fig, use_container_width=True)
#--------------------------------------------------------------
#--------------------------------------------------------------
sumstat.header("Deforestation")

sumstat.write("TBD: ")

###############################################################
###############################################################
###############################################################

sumstat.header("Risk factor??")

