from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Categorie, Evenement, Inscription


def event_list(request):
    evenements = (
        Evenement.objects.filter(date_debut__gt=timezone.now())
        .select_related('categorie')
        .order_by('date_debut')
    )

    q = request.GET.get('q', '').strip()
    categorie_id = request.GET.get('categorie', '')

    if q:
        evenements = evenements.filter(titre__icontains=q)
    if categorie_id.isdigit():
        evenements = evenements.filter(categorie_id=int(categorie_id))

    page_obj = Paginator(evenements, 6).get_page(request.GET.get('page'))

    return render(request, 'events/event_list.html', {
        'page_obj': page_obj,
        'categories': Categorie.objects.order_by('nom'),
        'q': q,
        'categorie_id': categorie_id,
    })


def event_detail(request, pk):
    evenement = get_object_or_404(
        Evenement.objects.select_related('categorie'), pk=pk
    )

    inscription_active = None
    if request.user.is_authenticated:
        inscription_active = Inscription.objects.filter(
            utilisateur=request.user, evenement=evenement, statut='confirmee'
        ).first()

    return render(request, 'events/event_detail.html', {
        'evenement': evenement,
        'inscription_active': inscription_active,
    })