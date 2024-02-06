import sys
import argparse
import geopandas as gpd

from climateandcompany.generate_asset_level_climate_trace import (
    process_and_save_climate_trace_data
)

from leaf.deforestation import (
    area,
    window
)

def main():

    class Command:
        AREA = 'area'
        CLIMATE_TRACE = 'climate_trace'
        CRS = 'crs'
        WINDOW = 'window'

    commands = [Command.AREA, Command.CLIMATE_TRACE, Command.CRS, Command.WINDOW]
    parser=argparse.ArgumentParser(description="""
    Perform a command...
    """)
    parser.add_argument("command", choices=commands)
    parser.add_argument("-g", "--gpkg", nargs='?', default="data/geoply-sample.gpkg")
    parser.add_argument("-l", "--location", nargs='*', default=[52.520008, 13.404954])
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
        case Command.CLIMATE_TRACE:
            process_and_save_climate_trace_data()
        case Command.CRS:
            gdf = gpd.read_file(gpkg)
            print(f'File {gpkg} contains CRS: {gdf.crs}')
        case Command.WINDOW:
            gdf = gpd.read_file(gpkg)
            result = window(gdf)
            print(f'File {gpkg} contains Window: {result}')

if __name__ == '__main__':
    main()