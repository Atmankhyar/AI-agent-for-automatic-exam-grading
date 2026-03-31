# ExamESICorrector (MVP)

Pipeline de correction automatisée (QCM, questions ouvertes, code) avec FastAPI/Next.js et orchestrateur Celery.

## Dossiers
- `backend/` : API FastAPI, tâches Celery, logique OCR/LLM.
- `frontend/` : UI Next.js (squelette à compléter).
- `infra/` : fichiers Docker.

## Démarrage rapide (local, dev)
1. Créez un fichier `backend/.env` (voir `backend/.env.example`).
2. Installez les dépendances Python : `pip install -r backend/requirements.txt`.
3. Lancez la base + redis via Docker : `docker compose up db redis`.
4. Appliquez les migrations (bientôt Alembic) puis démarrez l'API : `uvicorn app.main:app --reload --port 8000`.

## Prochaines étapes
- Ajouter migrations Alembic et modèles manquants.
- Compléter l'orchestrateur Celery + file MinIO/S3.
- Finaliser l'UI Next.js.
