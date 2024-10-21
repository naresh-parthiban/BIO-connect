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
