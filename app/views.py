from django.shortcuts import render

def home(request):
    return render(request, 'index.html')  # Pointing to templates/home.html

def about(request):
    return render(request, 'about.html')
