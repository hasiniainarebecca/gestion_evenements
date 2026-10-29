from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError # <--- AJOUT POUR LA VALIDATION

class Categorie(models.Model):
    nom = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.nom

class Evenement(models.Model):
    titre = models.CharField(max_length=150)
    description = models.TextField()
    lieu = models.CharField(max_length=150)
    date_debut = models.DateTimeField()
    capacite = models.PositiveIntegerField()
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT)
    createur = models.ForeignKey(User, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre

    def places_prises(self):
        # Compte uniquement les inscriptions confirmées
        return self.inscriptions.filter(statut='confirmee').count()

    def places_restantes(self):
        return self.capacite - self.places_prises()

    def est_passe(self):
        return self.date_debut < timezone.now()

    def est_complet(self):
        return self.places_restantes() <= 0

class Inscription(models.Model):
    STATUTS = [
        ('confirmee', 'Confirmée'),
        ('annulee', 'Annulée'),
    ]
    
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscriptions')
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name='inscriptions')
    statut = models.CharField(max_length=10, choices=STATUTS, default='confirmee')
    date_inscription = models.DateTimeField(auto_now_add=True)
    date_annulation = models.DateTimeField(null=True, blank=True)
    annulee_par = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='annulations_effectuees'
    )

    def __str__(self):
        return f"{self.utilisateur.username} - {self.evenement.titre}"

    # CORRECTION SOURCERY : Validation de la capacité et de la date
    def clean(self):
        # On ne vérifie que si l'inscription est (ou devient) confirmée
        if self.statut == 'confirmee':
            # Si c'est une nouvelle inscription (pas encore enregistrée en base)
            if not self.pk:
                if self.evenement.est_complet():
                    raise ValidationError("Impossible de s'inscrire : cet événement est déjà complet.")
                if self.evenement.est_passe():
                    raise ValidationError("Impossible de s'inscrire : cet événement est déjà passé.")

    class Meta:
        # Contrainte d'unicité : un utilisateur ne peut avoir qu'une seule inscription "confirmée" par événement
        constraints = [
            models.UniqueConstraint(
                fields=['utilisateur', 'evenement'],
                condition=models.Q(statut='confirmee'),
                name='unique_inscription_confirmee'
            )
        ]