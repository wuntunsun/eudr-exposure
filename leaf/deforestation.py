import pandas as pd
import geopandas as gpd

from typing import Callable, Iterator, Union, Optional

def area(df: pd.DataFrame, lat: float, long: float, year: int) -> float:
    """Query the deforestation area for location and year.

    Args:
        df (pd.DataFrame): The DataFrame conforming to query.
        lat (float): The latitude of the GPS coordinate.
        long (float): The longitude of the GPS coordinate.
        year (int): The deforestation year.

    Returns:
        float: _description_
    """
    return 0

