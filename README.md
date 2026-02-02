# ErgoLab

Το ErgoLab είναι μια ολοκληρωμένη πλατφόρμα διαχείρισης εργαστηρίων και έργων, που αποτελείται από Backend, Web Portal και Mobile εφαρμογή.

## 🏗️ Αρχιτεκτονική

Το σύστημα αποτελείται από τα εξής μέρη:

- **Backend**: Python (FastAPI), PostgreSQL, SQLAlchemy, Alembic.
- **Web Portal**: React, Vite, Tailwind CSS.
- **Mobile App**: Flutter (Android/iOS).
- **Infrastruture**: Docker, Nginx, MinIO (S3 compatible for local dev).

## 🚀 Εγκατάσταση και Εκτέλεση

### Προαπαιτούμενα
- Docker & Docker Compose
- Environment Files (Δείτε το `SECURITY_CHECKLIST.md` για λεπτομέρειες)

### Γρήγορη Εκκίνηση

1. **Ρύθμιση Περιβάλλοντος**
   Αντιγράψτε τα παραδείγματα ρυθμίσεων:
   ```bash
   cp .env.example .env
   cp portal-web/.env.example portal-web/.env
   ```

2. **Εκκίνηση Εφαρμογής**
   ```bash
   docker-compose up --build
   ```

Η εφαρμογή θα είναι διαθέσιμη στα:
- API Docs: `http://localhost:8000/docs`
- Web Portal: `http://localhost:5173` (ή 80 αναλόγως το config)
- MinIO Console: `http://localhost:9001`

## 🧪 Testing

Το project διαθέτει ενσωματωμένες εντολές για testing μέσω του `Makefile`.

```bash
# Εκτέλεση όλων των backend tests
make test-backend

# Εκτέλεση unit tests
make test-unit

# Έλεγχος κάλυψης κώδικα (Coverage)
make test-coverage

# Security checks (Bandit, Safety)
make test-security

# Linting (Black, Flake8, MyPy)
make test-lint
```

## 📂 Δομή Φακέλων

- `/backend`: Ο κώδικας του API (FastAPI)
- `/portal-web`: Η web εφαρμογή (React)
- `/mobile_app`: Η mobile εφαρμογή (Flutter)
- `/scripts`: Utility scripts για συντήρηση και setup
