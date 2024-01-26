"""
Filename: generate_asset_level_GEM.py

Description:
    This script collects and prepares asset level from the Global Energy Monitor (GEM) database.

Update:
   N/A
   
Outline:
    0) HELPER FUNCTION
    1) DATA IMPORT AND PREPARATION
        1.1) Wind
        1.2) Steel
        1.3) ....
    2) Consolidate all dataframes

NOTES/ #TODO:
    - Continue with other excel sheets (= sectors).
    - Turn the different elements Status, Capacity, Ownership, Sector into functions!
"""
# import packages
import os
import pandas as pd
from flags import PATH_TO_INPUT_FOLDER, PATH_TO_OUTPUT_FOLDER

def process_and_save_gem_data():
    ##################################################
    ######    0) HELPER FUNCTION                ######
    ##################################################

    # function that turns all columns into lowercase and replaces spaces with underscores
    def clean_col_names(df):
        df.columns = df.columns.str.lower()
        df.columns = df.columns.str.replace(" ", "_")
        return df

    # define variables to keep
    vars_to_keep = ["plant_id", "country", 
                    "capacity", "capacity_unit",
                    "latitude", "longitude", "location_accuracy",
                    "ownership_parent_name", "ownership_parent_id",
                    "ownership_owner_name", "ownership_owner_id",
                    "ownership_operator_name", "ownership_operator_id",
                    "sector"]
        
    # define input path
    input_path = os.path.join(PATH_TO_INPUT_FOLDER,
                                'asset_level_data/global_energy_monitor',"GEM_data_preprocessed.xlsx")

    ##################################################
    ######    1) DATA IMPORT AND PREPARATION    ######
    ##################################################


    """
    Let's start with the following structure:
    - STATUS (keep only active plants)
    - CAPACITY (needed as a weight for the aggregation)
    - OWNERSHIP INFORMARTION (crucial for mapping)
    - SECTOR (to be added as a variable)
    - EXPORT (prepare for export)
    """
    
    ### --- 1.1) WIND --- ###
    df_wind = pd.read_excel(input_path, sheet_name="data")
    df_wind = clean_col_names(df_wind) # turn cols into lowercase

    # STATUS 
    df_wind = df_wind[df_wind["status"] == "operating"]

    # CAPACITY
    df_wind = df_wind.rename(columns={"capacity_(mw)": "capacity"})
    df_wind["capacity_unit"] = "mw"

    # OWNERSHIP INFORMARTION
    df_wind["ownership_parent_name"] = "NA"
    df_wind["ownership_parent_id"] = "NA"
    df_wind["ownership_owner_name"] = df_wind["owner"]
    df_wind["ownership_owner_id"] = "NA"
    df_wind["ownership_operator_name"] = df_wind["operator"]
    df_wind["ownership_operator_id"] = "NA"

    # SECTOR
    # add information on onshore/offshore etc
    df_wind["sector"] = "wind/"+df_wind["installation_type"]

    # EXPORT
    df_wind = df_wind.rename(columns={"project_name": "plant_id"}) # in the lack of a plant_id

    # keep vars defined above
    df_wind = df_wind[vars_to_keep]                


    ### --- 1.2) STEEL --- ###
    df_steel = pd.read_excel(input_path, sheet_name="steel")
    df_steel = clean_col_names(df_steel) # turn cols into lowercase

    # STATUS 
    df_steel = df_steel[df_steel["status"] == "operating"]

    # CAPACITY 
    # bit tricky as we have multiple columns
    # nominal_crude_steel_capacity_(ttpa) = sum of bof_steel, eaf_steel, ohf_steel
    # nominal_iron_capacity_(ttpa) = sum of bf & dri
    # remaining capacity columns seem to be standalone
    # NOTE: we add different types of ttpa (total tonnes per annum) which assumes that 1 tonne of steel = 1 tonne of iron

    capacity_cols = ["nominal_crude_steel_capacity_(ttpa)", "nominal_iron_capacity_(ttpa)",
                    "ferronickel_capacity_(ttpa)", "sinter_plant_capacity_(ttpa)",
                    "coking_plant_capacity_(ttpa)", "pelletizing_plant_capacity_(ttpa)"]

    # cleaning of capacity columns
    # replace ">", "nan", "NA" and "unknown" with 0

    df_steel[capacity_cols] = df_steel[capacity_cols].replace([">0", "nan", "NA", "unknown"], 0)
    df_steel[capacity_cols] = df_steel[capacity_cols].astype(float)

    # create sum of capacity columns
    df_steel["capacity"] = df_steel[capacity_cols].sum(axis=1)
    df_steel["capacity_unit"] = "total tonnes per annum"

    # OWNERSHIP INFORMARTION

    # parent (parents with different ownership shares are listed separately)
    # extract only the first name, before the ";

    df_steel["parent_[formula]"] = df_steel["parent_[formula]"].str.split(";", expand=True)[0]
    df_steel["parent_permid_[formula]"] = df_steel["parent_permid_[formula]"].str.split(";", expand=True)[0]

    # remove the last 6 digits from both columns (i.e, [100%])
    df_steel["parent_[formula]"] = df_steel["parent_[formula]"].str[:-6]
    df_steel["parent_permid_[formula]"] = df_steel["parent_permid_[formula]"].str[:-6]

    # define final columns

    df_steel["ownership_parent_name"] = df_steel["parent_[formula]"]
    df_steel["ownership_parent_id"] = df_steel["parent_permid_[formula]"]
    df_steel["ownership_owner_name"] = df_steel["owner"]
    df_steel["ownership_owner_id"] = df_steel["owner_permid"]
    df_steel["ownership_operator_name"] = "NA"
    df_steel["ownership_operator_id"] = "NA"

    # SECTOR
    df_steel["sector"] = "steel"
    #TODO derive more information

    # EXPORT

    # extract latitude and longitude from the coordinates column
    df_steel["latitude"] = df_steel["coordinates"].str.split(",", expand=True)[0]
    df_steel["longitude"] = df_steel["coordinates"].str.split(",", expand=True)[1]
    df_steel = df_steel.rename(columns={"coordinate_accuracy": "location_accuracy"})

    # keep vars defined above
    df_steel = df_steel[vars_to_keep]

    ### --- 1.3) SOLAR --- ###
    df_solar = pd.read_excel(input_path, sheet_name="solar")
    df_solar = clean_col_names(df_solar) # turn cols into lowercase

    # STATUS
    df_solar = df_solar[df_solar["status"] == "operating"]

    # CAPACITY
    df_solar = df_solar.rename(columns={"capacity_(mw)": "capacity"})
    df_solar["capacity_unit"] = "mw (peak value, grid connected, or unknown)"

    # OWNERSHIP INFORMARTION
    df_solar["ownership_parent_name"] = "NA"
    df_solar["ownership_parent_id"] = "NA"
    df_solar["ownership_owner_name"] = df_solar["owner"]
    df_solar["ownership_owner_id"] = "NA"
    df_solar["ownership_operator_name"] = df_solar["operator"]
    df_solar["ownership_operator_id"] = "NA"

    # SECTOR
    df_solar["sector"] = "solar/"+df_solar["technology_type"]

    # EXPORT
    df_solar = df_solar.rename(columns={"project_name": "plant_id"}) # in the lack of a plant_id
    df_solar = df_solar[vars_to_keep]      

    ### --- 1.4) oil_gas_plants --- ###

    df_oil_gas_plants = pd.read_excel(input_path, sheet_name="oil_gas_plants")
    df_oil_gas_plants = clean_col_names(df_oil_gas_plants) # turn cols into lowercase

    # STATUS
    df_oil_gas_plants = df_oil_gas_plants[df_oil_gas_plants["status"] == "operating"]

    # CAPACITY
    df_oil_gas_plants = df_oil_gas_plants.rename(columns={"capacity_(mw)": "capacity"})
    df_oil_gas_plants["capacity_unit"] = "mw"

    # OWNERSHIP INFORMARTION
    df_oil_gas_plants["ownership_parent_name"] = df_oil_gas_plants["parent"]
    df_oil_gas_plants["ownership_parent_id"] = "NA"
    df_oil_gas_plants["ownership_owner_name"] = df_oil_gas_plants["owner"]
    df_oil_gas_plants["ownership_owner_id"] = "NA"
    df_oil_gas_plants["ownership_operator_name"] = df_oil_gas_plants["operator"]
    df_oil_gas_plants["ownership_operator_id"] = "NA"

    # SECTOR (extract information on fuel & technology type)
    df_oil_gas_plants["sector"] = "OilGasPlants/"+"Fuel: "+df_oil_gas_plants["fuel"]+" / Technology: "+df_oil_gas_plants["technology"]

    # EXPORT
    df_oil_gas_plants = df_oil_gas_plants.rename(columns={"gem_unit_id": "plant_id"}) # in the lack of a plant_id
    df_oil_gas_plants = df_oil_gas_plants[vars_to_keep]      

    ### --- 1.5) oil_gas_extraction --- ###
    df_oil_gas_extraction = pd.read_excel(input_path, sheet_name="oil_gas_extraction")
    df_oil_gas_extraction = clean_col_names(df_oil_gas_extraction) # turn cols into lowercase

    # STATUS
    df_oil_gas_extraction = df_oil_gas_extraction[df_oil_gas_extraction["status"] == "operating"]

    # CAPACITY
    df_oil_gas_extraction["capacity"] = "NA (O&G extraction)"
    df_oil_gas_extraction["capacity_unit"] = "NA"

    # OWNERSHIP INFORMARTION

    # clean up multiple parents/owners, see above (steel)
    df_oil_gas_extraction["parent"] = df_oil_gas_extraction["parent"].str.split(";", expand=True)[0]
    df_oil_gas_extraction["parent"] = df_oil_gas_extraction["parent"].str[:-6]
    df_oil_gas_extraction["owner"] = df_oil_gas_extraction["owner"].str.split(";", expand=True)[0]
    df_oil_gas_extraction["owner"] = df_oil_gas_extraction["owner"].str[:-6]

    # define final ownership columns
    df_oil_gas_extraction["ownership_parent_name"] = df_oil_gas_extraction["parent"]
    df_oil_gas_extraction["ownership_parent_id"] = "NA"
    df_oil_gas_extraction["ownership_owner_name"] = df_oil_gas_extraction["owner"]
    df_oil_gas_extraction["ownership_owner_id"] = "NA"
    df_oil_gas_extraction["ownership_operator_name"] = df_oil_gas_extraction["operator"]
    df_oil_gas_extraction["ownership_operator_id"] = "NA"

    # SECTOR
    df_oil_gas_extraction["sector"] = "OilGasExtraction/"+"fuel type="+df_oil_gas_extraction["fuel_type"]+"Unit type="+df_oil_gas_extraction["unit_type"]

    # EXPORT
    df_oil_gas_extraction = df_oil_gas_extraction.rename(columns={"unit_id": "plant_id"}) # in the lack of a plant_id
    df_oil_gas_extraction = df_oil_gas_extraction[vars_to_keep]      


    ### --- 1.X) TO DOS --- ###

    # continue with other tabs
    # nuclear', 'hydropower', 'geothermal', 'coal_terminals', 'coal_plants', 'coal_mines', 'blast_furnaces_relining', 'blast_furnaces', 'bioenergy', 'oil_pipelines', 'lng_terminals', 'gas_pipeline'


    ##################################################
    ######    2) CONSOLIDATION                  ######
    ##################################################

    # combine all dataframes
    list_of_dfs = [df_wind, df_steel, df_solar, df_oil_gas_plants, df_oil_gas_extraction]
    df_gem = pd.concat(list_of_dfs)
    
    # turn string variables into string type
    string_variables = ['ownership_parent_name', 'ownership_operator_name', 'ownership_owner_name']
    for var in string_variables:
        df_gem[var] = df_gem[var].astype(str)
        df_gem[var].fillna('', inplace=True) # fill nan with empty string
        
    # create unique id variable
    df_gem.rename(columns={"plant_id": "uid_gem"}, inplace=True)
    df_gem['uid'] = range(0, len(df_gem)) # unique id for each row
    
    return df_gem





    ### --- 1.X) BLUEPRINT --- ###
    """
    BLUEPRINT FOR COPY & PASTE

    df_XXX = pd.read_excel(input_path, sheet_name="XXX")
    df_XXX = clean_col_names(df_XXX) # turn cols into lowercase

    # STATUS
    df_XXX = df_XXX[df_XXX["status"] == "operating"]

    # CAPACITY
    df_XXX = df_XXX.rename(columns={"capacity_(mw)": "capacity"})
    df_XXX["capacity_unit"] = "TBD"

    # OWNERSHIP INFORMARTION
    df_XXX["ownership_parent_name"] = "TBD"
    df_XXX["ownership_parent_id"] = "TBD"
    df_XXX["ownership_owner_name"] = "TBD"
    df_XXX["ownership_owner_id"] = "TBD"
    df_XXX["ownership_operator_name"] = "TBD"
    df_XXX["ownership_operator_id"] = "TBD"

    # SECTOR
    df_XXX["sector"] = "TBD"

    # EXPORT
    df_XXX = df_XXX[vars_to_keep]      
    """