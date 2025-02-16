from django.shortcuts import render

def home(request):
    return render(request, 'index.html')  # Pointing to templates/home.html

def epl(request):
    return render(request, 'epl.html')

def contact(request):
    return render(request, 'contact.html')
