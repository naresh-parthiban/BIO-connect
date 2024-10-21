from django.shortcuts import render
from django.http import JsonResponse
import requests
import logging
import json
from .models import NCBIData
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger('ncbi_data')

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
    try:
        # 1. Remove duplicates
        unique_ids = list(set(data["esearchresult"]["idlist"]))
        data["esearchresult"]["idlist"] = unique_ids

        # 2. Handle missing entries
        if "idlist" not in data["esearchresult"] or not data["esearchresult"]["idlist"]:
            return None, None

        # 3. Standardize IDs
        id_list = list(map(int, data["esearchresult"]["idlist"]))
        data["esearchresult"]["idlist"] = id_list

        # 4. Clean irrelevant fields
        irrelevant_fields = ["translationset", "translationstack", "querytranslation"]
        for field in irrelevant_fields:
            if field in data["esearchresult"]:
                del data["esearchresult"][field]

        # 5. Convert data types
        data["esearchresult"]["count"] = int(data["esearchresult"]["count"])
        data["esearchresult"]["retmax"] = int(data["esearchresult"]["retmax"])
        data["esearchresult"]["retstart"] = int(data["esearchresult"]["retstart"])

        # 6. Parse nested data (optional)
        translation_term = None
        if "translationstack" in data["esearchresult"]:
            translation_stack = data["esearchresult"]["translationstack"]
            if translation_stack and isinstance(translation_stack[0], dict):
                translation_term = translation_stack[0].get("term")

        # 7. Add a timestamp for when the data was cleaned
        from datetime import datetime
        data["esearchresult"]["cleaned_timestamp"] = datetime.now().isoformat()

        # 8. Limit the number of results to improve performance
        max_results = 1000
        if len(id_list) > max_results:
            data["esearchresult"]["idlist"] = id_list[:max_results]
            data["esearchresult"]["warning"] = f"Results limited to {max_results} entries"

        return data, translation_term

    except Exception as e:
        # Log the error for debugging purposes
        logging.error(f"Error in clean_ncbi_data: {str(e)}")
        return None, None

def ncbi_data_view(request):
    if request.method == 'POST':
        # Validate required fields
        required_fields = ['db', 'query']
        for field in required_fields:
            if field not in request.POST:
                return JsonResponse({"error": f"Missing required field: {field}"}, status=400)

        db = request.POST.get('db')
        query = request.POST.get('query')
        retmax = request.POST.get('retmax', 20)
        sort = request.POST.get('sort', 'relevance')
        field = request.POST.get('field')

        # Validate db
        valid_dbs = ['pubmed', 'protein', 'nuccore', 'nucleotide', 'gene']
        if db not in valid_dbs:
            return JsonResponse({"error": f"Invalid database. Choose from: {', '.join(valid_dbs)}"}, status=400)

        # Validate query
        if not query.strip():
            return JsonResponse({"error": "Query cannot be empty"}, status=400)

        # Validate retmax
        try:
            retmax = int(retmax)
            if retmax < 1 or retmax > 100:
                return JsonResponse({"error": "retmax must be between 1 and 100"}, status=400)
        except ValueError:
            return JsonResponse({"error": "retmax must be an integer"}, status=400)

        # Validate sort
        valid_sort_options = ['relevance', 'pub_date']
        if sort not in valid_sort_options:
            return JsonResponse({"error": f"Invalid sort option. Choose from: {', '.join(valid_sort_options)}"}, status=400)

        # Validate field (optional)
        if field:
            valid_fields = ['title', 'abstract', 'author']
            if field not in valid_fields:
                return JsonResponse({"error": f"Invalid field. Choose from: {', '.join(valid_fields)}"}, status=400)

        # Check if data exists in the database
        try:
            ncbi_data = NCBIData.objects.get(db=db, query=query)
            logger.info(f"Retrieved existing data from database for db: {db}, query: {query}")
            print(f"Retrieved existing data from database for db: {db}, query: {query}")
            return JsonResponse({
                'cleaned_data': ncbi_data.get_data(),
                'translation_term': ncbi_data.translation_term
            })
        except ObjectDoesNotExist:
            logger.info(f"Data not found in database for db: {db}, query: {query}. Fetching from NCBI API.")
            print(f"Data not found in database for db: {db}, query: {query}. Fetching from NCBI API.")
            # If data doesn't exist, fetch it from the NCBI API
            data = fetch_ncbi_data(db=db, query=query, retmax=retmax, sort=sort, field=field)

            if "error" in data:
                logger.error(f"Error fetching data from NCBI API: {data['error']}")
                print(f"Error fetching data from NCBI API: {data['error']}")
                return JsonResponse({"error": data["error"]}, status=400)

            try:
                cleaned_data, translation_term = clean_ncbi_data(data)
                if cleaned_data is None:
                    logger.warning(f"No valid data found for db: {db}, query: {query}")
                    print(f"No valid data found for db: {db}, query: {query}")
                    return JsonResponse({"error": "No valid data found"}, status=404)

                # Store the cleaned data in the database
                ncbi_data = NCBIData(
                    db=db,
                    query=query,
                    translation_term=translation_term
                )
                ncbi_data.set_data(cleaned_data)
                ncbi_data.save()
                logger.info(f"Saved new data to database for db: {db}, query: {query}")
                print(f"Saved new data to database for db: {db}, query: {query}")

                return JsonResponse({
                    'cleaned_data': cleaned_data,
                    'translation_term': translation_term
                })
            except Exception as e:
                logger.exception(f"Error processing data for db: {db}, query: {query}")
                print(f"Error processing data for db: {db}, query: {query}: {str(e)}")
                return JsonResponse({"error": f"Error processing data: {str(e)}"}, status=500)

    return render(request, 'ncbi_data/form.html')
