import pandas as pd
import numpy as np
import os
from flags import PATH_TO_INPUT_FOLDER, PATH_TO_OUTPUT_FOLDER

def combine_asset_datasets(): 
    df_gem = pd.read_csv("data/asset_level_open_source_gem.csv")
    df_gem['data_source'] = 'GEM'

    df_clt = pd.read_csv("data/asset_level_open_source_climate_trace.csv")
    df_clt['data_source'] = 'Climate Trace'
    df_clt.rename(columns = {"company_name": "owner_name"}, inplace = True)

    df_sfi = pd.read_csv("data/asset_level_open_source_sfi.csv")
    df_sfi['data_source'] = 'SFI'

    df = pd.concat([df_gem, df_clt, df_sfi], axis = 0).reset_index()

    cols_to_keep = ['uid', 'asset_name', 'country',
                    'start_year', 'latitude', 'longitude',
                    'parent_name', 'owner_name', 'operator_name',
                    'sector', 'data_source']

    df = df[cols_to_keep]

    # turn columns into numeric
    num_cols = ['start_year', 'latitude', 'longitude']
    for col in num_cols: 
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # drop rows wehre all ownership info is missng
        
    df.dropna(axis = 0, subset = ['owner_name', 'latitude', 'longitude'], how = 'any', inplace = True)

    # export finalized dataset
    output_path = os.path.join(PATH_TO_OUTPUT_FOLDER,"combined_asset_data.csv")
    df.to_csv(output_path, index=False)

    return df
