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
import openpyxl
from flags import PATH_TO_INPUT_FOLDER, PATH_TO_OUTPUT_FOLDER
import warnings

warnings.filterwarnings("ignore")

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
    vars_to_keep = ["asset_name", "plant_id", "country", 
                    "capacity", "capacity_unit", "start_year",
                    "latitude", "longitude", "location_accuracy",
                    "ownership_parent_name", "ownership_parent_id",
                    "ownership_owner_name", "ownership_owner_id",
                    "ownership_operator_name", "ownership_operator_id",
                    "sector"]
        
    # define input path
    input_path = os.path.join(PATH_TO_INPUT_FOLDER,
                                'asset_level_data/global_energy_monitor')
    
    # define pairs of file and sheet name
    files_for_import = os.listdir(input_path)

    # remove files for pipelines and GEM preprocessed data
    files_for_import = [file for file in files_for_import if 'Pipeline' not in file and 'preprocessed' not in file]

    # get list of sectors
    def extract_sectors(files_for_import): 

        sectors = []
        for file in files_for_import: 
            if "Global" in file: 
            
                start = 'Global-'
                end = '-Tracker'
                
            else:
                start = 'GEM-GGIT-'
                end = '-2023'
            
            sector = file[file.find(start)+len(start):file.rfind(end)].lower().replace('-', '_')
            sectors.append(sector)
        
        return sectors

    sectors = extract_sectors(files_for_import)
    
    # get the sheet names 
    sheets = []

    for file in files_for_import:

        file_path = input_path + "/" + file

        xl = pd.ExcelFile(file_path, engine = "openpyxl")  

        names = xl.sheet_names  # see all sheet names
        
        if 'About' in names: 
            sheets.append(names[1])
        else: 
            sheets.append(names[0])

    # create a dictionary of {sector: [file, sheet]}
            
    source_dict = {sector: [file, sheet] for sector, file, sheet in list(zip(sectors, files_for_import, sheets))}
    
    #################################################
    #####    1) DATA IMPORT AND PREPARATION    ######
    #################################################


    """
    Let's start with the following structure:
    - STATUS (keep only active plants)
    - CAPACITY (needed as a weight for the aggregation)
    - OWNERSHIP INFORMARTION (crucial for mapping)
    - SECTOR (to be added as a variable)
    - EXPORT (prepare for export)
    """
    ###---------------------------------------------------------------
    ### --- 1.1) WIND --- ###
    file = source_dict['wind_power'][0]
    sheet = source_dict['wind_power'][1]

    df_wind = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_wind = clean_col_names(df_wind) # turn cols into lowercase

    # STATUS 
    df_wind = df_wind[df_wind["status"] == "operating"]

    # CAPACITY
    df_wind = df_wind.rename(columns={"capacity_(mw)": "capacity"})
    df_wind["capacity_unit"] = "mw"

    # CLEAN OWNER
    df_wind["owner"] = df_wind["owner"].str.split(";", expand=True)[0]
    df_wind["owner"] = df_wind.owner.str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    df_wind["operator"] = df_wind["operator"].str.split(";", expand=True)[0]
    df_wind["operator"] = df_wind.owner.str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # OWNERSHIP INFORMARTION
    df_wind["ownership_parent_name"] = "NA"
    df_wind["ownership_parent_id"] = "NA"
    df_wind["ownership_owner_name"] = df_wind["owner"]
    df_wind["ownership_owner_id"] = "NA"
    df_wind["ownership_operator_name"] = df_wind["operator"]
    df_wind["ownership_operator_id"] = "NA"

    # SECTOR
    # add information on onshore/offshore etc
    df_wind["sector"] = "wind power/"+df_wind["installation_type"]

    # EXPORT
    df_wind = df_wind.rename(columns={"project_name": "asset_name", 
                                      "gem_location_id": "plant_id"}) # in the lack of a plant_id

    # keep vars defined above
    df_wind = df_wind[vars_to_keep]             


    ###---------------------------------------------------------------
    ### --- 1.2) STEEL --- ###

    file = source_dict['steel_plant'][0]
    sheet = source_dict['steel_plant'][1]

    df_steel = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
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

#    CLEAN OWNER
    df_steel["parent_[formula]"] = df_steel["parent_[formula]"].str.split(";", expand=True)[0]
    df_steel["parent_permid_[formula]"] = df_steel["parent_permid_[formula]"].str.split(";", expand=True)[0]
    
    df_steel["parent_[formula]"] = df_steel["parent_[formula]"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()
    df_steel["parent_permid_[formula]"] = df_steel["parent_permid_[formula]"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

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
    df_steel = df_steel.rename(columns={"coordinate_accuracy": "location_accuracy", 
                                        "plant_name_(english)": "asset_name", 
                                        "start_date": "start_year"})


    # keep vars defined above
    df_steel = df_steel[vars_to_keep]

    ###---------------------------------------------------------------
    ### --- 1.3) SOLAR --- ###
    file = source_dict['solar_power'][0]
    sheet = source_dict['solar_power'][1]

    df_solar = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_solar = clean_col_names(df_solar) # turn cols into lowercase

    # STATUS
    df_solar = df_solar[df_solar["status"] == "operating"]

    # CAPACITY
    df_solar = df_solar.rename(columns={"capacity_(mw)": "capacity"})
    df_solar["capacity_unit"] = "mw (peak value, grid connected, or unknown)"

    # CLEAN OWNER
    df_solar["owner"] = df_solar["owner"].str.split(";", expand=True)[0]
    df_solar["owner"] = df_solar.owner.str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()
    
    df_solar["operator"] = df_solar["operator"].str.split(";", expand=True)[0]
    df_solar["operator"] = df_solar["operator"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # OWNERSHIP INFORMARTION
    df_solar["ownership_parent_name"] = "NA"
    df_solar["ownership_parent_id"] = "NA"
    df_solar["ownership_owner_name"] = df_solar["owner"]
    df_solar["ownership_owner_id"] = "NA"
    df_solar["ownership_operator_name"] = df_solar["operator"]
    df_solar["ownership_operator_id"] = "NA"

    # SECTOR
    df_solar["sector"] = "solar power/"+df_solar["technology_type"].str.lower()

    # EXPORT
    df_solar = df_solar.rename(columns={"project_name": "asset_name", 
                                      "gem_location_id": "plant_id"}) 
    
    df_solar = df_solar[vars_to_keep]        

    ###---------------------------------------------------------------
    ### --- 1.4) OIL & GAS EXTRACTION --- ###
    file = source_dict['oil_and_gas_extraction'][0]
    sheet = source_dict['oil_and_gas_extraction'][1]

    df_oil_gas_extraction = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_oil_gas_extraction = clean_col_names(df_oil_gas_extraction) # turn cols into lowercase

    # STATUS
    df_oil_gas_extraction = df_oil_gas_extraction[df_oil_gas_extraction["status"] == "operating"]
    
    # CAPACITY
    df_oil_gas_extraction["capacity"] = "NA (O&G extraction)"
    df_oil_gas_extraction["capacity_unit"] = "NA"

    # OWNERSHIP INFORMARTION

    # CLEAN OWNER
    df_oil_gas_extraction["parent"] = df_oil_gas_extraction["parent"].str.split(";", expand=True)[0]
    df_oil_gas_extraction["parent"] = df_oil_gas_extraction["parent"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()
    
    df_oil_gas_extraction["owner"] = df_oil_gas_extraction["owner"].str.split(";", expand=True)[0]
    df_oil_gas_extraction["owner"] = df_oil_gas_extraction["owner"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    df_oil_gas_extraction["operator"] = df_oil_gas_extraction["operator"].str.split(";", expand=True)[0]
    df_oil_gas_extraction["operator"] = df_oil_gas_extraction["operator"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # define final ownership columns
    df_oil_gas_extraction["ownership_parent_name"] = df_oil_gas_extraction["parent"]
    df_oil_gas_extraction["ownership_parent_id"] = "NA"
    df_oil_gas_extraction["ownership_owner_name"] = df_oil_gas_extraction["owner"]
    df_oil_gas_extraction["ownership_owner_id"] = "NA"
    df_oil_gas_extraction["ownership_operator_name"] = df_oil_gas_extraction["operator"]
    df_oil_gas_extraction["ownership_operator_id"] = "NA"

    # SECTOR
    df_oil_gas_extraction["sector"] = "oil & gas extraction/"+df_oil_gas_extraction["fuel_type"].str.lower()

    # EXPORT
    df_oil_gas_extraction = df_oil_gas_extraction.rename(columns={"unit_id": "plant_id", 
                                                                  "unit_name": "asset_name", 
                                                                  "production_start_year": "start_year"}) # in the lack of a plant_id
    df_oil_gas_extraction = df_oil_gas_extraction[vars_to_keep]      

    # ###---------------------------------------------------------------
    # ### --- 1.5) NUCLEAR --- ###

    file = source_dict['nuclear_power'][0]
    sheet = source_dict['nuclear_power'][1]

    df_nuclear = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_nuclear = clean_col_names(df_nuclear) # turn cols into lowercase

    # STATUS
    df_nuclear = df_nuclear[df_nuclear["status"] == "operating"]

    # CAPACITY
    df_nuclear = df_nuclear.rename(columns={"capacity_(mw)": "capacity"})
    df_nuclear["capacity_unit"] = "mw"

    # CLEAN OWNER
    df_nuclear["owner"] = df_nuclear["owner"].str.split(";", expand=True)[0]
    df_nuclear["owner"] = df_nuclear["owner"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    df_nuclear["operator"] = df_nuclear["operator"].str.split(";", expand=True)[0]
    df_nuclear["operator"] = df_nuclear["operator"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # OWNERSHIP INFORMARTION
    df_nuclear["ownership_parent_name"] = "NA"
    df_nuclear["ownership_parent_id"] = "NA"
    df_nuclear["ownership_owner_name"] = df_nuclear["owner"]
    df_nuclear["ownership_owner_id"] = "NA"
    df_nuclear["ownership_operator_name"] = df_nuclear["operator"]
    df_nuclear["ownership_operator_id"] = "NA"
    
    
    df_nuclear.rename(columns = {"project_name": "asset_name", 
                                 "gem_location_id": "plant_id",
                                 "start_year": "start_year"}, inplace = True)

    # SECTOR
    df_nuclear["sector"] = "nuclear/" + df_nuclear['reactor_type'].str.lower()

    # EXPORT
    df_nuclear = df_nuclear[vars_to_keep]

    # ###---------------------------------------------------------------
    # ### --- 1.6) HYDROPOWER --- ###

    file = source_dict['hydropower'][0]
    sheet = source_dict['hydropower'][1]

    df_hydropower = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_hydropower = clean_col_names(df_hydropower) # turn cols into lowercase

    # STATUS
    df_hydropower = df_hydropower[df_hydropower["status"] == "operating"]

    # CAPACITY
    df_hydropower = df_hydropower.rename(columns={"capacity_(mw)": "capacity"})
    df_hydropower["capacity_unit"] = "mw"

    # CLEAN OWNER
    df_hydropower["owner"] = df_hydropower["owner"].str.split(";", expand=True)[0]
    df_hydropower["owner"] = df_hydropower["owner"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    df_hydropower["operator"] = df_hydropower["operator"].str.split(";", expand=True)[0]
    df_hydropower["operator"] = df_hydropower["operator"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # OWNERSHIP INFORMARTION
    df_hydropower["ownership_parent_name"] = "NA"
    df_hydropower["ownership_parent_id"] = "NA"
    df_hydropower["ownership_owner_name"] = df_hydropower["owner"]
    df_hydropower["ownership_owner_id"] = "NA"
    df_hydropower["ownership_operator_name"] = df_hydropower["operator"]
    df_hydropower["ownership_operator_id"] = "NA"

    df_hydropower.rename(columns = {"project_name": "asset_name", 
                                    "gem_location_id": "plant_id",
                                    "start_year": "start_year", 
                                    "country_1": "country"}, inplace = True)


    # SECTOR
    df_hydropower["sector"] = "hydropower/"+df_hydropower["technology_type"].str.lower()

    # EXPORT
    df_hydropower = df_hydropower[vars_to_keep]      


    # ###---------------------------------------------------------------
    # ### --- 1.7) GEOTHERMAL --- ###

    file = source_dict['geothermal_power'][0]
    sheet = source_dict['geothermal_power'][1]

    df_geothermal = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_geothermal = clean_col_names(df_geothermal) # turn cols into lowercase

    # STATUS
    df_geothermal = df_geothermal[df_geothermal["status"] == "operating"]

    # CAPACITY
    df_geothermal = df_geothermal.rename(columns={"unit_capacity_(mw)": "capacity"})
    df_geothermal["capacity_unit"] = "mw"

    # CLEAN OWNER
    df_geothermal["owner"] = df_geothermal["owner"].str.split(";", expand=True)[0]
    df_geothermal["owner"] = df_geothermal["owner"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    df_geothermal["operator"] = df_geothermal["operator"].str.split(";", expand=True)[0]
    df_geothermal["operator"] = df_geothermal["operator"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # OWNERSHIP INFORMARTION
    df_geothermal["ownership_parent_name"] = "NA"
    df_geothermal["ownership_parent_id"] = "NA"
    df_geothermal["ownership_owner_name"] = df_geothermal["owner"]
    df_geothermal["ownership_owner_id"] = "NA"
    df_geothermal["ownership_operator_name"] = df_geothermal["operator"]
    df_geothermal["ownership_operator_id"] = "NA"


    df_geothermal.rename(columns = {"project_name": "asset_name", 
                                 "gem_location_id": "plant_id",
                                 "start_year": "start_year"}, inplace = True)
    
    # SECTOR
    df_geothermal["sector"] = "geothermal/" + df_geothermal['type'].str.lower()

    # EXPORT
    df_geothermal = df_geothermal[vars_to_keep]      

    # ###---------------------------------------------------------------
    # ### --- 1.8) COAL TERMINALS --- ###

    file = source_dict['coal_terminals'][0]
    sheet = source_dict['coal_terminals'][1]

    df_coal_terminals = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_coal_terminals = clean_col_names(df_coal_terminals) # turn cols into lowercase

    # STATUS
    df_coal_terminals = df_coal_terminals[df_coal_terminals["status"] == "Operating"]

    # CAPACITY
    df_coal_terminals = df_coal_terminals.rename(columns={"capacity_(mt)": "capacity"})
    df_coal_terminals["capacity_unit"] = "mt"

    # CLEAN OWNER
    df_coal_terminals["owner"] = df_coal_terminals["owner"].str.split(";", expand=True)[0]
    df_coal_terminals["owner"] = df_coal_terminals["owner"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # OWNERSHIP INFORMARTION
    df_coal_terminals["ownership_parent_name"] = "NA"
    df_coal_terminals["ownership_parent_id"] = "NA"
    df_coal_terminals["ownership_owner_name"] = df_coal_terminals["owner"]
    df_coal_terminals["ownership_owner_id"] = "NA"
    df_coal_terminals["ownership_operator_name"] = "NA"
    df_coal_terminals["ownership_operator_id"] = "NA"


    df_coal_terminals.rename(columns = {"coal_terminal_name": "asset_name", 
                                 "terminal_id": "plant_id",
                                 "opening_year": "start_year", 
                                 "accuracy": "location_accuracy"}, inplace = True)


    # SECTOR
    df_coal_terminals["sector"] = "coal terminal/"+df_coal_terminals['product_type'].str.lower()

    # EXPORT
    df_coal_terminals = df_coal_terminals[vars_to_keep]      

    # ###---------------------------------------------------------------
    # ### --- 1.9) COAL PLANTS --- ###

    file = source_dict['coal_plant'][0]
    sheet = source_dict['coal_plant'][1]

    df_coal_plant = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_coal_plant = clean_col_names(df_coal_plant) # turn cols into lowercase

    # STATUS
    df_coal_plant = df_coal_plant[df_coal_plant["status"] == "operating"]

    # CAPACITY
    df_coal_plant = df_coal_plant.rename(columns={"capacity_(mw)": "capacity"})
    df_coal_plant["capacity_unit"] = "mw"

    # CLEAN OWNER
    df_coal_plant["owner"] = df_coal_plant["owner"].str.split(";", expand=True)[0]
    df_coal_plant["owner"] = df_coal_plant["owner"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    df_coal_plant["parent"] = df_coal_plant["parent"].str.split(";", expand=True)[0]
    df_coal_plant["parent"] = df_coal_plant["parent"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # OWNERSHIP INFORMARTION
    df_coal_plant["ownership_parent_name"] = df_coal_plant["parent"]
    df_coal_plant["ownership_parent_id"] = "NA"
    df_coal_plant["ownership_owner_name"] = df_coal_plant["owner"]
    df_coal_plant["ownership_owner_id"] = "NA"
    df_coal_plant["ownership_operator_name"] = "NA"
    df_coal_plant["ownership_operator_id"] = "NA"


    df_coal_plant.rename(columns = {"plant_name": "asset_name", 
                                    "gem_location_id": "plant_id",
                                    "start_year": "start_year"}, inplace = True)


    # SECTOR
    df_coal_plant["sector"] = "coal plant/"+ df_coal_plant['coal_type'].str.lower()

    # EXPORT
    df_coal_plant = df_coal_plant[vars_to_keep]      

    # ###---------------------------------------------------------------
    # ### --- 1.10) COAL MINES --- ###

    file = source_dict['coal_mine'][0]
    sheet = source_dict['coal_mine'][1]

    df_coal_mine = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_coal_mine = clean_col_names(df_coal_mine) # turn cols into lowercase

    # STATUS
    df_coal_mine = df_coal_mine[df_coal_mine["status"] == "Operating"]

    # CAPACITY
    df_coal_mine = df_coal_mine.rename(columns={"coal_output_(annual,_mt)": "capacity"})
    df_coal_mine["capacity_unit"] = "mt per year"

    # CLEAN OWNER
    df_coal_mine["owners"] = df_coal_mine["owners"].str.split(";", expand=True)[0]
    df_coal_mine["owners"] = df_coal_mine["owners"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()
   
    df_coal_mine["parent_company"] = df_coal_mine["parent_company"].str.split(";", expand=True)[0]
    df_coal_mine["parent_company"] = df_coal_mine["parent_company"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # OWNERSHIP INFORMARTION
    df_coal_mine["ownership_parent_name"] = df_coal_mine["parent_company"]
    df_coal_mine["ownership_parent_id"] = "NA"
    df_coal_mine["ownership_owner_name"] = df_coal_mine["owners"]
    df_coal_mine["ownership_owner_id"] = "NA"
    df_coal_mine["ownership_operator_name"] = "NA"
    df_coal_mine["ownership_operator_id"] = "NA"


    df_coal_mine.rename(columns = {"mine_name": "asset_name", 
                                 "mine_ids": "plant_id",
                                 "opening_year": "start_year"}, inplace = True)


    # SECTOR
    df_coal_mine["sector"] = "coal mine/"+df_coal_mine["mine_type"].str.lower()

    # EXPORT
    df_coal_mine = df_coal_mine[vars_to_keep]      

    # ###---------------------------------------------------------------
    # ### --- 1.11) LNG TERMINAL --- ###

    file = source_dict['lng_terminals'][0]
    sheet = source_dict['lng_terminals'][1]

    df_lng_terminals = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_lng_terminals = clean_col_names(df_lng_terminals) # turn cols into lowercase

    # STATUS
    df_lng_terminals = df_lng_terminals[df_lng_terminals["status"] == "Operating"]

    # CAPACITY
    df_lng_terminals = df_lng_terminals.rename(columns={"capacity": "capacity"})
    df_lng_terminals["capacity_unit"] = df_lng_terminals["capacityunits"]

    # CLEAN OWNER
    df_lng_terminals["owner"] = df_lng_terminals["owner"].str.split(";", expand=True)[0]
    df_lng_terminals["owner"] = df_lng_terminals["owner"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()
   
    df_lng_terminals["parent"] = df_lng_terminals["parent"].str.split(";", expand=True)[0]
    df_lng_terminals["parent"] = df_lng_terminals["parent"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()
   
   # OWNERSHIP INFORMARTION
    df_lng_terminals["ownership_parent_name"] = df_lng_terminals["parent"]
    df_lng_terminals["ownership_parent_id"] = "NA"
    df_lng_terminals["ownership_owner_name"] = df_lng_terminals["owner"]
    df_lng_terminals["ownership_owner_id"] = "NA"
    df_lng_terminals["ownership_operator_name"] = "NA"
    df_lng_terminals["ownership_operator_id"] = "NA"


    df_lng_terminals.rename(columns = {"terminalname": "asset_name", 
                                 "terminalid": "plant_id",
                                 "startyear1": "start_year", 
                                 "accuracy": "location_accuracy"}, inplace = True)


    # SECTOR
    df_lng_terminals["sector"] = "LNG terminal/"+df_lng_terminals['facilitytype'].str.lower()

    # EXPORT
    df_lng_terminals = df_lng_terminals[vars_to_keep]     
 
    # ###---------------------------------------------------------------
    # ### --- 1.12) BIOENERGY --- ###

    file = source_dict['bioenergy_power'][0]
    sheet = source_dict['bioenergy_power'][1]

    df_bioenergy = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
    df_bioenergy = clean_col_names(df_bioenergy) # turn cols into lowercase

    # STATUS
    df_bioenergy = df_bioenergy[df_bioenergy["operating_status"] == "operating"]

    # CAPACITY
    df_bioenergy = df_bioenergy.rename(columns={"capacity_(mw)": "capacity"})
    df_bioenergy["capacity_unit"] = "mw"

    # CLEAN OWNER
    df_bioenergy["owner"] = df_bioenergy["owner"].str.split(";", expand=True)[0]
    df_bioenergy["owner"] = df_bioenergy["owner"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()
    
    df_bioenergy["operator"] = df_bioenergy["operator"].str.split(";", expand=True)[0]
    df_bioenergy["operator"] = df_bioenergy["operator"].str.replace("[\[\(]\d*[.]?\d*[%][\s*]?[\]\)]", '', regex=True).str.strip()

    # OWNERSHIP INFORMARTION
    df_bioenergy["ownership_parent_name"] = "NA"
    df_bioenergy["ownership_parent_id"] = "NA"
    df_bioenergy["ownership_owner_name"] = df_bioenergy["owner"]
    df_bioenergy["ownership_owner_id"] = "NA"
    df_bioenergy["ownership_operator_name"] = df_bioenergy["operator"]
    df_bioenergy["ownership_operator_id"] = "NA"


    df_bioenergy.rename(columns = {"project_name": "asset_name", 
                                 "gem_location_id": "plant_id",
                                 "unit_start_year": "start_year", 
                                 "operating_status": "status"}, inplace = True)


    # SECTOR
    df_bioenergy["sector"] = "bioenergy"

    # EXPORT
    df_bioenergy = df_bioenergy[vars_to_keep]

    # ###---------------------------------------------------------------
    # ### --- 1.X) TO DOS --- ###

    # # continue with other tabs
    # #'', '', '', '', 'blast_furnaces_relining', 'blast_furnaces', 'bioenergy', 'oil_pipelines', 'lng_terminals', 'gas_pipeline'


    ##################################################
    ######    2) CONSOLIDATION                  ######
    ##################################################

    # combine all dataframes
    list_of_dfs = [df_wind, df_steel, df_solar, df_oil_gas_extraction, df_nuclear, 
                   df_hydropower, df_geothermal, df_coal_terminals, df_coal_plant, df_coal_mine, 
                   df_lng_terminals, df_bioenergy] #, df_steel, df_solar, df_oil_gas_plants, df_oil_gas_extraction]
    df_gem = pd.concat(list_of_dfs)
    
    # turn string variables into string type
    string_variables = ['ownership_parent_name', 'ownership_operator_name', 'ownership_owner_name']
    for var in string_variables:
        df_gem[var] = df_gem[var].astype(str)
        df_gem[var].fillna('', inplace=True) # fill nan with empty string
        
    # create unique id variable
    df_gem.rename(columns={"plant_id": "uid_gem"}, inplace=True)
    df_gem['uid'] = ['GEM_' + str(num) for num in list(range(len(df_gem)))]

    # rename columns to streamline with other data sets
    df_gem.rename(columns = {'ownership_parent_name': 'parent_name',
                        'ownership_owner_name': 'owner_name', 
                        'ownership_operator_name': 'operator_name'}, inplace=True)
    
    # Save output to CSV
    output_path = os.path.join(PATH_TO_OUTPUT_FOLDER,"asset_level_open_source_gem.csv")
    df_gem.to_csv(output_path, index=False)

    return df_gem

    ### --- 1.X) BLUEPRINT --- ###
    """
    BLUEPRINT FOR COPY & PASTE

    file = source_dict['TBD'][0]
    sheet = source_dict['TBD'][1]

    df_XXX = pd.read_excel(input_path + "/" + file, sheet_name=sheet)
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


     df_XXX.rename(columns = {"project_name": "asset_name", 
                                 "gem_location_id": "plant_id",
                                 "start_year": "start_year"}, inplace = True)


    # SECTOR
    df_XXX["sector"] = "TBD"

    # EXPORT
    df_XXX = df_XXX[vars_to_keep]      
    """