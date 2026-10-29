from django.contrib import admin
from .models import Categorie, Evenement, Inscription

class InscriptionInline(admin.TabularInline):
    model = Inscription
    extra = 0
    readonly_fields = ('date_inscription', 'date_annulation', 'annulee_par')

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'date_debut', 'lieu', 'capacite', 'categorie')
    list_filter = ('categorie', 'date_debut')
    search_fields = ('titre', 'lieu')
    inlines = [InscriptionInline]

@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'evenement', 'statut', 'date_inscription')
    list_filter = ('statut', 'evenement')
    search_fields = ('utilisateur__username', 'evenement__titre')