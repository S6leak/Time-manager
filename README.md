# Time Manager

Application de gestion du temps de travail : pointages, absences, équipes et KPI, avec trois rôles (admin/RH, manager, employé).

## Stack

| Couche | Technologie |
|---|---|
| Base de données | PostgreSQL 17 |
| Backend | Python 3.14, FastAPI, SQLAlchemy |
| Dépendances Python | uv |
| Lint / format | ruff |
| Tests | pytest |
| Conteneurs | Docker, Docker Compose |
| Frontend | à venir |

## Structure du dépôt

```
Time-manager/
├── backend/
│   ├── src/                # Code de l'API (main.py = point d'entrée)
│   ├── tests/              # Tests pytest
│   ├── pyproject.toml      # Dépendances + config ruff et pytest
│   ├── uv.lock             # Versions exactes des dépendances (généré par uv)
│   ├── .python-version     # Version de Python du projet
│   ├── Dockerfile.dev      # Image de développement
│   ├── Dockerfile.prod     # Image de production
│   └── .dockerignore
├── frontend/
├── compose.yaml            # Production : lancé par `docker compose up`
├── compose.dev.yaml        # Surcouche de développement
├── .env.example            # Variables d'environnement surchargeables
└── .gitignore
```

---

## 1. Prérequis

| Outil | Obligatoire ? | Vérification |
|---|---|---|
| Git | Oui | `git --version` |
| Docker + Docker Compose | Oui | `docker --version` puis `docker compose version` |
| uv | Pour travailler sur le backend (dépendances, IDE, tests en local) | `uv --version` |

**Windows (WSL)** : Docker Desktop doit être lancé, avec l'intégration WSL activée pour la distribution utilisée (*Settings → Resources → WSL Integration*).

**Installer uv** :

```bash
# Linux / macOS / WSL
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## 2. Premier lancement

Toutes les commandes `docker compose` se lancent **depuis la racine du dépôt**.

```bash
git clone <url-du-repo>
cd Time-manager
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Aucun fichier `.env` n'est nécessaire : `compose.yaml` fournit des valeurs par défaut. Pour les modifier, créer un `.env` à partir du modèle :

```bash
cp .env.example .env
```

Une fois les conteneurs démarrés :

| Service | Adresse |
|---|---|
| API | http://127.0.0.1:8000/api/health |
| Documentation Swagger | http://127.0.0.1:8000/api/docs |
| PostgreSQL (dev uniquement) | `localhost:5432`, base / utilisateur / mot de passe : `timemanager` |

> Le terminal de `fastapi` affiche `/docs` comme adresse de documentation : c'est une valeur générique de l'outil. La documentation de ce projet est sur `/api/docs`.

---

## 3. Développement au quotidien

### Lancer et arrêter l'environnement de dev

```bash
# Démarrer (logs dans le terminal, Ctrl+C pour arrêter)
docker compose -f compose.yaml -f compose.dev.yaml up

# Démarrer en arrière-plan
docker compose -f compose.yaml -f compose.dev.yaml up -d

# Arrêter et supprimer les conteneurs (les données de la base sont conservées)
docker compose -f compose.yaml -f compose.dev.yaml down
```

Le dossier `backend/` est monté dans le conteneur : chaque fichier enregistré recharge l'API automatiquement, sans reconstruire l'image.

### Quand faut-il ajouter `--build` ?

Après toute modification de :

- `pyproject.toml` ou `uv.lock` (nouvelle dépendance) ;
- `Dockerfile.dev` ou `Dockerfile.prod` ;
- après un `git pull` qui touche l'un de ces fichiers.

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

Une modification de code dans `src/` ou `tests/` ne nécessite **pas** de rebuild en dev.

### Suivre l'état des services

```bash
docker compose -f compose.yaml -f compose.dev.yaml ps              # Services lancés et état (healthy…)
docker compose -f compose.yaml -f compose.dev.yaml logs -f backend # Logs du backend en continu
docker compose -f compose.yaml -f compose.dev.yaml logs -f db      # Logs de PostgreSQL
```

### Ouvrir un shell dans le conteneur backend

```bash
docker compose -f compose.yaml -f compose.dev.yaml exec backend sh
```

---

## 4. Tests, lint et format

Les mêmes vérifications que la CI, à lancer **avant chaque commit**.

### Dans Docker (aucune installation locale nécessaire)

Avec l'environnement de dev démarré :

```bash
docker compose -f compose.yaml -f compose.dev.yaml exec backend pytest
docker compose -f compose.yaml -f compose.dev.yaml exec backend ruff check .
docker compose -f compose.yaml -f compose.dev.yaml exec backend ruff format --check .
```

### En local avec uv

Depuis `backend/` :

```bash
uv run pytest                 # Tests
uv run ruff check .           # Lint
uv run ruff format --check .  # Vérifie le format sans modifier
uv run ruff format .          # Corrige le format automatiquement
```

> Les fichiers de test se lancent **avec pytest**, jamais directement avec `python` ni avec le bouton « Run » de l'éditeur : la configuration des imports (`pythonpath = ["src"]`) n'est lue que par pytest.

---

## 5. Travailler en local avec uv

### Installer l'environnement après un clone ou un `git pull`

Depuis `backend/` :

```bash
uv sync
```

Crée ou met à jour `backend/.venv` à partir de `uv.lock`, avec la version de Python fixée dans `.python-version`. Dans l'éditeur, sélectionner l'interpréteur `backend/.venv/bin/python`.

### Lancer l'API sans Docker

Depuis `backend/` :

```bash
uv run fastapi dev src/main.py
```

`uv run` exécute la commande dans le `.venv` du projet, sans avoir à l'activer.

Pour disposer de la base sans lancer le backend dans Docker :

```bash
# Depuis la racine
docker compose -f compose.yaml -f compose.dev.yaml up -d db
```

### Gérer les dépendances

Depuis `backend/` :

```bash
uv add <paquet>            # Dépendance de l'application
uv add --dev <paquet>      # Outil de développement (tests, lint…), absent de l'image de prod
uv remove <paquet>         # Retirer une dépendance
uv lock --check            # Vérifier que uv.lock est à jour
```

Règles :

1. Toujours passer par `uv add` / `uv remove`, jamais par `pip install` : `uv.lock` ne serait pas mis à jour.
2. Toujours committer `pyproject.toml` **et** `uv.lock` ensemble.
3. Reconstruire l'image ensuite (`up --build`).

Les images Docker sont construites avec `uv sync --locked` : le build échoue si `uv.lock` ne correspond pas à `pyproject.toml`.

---

## 6. Base de données

```bash
# Ouvrir un terminal PostgreSQL
docker compose -f compose.yaml -f compose.dev.yaml exec db psql -U timemanager -d timemanager

# Lister les bases sans pagination
docker compose -f compose.yaml -f compose.dev.yaml exec db psql -U timemanager -P pager=off -c '\l'
```

Dans `psql` : `\dt` liste les tables, `\q` quitte.

### Repartir d'une base vierge

```bash
docker compose -f compose.yaml -f compose.dev.yaml down -v
```

⚠️ `-v` supprime le volume `db-data` : **toutes les données sont effacées**. À ne jamais lancer sur un serveur de préprod ou de prod.

PostgreSQL ne lit `POSTGRES_USER`, `POSTGRES_PASSWORD` et `POSTGRES_DB` qu'à la **création** de la base. Après une modification de ces variables, il faut supprimer le volume pour qu'elles soient prises en compte.

---

## 7. Production et préprod

Sur le serveur, créer un `.env` avec de vrais secrets, puis lancer `compose.yaml` seul :

```bash
cp .env.example .env     # puis renseigner les vraies valeurs
docker compose up -d --build
```

| | Dev | Prod / préprod |
|---|---|---|
| Fichiers | `compose.yaml` + `compose.dev.yaml` | `compose.yaml` seul |
| Image backend | `Dockerfile.dev` | `Dockerfile.prod` |
| Rechargement auto | Oui (code monté) | Non |
| Outils de dev (pytest, ruff) | Oui | Non |
| Utilisateur dans le conteneur | root | `appuser` (non-root) |
| Base accessible depuis l'hôte | Oui (port 5432) | Non (réseau Docker uniquement) |
| Redémarrage automatique | Non | Oui (`unless-stopped`) |

### Tester une image seule, sans Compose

Depuis `backend/` :

```bash
docker build -f Dockerfile.prod -t time-manager-backend:prod .
docker run --rm -p 8000:8000 -e APP_ENV=production time-manager-backend:prod
```

---

## 8. Nettoyage

```bash
docker compose -f compose.yaml -f compose.dev.yaml down    # Conteneurs supprimés, données conservées
docker compose -f compose.yaml -f compose.dev.yaml down -v # + suppression de la base
docker compose -f compose.yaml -f compose.dev.yaml build --no-cache backend  # Rebuild complet, sans cache
docker image prune         # Supprime les images inutilisées
```

---

## 9. Dépannage

| Symptôme | Cause | Solution |
|---|---|---|
| `Path does not exist src/main.py` | Commande lancée depuis la racine | `cd backend` avant `uv run fastapi dev src/main.py` |
| `failed to read dockerfile: open Dockerfile.dev` | `docker build` lancé hors de `backend/` | `cd backend`, ou passer par `docker compose` depuis la racine |
| `The command 'docker' could not be found in this WSL 2 distro` | Intégration WSL désactivée | Docker Desktop → *Settings → Resources → WSL Integration* |
| `Cannot connect to the Docker daemon` | Docker Desktop fermé | Lancer Docker Desktop |
| `port is already allocated` | Port 8000 ou 5432 déjà utilisé | Arrêter le service qui l'occupe (`docker ps`) ou un PostgreSQL local |
| `ModuleNotFoundError: No module named 'main'` | Fichier de test lancé avec `python` | Lancer `uv run pytest` |
| Le backend n'arrive pas à se connecter à la base après un changement de mot de passe | Base créée avec l'ancien mot de passe | `down -v` puis `up` |
| `uv sync --locked` échoue au build | `uv.lock` pas à jour | `uv lock` dans `backend/`, puis committer `uv.lock` |
| `{"detail":"Not Found"}` sur http://127.0.0.1:8000/ | Aucune route sur `/` | Utiliser `/api/health` ou `/api/docs` |

---

## 10. Conventions Git

- Une branche par fonctionnalité, nommée selon ce qu'elle fait (jamais par le nom d'une personne) : `feature/clock-in`, `fix/login-error`, `ci/github-actions`.
- Intégration par pull request uniquement, après review et CI au vert.
- Messages de commit en anglais, au format [Conventional Commits](https://www.conventionalcommits.org/) :

| Type | Usage |
|---|---|
| `feat` | Nouvelle fonctionnalité |
| `fix` | Correction de bug |
| `test` | Ajout ou modification de tests |
| `build` | Dépendances, Dockerfile, Compose |
| `ci` | Pipeline GitHub Actions |
| `docs` | Documentation |
| `chore` | Maintenance du dépôt |

Exemples : `feat(backend): add clock-in endpoint`, `build(backend): add sqlalchemy`, `docs: update readme`.
