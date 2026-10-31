# Portail d'inscription aux événements

Projet pratique Django, M1 GL, Université de Vakinankaratra. Application web de gestion des inscriptions à des événements (ateliers, conférences, rencontres).

## Fonctionnalités

- **Visiteur** : liste des événements à venir (recherche par titre, filtre par catégorie, pagination), page détail, création de compte, connexion.
- **Participant** : inscription à un événement (pas de doublon, pas d'événement passé ou complet), page « Mes inscriptions », annulation avant le début de l'événement.
- **Gestionnaire** : création et modification des événements, liste des inscrits avec filtre par statut, annulation de l'inscription d'un participant.
- **Administration Django** : `/admin/`.

## Prérequis

- Python 3.11 ou plus récent
- Git
- Node.js n'est pas nécessaire : le CSS compilé est fourni.

## Installation

```bash
git clone https://github.com/hasiniainarebecca/gestion_evenements.git
cd gestion_evenements
python -m venv venv
venv\Scripts\activate          # Windows (Invite de commandes)
.\venv\Scripts\Activate.ps1    # Windows (PowerShell)
source venv/bin/activate       # Linux et Mac
pip install -r requirements.txt
python manage.py migrate       # crée la base SQLite (db.sqlite3)
python manage.py seed_demo     # données de démonstration
python manage.py runserver
```

Ouvrir ensuite http://127.0.0.1:8000/ dans le navigateur. Sous Linux et Mac, remplacer `python` par `python3` si besoin.
Si PowerShell refuse d'exécuter le script d'activation, taper une fois `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, puis relancer l'activation.

## Comptes de démonstration

- Gestionnaire : `gestionnaire` / (mot de passe généré par `seed_demo`)
- Participants : `participant1`, `participant2`, `participant3` / (même mot de passe)

Tous les comptes de démonstration ont le même mot de passe. Il est affiché une seule fois dans le terminal quand on lance `seed_demo`. Pour choisir soi-même ce mot de passe, il faut le définir avant la commande :

- PowerShell : `$env:DEMO_PASSWORD="MonMotDePasse"`
- Linux et Mac : `export DEMO_PASSWORD=MonMotDePasse`

puis : `python manage.py seed_demo`

Aucun mot de passe n'est écrit dans le code.

## Créer un compte gestionnaire

1. Lancer d'abord `python manage.py seed_demo`. Cette commande crée le groupe « Gestionnaire » avec la permission `events.add_evenement`.
2. Créer un administrateur : `python manage.py createsuperuser`
3. Lancer le serveur et se connecter sur http://127.0.0.1:8000/admin/
4. Ouvrir l'utilisateur à promouvoir (ou en créer un), dans la section « Groupes » ajouter « Gestionnaire », puis enregistrer.

L'utilisateur voit alors le lien « Gestion » après sa connexion. Un groupe créé à la main dans `/admin/` n'a pas la permission : il faut utiliser celui créé par `seed_demo`. Un superutilisateur a aussi accès à l'espace `/gestion/`.

## Tests

```bash
python manage.py test
```

## Modifier le CSS (développement seulement)

Le fichier `static/css/output.css` est déjà fourni, Node.js n'est pas nécessaire pour lancer le projet. Il sert seulement si on modifie les templates :

```bash
npm install
npm run build
```
