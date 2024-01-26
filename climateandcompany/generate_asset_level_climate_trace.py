"""
Filename: generate_asset_level_climate_trace.py

Description:
    This script is designed to collect and preprocess climate trace data.
    
Update:
    Last updated in November 2023

Output:
    A cleaned and structured DataFrame saved as a CSV file
    
NOTES/ #TODO:
- Get access to more disaggregated data with ownership information (i.e., reach out to them).

"""

import os
import pandas as pd
from flags import PATH_TO_INPUT_FOLDER, PATH_TO_OUTPUT_FOLDER

def process_and_save_climate_trace_data(ownership_threshold=10):
    """
    Process and save Climate Trace data from the specified input folder to the output folder.

    Args:
        climate_trace_input_folder (str): The path to the folder containing the Climate Trace data.
        ownership_threshold (int): The minimum percent interest to include an asset with multiple owners.

    Output:
        Saves a cleaned and structured DataFrame as a CSV file in the output folder.
    """
    ### Load all Climate Trace data files
    climate_trace_input_folder = os.path.join(PATH_TO_INPUT_FOLDER, "asset_level_data/climate_trace")
    
    # Collect all filenames in the input folder ending with _ownership.csv
    climate_trace_files = [file for file in os.listdir(climate_trace_input_folder) if file.endswith("_ownership.csv")]
    temp_list = [pd.read_csv(os.path.join(climate_trace_input_folder, file)) for file in climate_trace_files]
    
    # Turning the list of dataframes into a single dataframe
    df_climate_trace = pd.concat(temp_list, ignore_index=True)
    del temp_list

    ### DATA CLEANING
    # Store assets with one owner in separate df
    unique_assets = df_climate_trace.drop_duplicates(subset='source_id', keep=False)
    
    # Store assets with multiple owners in separate df (and keep only >10% ownership)
    multiple_owners = df_climate_trace[df_climate_trace.duplicated(subset='source_id', keep=False)]
    multiple_owners = multiple_owners[multiple_owners['percent_interest_parent'] >= ownership_threshold]
    
    # Combine both
    df_climate_trace = pd.concat([unique_assets, multiple_owners], ignore_index=True)

    ### PREPARE OUTPUT
    relevant_columns = ['source_id', 'source_name', 'company_name', 'ultimate_parent_name',
                        'iso3_country', 'original_inventory_sector', 'lat', 'lon']
    df_climate_trace = df_climate_trace[relevant_columns]
    df_climate_trace.rename(columns={'source_id': 'asset_id', 'source_name': 'asset_name',
                                'company_name': 'company_name', 'ultimate_parent_name': 'parent_name',
                                'iso3_country': 'country', 'original_inventory_sector': 'sector',
                                'lat': 'latitude', 'lon': 'longitude'}, inplace=True)
    df_climate_trace.reset_index(drop=True, inplace=True)
    
    ## CLEANING
    
    # turn asset_name, company_name, parent_name into strings
    string_variables = ['asset_name', 'company_name', 'parent_name']
    for var in string_variables:
        df_climate_trace[var] = df_climate_trace[var].astype(str)
        df_climate_trace[var].fillna('', inplace=True) # fill nan with empty string
        
    # create unique id for each row, counting from 0 to len(df_climate_trace)
    df_climate_trace['uid'] = range(0, len(df_climate_trace))

    ### SAVE OUTPUT TO CSV
    output_file_path = os.path.join(PATH_TO_OUTPUT_FOLDER, "asset_level_open_source_climate_trace.csv")
    df_climate_trace.to_csv(output_file_path, index=False)
    
    return df_climate_trace

