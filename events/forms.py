from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


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