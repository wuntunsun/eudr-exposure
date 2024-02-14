import pandas as pd
    
def gem_data_for_ml(gem_data):

    df_gem = pd.read_csv(gem_data, low_memory=False)

    # coerce start year into numerical format
    for var in ['start_year', 'capacity']:
        df_gem[var] = pd.to_numeric(df_gem[var], errors='coerce') 

    # drop all observations with a missing start_year
    df_gem = df_gem[df_gem.start_year.notnull()].reset_index()

    # drop all observations with a start year outside of 2001-2022
    df_gem = df_gem[df_gem.start_year.between(2001, 2023)]

    # keep only relevant columns
    cols_to_keep = ['latitude', 'longitude', 'uid_gem', 'sector', 'start_year', 'capacity', 'capacity_unit', 'asset_name', 'country']

    df_gem = df_gem[cols_to_keep]

    # aggregate, keeping a list of start_years, and capacities, and also first_start_year and capacity of first unit
    cols_agg = ['latitude', 'longitude', 'uid_gem', 'sector', 'capacity_unit', 'asset_name', 'country']

    df_gem_min = df_gem.groupby(cols_agg).agg(min) \
                        .rename(columns={'start_year': 'start_year_first', 'capacity': 'capacity_first'}).reset_index()

    df_gem_list = df_gem.groupby(cols_agg).agg(list).reset_index()

    # merge aggregated datasets 
    df_gem = pd.merge(df_gem_min, df_gem_list, on = cols_agg)

    # retrieve number of units within an asset
    df_gem['number_units'] = df_gem.start_year.apply(lambda x: len(x))

    # export data
    df_gem.to_csv('data/assets_for_deforestation.csv', index=False, sep='\t', encoding='utf-8')
    
    return df_gem
