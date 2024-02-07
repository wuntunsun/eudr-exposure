# Forest Data

[Global Forest Watch](https://data.globalforestwatch.org/pages/data-policy)

All of the data, graphics, charts and other material we produce carry the Creative Commons CC BY 4.0 licensing. This means you are able to download, share, and adapt the data for any use, including commercial and noncommercial uses. You must attribute the data appropriately, using the information provided in the data set description.

## Sources 

1. https://land.copernicus.eu/en/products/vegetation/fraction-of-green-vegetation-cover-v1-0-300m
2. https://www.copernicus.eu/en/events/events/copernicus-webinar-copernicus-tackling-deforestation-and-forest-degradation

National Forest Inventory is challenging and variable in quality. Its improvement is motivated by access to climate financing.

https://openforis.org/
https://docs.sepal.io/en/latest/setup/resource.html

## Deforestation

Significant work is required to convert remote sensing data into data which attributes land use change to deforestation. 

### Global Forest Change 2000-2022 (Hansen et al.)

"Results from time-series analysis of Landsat images in characterizing global forest extent and change from 2000 through 2022. For additional information about these results, please see the associated journal article (Hansen et al., Science 2013)."

https://data.globalforestwatch.org/documents/gfw::tree-cover-loss/about
https://data.globalforestwatch.org/documents/gfw::tree-cover-loss/explore

While the resulting map data are a largely viable relative indicator of trends, care must be taken when comparing change across any interval. Applying a temporal filter, for example a 3-year moving average, is often useful in discerning trends. However, definitive area estimation should not be made using pixels counts from the forest loss layers.

This global dataset is divided into 10x10 degree tiles, consisting of seven files per tile. All files contain unsigned 8-bit values and have a spatial resolution of 1 arc-second per pixel, or approximately 30 meters per pixel at the equator. Only lossyear and last are updated annualy.

The 'granules' come as GeoTiff .tif files that can be converted via geopandas or similar
e.g. https://stackoverflow.com/questions/64589390/python-georasters-geotiff-image-into-geopandas-dataframe-or-pandas-dataframe

Stand-replacement disturbance events in forests create large areas free of tree dominance...
Deforestation is: Decision 11/CP. 7 (UNFCCC, 2001): the direct human-induced conversion of forested land to non-forested land.

Objective information is required to monitor and characterize disturbances and disturbance regimes as related to changing climate and anthropogenic pressures. Forest disturbances occur over a range of spatial and temporal scales, with varying extent, severity, and persistence. To date, most of our understanding of detecting forest disturbances using remotely sensed imagery has been based on...

...detecting abrupt and rapid, stand replacing disturbances, such as those related to wildfire and forest harvesting.

Conversely, more continuous, subtle, and gradual non-stand replacing (NSR) disturbances, such as those related to drought stress or insect infestation have been subject to less focus. This can be attributed to the variability of NSR in space and time, as well as detection difficulties due to their often-subtle alterations to forest canopies and structure.

Thus 'Stand-replacement disturbance events in forests' will indicate abrupt changes that may be attributable to 'deforestation' but not exclusively.

Some examples of improved change detection in the 2011-2022 update include the following:

    Improved detection of boreal forest loss due to fire.
    Improved detection of smallholder rotation agricultural clearing in dry and humid tropical forests.
    Improved detection of selective logging.
    Improved detection of the clearing of short cycle plantations in sub-tropical and tropical ecozones.

Thus the most reliable data is from 2011-2022. The EUDR specifies that "forest degradation after the year 2020 are subject to the regulation."

#### Conclusion

https://www.science.org/doi/10.1126/science.aau3445

The Hansen et al. dataset (3), updated annually on Global Forest Watch, does not distinguish permanent forest conversion associated with a change in land use [i.e., deforestation (5)] from other forms of forest disturbance that may be associated with subsequent regrowth (i.e., forestry, shifting cultivation, wildfire).

### Tree Cover Loss by Dominant Driver 2022

The Hansen dataset, together with additional datasets, was used in a study to derive dominant driver for tree cover loss. They 

https://data.globalforestwatch.org/documents/gfw::tree-cover-loss-by-dominant-driver-2022/about
https://www.science.org/doi/10.1126/science.aau3445



### Outlook

...machine learning is applied to iteratively improve outputs.

...using different geospatial data approaches it is possible to assess the asset against ‘observational data’, to provide insights into initial and ongoing environmental impact and other social and governance variables.

The advantage is clear: an additional data source, capable of providing independent, global, high frequency insights into the environmental impact and risks 3 of single assets or companies (by grouping the assets of a company and its supply chain), or within a given area such as a state or country.

DATA AGGREGATED GLOBALLY = CORPORATE PERFORMANCE
DATA AGGREGATED BY COUNTRY = NATIONAL PERFORMANCE
DATA COLLECTED AROUND EACH POWER PLANT = SITE PERFORMANCE

TIER 3 - ASSET LEVEL
Assessment of the asset - GIS overlaps,
remote sensing, plus Tier 4.

1. Reduce global list to cover land mass only (refer to grid on main page).
    - Also possible via Data mask (datamask): Three values representing areas of no data (0), mapped land surface (1), and persistent water bodies (2) based on 2000-2012.

2. Year of gross forest cover loss event (lossyear): Forest loss during the period 2000-2022, defined as a stand-replacement disturbance, or a change from a forest to non-forest state. Encoded as either 0 (no loss) or else a value in the range 1-20, representing loss detected primarily in the year 2001-2022, respectively.

3. Possibly aggregate from 30x30 meters (at the equator) due to the size of the data e.g. 10GB compressed for the 'lossyear' GeoTiff.

Example for deforestation prediction: 
https://www.mdpi.com/2076-3417/13/3/1772

My idea would be to predict 'spread' in trend GeoTiff data such as the 'Hansen' dataset. 

Hypothesis: Regions are at higher risk of 'deforestation' when certain 'sector' assets are established.

Deforestation is marked by 'lossyear',
Cluster based on same 'lossyear' and 'distance'... 'stand replacing disturbances'...
We expect a lot of noise so DBSCAN is best...
Note that expanding areas may indicate increasing 'deforestation'.

"It is important to differentiate variables within observational datasets to better understand
initial and ongoing impacts."

Rapid expansion from one year to the next related to 'sector' assets. Given past data where 'sector' assets were established in areas.

## Earth Engine

The size of data may preclude a local or non-dedicated cloud hosting solution. The Hansen dataset is available on Google's Earth Engine where I have registered:

https://code.earthengine.google.com/?project=ee-robertdereknorris
https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2022_v1_10
https://developers.google.com/earth-engine/apidocs

1. Choose an area to bake-in to the app...
2. Allow for 



