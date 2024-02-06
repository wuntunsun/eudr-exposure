import pandas as pd
import geopandas as gpd
import rasterio as rio
from rasterio.warp import transform
from shapely.geometry import Point

from typing import Tuple, Optional

def window(gdf: gpd.GeoDataFrame) -> Tuple[float, float, float, float]:
    """_summary_

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
        verbose (bool): Print additional information to console.

    Returns:
        Optional[float]: The 'area' in EPSG:4326 or None if 'area' is missing or location does not match.
    """

    to_crs = gdf.crs
    from_crs = rio.crs.CRS.from_epsg(4326)
    x, y = transform(from_crs, to_crs, [long], [lat])
    pt = Point(x, y)

    # TODO: there should be 0 or 1 matches but maybe we should check?
    mask = gdf.geometry.contains(pt)
    first_valid_index = None if not mask.any() else gdf[mask].index[0]
    area = None if first_valid_index == None else gdf.loc[first_valid_index].area

    if verbose:
        print(f'location: [{lat}, {long}], in CRS: {pt}, index: {first_valid_index}')
        if not first_valid_index == None:
            print(f'geometry: {gdf.loc[first_valid_index].geometry}')

    return area



