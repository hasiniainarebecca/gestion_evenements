from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def est_gestionnaire(user):
    """Vrai pour un membre du groupe « Gestionnaire » ou un superutilisateur.

    Le groupe « Gestionnaire » (créé par seed_demo) possède la permission
    events.add_evenement : on s'appuie dessus, comme le menu de base.html.
    Un superutilisateur a toutes les permissions, donc il passe aussi.
    """
    return user.is_authenticated and user.has_perm('events.add_evenement')


def gestionnaire_requis(vue):
    """Protège une vue réservée au gestionnaire (RG10).

    - visiteur non connecté : redirection vers la connexion (puis retour, F04) ;
    - connecté sans le droit : erreur 403.
    """
    @wraps(vue)
    def _vue(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if not est_gestionnaire(request.user):
            raise PermissionDenied
        return vue(request, *args, **kwargs)
    return _vue