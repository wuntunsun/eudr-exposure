import pandas as pd
import geopandas as gpd
import rasterio as rio
from rasterio.warp import transform
from rasterio.windows import Window
from rasterio import features
from shapely.geometry import Polygon
from shapely.geometry import Point
import itertools as it
from tqdm import tqdm
import time

from typing import Tuple, Optional

def closest_index(gdf: gpd.GeoDataFrame, lat: float, long: float, year: int, verbose: bool = False) -> Tuple[float, int]:

    if verbose:
        print(f'location: [{lat}, {long}]')

    distances = gdf.distance(Point(lat, long)).sort_values()
    return distances.index[0]

def window(gdf: gpd.GeoDataFrame) -> Tuple[float, float, float, float]:
    """Query the 'total_bounds' of the GeoDataFrame.

    Args:
        gdf (gpd.GeoDataFrame): The DataFrame to query.

    Returns:
        Tuple[float, float, float, float]: minx, miny, maxx, maxy
    """

    minx, miny, maxx, maxy = gdf.total_bounds

    from_crs = gdf.crs
    to_crs = rio.crs.CRS.from_epsg(4326)
    x, y = transform(from_crs, to_crs, [minx, maxx], [miny, maxy])

    return (x[0], y[0], x[1], y[1])

def area(gdf: gpd.GeoDataFrame, lat: float, long: float, year: int, verbose: bool = False) -> Optional[float]:
    """Query the deforestation area for a given GPS location and year.

    The GeoDataFrame should include Series 'area' where all values are in gdf.crs.

    Args:
        gdf (gpd.GeoDataFrame): The DataFrame to query.
        lat (float): The latitude of the GPS coordinate.
        long (float): The longitude of the GPS coordinate.
        year (int): The deforestation year.
        verbose (bool, optional): Print additional information to console. Defaults to False.

    Returns:
        Optional[float]: The 'area' in EPSG:4326 or None if 'area' is missing or location does not match.
    """

    to_crs = gdf.crs
    from_crs = rio.crs.CRS.from_epsg(4326)
    x, y = transform(from_crs, to_crs, [long], [lat])
    pt = Point(x, y)

    # TODO: there should be 0 or 1 matches but maybe we should check?
    mask = gdf.geometry.contains(pt)
    first_valid_index = None if not mask.any() else gdf.loc[mask].index[0]
    area = None if first_valid_index == None else gdf.iloc[first_valid_index]['area']

    if verbose:
        print(f'shape: {gdf.shape}')
        print(gdf.head())
        print(f'location: [{lat}, {long}], in CRS: {pt}, index: {first_valid_index}')
        if not first_valid_index == None:
            print(f'geometry: {gdf.iloc[first_valid_index]}')

    return area

def to_series(geoTIFF: str, window: Tuple[float, float, float, float] = None, verbose: bool = False) -> gpd.GeoDataFrame:
    """_summary_

    Args:
        geoTIFF (str): _description_
        window (Tuple[float, float, float, float], optional): _description_. Defaults to None.
        verbose (bool, optional): Print additional information to console. Defaults to False.

    Returns:
        gpd.GeoDataFrame: _description_
    """

    # TODO: handle geoTIFF with multiple bands

    BAND_INDEX = 1

    class Token:
        VALUE = 'lossyear'
        GROUP_ID = 'group'
        GEOMETRY = 'geometry'
        AREA = 'area'
        INDEX_LEFT = 'index_left'
        INDEX_RIGHT = 'index_right'
        VALUE_LEFT = 'lossyear_left'
        VALUE_RIGHT = 'lossyear_right'
        INDICES = 'indices'

    if verbose:
        print(f'geoTIFF: {geoTIFF}, window: {window}')

    with rio.open(geoTIFF) as src:

        start_time = time.time()

        if verbose:
            print(src.meta)
            print(f'crs: {src.crs}')
            print(f'is_epsg_code: {src.crs.is_epsg_code}')
            if src.crs.is_epsg_code:
                print(f'epsg: {src.crs.to_epsg}')
            print(f'is_geographic: {src.crs.is_geographic}')
            print(f'is_projected: {src.crs.is_projected}')
            print(f'linear_units: {src.crs.linear_units}')
            if src.crs.is_projected:
                print(f'linear_units_factor: {src.crs.linear_units_factor}')

        band = src.read(BAND_INDEX, window=Window(window[0], window[1], window[2], window[3]))

        read_time = time.time()

        mask = band != 0
        # Object holding a feature collection that implements the __geo_interface__
        results = (
            {'properties': {Token.VALUE: v}, 'geometry': s}
            for i, (s, v) in enumerate(
                features.shapes(band, mask=mask, connectivity=8, transform=src.transform)
            )
        )
        geoms=list(results)
        gdf = gpd.GeoDataFrame.from_features(geoms, crs=src.crs)

        shapes_time = time.time()

        if verbose:
            print(f'Window results in GeoDataFrame of shape: {gdf.shape}')

        intersects = gdf.sjoin(gdf, how="left", predicate="intersects")
        intersects.shape, intersects.index.value_counts()
        
        intersects.reset_index(inplace=True)
        intersects.rename(columns={'index': Token.INDEX_LEFT}, inplace=True)

        sjoin_time = time.time()

        groups = intersects.groupby(Token.INDEX_LEFT)
        temp = intersects[intersects[Token.INDEX_LEFT] == intersects[Token.INDEX_RIGHT]].set_index(Token.INDEX_LEFT)
        temp[Token.INDICES] = groups[Token.INDEX_RIGHT].aggregate(lambda x: x.tolist())
        temp.index.name = None
        temp[Token.VALUE] = temp[Token.VALUE_LEFT].astype("int") + 2000
        temp.drop([Token.INDEX_RIGHT, Token.VALUE_LEFT, Token.VALUE_RIGHT], axis=1, inplace=True)

        start = time.time()
        counter = it.count()

        indices = temp[Token.INDICES].to_numpy()
        groups = pd.Series([None] * len(temp))

        for i, array in tqdm(zip(counter, indices), total=len(temp)):
            first_valid_index = groups.loc[array].first_valid_index()
            id = i if first_valid_index == None else groups.loc[first_valid_index]
            groups.loc[array] = id
        end = time.time()

        #if verbose:
            #print(f'Loop over {len(temp)} took {end-start}s')

        temp[Token.GROUP_ID] = groups.copy()
        temp.drop(Token.INDICES, axis=1, inplace=True)

        group_time = time.time()

        # dissolve based on lossyear to generate any MULTIPOLYGON from disjoint geometry from same lossyear...
        temp2 = temp.dissolve(
            [Token.GROUP_ID, Token.VALUE]
        )

        dissolve_time = time.time()

        group_ids = temp2.index.get_level_values(0).unique()
        lossyears = range(2001, 2023)

        index = pd.MultiIndex.from_tuples(tuples=it.product(group_ids, lossyears), names=(Token.GROUP_ID, Token.VALUE))
        temp3 = temp2.reindex(index)

        reindex_time = time.time()

        # geodetic coordinates (e.g. 4826) to meters (e.g. 3857) and vice-versa

        temp3.loc[temp3[Token.GEOMETRY].isna(), Token.GEOMETRY] = Polygon([])
        proj_3857 = temp3.to_crs(epsg=3347) # lambert projection
        temp3[Token.AREA] = proj_3857.geometry.area

        area_time = time.time()

        #temp3['cum_area'] = proj_3857.groupby(group_id).area.cumsum()

        #for i in tqdm(group_ids.to_numpy()):
        #    temp3.loc[i, 'cum_geometry'] = list(it.accumulate(temp3.loc[i, 'geometry'], func=lambda x,y: x.union(y)))

        temp3.drop(temp3[temp3[Token.AREA] == 0].index, inplace=True)
        temp3.reset_index(inplace=True)

        if verbose:
            print(f'...and a final GeoDataFrame of .shape: {temp3.shape}')

        end_time = time.time()

        return temp3



