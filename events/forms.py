from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Categorie, Evenement


class TailwindFormMixin:
    """Applique les classes Tailwind de la charte graphique (section 9.6)
    à tous les champs d'un formulaire."""
    champ = (
        'block w-full rounded-lg border border-slate-300 px-3 py-2 '
        'text-slate-900 shadow-sm focus:border-brand-500 '
        'focus:outline-none focus:ring-2 focus:ring-brand-500/30'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = self.champ


class ConnexionForm(TailwindFormMixin, AuthenticationForm):
    """Formulaire de connexion (F02)."""


class InscriptionForm(TailwindFormMixin, UserCreationForm):
    """Création de compte (F01) : nom d'utilisateur, e-mail, mot de passe x2."""
    email = forms.EmailField(label="Adresse e-mail", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')


class EvenementForm(TailwindFormMixin, forms.ModelForm):
    """Création et modification d'un événement (F13, F14).

    Règles vérifiées côté serveur : RG11, RG12 et RG14.
    """

    class Meta:
        model = Evenement
        fields = ('titre', 'description', 'lieu', 'date_debut', 'capacite', 'categorie')
        labels = {
            'titre': "Titre",
            'description': "Description",
            'lieu': "Lieu",
            'date_debut': "Date et heure de début",
            'capacite': "Capacité (nombre de places)",
            'categorie': "Catégorie",
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'date_debut': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categorie'].queryset = Categorie.objects.order_by('nom')
        self.fields['categorie'].empty_label = "Choisir une catégorie"
        self.fields['date_debut'].input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M']
        # On retient l'état de l'événement AVANT que le formulaire ne modifie l'instance.
        self._etait_passe = bool(self.instance.pk) and self.instance.est_passe()

    def clean_date_debut(self):
        date_debut = self.cleaned_data['date_debut']
        # RG12 : date dans le futur. À la modification, on ne revérifie que si la
        # date a vraiment été changée (sinon on bloquerait un simple changement de
        # lieu fait quelques minutes avant le début).
        if (not self.instance.pk or 'date_debut' in self.changed_data) \
                and date_debut <= timezone.now():
            raise forms.ValidationError("La date de début doit être dans le futur.")
        return date_debut

    def clean_capacite(self):
        capacite = self.cleaned_data['capacite']
        # RG12 : capacité d'au moins 1.
        if capacite < 1:
            raise forms.ValidationError("La capacité doit être d'au moins 1.")
        # RG11 : pas moins que le nombre d'inscrits confirmés.
        if self.instance.pk:
            inscrits = self.instance.places_prises()
            if capacite < inscrits:
                raise forms.ValidationError(
                    f"La capacité ne peut pas être inférieure au nombre "
                    f"d'inscrits confirmés ({inscrits})."
                )
        return capacite

    def clean(self):
        cleaned = super().clean()
        # RG14 : un événement passé ne se modifie plus.
        if self._etait_passe:
            raise forms.ValidationError(
                "Cet événement est déjà passé : il ne peut plus être modifié."
            )
        return cleaned