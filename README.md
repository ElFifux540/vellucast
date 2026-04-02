# Vellucast

Plateforme de **streaming multimédia auto-hébergée** : catalogue de films et séries, lecture vidéo dans le navigateur (HTTP Range), **transcodage** et **optimisation** de fichiers via FFmpeg, paramètres de transcodage persistés en base, et **accès invité** par liens temporaires partageables.  
Stack : **FastAPI** + SQLite (async) côté serveur, **Vue 3** + Vite + Tailwind CSS côté client.

---

## Sommaire

- [Fonctionnalités principales](#-fonctionnalités-principales)
- [Prérequis système](#-prérequis-système)
- [Installation](#-installation)
- [Lancement en local](#-lancement-en-local)
- [Configuration](#-configuration)
- [Structure du dépôt](#-structure-du-dépôt)
- [Production & sécurité](#-production--sécurité)

---

## Fonctionnalités principales

- Authentification par jetons (utilisateurs et rôles admin / utilisateur).
- Catalogue de contenus (`contents`) avec chemins médias validés sous un dossier racine configurable.
- **Streaming** avec support des en-têtes `Range` et authentification adaptée au lecteur HTML5.
- **Transcodage** (ex. MKV → MP4) et **worker d’optimisation** en arrière-plan (FFmpeg, archivage des originaux).
- **Partage invité** : création de liens à durée et usages limités, éventuellement protégés par code.
- Interface d’administration (paramètres dossiers médias, transcodage, utilisateurs, liens).
- Journalisation d’audit et API de santé (`/health`).

---

## Prérequis système

| Outil | Rôle |
|--------|------|
| **Python** 3.10+ (recommandé 3.11+) | Backend FastAPI, SQLite async |
| **Node.js** 18+ et **npm** | Build et serveur de dev Vite (Vue 3) |
| **FFmpeg** (et **ffprobe**, souvent inclus) | Transcodage, streaming, worker d’optimisation |

Vérifiez que `ffmpeg` et `ffprobe` sont dans le `PATH` du système :

```bash
ffmpeg -version
ffprobe -version
```

---

## Installation

### 1. Cloner ou copier le projet

Placez-vous à la racine du dépôt (dossier contenant `backend/` et `frontend/`).

### 2. Backend

```bash
cd backend
python -m venv .venv
```

**Windows (PowerShell)** :

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS** :

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

La base SQLite est créée au premier démarrage (fichier sous `backend/data/` selon la configuration du projet).

### 3. Frontend

```bash
cd frontend
npm install
```

---

## Lancement en local

Deux terminaux sont nécessaires : **API** (port **8000**) et **interface** (port **5173** par défaut avec Vite).

### Backend — Uvicorn

Depuis le dossier `backend` avec l’environnement virtuel activé :

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Documentation interactive Swagger : [http://localhost:8000/docs](http://localhost:8000/docs)
- Santé : [http://localhost:8000/health](http://localhost:8000/health)

### Frontend — Vite

Depuis le dossier `frontend` :

```bash
npm run dev
```

L’application Vue charge l’API via l’URL définie dans `frontend/src/config.js` (`API_BASE`, par défaut `http://localhost:8000`). Adaptez-la si votre API tourne sur un autre hôte ou port.

### Script Windows (optionnel)

À la racine du projet, `start.ps1` peut lancer backend et frontend dans des fenêtres séparées (voir le script pour le détail).

### Build de production du frontend

```bash
cd frontend
npm run build
```

Les fichiers statiques sont générés dans `frontend/dist/`. Le mode `preview` Vite (`npm run preview`) permet de tester le build localement ; l’hébergement du build derrière un reverse-proxy ou la copie vers un serveur de fichiers est à prévoir selon votre déploiement.

---

## Configuration

Les paramètres sont lus depuis les **variables d’environnement** du processus. Il n’y a pas de fichier `.env` imposé dans le dépôt : vous pouvez exporter les variables dans le shell ou utiliser un fichier `.env` chargé par votre outil (par exemple **`uvicorn --env-file .env`** si vous utilisez cette option).

### Variables principales (`backend/app/config.py`)

| Variable | Description | Défaut (dev) |
|----------|-------------|----------------|
| `APP_ENV` | Environnement (`dev` désactive certaines contraintes de sécurité au démarrage) | `dev` |
| `APP_SECRET` | Secret pour la signature des jetons (**à changer en production**, min. 32 caractères si `APP_ENV` ≠ `dev`) | `dev-secret-change` |
| `TOKEN_TTL_MINUTES` | Durée de vie des jetons (minutes) | `60` |
| `CORS_ORIGINS` | Origines autorisées pour le navigateur, séparées par des virgules | `http://localhost:5173` |
| `MEDIA_FOLDER` | Dossier racine des médias (chemins des contenus doivent y rester) | *(vide)* |
| `ARCHIVES_FOLDER` | Racine des archives après optimisation ; si vide : `MEDIA_FOLDER/archives` | *(vide)* |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Compte administrateur initial (seed) | `admin` / `admin123456!` |
| `USER_USERNAME` / `USER_PASSWORD` | Compte utilisateur initial (seed) | `user` / `user123456!` |
| `PASSWORD_MIN_LENGTH` | Longueur minimale des mots de passe | `10` |
| `PASSWORD_ITERATIONS` | Itérations PBKDF2 | `120000` |
| `AUTH_RATE_LIMIT_*` / `GUEST_RATE_LIMIT_*` | Fenêtres et plafonds pour le rate limiting | *(voir code)* |

### Cohérence frontend / API

- Le frontend utilise **`API_BASE`** dans `frontend/src/config.js` pour toutes les requêtes. En développement, gardez l’origine dans **`CORS_ORIGINS`** côté backend (ex. `http://localhost:5173`).

### Paramètres applicatifs (base de données)

Dossiers films/séries, options de transcodage et d’optimisation sont aussi stockés dans la table **`app_settings`** et modifiables via l’interface administrateur après connexion.

---

## Structure du dépôt

```
Projet TFE/
├── backend/
│   ├── app/           # Application FastAPI (routes, DB, streaming, upload, optimizer…)
│   ├── data/          # Base SQLite (créée au runtime)
│   └── requirements.txt
├── frontend/
│   ├── src/           # Vue 3, Vite, Tailwind
│   └── package.json
├── start.ps1          # Démarrage rapide Windows (optionnel)
├── ops_log.md         # Journal d’exploitation (projet)
└── version_log.md     # Journal de versions (projet)
```

---

## Production & sécurité

- Définissez **`APP_ENV`** sur une valeur autre que `dev` uniquement lorsque **`APP_SECRET`**, **`PASSWORD_*`** et les mots de passe admin/utilisateur respectent les règles vérifiées au démarrage (`validate_security_settings`).
- Ne commitez pas de secrets : utilisez des variables d’environnement ou un fichier `.env` ignoré par Git.
- Placez **`MEDIA_FOLDER`** sur un disque dédié avec sauvegardes adaptées ; **`ARCHIVES_FOLDER`** peut être sur le même volume ou un autre chemin absolu.
- Servez l’API derrière HTTPS (reverse-proxy) et restreignez l’accès réseau si nécessaire.

---

## Licence

Projet lié à un travail de fin d’études (TFE) — précisez ici la licence souhaitée (ex. MIT, usage privé) selon votre établissement.

---

*Documentation générée pour le dépôt Vellucast — FastAPI + Vue 3.*
