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
    window
)

def main():

    class Command:
        AREA = 'area'
        ASSETS = 'assets'
        CRS = 'crs'
        WINDOW = 'window'

    commands = [Command.AREA, Command.ASSETS, Command.CRS, Command.WINDOW]
    parser=argparse.ArgumentParser(description="""
    Perform a command...
    """)
    parser.add_argument("command", choices=commands)
    parser.add_argument("-g", "--gpkg", nargs='?', default="data/geoply-sample.gpkg")
    parser.add_argument("-l", "--location", nargs='*', default=[-20.00027, -59.99658])
    parser.add_argument("-y", "--year", nargs='?', default="2020", type=int)
    parser.add_argument("-v", "--verbose", default=False, action=argparse.BooleanOptionalAction)
    args=parser.parse_args()

    location = args.location
    year = args.year
    gpkg = args.gpkg
    verbose = args.verbose

    command = args.command

    match command:
        case Command.AREA:
            gdf = gpd.read_file(gpkg)
            result = area(gdf, location[0], location[1], year, verbose)
            # TODO: must convert area to EPSG:4326
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
            gdf = gpd.read_file(gpkg)
            print(f'File {gpkg} contains CRS: {gdf.crs}')
        case Command.WINDOW:
            gdf = gpd.read_file(gpkg)
            result = window(gdf)
            print(f'File {gpkg} contains Window: {result}')


if __name__ == '__main__':
    main()