29-01-26 : Création de la structure Backend/Frontend
29-01-26 : Création des fichiers initiaux FastAPI/Vue
29-01-26 : Initialisation des fichiers de logs
29-01-26 : Ajout des scripts de demarrage et arret
29-01-26 : Ajout des scripts Linux de demarrage et arret
29-01-26 : Correction du script start.ps1
29-01-26 : Ajustement du script start.ps1 (working directory)
29-01-26 : Correction du script stop.ps1 (arret des sous-processus)
29-01-26 : Ajout du module DB et des endpoints de partage
29-01-26 : Ajout des tables contenus et audit + endpoints invites
29-01-26 : Ajout table users et endpoints de login
29-01-26 : Seed des users par defaut et securisation des endpoints
29-01-26 : Durcissement securite (hash, CORS, rate limit, headers)
29-01-26 : Correction du contexte aiosqlite (startup)
29-01-26 : Correction complementaire aiosqlite (autres appels)
29-01-26 : Mise a jour des mots de passe par defaut (seed)
29-01-26 : Ajout first_login + menu admin + changement mdp
29-01-26 : Refonte UI accueil/login + gestion users admin
29-01-26 : Liste tokens/contenus + UI accueil moderne
29-01-26 : Correction balise App.vue (template)
29-01-26 : Restrictions user (lecture seule contenus)
29-01-26 : Statut invite (valide/refuse/expire)
29-01-26 : Max usages a 0 = infini
29-01-26 : Duree token multi-unites + 0 = infini
29-01-26 : UI accueil Tailwind (mesh, cartes, icones)
29-01-26 : Scanner media + route admin /admin/media/scan
29-01-26 : Route GET /api/stream avec Range + auth
02-04-26 : Lecteur HTML5 sans header Authorization -> Auth streaming Bearer ou query ?token= (get_stream_user)
02-04-26 : Frontend catalogue grille + VideoPlayer + transition fade-slide dans App.vue
02-04-26 : Service transcoder.py — MKV→MP4 H.264/AAC async, progression FFmpeg non bloquante
02-04-26 : Endpoint POST /api/upload admin -> Création upload chunks + dossiers films/séries + insertion contents
02-04-26 : UI admin upload média -> Ajout bouton + modal UploadMediaModal.vue + barre progression XHR + refresh contenus
02-04-26 : Upload admin -> Correction regex de sanitization (chemins/titres)
02-04-26 : Erreur FastAPI Form/UploadFile -> Ajout dépendance python-multipart dans requirements.txt + pip install
02-04-26 : Refonte UI dashboard -> Library par défaut + Settings admin + table app_settings + GET/PUT /api/settings + upload utilise dossiers DB
02-04-26 : Settings utilisateurs -> Rôle en <select> (ALLOWED_ROLES) + tableau avec changement de rôle inline
02-04-26 : Backend GET /api/files/browse admin + ids courts 8 chars + renommage {id}-{stem}.mp4|mkv + validation contenus
02-04-26 : Finalisation UI formulaire « Créer un contenu » (toast, erreurs inline, grille série) -> Ajout styles scoped dans Settings.vue + build Vite OK
02-04-26 : Mise à jour contenu admin -> Recherche auto-complétion sur contents (titre/ID), liste déroulante, validation titre/sélection + updateContent() retour structuré dans App.vue
02-04-26 : Liste contenus existants (Settings) -> Onglets Films/Séries, accordéons <details>, regroupement séries par titre (parse titre)
02-04-26 : Tokens admin -> Sections actifs / expirés-inactifs + retours verts/rouges formulaires Settings + App méthodes users/shares avec { ok, detail }
02-04-26 : Identité Vellucast (titre, nav, sections UI, FastAPI) + recherche contenu pour tokens + listes tokens en accordéons <details>
02-04-26 : Library.vue -> Onglets Films/Séries, zone hero (aperçu + bannière placeholder + Lecture), flux App sans Catalog
02-04-26 : Menu contextuel médias (Library + Settings) + colonne contents.do_not_optimize + PUT/PATCH API + fermeture clic extérieur
02-04-26 : Section admin Paramètres de Transcodage + clés app_settings + GET/PUT /api/settings étendu (transcodage / FFmpeg / plages horaires)
02-04-26 : Alignement transcodage (clés stream_* / ffmpeg_params / optimize_*) + lecture legacy app_settings + POST /api/contents/{id}/toggle-optimize + frontend Settings/Library
02-04-26 : Worker optimizer.py (asyncio + FFmpeg tmp, archives miroir, verrou lecture streaming) + list_optimizable_contents + ARCHIVES_FOLDER + startup/shutdown main
02-04-26 : Menu contextuel média : libellé dynamique Optimiser / Ne pas optimiser + MAJ locale do_not_optimize (Library + applyContentDoNotOptimizeToggle App)
02-04-26 : Library.vue onglet Séries : grille tuiles + accordéons par série / saisons / épisodes (aperçu lecteur uniquement sur clic épisode)
02-04-26 : Documentation — README.md racine (prérequis, install, uvicorn, npm, variables d'environnement)
