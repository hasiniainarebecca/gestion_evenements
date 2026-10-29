import os
import random
import string
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission # <-- AJOUT DE Permission ICI
from django.utils import timezone
from datetime import timedelta
from events.models import Categorie, Evenement, Inscription

class Command(BaseCommand):
    help = 'Génère des données de démonstration'

    def handle(self, *args, **kwargs):
        # 1. Créer le groupe Gestionnaire
        group, _ = Group.objects.get_or_create(name='Gestionnaire')

        # --- AJOUT : Donner la permission events.add_evenement au groupe ---
        try:
            # On cherche la permission de créer un événement (add_evenement)
            permission = Permission.objects.get(codename='add_evenement')
            group.permissions.add(permission)
        except Permission.DoesNotExist:
            self.stdout.write(self.style.WARNING("La permission add_evenement n'existe pas encore. Assurez-vous d'avoir fait 'migrate'."))
        # -------------------------------------------------------------------

        # 2. Gérer le mot de passe
        password = os.environ.get('DEMO_PASSWORD')
        if not password:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            self.stdout.write(self.style.WARNING(f"Aucun DEMO_PASSWORD fourni. Mot de passe généré : {password}"))

        # 3. Créer les utilisateurs
        users = []
        for i in range(1, 4):
            username = f"participant{i}"
            user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@example.com'})
            if created:
                user.set_password(password)
                user.save()
            users.append(user)

        manager, created = User.objects.get_or_create(username="gestionnaire", defaults={'email': 'manager@example.com'})
        if created:
            manager.set_password(password)
            manager.save()
        manager.groups.add(group)

        # 4. Créer les catégories
        cats = ['Atelier', 'Conférence', 'Rencontre', 'Formation']
        categories = []
        for c in cats:
            cat, _ = Categorie.objects.get_or_create(nom=c)
            categories.append(cat)

        # 5. Créer les événements
        now = timezone.now()
        events_data = [
            {"titre": "Atelier Django", "lieu": "Salle A", "days": 5, "cap": 20, "cat": 0},
            {"titre": "Conférence Tech", "lieu": "Amphi", "days": 10, "cap": 50, "cat": 1},
            {"titre": "Rencontre Networking", "lieu": "Cafétéria", "days": 2, "cap": 15, "cat": 2},
            {"titre": "Formation Python", "lieu": "Salle B", "days": -2, "cap": 10, "cat": 3}, # Passé
        ]

        events = []
        for data in events_data:
            ev, created = Evenement.objects.get_or_create(
                titre=data["titre"],
                defaults={
                    'description': f"Description pour {data['titre']}",
                    'lieu': data["lieu"],
                    'date_debut': now + timedelta(days=data["days"]),
                    'capacite': data["cap"],
                    'categorie': categories[data["cat"]],
                    'createur': manager
                }
            )
            events.append(ev)

        # 6. Créer des inscriptions (pour le premier événement)
        if not Inscription.objects.exists():
            Inscription.objects.create(utilisateur=users[0], evenement=events[0], statut='confirmee')
            Inscription.objects.create(utilisateur=users[1], evenement=events[0], statut='confirmee')
            # Une inscription annulée
            Inscription.objects.create(
                utilisateur=users[2], 
                evenement=events[0], 
                statut='annulee',
                date_annulation=now,
                annulee_par=users[2]
            )

        self.stdout.write(self.style.SUCCESS('Données de démonstration générées avec succès.'))