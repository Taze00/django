from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def freundin_page(request):
    return render(request, "schubi.html")

def impressum(request):
    return render(request, 'impressum.html')

def fitness_page(request):
    return render(request, 'fitness.html')

def festival_page(request):
    return render(request, 'festival.html')

def skills_page(request):
    return render(request, 'skills.html')

def fitness_landing_page(request):
    return render(request, 'fitness-landing.html')

