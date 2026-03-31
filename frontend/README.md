# Frontend ExamESICorrector

Interface Next.js pour l'application ExamESICorrector.

## Fonctionnalités

- **Connexion / Inscription** : Authentification sécurisée
- **Tableau de bord** : Vue d'ensemble des examens et copies
- **Gestion des examens** : Création, liste, détail avec questions (QCM, ouvertes, code)
- **Dépôt de copies** : Upload PDF ou images
- **Scores** : Consultation des scores détaillés par question
- **Correction** : Bouton pour lancer la correction des copies en attente

## Démarrage

```bash
npm install
npm run dev
```

Ouvrez [http://localhost:3000](http://localhost:3000).

## Configuration

Créez un fichier `.env.local` (optionnel) :

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

L'API backend doit être accessible à cette URL. Lancez d'abord le backend (voir README principal).

**Compte de test** : enseignant@example.com / enseignant123
