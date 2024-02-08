import sys
import argparse
import geopandas as gpd

from climateandcompany.generate_asset_level_climate_trace import (
    process_and_save_climate_trace_data
)

from climateandcompany.generate_asset_level_SFI import (
    process_and_save_sfi_data
)

from climateandcompany.generate_asset_level_GEM import (
    process_and_save_gem_data
)

from climateandcompany.combine_asset_data import (
    combine_asset_datasets
)

from leaf.deforestation import (
    area,
    window,
    to_series
)

def main():

    class Command:
        AREA = 'area'
        ASSETS = 'assets'
        CRS = 'crs'
        SERIES = 'series'
        WINDOW = 'window'

    commands = [Command.AREA, Command.ASSETS, Command.CRS, Command.SERIES, Command.WINDOW]
    parser=argparse.ArgumentParser(description="""
    Perform a command...
    """)
    parser.add_argument("command", choices=commands)
    parser.add_argument("-gt", "--geoTIFF", nargs='?',
                        default="data/Hansen_GFC-2022-v1.10_lossyear_20S_060W.tif", 
                        const="data/Hansen_GFC-2022-v1.10_lossyear_20S_060W.tif",
                        help="Path to a GeoTIFF file.")
    parser.add_argument("-w", "--window", nargs=4, type=float,
                        default=[2100, 2000, 500, 500],
                        help="A window into the GeoTIFF file as: col_off row_off width, height")
    parser.add_argument("-g", "--geometry", nargs='?',
                        default="data/geoply-sample.gpkg", const="data/geoply-sample.gpkg",
                        help="Path to a geometry file e.g. .gpkg file to be output by series command, or to be used as input for the area command.")
    parser.add_argument("-l", "--location", nargs=2, type=float,
                        default=[-20.00027, -59.99658],
                        help="The location as: lat long")
    parser.add_argument("-y", "--year", nargs='?', type=int,
                        default="2020", const="2020", )
    parser.add_argument("-v", "--verbose", action=argparse.BooleanOptionalAction,
                         default=False)
    args=parser.parse_args()

    location = args.location
    year = args.year
    geometry = args.geometry
    geoTIFF = args.geoTIFF
    verbose = args.verbose
    window = args.window

    command = args.command

    match command:
        case Command.AREA:
            gdf = gpd.read_file(geometry)
            result = area(gdf, location[0], location[1], year, verbose)
            if result == None:
                print('The given location is not contained in an area of deforestaton.')
            else:
                print(f'The given location is contained in an area of {result} units.')
        case Command.ASSETS:
            process_and_save_climate_trace_data()
            process_and_save_sfi_data()
            process_and_save_gem_data()
            combine_asset_datasets()
        case Command.CRS:
            gdf = gpd.read_file(geometry)
            print(f'File {geometry} contains CRS: {gdf.crs}')
        case Command.SERIES:
            gdf = to_series(geoTIFF, window, verbose)
            gdf.to_file(geometry, driver='GPKG')
        case Command.WINDOW:
            gdf = gpd.read_file(geometry)
            result = window(gdf)
            print(f'File {geometry} contains Window: {result}')


if __name__ == '__main__':
    main()