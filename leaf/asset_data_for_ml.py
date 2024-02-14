import pandas as pd
from sklearn.preprocessing import LabelEncoder

    
def gem_data_for_ml(gem_data):
    
    df_gem = pd.read_csv(gem_data, low_memory=False)

    # coerce start year into numerical format
    for var in ['start_year', 'capacity']:
        df_gem[var] = pd.to_numeric(df_gem[var], errors='coerce') 

    # drop all observations with a missing start_year
    df_gem = df_gem[df_gem.start_year.notnull()].reset_index()

    # drop all observations with a start year outside of 2001-2022
    df_gem = df_gem[df_gem.start_year.between(2001, 2023)]

    # main and sub sector
    df_gem[['sector_main', 'sector_sub']] = df_gem.sector.str.split("/", expand = True, n = 1)
    df_gem.isnull().sum()

    # encode subsectors
    label_encoder = LabelEncoder()
    df_gem['sector_main_num'] = label_encoder.fit_transform(df_gem['sector_main'])
    df_gem['sector_num'] = label_encoder.fit_transform(df_gem['sector'])

    # keep only relevant columns
    cols_to_keep = ['latitude', 'longitude', 'uid_gem', 'sector_main', 
                    'sector_sub', 'sector_main_num', 
                    'start_year', 'capacity', 'capacity_unit', 'asset_name', 'owner_name', 'country']

    df_gem = df_gem[cols_to_keep]

    #=========================================================
    # AGGREGATE TO ASSET LEVEL (ON UID_GEM)
    
    # step 1: aggregate unit-specific information by uid_gem

    cols_for_agg = ['capacity', 'start_year', 'sector_sub', 'uid_gem']

    # 1a: first observaitons 
    df_gem_first = df_gem[cols_for_agg].groupby('uid_gem').nth(0) \
                        .rename(columns={'start_year': 'start_year_first', 
                                            'capacity': 'capacity_first', 
                                            'sector_sub': 'sector_sub_first'}).reset_index()

    assert(len(df_gem_first) == df_gem_first.uid_gem.nunique())

    # 1b: list of info for subsequent units
    df_gem_list = df_gem[cols_for_agg].groupby('uid_gem').agg(list).reset_index()

    assert(len(df_gem_list) == df_gem_list.uid_gem.nunique())

    # step 2: keep non-changing information about each asset

    invariant_cols = ['latitude', 'longitude', 'uid_gem', 'sector_main', 'sector_main_num', 
                'capacity_unit', 'country']

    df_gem_invariant = df_gem[invariant_cols].drop_duplicates('uid_gem', keep='first')

    assert(len(df_gem_invariant) == df_gem_invariant.uid_gem.nunique())

    # merge aggregated datasets 
    df_gem = pd.merge(df_gem_invariant, df_gem_first, on = 'uid_gem')
    df_gem = pd.merge(df_gem, df_gem_list, on = 'uid_gem').reset_index(drop=True)

    # retrieve number of units within an asset
    df_gem['number_units'] = df_gem.start_year.apply(lambda x: len(x))

    # check lenght of data 
    assert(len(df_gem) == df_gem.uid_gem.nunique())

    # export data
    df_gem.to_csv('data/assets_for_deforestation.csv', index=False, sep='\t', encoding='utf-8')

