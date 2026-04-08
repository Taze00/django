from django.shortcuts import render


def geo_page(request):
    return render(request, 'geo.html')
