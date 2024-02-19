import numpy as np
import pandas as pd

import geopandas as gpd
import rasterio as rio
from rasterio.warp import transform
from rasterio.windows import Window
from rasterio.transform import (xy, rowcol)
from rasterio.coords import BoundingBox
from rasterio import features
import rioxarray as rx
import xarray as xr
from shapely.geometry import Polygon
from shapely.geometry import Point

from concurrent.futures import (ThreadPoolExecutor, wait)
import requests
import threading

from string import Template
import itertools as it
from functools import partial
from tqdm import tqdm
import time
import math
import os
import shutil


from typing import Tuple, Optional, List

def closest_index(gdf: gpd.GeoDataFrame, lat: float, long: float, year: int, verbose: bool = False) -> Tuple[float, int]:
    """_summary_

    Args:
        gdf (gpd.GeoDataFrame): _description_
        lat (float): _description_
        long (float): _description_
        year (int): _description_
        verbose (bool, optional): _description_. Defaults to False.

    Returns:
        Tuple[float, int]: _description_
    """
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

def to_lossyear_timeseries(geoTIFF: str, window: Tuple[float, float, float, float] = None, verbose: bool = False) -> gpd.GeoDataFrame:
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
        VARIABLE = 'lossyear'
        GROUP_ID = 'group'
        GEOMETRY = 'geometry'
        AREA = 'area'
        INDEX_LEFT = 'index_left'
        INDEX_RIGHT = 'index_right'
        VARIABLE_LEFT = 'lossyear_left'
        VARIABLE_RIGHT = 'lossyear_right'
        INDICES = 'indices'

    if verbose:
        print(f'geoTIFF: {geoTIFF}, window: {window}')

    with rio.open(geoTIFF) as src:

        start_time = time.time()

        if verbose:
            print(src.profile)
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
            {'properties': {Token.VARIABLE: v}, 'geometry': s}
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
        temp[Token.VARIABLE] = temp[Token.VARIABLE_LEFT].astype("int") + 2000
        temp.drop([Token.INDEX_RIGHT, Token.VARIABLE_LEFT, Token.VARIABLE_RIGHT], axis=1, inplace=True)

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
            [Token.GROUP_ID, Token.VARIABLE]
        )

        dissolve_time = time.time()

        group_ids = temp2.index.get_level_values(0).unique()
        lossyears = map(str, range(2001, 2023))

        index = pd.MultiIndex.from_tuples(tuples=it.product(group_ids, lossyears), names=(Token.GROUP_ID, Token.VARIABLE))
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

def safe_floor(value: float) -> int:
    """_summary_

    Args:
        value (float): _description_

    Returns:
        int: _description_
    """
    return -1 if math.isnan(value) else math.floor(value)

def to_assets_with_treecover2000(geoTIFF: str, GEMFile: str, seperator: str, window: Tuple[float, float, float, float] = None, verbose: bool = False) -> pd.DataFrame:
    """_summary_

    Args:
        geoTIFF (str): _description_
        GEMFile (str): _description_
        seperator (str): _description_
        window (Tuple[float, float, float, float], optional): _description_. Defaults to None.
        verbose (bool, optional): _description_. Defaults to False.

    Returns:
        pd.DataFrame: _description_
    """
    class Token:
        INDEX = 'uid_gem'
        ROW = 'row'
        COL = 'col'
        XDARRAY = 'xdarray'
        TREECOVER2000 = 'treecover2000'

    def select(row, col, xdarray):
        result = xdarray.isel(x=row, y=col) 
        return result

    lookup = np.vectorize(select, excluded=[Token.XDARRAY], cache=False)

    assets = pd.read_csv(GEMFile, sep=seperator)

    if verbose:
        print(f'{GEMFile}')
        print(f'Of {len(assets)} assets, {assets[Token.INDEX].nunique()} are unique.')
        print(assets[assets[Token.INDEX].duplicated(keep='first')][Token.INDEX])
        #print(assets[assets.isna().any(axis=1)])

    assert assets[Token.INDEX].nunique() == len(assets)
    assets = assets.set_index(Token.INDEX)

    with rx.open_rasterio(geoTIFF).squeeze() as xda:
    
        if verbose:
            print(f'{geoTIFF}')
            print(xda)
            unique, counts = np.unique(xda.data, return_counts=True)
            print(dict(zip(unique, counts)))

        to_crs = xda.rio.crs
        from_crs = rio.crs.CRS.from_epsg(4326)
        xs, ys = transform(from_crs, to_crs, assets.longitude, assets.latitude)

        rows, cols = rowcol(xda.rio.transform(), xs, ys, op=safe_floor)
        assets[Token.ROW] = rows
        assets[Token.COL] = cols
        
        # Nota bene: Robert Norris - we may have coordinates beyond the extent of the DataArray
        # TODO: handle Window...
        local_assets = assets[(assets.row >= 0) & 
                        (assets.col >= 0) & 
                        (assets.row < xda.rio.height) & 
                        (assets.col < xda.rio.width)].copy()
    
        np_row = local_assets.row.to_numpy()
        np_col = local_assets.col.to_numpy()
        
        if verbose:
            print(f'{len(np_row)} {len(np_col)}')

        if len(np_row) == 0 or len(np_col) == 0:
            return assets

        # Nota bene: Robert Norris - np.vectorize is consistently a little quicker than apply... %timeit 
        result = lookup(row=np_row, col=np_col, xdarray=xda)

        local_assets[Token.TREECOVER2000] = pd.Series(result, index=local_assets.index)

        mergeable_columns = local_assets.columns.difference(assets.columns)
        mergeable_local_assets = local_assets[mergeable_columns]
        assets = assets.merge(mergeable_local_assets, how='left', validate='one_to_one', left_on=Token.INDEX, right_on=Token.INDEX)
        assets.update(local_assets)

    return assets

def to_assets_with_lossyear(geoTIFF: str, GEMFile: str, seperator: str, offset: int = 16, window: Tuple[float, float, float, float] = None, verbose: bool = False) -> pd.DataFrame:
    """_summary_

    Args:
        geoTIFF (str): _description_
        GEMFile (str): _description_
        seperator (str): _description_
        offset (int, optional): _description_. Defaults to 16.
        window (Tuple[float, float, float, float], optional): _description_. Defaults to None.
        verbose (bool, optional): _description_. Defaults to False.

    Returns:
        pd.DataFrame: _description_
    """
    class Token:
        INDEX = 'uid_gem'
        VARIABLE = 'lossyear'
        VALUE = 'proportion'
        ROW = 'row'
        COL = 'col'
        XDARRAY = 'xdarray'
        OFFSET = 'offset'
        REGION = 'region'

    def select(row, col, xdarray, offset):
        s1 = slice(col-offset-1, col+offset)
        s2 = slice(row-offset-1, row+offset)
        roi = xdarray.isel(x=s1, y=s2)
        data = np.empty([0,]) if roi.size == 0 else roi.data
        unique, counts = np.unique(data, return_counts=True)
        area = (offset*2+1)**2
        proportions = counts / area
        years = unique + 2000
        return dict(zip(years.astype(str), proportions))

    lookup = np.vectorize(select, excluded=[Token.XDARRAY, Token.OFFSET], cache=False)

    assets = pd.read_csv(GEMFile, sep=seperator)
    
    if verbose:
        print(f'{GEMFile}')
        print(f'Of {len(assets)} assets, {assets[Token.INDEX].nunique()} are unique.')
        print(assets[assets[Token.INDEX].duplicated(keep='first')][Token.INDEX])
        #print(assets[assets.isna().any(axis=1)])

    assert assets[Token.INDEX].nunique() == len(assets)
    assets = assets.set_index(Token.INDEX)

    # Prepare final index
    indices = assets.index.unique()
    lossyears = map(str, range(2001, 2023))
    index = pd.MultiIndex.from_tuples(tuples=it.product(indices, lossyears), names=(Token.INDEX, Token.VARIABLE))

    with rx.open_rasterio(geoTIFF).squeeze() as xda:

        if verbose:
            print(f'{geoTIFF}')
            print(xda)
            unique, counts = np.unique(xda.data, return_counts=True)
            print(dict(zip(unique, counts)))

        to_crs = xda.rio.crs
        from_crs = rio.crs.CRS.from_epsg(4326)
        xs, ys = transform(from_crs, to_crs, assets.longitude, assets.latitude)

        rows, cols = rowcol(xda.rio.transform(), xs, ys, op=safe_floor)

        assets[Token.ROW] = rows
        assets[Token.COL] = cols
        
        # Nota bene: Robert Norris - we may have coordinates beyond the extent of the DataArray,
        # and have assets within offset of bounds
        # TODO: handle Window...
        local_assets = assets[(assets.row >= offset) & 
                        (assets.col >= offset) & 
                        (assets.row < xda.rio.height - offset) & 
                        (assets.col < xda.rio.width - offset)].copy()
    
        np_row = local_assets.row.to_numpy()
        np_col = local_assets.col.to_numpy()

        if verbose:
            if len(np_row) == 0 or len(np_col) == 0:
                print(f'No assets match to {geoTIFF}')

        if len(np_row) == 0 or len(np_col) == 0:
            return assets

        # Nota bene: Robert Norris - np.vectorize is consistently a little quicker than apply... %timeit 
        result = lookup(row=np_row, col=np_col, xdarray=xda, offset=offset)

        local_assets[Token.REGION] = pd.Series(result, index=local_assets.index)
        columns = local_assets.columns.drop(Token.REGION)
        # expand to columns i.e. to wide format... indexed by uid_gem
        local_assets_with_lossyears = pd.concat([local_assets[Token.REGION].apply(pd.Series)], axis=1)

        years = local_assets_with_lossyears.columns
        local_assets_per_lossyear = pd.melt(local_assets_with_lossyears, value_vars=years, var_name=Token.VARIABLE, value_name=Token.VALUE, ignore_index=False)

        local_assets_by_lossyear = local_assets_per_lossyear.groupby([Token.INDEX, Token.VARIABLE]).first()
        local_assets_by_lossyear = local_assets_by_lossyear.reindex(index)
        local_assets_by_lossyear.fillna(0, inplace=True)
        local_assets_by_lossyear.reset_index(inplace=True)

        local_assets = local_assets_by_lossyear.pivot(index=Token.INDEX, columns=Token.VARIABLE, values=Token.VALUE)
        mergeable_columns = local_assets.columns.difference(assets.columns)
        mergeable_local_assets = local_assets[mergeable_columns]
        assets = assets.merge(mergeable_local_assets, how='left', validate='one_to_one', left_on=Token.INDEX, right_on=Token.INDEX)
        assets.update(local_assets)

    return assets

def to_degrees(lat: int, long: int, step: int = 10) -> Tuple[str, str]:
    """ Convert latitude and longitude to degrees of the form e.g. ('020S', '50W').

    Positive latitudes are north of the equator, negative latitudes are south of the equator. 
    Positive longitudes are east of the Prime Meridian; negative longitudes are west of the Prime Meridian.

    Args:
        lat (int): A latitude value.
        long (int): A longitude value.
        step (int, optional): Step in degrees. Defaults to 10.

    Returns:
        Tuple[str, str]: Degrees of the form e.g. ('020S', '50N').
    """
    div_lat, mod_lat = divmod(lat, step)
    div_long, mod_long = divmod(long, step)
    clat = div_lat * step if mod_lat == 0 else (div_lat + 1) * step
    clong = div_long * step if mod_long == 0 else (div_long) * step
    slat = 'S' if clat <= 0 else 'N'
    slong = 'E' if clong > 0 else 'W'
    return (f'{abs(clat):>02}' + slat, f'{abs(clong):>03}' + slong)

def download_file(session: requests.Session, url, path, verbose: bool = False) -> str:
    """_summary_

    Args:
        session (requests.Session): _description_
        url (_type_): _description_
        path (_type_): _description_

    Returns:
        str: _description_
    """

    if verbose:
        print(f'download_file {path} from {url}')

    with session.get(url, stream=False) as response:
        response.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): 
                f.write(chunk)

    return path

def cache(session: requests.Session, root: str, files: List[str], base_url: str, verbose: bool = False):
    """_summary_

    Args:
        session (requests.Session): _description_
        data (str): _description_
        files (List[str]): _description_
        base_url (str): _description_
    """
    missing = [(f'{base_url}/{file}', f'{root}/{file}') for file in files if not os.path.isfile(f'{root}/{file}')]
    #urls = [f'{base_url}/{file}' for file in files if not os.path.isfile(f'{root}/{file}')]
    #locals = [f'{root}/{file}' for file in files if not os.path.isfile(f'{root}/{file}')]

    #session_download_file = partial(download_file, session=session, verbose=verbose)
    with ThreadPoolExecutor(max_workers=5) as executor:
        for url, file in missing:
            future = executor.submit(download_file, session=session, url=url, path=file, verbose=verbose)
            _ = future.result()
        #TODO why was the map a problem?
        #for result in executor.map(session_download_file, urls, locals):
            #print(f'submit {result}')


def cache_earthenginepartners_hansen(latitudes: range, longitudes: range, root: str = 'data', verbose: bool = False) -> dict:
    """_summary_

    Args:
        latitudes (range): _description_
        longitudes (range): _description_

    Returns:
        _type_: _description_
    """
    def file(layer: str, lat: int, long: int) -> str:
        slat, slong = to_degrees(lat, long)
        t = Template('Hansen_GFC-2022-v1.10_${layer}_${lat}_${long}.tif')
        filename = t.substitute({'layer': layer, 'lat': slat, 'long': slong})
        return filename

    def files(layers: List[str], latitudes: range, longitudes: range) -> dict:
        files_per_layer = {}
        permutations = list(it.product(latitudes, longitudes))
        for layer in layers:
            files_per_layer[layer] = [file(layer, lat, long) for (lat, long) in permutations]
        return files_per_layer

    thread_local = threading.local()
    thread_local.session = requests.Session()

    layers = files(['lossyear', 'treecover2000'], latitudes, longitudes)
    for _, files in layers.items():
        cache(thread_local.session, root, files, 'https://storage.googleapis.com/earthenginepartners-hansen/GFC-2022-v1.10', verbose=verbose)

    return layers

def earthenginepartners_hansen(GEMFile: str, seperator: str, latitudes: range, longitudes: range, data: str, root: str = 'data', verbose: bool = False):

    layers = cache_earthenginepartners_hansen(latitudes, longitudes, root, verbose=verbose)
    
    lossyears = layers['lossyear']
    treecover2000 = layers['treecover2000']

    # TODO: use a temporary file that the os chooses...
    temp = f'{root}/earthenginepartners_hansen.csv'
    shutil.copyfile(GEMFile, temp)

    for lossyear in tqdm(lossyears, desc=f'to_assets_with_lossyear for latitudes: {latitudes} and longitudes: {longitudes}'):
        df = to_assets_with_lossyear(f'{root}/{lossyear}', temp, seperator, 16, verbose = verbose)
        df.to_csv(temp, sep=seperator)

    for treecover2000 in tqdm(treecover2000, desc=f'to_assets_with_treecover2000 for latitudes: {latitudes} and longitudes: {longitudes}'):
        df = to_assets_with_treecover2000(f'{root}/{treecover2000}', temp, seperator, verbose = verbose)
        df.to_csv(temp, sep=seperator)

    shutil.move(temp, data)

def to_reg_sample(data, separator = "\t", max_year = 7): 

    df = pd.read_csv(data, sep = separator)

    # rename year columns to have a prefix
    rename_aux = {str(x): "deforestation_"+str(x) for x in range(2000, 2023)}
    df.rename(columns = rename_aux, inplace = True)

    # get columns which are not about deforstation
    i_cols = [col for col in df.columns if not col.startswith('deforestation_')]

    # reshape
    df = pd.wide_to_long(df, "deforestation_", i = i_cols, j = 'year').reset_index()

    # convert start year to integer
    df['start_year_first'] = df.start_year_first.astype(int)
    
    # function to create year indicators around start-year of asset
    def year_var(n):
        return lambda x: 1 if x.year in range(x.start_year_first - math.floor(n/2), x.start_year_first + math.ceil(n/2)) else 0

    for i in list(range(1, max_year + 1, 2)): 
        var = 'y' + str(i)
        df[var] = df.apply(year_var(i), axis = 1)

    # function to get the deforestation for specific time windows
    def defo_var(n): 
        var = 'y' + str(n)
        return lambda x: x.deforestation_ if x[var] == 1 else 0

    for i in list(range(1, max_year + 1, 2)): 
        var = 'defo_y' + str(i)
        df[var] = df.apply(defo_var(i), axis = 1)

    # aggregate on uid_gem level (step-wise to prevent losing observations)
    sum_cols = [x for x in df.columns if x not in i_cols and x != 'year'] + ['uid_gem']
    sum_cols

    df_group = df[sum_cols].groupby('uid_gem').sum().rename(columns = {'deforestation_': 'defo_total'}).reset_index()
    df_group.uid_gem.nunique()

    df_invariant = df[i_cols].groupby('uid_gem').agg('first').reset_index()
    df_invariant.uid_gem.nunique()

    df = pd.merge(df_invariant, df_group, how = 'inner', on = 'uid_gem')

    # replace with nans the defo_ vars where there are not enough periods
    def defo_fix(n): 
        var_yr = 'y' + str(n)
        var_defo = 'defo_' + var_yr
        return lambda x: np.nan if x[var_yr] < n else x[var_defo]

    for i in list(range(1, max_year + 1, 2)): 
        var = 'defo_y' + str(i)
        df[var] = df.apply(defo_fix(i), axis = 1)

    # save output 
    df.to_csv('data/regression_sample.csv', index=False, sep='\t', encoding='utf-8')

    return df
