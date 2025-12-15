from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def freundin_page(request):
    return render(request, "schubi.html")

def impressum(request):
    return render(request, 'impressum.html')