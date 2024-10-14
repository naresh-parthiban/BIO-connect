from django.shortcuts import render
from django.http import JsonResponse
import requests

def fetch_ncbi_data(db, query, rettype="json", retmax=20, sort="relevance", field=None):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    params = {
        "db": db,
        "term": query,
        "rettype": rettype,
        "retmode": "json",
        "retmax": retmax,
        "sort": sort
    }
    if field:
        params["field"] = field

    try:
        response = requests.get(f"{base_url}esearch.fcgi", params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": f"Error fetching data from NCBI: {str(e)}"}

def clean_ncbi_data(data):
    # 1. Remove duplicates
    unique_ids = list(set(data["esearchresult"]["idlist"]))
    data["esearchresult"]["idlist"] = unique_ids
    
    # 2. Handle missing entries
    if "idlist" not in data["esearchresult"] or not data["esearchresult"]["idlist"]:
        return None
    
    # 3. Standardize IDs
    id_list = list(map(int, data["esearchresult"]["idlist"]))
    
    # 4. Clean irrelevant fields
    if "translationset" in data["esearchresult"]:
        del data["esearchresult"]["translationset"]
    
    # 5. Convert data types
    data["esearchresult"]["count"] = int(data["esearchresult"]["count"])
    
    # 6. Parse nested data (optional)
    translation_term = data["esearchresult"]["translationstack"][0]["term"] if "translationstack" in data["esearchresult"] else None
    
    return data, translation_term

def ncbi_data_view(request):
    if request.method == 'POST':
        db = request.POST.get('db')
        query = request.POST.get('query')
        retmax = request.POST.get('retmax', 20)
        sort = request.POST.get('sort', 'relevance')
        field = request.POST.get('field')
        
        data = fetch_ncbi_data(db=db, query=query, retmax=retmax, sort=sort, field=field)
        
        if "error" in data:
            return JsonResponse({"error": data["error"]}, status=400)
        
        try:
            cleaned_data, translation_term = clean_ncbi_data(data)
            if cleaned_data is None:
                return JsonResponse({"error": "No valid data found"}, status=404)
            
            return JsonResponse({
                'cleaned_data': cleaned_data,
                'translation_term': translation_term
            })
        except Exception as e:
            return JsonResponse({"error": f"Error processing data: {str(e)}"}, status=500)
    
    return render(request, 'ncbi_data/form.html')
