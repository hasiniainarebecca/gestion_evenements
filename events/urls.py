from django.urls import path
from . import views

urlpatterns = [
    path('', views.event_list, name='event_list'),
    path('evenements/<int:pk>/', views.event_detail, name='event_detail'),
    path('evenements/<int:pk>/inscription/', views.register, name='register'),
    path('mes-inscriptions/', views.my_registrations, name='my_registrations'),
    path('inscriptions/<int:pk>/annuler/', views.cancel_registration, name='cancel_registration'),
    path('compte/inscription/', views.signup, name='signup'),
    path('compte/connexion/', views.login_view, name='login'),
    path('compte/deconnexion/', views.logout_view, name='logout'),
    path('gestion/', views.manager_dashboard, name='manager_dashboard'),
    path('gestion/evenements/nouveau/', views.event_create, name='event_create'),
    path('gestion/evenements/<int:pk>/modifier/', views.event_update, name='event_update'),
    path('gestion/evenements/<int:pk>/inscrits/', views.event_registrants, name='event_registrants'),
    path('gestion/inscriptions/<int:pk>/annuler/', views.manager_cancel_registration, name='manager_cancel_registration'),
]