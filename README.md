# AVC Medical Analysis API

Application modulaire d'aide à l'analyse de l'AVC avec un backend FastAPI et un
frontend React. Aucun modèle ML ni résultat médical simulé n'est inclus.

## Démarrage local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Démarrage avec Docker

```bash
docker compose up --build
```

Ouvrir ensuite `http://localhost:8088`. Nginx sert le frontend et transmet
automatiquement les requêtes `/api` au backend FastAPI. PostgreSQL et le
stockage médical utilisent des volumes Docker persistants.

L'API expose `/health`, la documentation `/docs`, l'authentification sous `/auth`,
le CRUD admin sous `/users` et les routes patient sous `/patients`.

Le premier appel de connexion crée le compte initial si nécessaire :
`admin` / `admin123`. Ces valeurs et la clé JWT doivent être remplacées dans
`.env` avant tout déploiement réel.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

L'interface est alors disponible sur `http://127.0.0.1:5173`. Elle consomme par
défaut l'API sur `http://127.0.0.1:8000`. Une autre URL peut être définie avec
`VITE_API_URL`.

Le frontend couvre la connexion, les utilisateurs, les dossiers patients, le
formulaire clinique, l'upload DICOM, les analyses, la validation médicale, les
rapports, les exports et l'audit. Les patients restent de simples dossiers de
données et ne possèdent aucun compte utilisateur.

## Tests

```bash
pytest

cd frontend
npm run build
```
