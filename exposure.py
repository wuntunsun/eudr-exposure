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

from leaf.asset_data_for_ml import (
    gem_data_for_ml
)

from leaf.deforestation import (
    area,
    to_reg_sample,
    window,
    to_lossyear_timeseries,
    to_assets_with_lossyear,
    to_assets_with_treecover2000
)

def main():

    class Command:
        AREA = 'area'
        ASSETS = 'assets'
        CRS = 'crs'
        LOSSYEAR_TIMESERIES = 'series'
        ASSETS_WITH_LOSSYEAR = 'lossyear'
        ASSETS_WITH_TREECOVER2000 = 'treecover2000'
        WINDOW = 'window'
        REG_SAMPLE = 'reg_sample'

    commands = [Command.AREA, 
                Command.ASSETS, 
                Command.CRS, 
                Command.LOSSYEAR_TIMESERIES, 
                Command.ASSETS_WITH_LOSSYEAR, 
                Command.ASSETS_WITH_TREECOVER2000, 
                Command.WINDOW, 
                Command.REG_SAMPLE]
    parser=argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
    Perform a command...\n
    
    > python -m exposure lossyear -a data/assets_for_deforestation.csv -gt data/Hansen_GFC-2022-v1.10_lossyear_20S_060W.tif -d data/assets_with_lossyear.csv -s ','\n
                                                                
    > python -m exposure treecover2000 -a data/assets_with_lossyear.csv -gt data/Hansen_GFC-2022-v1.10_treecover2000_20S_060W.tif -d data/assets_with_deforestation.csv -s ','\n

    Default seperator is , so use -s '\\t' for TAB.

    """)
    parser.add_argument("command", choices=commands)
    parser.add_argument("-gt", "--geoTIFF", nargs='?',
                        default="data/Hansen_GFC-2022-v1.10_lossyear_20S_060W.tif", 
                        const="data/Hansen_GFC-2022-v1.10_lossyear_20S_060W.tif",
                        help="Path to a GeoTIFF file.")
    parser.add_argument("-w", "--window", nargs=4, type=float,
                        default=[2100, 2000, 500, 500],
                        help="A window into the GeoTIFF file as: col_off row_off width, height. Defaults to None for full extent.")
    parser.add_argument("-g", "--geometry", nargs='?',
                        default="data/geoply-sample.gpkg", const="data/geoply-sample.gpkg",
                        help="Path to a geometry file e.g. .gpkg file to be output by series command, or to be used as input for the area command.")
    parser.add_argument("-a", "--assets", nargs='?',
                        default="data/assets_for_deforestation.csv", const="data/assets_for_deforestation.csv",
                        help="Path to a data file e.g. .csv file containing the assets to query, or the output from the lossyear/treecover2000 commands.")
    parser.add_argument("-d", "--data", nargs='?',
                        default="data/geotiff-sample.csv", const="data/geotiff-sample.csv",
                        help="Path to a data file e.g. .csv file to be output by lossyear or treecover2000 commands.")
    parser.add_argument("-o", "--offset", nargs='?', type=int,
                        default="16", const="16", )
    parser.add_argument("-l", "--location", nargs=2, type=float,
                        default=[-20.00027, -59.99658],
                        help="The location as: lat long")
    parser.add_argument("-y", "--year", nargs='?', type=int,
                        default="2020", const="2020")
    parser.add_argument("-s", "--seperator", nargs='?',
                        default=",", const=",", )
    parser.add_argument("-v", "--verbose", action=argparse.BooleanOptionalAction,
                         default=False)
    args=parser.parse_args()

    location = args.location
    year = args.year
    geometry = args.geometry
    data = args.data
    assets = args.assets
    offset = args.offset
    geoTIFF = args.geoTIFF
    verbose = args.verbose
    seperator = args.seperator.encode().decode('unicode_escape')
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
            # process_and_save_climate_trace_data()
            # process_and_save_sfi_data()
            process_and_save_gem_data()

            # combine_asset_datasets()
            gem_data_for_ml("data/loaded_asset/asset_level_open_source_gem.csv")
            
        case Command.CRS:
            gdf = gpd.read_file(geometry)
            print(f'File {geometry} contains CRS: {gdf.crs}')
        case Command.LOSSYEAR_TIMESERIES:
            gdf = to_lossyear_timeseries(geoTIFF, window, verbose)
            gdf.to_file(geometry, driver='GPKG')
        case Command.ASSETS_WITH_LOSSYEAR:
            df = to_assets_with_lossyear(geoTIFF, assets, seperator, offset, window, verbose)
            df.to_csv(data, sep=seperator)
        case Command.ASSETS_WITH_TREECOVER2000:
            df = to_assets_with_treecover2000(geoTIFF, assets, seperator, window, verbose)
            df.to_csv(data, sep=seperator)
        case Command.WINDOW:
            gdf = gpd.read_file(geometry)
            result = window(gdf)
            print(f'File {geometry} contains Window: {result}')
        case Command.REG_SAMPLE:
            to_reg_sample("data/assets_with_deforestation.csv")


if __name__ == '__main__':
    main()