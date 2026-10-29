from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from .models import Evenement, Categorie, Inscription
from django.core.exceptions import ValidationError

class EvenementModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.cat = Categorie.objects.create(nom='Test')
        
    def test_evenement_date_passee(self):
        """Validation : Un événement avec une date dans le passé doit être refusé (par le formulaire plus tard)"""
        # Note: La validation se fait généralement dans les forms, mais on peut tester la méthode
        ev = Evenement(
            titre="Vieux", description="Test", lieu="Ici", 
            date_debut=timezone.now() - timedelta(days=1), 
            capacite=10, categorie=self.cat, createur=self.user
        )
        self.assertTrue(ev.est_passe())

    def test_places_restantes_ignore_annulees(self):
        """Règle métier : Les places restantes ignorent les inscriptions annulées (RG2)"""
        ev = Evenement.objects.create(
            titre="Event", description="Desc", lieu="Lieu", 
            date_debut=timezone.now() + timedelta(days=5), 
            capacite=10, categorie=self.cat, createur=self.user
        )
        # 1 inscription confirmée
        Inscription.objects.create(utilisateur=self.user, evenement=ev, statut='confirmee')
        # 1 inscription annulée
        user2 = User.objects.create_user(username='user2', password='pwd')
        Inscription.objects.create(utilisateur=user2, evenement=ev, statut='annulee')

        self.assertEqual(ev.places_prises(), 1)
        self.assertEqual(ev.places_restantes(), 9)

    def test_double_inscription_refusee(self):
        """Règle métier : Une double inscription confirmée est refusée (RG4)"""
        ev = Evenement.objects.create(
            titre="Event", description="Desc", lieu="Lieu", 
            date_debut=timezone.now() + timedelta(days=5), 
            capacite=10, categorie=self.cat, createur=self.user
        )
        Inscription.objects.create(utilisateur=self.user, evenement=ev, statut='confirmee')
        
        # Tenter de créer une deuxième inscription confirmée
        with self.assertRaises(Exception): # Django lèvera une IntegrityError à cause de la UniqueConstraint
            Inscription.objects.create(utilisateur=self.user, evenement=ev, statut='confirmee')