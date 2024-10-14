import requests

def fetch_ncbi_data(db, query, rettype="json"):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    url = f"{base_url}esearch.fcgi?db={db}&term={query}&rettype={rettype}&retmode=json"
    response = requests.get(url)
    return response.json()

def clean_ncbi_data(data):
    # 1. Remove duplicates
    data = remove_duplicates(data)
    
    # 2. Handle missing entries
    data = remove_missing_entries(data)
    
    # 3. Standardize IDs
    data = standardize_ids(data)
    
    # 4. Clean irrelevant fields
    data = clean_irrelevant_fields(data)
    
    # 5. Convert data types
    data = convert_data_types(data)
    
    # 6. Parse nested data (optional)
    translation_term = parse_nested_data(data)
    
    return data, translation_term

def remove_duplicates(data):
    unique_ids = list(set(data["esearchresult"]["idlist"]))
    data["esearchresult"]["idlist"] = unique_ids
    return data

def remove_missing_entries(data):
    if "idlist" in data["esearchresult"] and data["esearchresult"]["idlist"]:
        return data
    else:
        return None

def standardize_ids(data):
    data["esearchresult"]["idlist"] = [int(id) for id in data["esearchresult"]["idlist"]]
    return data

def clean_irrelevant_fields(data):
    if "translationset" in data["esearchresult"]:
        del data["esearchresult"]["translationset"]
    return data

def convert_data_types(data):
    data["esearchresult"]["count"] = int(data["esearchresult"]["count"])
    return data

def parse_nested_data(data):
    translation_info = data["esearchresult"]["translationstack"][0]["term"]
    return translation_info

# Fetch, clean, and analyze data
data = fetch_ncbi_data(db="gene", query="BRCA1")
cleaned_data, translation_term = clean_ncbi_data(data)
print(cleaned_data)
print(f"Translation Term: {translation_term}")
