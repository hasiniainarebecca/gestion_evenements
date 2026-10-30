from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ConnexionForm, EvenementForm, InscriptionForm
from .models import Evenement, Inscription
from .permissions import gestionnaire_requis


# ---------------------------------------------------------------------------
# PARTICIPANT : s'inscrire, voir ses inscriptions, annuler (F10, F11, F12)
# ---------------------------------------------------------------------------

@login_required
@require_POST
def register(request, pk):
    """F10 : s'inscrire à un événement (POST uniquement). Règles RG3 à RG6."""
    try:
        # transaction.atomic : la vérification de la capacité et la création
        # de l'inscription forment un seul bloc (évite de dépasser la capacité).
        with transaction.atomic():
            evenement = get_object_or_404(
                Evenement.objects.select_for_update(), pk=pk
            )
            if evenement.est_passe():  # RG5
                messages.error(request, "Cet événement a déjà commencé : l'inscription est fermée.")
            elif Inscription.objects.filter(  # RG4
                utilisateur=request.user, evenement=evenement, statut='confirmee'
            ).exists():
                messages.error(request, "Vous êtes déjà inscrit à cet événement.")
            elif evenement.est_complet():  # RG6
                messages.error(request, "Événement complet : il n'y a plus de place.")
            else:
                Inscription.objects.create(
                    utilisateur=request.user, evenement=evenement
                )
                messages.success(request, "Votre inscription est confirmée.")
    except IntegrityError:
        # Garde-fou : la contrainte d'unicité de la base a bloqué un doublon.
        messages.error(request, "Vous êtes déjà inscrit à cet événement.")
    return redirect('event_detail', pk=pk)


@login_required
def my_registrations(request):
    """F11 : liste de MES inscriptions, séparées en « à venir » et « passées »."""
    maintenant = timezone.now()
    mes_inscriptions = Inscription.objects.filter(
        utilisateur=request.user
    ).select_related('evenement', 'evenement__categorie')

    a_venir = mes_inscriptions.filter(
        evenement__date_debut__gt=maintenant
    ).order_by('evenement__date_debut')
    passees = mes_inscriptions.filter(
        evenement__date_debut__lte=maintenant
    ).order_by('-evenement__date_debut')

    return render(request, 'events/my_registrations.html', {
        'a_venir': a_venir,
        'passees': passees,
    })


def _annuler(inscription_id, par):
    """Annule une inscription (RG9). Sert au participant ET au gestionnaire (F18).

    Retourne None si tout s'est bien passé, sinon le message d'erreur.
    """
    with transaction.atomic():
        # On relit la ligne verrouillée : deux annulations simultanées
        # ne peuvent pas passer toutes les deux.
        inscription = Inscription.objects.select_for_update().select_related(
            'evenement'
        ).get(pk=inscription_id)
        if inscription.statut == 'annulee':  # RG17
            return "Cette inscription est déjà annulée."
        if inscription.evenement.est_passe():  # RG7 / RG13
            return "Impossible d'annuler : l'événement a déjà commencé."
        inscription.statut = 'annulee'
        inscription.date_annulation = timezone.now()
        inscription.annulee_par = par
        inscription.save(update_fields=['statut', 'date_annulation', 'annulee_par'])
    return None


@login_required
def cancel_registration(request, pk):
    """F12 : annuler SA propre inscription (GET = confirmation, POST = annulation)."""
    inscription = get_object_or_404(
        Inscription.objects.select_related('evenement'), pk=pk
    )
    if inscription.utilisateur != request.user:  # RG8
        raise PermissionDenied

    if request.method == 'POST':
        erreur = _annuler(inscription.pk, par=request.user)
        if erreur:
            messages.error(request, erreur)
        else:
            messages.success(request, "Votre inscription a bien été annulée.")
        return redirect('my_registrations')

    # GET : on affiche la page de confirmation, sauf si l'annulation est impossible.
    if inscription.statut == 'annulee':
        messages.error(request, "Cette inscription est déjà annulée.")
        return redirect('my_registrations')
    if inscription.evenement.est_passe():
        messages.error(request, "Impossible d'annuler : l'événement a déjà commencé.")
        return redirect('my_registrations')
    return render(request, 'events/cancel_confirm.html', {'inscription': inscription})

# ---------------------------------------------------------------------------
# COMPTES : inscription, connexion, déconnexion (F01 à F04)
# ---------------------------------------------------------------------------

def signup(request):
    """F01 : créer un compte, puis connecter directement la personne."""
    if request.user.is_authenticated:
        return redirect('event_list')
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Votre compte a été créé. Bienvenue !")
            return redirect('event_list')
    else:
        form = InscriptionForm()
    return render(request, 'registration/signup.html', {'form': form})


class ConnexionView(LoginView):
    """F02 : connexion. Gère aussi le paramètre ?next= (F04)."""
    template_name = 'registration/login.html'
    authentication_form = ConnexionForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, "Vous êtes connecté.")
        return super().form_valid(form)


login_view = ConnexionView.as_view()


@require_POST
def logout_view(request):
    """F03 : déconnexion, uniquement en POST (protégée par CSRF)."""
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Vous êtes déconnecté.")
    return redirect('event_list')


# ---------------------------------------------------------------------------
# GESTIONNAIRE : tableau de bord, événements, inscrits, annulation (F13 à F16, F18)
# Toutes ces vues sont protégées par @gestionnaire_requis (RG10) :
# visiteur -> page de connexion, connecté sans droit -> erreur 403.
# ---------------------------------------------------------------------------

@gestionnaire_requis
def manager_dashboard(request):
    """F15 : tous les événements (même passés), avec inscrits confirmés / capacité."""
    evenements = (
        Evenement.objects.select_related('categorie')
        .annotate(nb_confirmees=Count(
            'inscriptions', filter=Q(inscriptions__statut='confirmee')
        ))
        .order_by('-date_debut')
    )
    page_obj = Paginator(evenements, 10).get_page(request.GET.get('page'))
    return render(request, 'manager/dashboard.html', {'page_obj': page_obj})


@gestionnaire_requis
def event_create(request):
    """F13 : créer un événement (validation RG12 dans EvenementForm)."""
    if request.method == 'POST':
        form = EvenementForm(request.POST)
        if form.is_valid():
            evenement = form.save(commit=False)
            evenement.createur = request.user
            evenement.save()
            messages.success(request, f"L'événement « {evenement.titre} » a été créé.")
            return redirect('manager_dashboard')
    else:
        form = EvenementForm()
    return render(request, 'manager/event_form.html', {'form': form})


@gestionnaire_requis
def event_update(request, pk):
    """F14 : modifier un événement (RG11, RG12, RG14)."""
    evenement = get_object_or_404(Evenement, pk=pk)
    if evenement.est_passe():  # RG14
        messages.error(request, "Cet événement est déjà passé : il ne peut plus être modifié.")
        return redirect('manager_dashboard')

    if request.method == 'POST':
        # La vérification de la capacité (RG11) et l'enregistrement sont dans
        # la même transaction : une inscription qui arrive entre les deux ne
        # peut pas faire passer la capacité sous le nombre d'inscrits.
        with transaction.atomic():
            a_modifier = Evenement.objects.select_for_update().get(pk=pk)
            form = EvenementForm(request.POST, instance=a_modifier)
            if form.is_valid():
                form.save()
                messages.success(request, "L'événement a bien été modifié.")
                return redirect('manager_dashboard')
    else:
        form = EvenementForm(instance=evenement)
    return render(request, 'manager/event_form.html', {
        'form': form, 'evenement': evenement,
    })


@gestionnaire_requis
def event_registrants(request, pk):
    """F16 : liste des inscrits d'un événement, avec totaux et filtre par statut."""
    evenement = get_object_or_404(Evenement.objects.select_related('categorie'), pk=pk)

    toutes = evenement.inscriptions.select_related('utilisateur', 'annulee_par')
    totaux = toutes.aggregate(
        nb_confirmees=Count('pk', filter=Q(statut='confirmee')),
        nb_annulees=Count('pk', filter=Q(statut='annulee')),
    )

    statut = request.GET.get('statut', '')
    if statut in ('confirmee', 'annulee'):
        inscriptions = toutes.filter(statut=statut)
    else:
        statut = ''
        inscriptions = toutes

    return render(request, 'manager/registrants.html', {
        'evenement': evenement,
        'inscriptions': inscriptions.order_by('date_inscription'),
        'nb_confirmees': totaux['nb_confirmees'],
        'nb_annulees': totaux['nb_annulees'],
        'statut': statut,
    })


@gestionnaire_requis
def manager_cancel_registration(request, pk):
    """F18 : le gestionnaire annule l'inscription d'un participant (RG13, RG17).

    GET = page de confirmation, POST = annulation. Le gestionnaire est
    enregistré dans annulee_par.
    """
    inscription = get_object_or_404(
        Inscription.objects.select_related('evenement', 'utilisateur'), pk=pk
    )
    retour = redirect('event_registrants', pk=inscription.evenement_id)

    if request.method == 'POST':
        erreur = _annuler(inscription.pk, par=request.user)
        if erreur:
            messages.error(request, erreur)
        else:
            messages.success(
                request,
                f"L'inscription de {inscription.utilisateur.username} a bien été annulée."
            )
        return retour

    # GET : on n'affiche la confirmation que si l'annulation est possible.
    if inscription.statut == 'annulee':
        messages.error(request, "Cette inscription est déjà annulée.")
        return retour
    if inscription.evenement.est_passe():
        messages.error(request, "Impossible d'annuler : l'événement a déjà commencé.")
        return retour
    return render(request, 'manager/cancel_confirm.html', {'inscription': inscription})