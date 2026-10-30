"""Tests du membre C : droits d'accès, espace gestionnaire et annulations.

Fichier séparé de tests.py (qui appartient au membre A) : Django le trouve
automatiquement grâce à son nom (test*.py). Lancer : python manage.py test
"""
from datetime import timedelta

from django.contrib.auth.models import Group, Permission, User
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categorie, Evenement, Inscription


class BaseTestCase(TestCase):
    """Prépare une catégorie, un groupe Gestionnaire et quelques comptes."""

    @classmethod
    def setUpTestData(cls):
        groupe = Group.objects.create(name='Gestionnaire')
        groupe.permissions.add(Permission.objects.get(codename='add_evenement'))

        cls.gestionnaire = User.objects.create_user('gestionnaire', password='x')
        cls.gestionnaire.groups.add(groupe)
        cls.participant = User.objects.create_user('participant', password='x')
        cls.autre = User.objects.create_user('autre', password='x')
        cls.admin = User.objects.create_superuser('admin', 'a@example.com', 'x')
        cls.categorie = Categorie.objects.create(nom='Atelier')

    def creer_evenement(self, jours=5, capacite=10, titre='Atelier Django'):
        return Evenement.objects.create(
            titre=titre, description='Description', lieu='Salle A',
            date_debut=timezone.now() + timedelta(days=jours),
            capacite=capacite, categorie=self.categorie, createur=self.gestionnaire,
        )

    def messages(self, response):
        return [str(m) for m in get_messages(response.wsgi_request)]

    @staticmethod
    def champ_date(date):
        """Format envoyé par un champ <input type="datetime-local">."""
        return timezone.localtime(date).strftime('%Y-%m-%dT%H:%M')

    def donnees(self, **changements):
        donnees = {
            'titre': 'Nouvel atelier', 'description': 'Une description',
            'lieu': 'Amphi', 'categorie': self.categorie.pk, 'capacite': 20,
            'date_debut': self.champ_date(timezone.now() + timedelta(days=7)),
        }
        donnees.update(changements)
        return donnees


# ---------------------------------------------------------------------------
# Restrictions d'accès
# ---------------------------------------------------------------------------

class AccesGestionnaireTests(BaseTestCase):

    def urls_gestionnaire(self):
        ev = self.creer_evenement()
        ins = Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        return [
            reverse('manager_dashboard'),
            reverse('event_create'),
            reverse('event_update', args=[ev.pk]),
            reverse('event_registrants', args=[ev.pk]),
            reverse('manager_cancel_registration', args=[ins.pk]),
        ]

    def test_visiteur_redirige_vers_la_connexion(self):
        for url in self.urls_gestionnaire():
            reponse = self.client.get(url)
            self.assertRedirects(
                reponse, f"{reverse('login')}?next={url}", fetch_redirect_response=False
            )

    def test_participant_recoit_403(self):
        self.client.force_login(self.participant)
        for url in self.urls_gestionnaire():
            self.assertEqual(self.client.get(url).status_code, 403, url)

    def test_participant_ne_peut_pas_annuler_via_url_gestionnaire(self):
        """F18 : même en POST direct, l'inscription n'est pas touchée."""
        ev = self.creer_evenement()
        ins = Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        self.client.force_login(self.participant)
        url = reverse('manager_cancel_registration', args=[ins.pk])
        self.assertEqual(self.client.post(url).status_code, 403)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, 'confirmee')

    def test_participant_ne_peut_pas_creer_un_evenement(self):
        self.client.force_login(self.participant)
        reponse = self.client.post(reverse('event_create'), self.donnees())
        self.assertEqual(reponse.status_code, 403)
        self.assertEqual(Evenement.objects.count(), 0)

    def test_gestionnaire_et_superuser_ont_acces(self):
        for compte in (self.gestionnaire, self.admin):
            self.client.force_login(compte)
            for url in self.urls_gestionnaire():
                self.assertEqual(self.client.get(url).status_code, 200, (compte, url))


class AccesParticipantTests(BaseTestCase):

    def test_get_sur_inscription_ne_modifie_rien(self):
        ev = self.creer_evenement()
        self.client.force_login(self.participant)
        reponse = self.client.get(reverse('register', args=[ev.pk]))
        self.assertEqual(reponse.status_code, 405)
        self.assertEqual(Inscription.objects.count(), 0)

    def test_visiteur_redirige_pour_sinscrire(self):
        ev = self.creer_evenement()
        url = reverse('register', args=[ev.pk])
        reponse = self.client.post(url)
        self.assertRedirects(
            reponse, f"{reverse('login')}?next={url}", fetch_redirect_response=False
        )
        self.assertEqual(Inscription.objects.count(), 0)

    def test_on_ne_peut_pas_annuler_linscription_dun_autre(self):
        ev = self.creer_evenement()
        ins = Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        self.client.force_login(self.autre)
        url = reverse('cancel_registration', args=[ins.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url).status_code, 403)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, 'confirmee')

    def test_get_sur_annulation_ne_modifie_rien(self):
        ev = self.creer_evenement()
        ins = Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        self.client.force_login(self.participant)
        reponse = self.client.get(reverse('cancel_registration', args=[ins.pk]))
        self.assertEqual(reponse.status_code, 200)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, 'confirmee')


# ---------------------------------------------------------------------------
# Inscription et annulation par le participant (F10, F12)
# ---------------------------------------------------------------------------

class InscriptionTests(BaseTestCase):

    def sinscrire(self, ev, compte=None):
        self.client.force_login(compte or self.participant)
        return self.client.post(reverse('register', args=[ev.pk]))

    def test_inscription_reussie_reduit_les_places(self):
        ev = self.creer_evenement(capacite=5)
        reponse = self.sinscrire(ev)
        self.assertEqual(ev.places_restantes(), 4)
        self.assertIn("Votre inscription est confirmée.", self.messages(reponse))

    def test_double_inscription_refusee(self):
        ev = self.creer_evenement()
        self.sinscrire(ev)
        reponse = self.sinscrire(ev)
        self.assertEqual(ev.places_prises(), 1)
        self.assertIn("Vous êtes déjà inscrit à cet événement.", self.messages(reponse))

    def test_evenement_complet_refuse(self):
        ev = self.creer_evenement(capacite=1)
        self.sinscrire(ev, self.autre)
        reponse = self.sinscrire(ev)
        self.assertEqual(ev.places_prises(), 1)
        self.assertTrue(any('complet' in m for m in self.messages(reponse)))

    def test_evenement_passe_refuse(self):
        ev = self.creer_evenement(jours=-1)
        reponse = self.sinscrire(ev)
        self.assertEqual(ev.places_prises(), 0)
        self.assertTrue(any('déjà commencé' in m for m in self.messages(reponse)))

    def test_annulation_libere_la_place_et_garde_lhistorique(self):
        ev = self.creer_evenement(capacite=1)
        ins = Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        self.client.force_login(self.participant)
        self.client.post(reverse('cancel_registration', args=[ins.pk]))
        ins.refresh_from_db()
        self.assertEqual(ins.statut, 'annulee')
        self.assertEqual(ins.annulee_par, self.participant)
        self.assertIsNotNone(ins.date_annulation)
        self.assertEqual(ev.places_restantes(), 1)

    def test_double_annulation_refusee(self):
        ev = self.creer_evenement()
        ins = Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        self.client.force_login(self.participant)
        url = reverse('cancel_registration', args=[ins.pk])
        self.client.post(url)
        reponse = self.client.post(url)
        self.assertIn("Cette inscription est déjà annulée.", self.messages(reponse))

    def test_reinscription_possible_apres_annulation(self):
        ev = self.creer_evenement()
        ins = Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        self.client.force_login(self.participant)
        self.client.post(reverse('cancel_registration', args=[ins.pk]))
        self.client.post(reverse('register', args=[ev.pk]))
        self.assertEqual(Inscription.objects.filter(utilisateur=self.participant).count(), 2)
        self.assertEqual(ev.places_prises(), 1)


# ---------------------------------------------------------------------------
# Formulaire d'événement : validations RG11, RG12, RG14
# ---------------------------------------------------------------------------

class EvenementFormTests(BaseTestCase):

    def setUp(self):
        self.client.force_login(self.gestionnaire)

    def test_creation_reussie(self):
        reponse = self.client.post(reverse('event_create'), self.donnees())
        self.assertRedirects(reponse, reverse('manager_dashboard'))
        ev = Evenement.objects.get()
        self.assertEqual(ev.createur, self.gestionnaire)
        self.assertEqual(ev.titre, 'Nouvel atelier')

    def test_date_passee_refusee(self):
        date = self.champ_date(timezone.now() - timedelta(days=1))
        reponse = self.client.post(reverse('event_create'), self.donnees(date_debut=date))
        self.assertEqual(reponse.status_code, 200)
        self.assertIn('date_debut', reponse.context['form'].errors)
        self.assertEqual(Evenement.objects.count(), 0)

    def test_capacite_zero_refusee(self):
        reponse = self.client.post(reverse('event_create'), self.donnees(capacite=0))
        self.assertIn('capacite', reponse.context['form'].errors)
        self.assertEqual(Evenement.objects.count(), 0)

    def test_capacite_sous_les_inscrits_refusee(self):
        ev = self.creer_evenement(capacite=10)
        for nom in ('a', 'b', 'c'):
            Inscription.objects.create(
                utilisateur=User.objects.create_user(nom, password='x'), evenement=ev
            )
        reponse = self.client.post(
            reverse('event_update', args=[ev.pk]),
            self.donnees(date_debut=self.champ_date(ev.date_debut), capacite=2),
        )
        self.assertIn('capacite', reponse.context['form'].errors)
        ev.refresh_from_db()
        self.assertEqual(ev.capacite, 10)

    def test_capacite_egale_aux_inscrits_acceptee(self):
        ev = self.creer_evenement(capacite=10)
        Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        reponse = self.client.post(
            reverse('event_update', args=[ev.pk]),
            self.donnees(date_debut=self.champ_date(ev.date_debut), capacite=1),
        )
        self.assertRedirects(reponse, reverse('manager_dashboard'))
        ev.refresh_from_db()
        self.assertEqual(ev.capacite, 1)

    def test_modification_dun_evenement_passe_refusee(self):
        ev = self.creer_evenement(jours=-2)
        url = reverse('event_update', args=[ev.pk])
        reponse = self.client.get(url)
        self.assertRedirects(reponse, reverse('manager_dashboard'))
        self.assertTrue(any('plus être modifié' in m for m in self.messages(reponse)))
        reponse = self.client.post(url, self.donnees())
        self.assertRedirects(reponse, reverse('manager_dashboard'))
        ev.refresh_from_db()
        self.assertEqual(ev.titre, 'Atelier Django')

    def test_changer_le_lieu_sans_toucher_la_date(self):
        """La date inchangée n'est pas revalidée : changement de lieu accepté."""
        ev = self.creer_evenement(jours=1)
        reponse = self.client.post(
            reverse('event_update', args=[ev.pk]),
            self.donnees(date_debut=self.champ_date(ev.date_debut), lieu='Nouvelle salle'),
        )
        self.assertRedirects(reponse, reverse('manager_dashboard'))
        ev.refresh_from_db()
        self.assertEqual(ev.lieu, 'Nouvelle salle')

    def test_formulaire_prerempli_a_la_modification(self):
        ev = self.creer_evenement()
        reponse = self.client.get(reverse('event_update', args=[ev.pk]))
        self.assertContains(reponse, 'value="Atelier Django"')
        self.assertContains(reponse, f'value="{self.champ_date(ev.date_debut)}"')


# ---------------------------------------------------------------------------
# Tableau de bord, liste des inscrits et annulation par le gestionnaire (F15, F16, F18)
# ---------------------------------------------------------------------------

class EspaceGestionnaireTests(BaseTestCase):

    def setUp(self):
        self.client.force_login(self.gestionnaire)

    def test_tableau_de_bord_montre_aussi_les_evenements_passes(self):
        futur = self.creer_evenement(jours=3, titre='Futur')
        passe = self.creer_evenement(jours=-3, titre='Passé')
        Inscription.objects.create(utilisateur=self.participant, evenement=futur)
        Inscription.objects.create(utilisateur=self.autre, evenement=futur, statut='annulee')
        reponse = self.client.get(reverse('manager_dashboard'))
        evenements = {e.titre: e for e in reponse.context['page_obj']}
        self.assertEqual(set(evenements), {'Futur', 'Passé'})
        self.assertEqual(evenements['Futur'].nb_confirmees, 1)  # l'annulée ne compte pas
        self.assertEqual(evenements['Passé'].nb_confirmees, 0)
        # Un événement passé n'a pas de lien « Modifier » (RG14).
        self.assertNotContains(reponse, reverse('event_update', args=[passe.pk]))
        self.assertContains(reponse, reverse('event_update', args=[futur.pk]))

    def test_tableau_de_bord_pagine(self):
        for i in range(12):
            self.creer_evenement(titre=f'Evt {i}')
        reponse = self.client.get(reverse('manager_dashboard'))
        self.assertEqual(len(reponse.context['page_obj']), 10)
        self.assertTrue(reponse.context['page_obj'].has_next())

    def test_liste_des_inscrits_totaux_et_filtre(self):
        ev = self.creer_evenement(capacite=5)
        Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        Inscription.objects.create(utilisateur=self.autre, evenement=ev, statut='annulee')
        url = reverse('event_registrants', args=[ev.pk])

        tous = self.client.get(url)
        self.assertEqual(tous.context['nb_confirmees'], 1)
        self.assertEqual(tous.context['nb_annulees'], 1)
        self.assertEqual(len(tous.context['inscriptions']), 2)

        confirmes = self.client.get(url, {'statut': 'confirmee'})
        self.assertEqual([i.utilisateur for i in confirmes.context['inscriptions']], [self.participant])
        annules = self.client.get(url, {'statut': 'annulee'})
        self.assertEqual([i.utilisateur for i in annules.context['inscriptions']], [self.autre])
        # Un statut inconnu est ignoré.
        inconnu = self.client.get(url, {'statut': 'nimporte'})
        self.assertEqual(len(inconnu.context['inscriptions']), 2)
        self.assertEqual(inconnu.context['statut'], '')

    def test_gestionnaire_annule_une_inscription(self):
        ev = self.creer_evenement(capacite=1)
        ins = Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        url = reverse('manager_cancel_registration', args=[ins.pk])
        # GET : simple page de confirmation, rien ne change.
        self.assertEqual(self.client.get(url).status_code, 200)
        ins.refresh_from_db()
        self.assertEqual(ins.statut, 'confirmee')
        # POST : annulation.
        reponse = self.client.post(url)
        self.assertRedirects(reponse, reverse('event_registrants', args=[ev.pk]))
        ins.refresh_from_db()
        self.assertEqual(ins.statut, 'annulee')
        self.assertEqual(ins.annulee_par, self.gestionnaire)
        self.assertIsNotNone(ins.date_annulation)
        self.assertEqual(ev.places_restantes(), 1)

    def test_gestionnaire_ne_peut_pas_annuler_deux_fois(self):
        ev = self.creer_evenement()
        ins = Inscription.objects.create(
            utilisateur=self.participant, evenement=ev, statut='annulee',
            annulee_par=self.participant, date_annulation=timezone.now(),
        )
        url = reverse('manager_cancel_registration', args=[ins.pk])
        reponse = self.client.post(url)
        self.assertIn("Cette inscription est déjà annulée.", self.messages(reponse))
        ins.refresh_from_db()
        self.assertEqual(ins.annulee_par, self.participant)  # pas écrasé
        # Même la page de confirmation est refusée (redirection).
        self.assertRedirects(self.client.get(url), reverse('event_registrants', args=[ev.pk]))

    def test_gestionnaire_ne_peut_pas_annuler_apres_le_debut(self):
        ev = self.creer_evenement(jours=-1)
        ins = Inscription.objects.create(utilisateur=self.participant, evenement=ev)
        url = reverse('manager_cancel_registration', args=[ins.pk])
        self.assertRedirects(self.client.get(url), reverse('event_registrants', args=[ev.pk]))
        reponse = self.client.post(url)
        self.assertTrue(any('déjà commencé' in m for m in self.messages(reponse)))
        ins.refresh_from_db()
        self.assertEqual(ins.statut, 'confirmee')