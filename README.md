Gestion des Événements - Projet Django 

Installation
1. Cloner le projet : `git clone https://github.com/hasiniainarebecca/gestion_evenements.git
cd gestion_evenements`
2. Créer l'environnement virtuel : `python -m venv venv`
3. Activer l'environnement : `venv\Scripts\activate` (Windows)
4. Installer les dépendances : `pip install -r requirements.txt`
5. Lancer les migrations : `python manage.py migrate`
6. Générer les données de démo : `python manage.py seed_demo`
7. Lancer le serveur : `python manage.py runserver`

Comptes de démonstration
- Gestionnaire : `gestionnaire` / (mot de passe généré par seed_demo)
- Participant : `participant1` / (mot de passe généré par seed_demo)

Tests
Lancer les tests avec : `python manage.py test`

Mot de passe des comptes de démonstration
Tous les comptes de démonstration ont le même mot de passe. Il est affiché une seule fois dans le terminal quand on lance seed_demo. Pour choisir soi-même ce mot de passe, il faut le définir avant la commande :
- PowerShell : $env:DEMO_PASSWORD="MonMotDePasse"
- Linux et Mac : export DEMO_PASSWORD=MonMotDePasse
puis : python manage.py seed_demo
Aucun mot de passe n'est écrit dans le code.

Créer un compte gestionnaire
1. Lancer d'abord python manage.py seed_demo. Cette commande crée le groupe « Gestionnaire » avec la permission events.add_evenement.
2. Créer un administrateur : python manage.py createsuperuser
3. Lancer le serveur et se connecter sur http://127.0.0.1:8000/admin/
4. Ouvrir l'utilisateur à promouvoir (ou en créer un), dans la section « Groupes » ajouter « Gestionnaire », puis enregistrer.
L'utilisateur voit alors le lien « Gestion » après sa connexion. Un groupe créé à la main dans /admin/ n'a pas la permission : il faut utiliser celui créé par seed_demo. Un superutilisateur a aussi accès à l'espace /gestion/.

Modifier le CSS (développement seulement)
Le fichier static/css/output.css est déjà fourni, Node.js n'est pas nécessaire pour lancer le projet. Il sert seulement si on modifie les templates :
npm install
npm run build