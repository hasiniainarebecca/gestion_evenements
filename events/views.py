from django.shortcuts import render
from django.http import HttpResponse

# --- VUES TEMPORAIRES (À remplacer par le Membre C) ---

def event_list(request):
    # Pour l'instant, on affiche juste le template base.html pour tester
    return render(request, 'base.html') 

def event_detail(request, pk):
    return HttpResponse(f"Détail de l'événement {pk}")

def register(request, pk):
    return HttpResponse("Page d'inscription")

def my_registrations(request):
    return HttpResponse("Mes inscriptions")

def cancel_registration(request, pk):
    return HttpResponse("Annuler inscription")

def signup(request):
    return HttpResponse("Créer un compte")

def login_view(request):
    return HttpResponse("Connexion")

def logout_view(request):
    return HttpResponse("Déconnexion")

def manager_dashboard(request):
    return HttpResponse("Tableau de bord gestionnaire")

def event_create(request):
    return HttpResponse("Créer un événement")

def event_update(request, pk):
    return HttpResponse(f"Modifier l'événement {pk}")

def event_registrants(request, pk):
    return HttpResponse(f"Liste des inscrits pour {pk}")

def manager_cancel_registration(request, pk):
    return HttpResponse(f"Annulation gestionnaire pour {pk}")