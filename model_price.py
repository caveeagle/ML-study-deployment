# model_price.py
# This module contains the logic that calculates the price
# based on the form data received from Shiny.

import pandas as pd
from joblib import load

mapping_dataset = "./data/postal_code_mapping.csv"
df = pd.read_csv(   mapping_dataset, 
                    na_values=["None"],
                    keep_default_na=True,
                    delimiter=","
                 )

best_model_path = "./data/best_model.joblib"
best_model = load(best_model_path)

def calculate_price(data: dict) -> int:
    """
    form_data: dictionary containing all form fields collected from Shiny.
    Returns: integer price in euros.
    """
    # print( repr(data) )

    model_params = {}
    
    postal_code: int
    
    ####################################################
    
    if not data.get('postal_code'):
        model_params['postal_code'] = 4000  # the most frequent value
        postal_code = 4000  # also to the val.
    else:    
        model_params['postal_code'] = data.get('postal_code')
        postal_code = data.get('postal_code')
        
    ####################################################
    ####################################################
    
    median_fields = ["area", "rooms", "cadastral_income","number_floors",
                     "bathrooms", "toilets","facades_number","primary_energy_consumption"]
    
    for field in median_fields:
        if not data.get(field):
            # имя столбца в DataFrame: median_area, median_rooms, …
            col = f"median_{field}"
            model_params[field] = df.set_index("postal_code")[col].get(postal_code)
        else:
            model_params[field] = data.get(field)

    ####################################################
    
    bool_fields = [
        "has_swimming_pool",
        "has_terrace",
        "has_garden",
        "has_garage",
        "is_furnished",
        "elevator"
    ]
    
    for field in bool_fields:
        value = data.get(field)
        model_params[field] = int(bool(value))

    ####################################################

    # Constant fields, not important for model
    model_params['running_water'] = 1
    model_params['leased'] = 0

    ####################################################
    
    valid_localities = [
        "antwerp",
        "braine-l-alleud",
        "brussels",
        "gent",
        "laken",
        "liege",
        "lier",
        "mons",
        "mouscron",
        "namur",
        "nivelles",
        "oostende",
        "other",
        "pont-a-celles",
        "roeselare",
        "seraing",
        "tournai",
        "tubize",
        "turnhout",
        "wavre"
    ]
    
    # 1) Read locality from mapping_df for this postal_code
    row = df.loc[df["postal_code"] == postal_code, "locality"]
    
    if row.empty:
        locality = None
    else:
        val = row.iloc[0]
        # If val is NaN → treat as None
        if pd.isna(val):
            locality = None
        else:
            locality = str(val).strip().lower()
    
    # 2) Fill all locality_* boolean fields: one-hot or all False
    for name in valid_localities:
        key = f"locality_{name}"
        model_params[key] = (locality == name)
    
    ####################################################

    if not data.get('build_year'):
        model_params['build_year'] = 2010  # median
    else:    
        model_params['build_year'] = data.get('build_year')
    
    model_params["property_type_house"] = (data.get("property_type") == "house")
    model_params["property_type_other"] = (data.get("property_type") != "house")
   
    subtype = data.get("property_subtype")
    
    if subtype == "":
        subtype = "other"
    
    for name in ["studio", "duplex", "residence", "villa", "other"]:
        key = f"property_subtype_{name}"
        model_params[key] = (subtype == name)
    
    ####################################################

    ek = (data.get("equipped_kitchen") or "").strip()
    
    if ek == "Fully equipped":
        ek_mapped = "Super equipped"
    else:
        ek_mapped = ek  # "Not equipped" or "Partially equipped"
    
    ek_levels = [
        "Not equipped",
        "Partially equipped",
        "Super equipped",
    ]
    
    for level in ek_levels:
        key = f"has_equipped_kitchen_{level}"  # spaces stay in the key
        model_params[key] = (ek_mapped == level)
    
    ####################################################
    ####################################################
    ####################################################
    
    #print(best_model.feature_names_in_)
    #print(model_params)
    
    # Get feature names from the model (exact order used during training)
    required_cols = list(best_model.feature_names_in_)
    
    # Build DataFrame exactly in this order
    X = pd.DataFrame([[model_params[col] for col in required_cols]], columns=required_cols)
    
    # Predict
    pred_price = best_model.predict(X)[0]
    
    
    ####################################################
    ####################################################
    ####################################################
    #####################################################
    
    pred_price = int(round(pred_price,-2))

    return pred_price

#####################################################
#####################################################
#####################################################


data_empty_form = "{'postal_code': 9000, 'rooms': None, 'area': None, 'number_floors': None, 'bathrooms': 1, 'toilets': 1, 'equipped_kitchen': 'Fully equipped', 'property_type': '', 'property_subtype': '', 'has_swimming_pool': False, 'has_terrace': False, 'has_garden': False, 'has_garage': False, 'elevator': False, 'is_furnished': False, 'facades_number': None, 'build_year': None, 'cadastral_income': None, 'primary_energy_consumption': None}"

data_full_form = "{'postal_code': 1030, 'rooms': 4, 'area': 1100, 'number_floors': 2, 'bathrooms': 1, 'toilets': 1, 'equipped_kitchen': 'Fully equipped', 'property_type': 'apartment', 'property_subtype': 'residence', 'has_swimming_pool': False, 'has_terrace': True, 'has_garden': False, 'has_garage': False, 'elevator': True, 'is_furnished': False, 'facades_number': 3, 'build_year': 2000, 'cadastral_income': None, 'primary_energy_consumption': None}"    

#data_dict = eval(data_full_form)
data_dict = eval(data_empty_form)

result = calculate_price(data_dict)

print('Result:',result)
