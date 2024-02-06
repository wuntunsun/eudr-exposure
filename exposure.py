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

def main():
    process_and_save_climate_trace_data()

    process_and_save_sfi_data()

    process_and_save_gem_data()

    combine_asset_datasets()

if __name__ == '__main__':
    main()