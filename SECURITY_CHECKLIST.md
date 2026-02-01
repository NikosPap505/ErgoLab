# Security Checklist - ErgoLab

## ✅ Τι Έχει Γίνει

### 1. .gitignore Ενημέρωση
Το `.gitignore` έχει ενημερωθεί για να αποκλείει:

#### Ευαίσθητα Αρχεία Διαμόρφωσης
- ✅ `.env` και παραλλαγές (.env.local, .env.production, κλπ)
- ✅ Πιστοποιητικά (*.pem, *.key, *.crt, *.pfx)
- ✅ Φάκελοι secrets/ και .secrets/
- ✅ Backup αρχεία που μπορεί να περιέχουν credentials (*.backup, *.dump, *.sql)

#### Build & Dependencies
- ✅ Python: __pycache__/, venv/, .venv/, *.egg-info/
- ✅ Node.js: node_modules/, build/, dist/
- ✅ Flutter: .dart_tool/, build/

#### Databases
- ✅ SQLite: *.db, *.sqlite, *.sqlite3
- ✅ PostgreSQL data directories

#### Logs & Temporary
- ✅ Όλα τα log αρχεία (*.log)
- ✅ Temporary directories (tmp/, temp/, .cache/)

## 🔒 Συστάσεις Ασφαλείας

### 1. Environment Variables
**ΣΗΜΑΝΤΙΚΟ**: Μην κάνετε commit τα πραγματικά `.env` αρχεία!

Υπάρχουν `.env.example` αρχεία που δείχνουν τη δομή:
Υπάρχουν `.env.example` αρχεία που δείχνουν τη δομή:
- `./.env.example`
- `./portal-web/.env.example`

**Πώς να δημιουργήσετε το .env σας:**
```bash
# Root directory
cp .env.example .env
# Επεξεργαστείτε το .env και προσθέστε πραγματικά credentials

# Portal web
cp portal-web/.env.example portal-web/.env
```

### 2. Ευαίσθητα Δεδομένα στο .env

Τα παρακάτω **ΠΟΤΕ** δεν πρέπει να γίνουν commit:

#### Database
```
POSTGRES_PASSWORD=your_secure_postgres_password
DATABASE_URL=postgresql://...
REDIS_PASSWORD=your_secure_redis_password
```

#### Authentication
```
SECRET_KEY=your_super_secret_jwt_key_min_32_characters
```

#### S3/MinIO
```
MINIO_ROOT_PASSWORD=your_secure_minio_password
S3_SECRET_KEY=your_secure_minio_password
```

#### Email (SMTP)
```
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 3. Docker Secrets (Production)

Για production, χρησιμοποιήστε Docker secrets αντί για environment variables:

```yaml
services:
  backend:
    secrets:
      - db_password
      - jwt_secret
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
      JWT_SECRET_FILE: /run/secrets/jwt_secret

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

### 4. Έλεγχος για Leaked Secrets

Εγκαταστήστε το `gitleaks` για έλεγχο:
```bash
# Installation (Ubuntu/Debian)
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz
tar xvzf gitleaks_8.18.0_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/

# Scan repository
gitleaks detect --source . --verbose
```

### 5. Pre-commit Hooks

Υπάρχει `.pre-commit-config.yaml` που μπορεί να επεκταθεί:

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
        name: Detect hardcoded secrets
        description: Detect hardcoded secrets using Gitleaks
        entry: gitleaks protect --staged --redact -v
        language: system
        pass_filenames: false
```

Ενεργοποίηση:
```bash
pip install pre-commit
pre-commit install
```

### 6. Αρχεία που ΔΕΝ Πρέπει Ποτέ να Γίνουν Commit

❌ `.env` (μόνο .env.example)  
❌ `*.key`, `*.pem`, `*.pfx` (πιστοποιητικά)  
❌ `secrets/` directories  
❌ `*.backup`, `*.dump` (database backups)  
❌ `config.local.*` (local configurations με credentials)  
❌ Οποιοδήποτε αρχείο με passwords/tokens στο όνομα  

### 7. CI/CD Environment Variables

Για GitLab CI (`.gitlab-ci.yml`), χρησιμοποιήστε protected variables:

**Settings → CI/CD → Variables:**
- `DATABASE_URL` (Protected, Masked)
- `SECRET_KEY` (Protected, Masked)
- `SMTP_PASSWORD` (Protected, Masked)
- `MINIO_ROOT_PASSWORD` (Protected, Masked)

### 8. Έλεγχος Git History

Αν τυχαίως έχετε κάνει commit sensitive data:

```bash
# Έλεγχος git history για credentials
git log --all --full-history -- "*.env"
git log -S "PASSWORD" --source --all

# Αφαίρεση από history (ΠΡΟΣΟΧΗ: rewrite history)
git filter-repo --path .env --invert-paths
```

### 9. Rotate Credentials

Αν έχετε κάνει λάθος commit credentials:

1. **Αλλάξτε ΑΜΕΣΑ** όλα τα passwords/keys που διέρρευσαν
2. Αφαιρέστε τα από git history
3. Ενημερώστε το .gitignore
4. Force push (αν είναι private repo)

### 10. Regular Security Audits

```bash
# Python dependencies
pip-audit

# Node.js dependencies
npm audit
npm audit fix

# Docker image scanning
docker scan ergolab-backend:latest
```

## 📋 Quick Checklist Πριν το Commit

- [ ] Δεν υπάρχουν .env αρχεία στο git status
- [ ] Δεν υπάρχουν αρχεία με passwords/keys
- [ ] Τα .env.example δεν έχουν πραγματικά credentials
- [ ] Τα logs δεν περιέχουν sensitive data
- [ ] Τα database dumps είναι excluded
- [ ] Έτρεξα `git status` και τσέκαρα τα untracked files

## 🚨 Τι Να Κάνετε Αν...

### Έκανα commit ένα .env αρχείο;

```bash
# Αμέσως:
git rm --cached .env
git commit -m "Remove accidentally committed .env file"

# Rotate όλα τα credentials που ήταν μέσα
# Clean git history αν χρειάζεται
```

### Βρήκα hardcoded password στον κώδικα;

```bash
# 1. Αφαιρέστε το hardcoded password
# 2. Μετακινήστε το στο .env
# 3. Ενημερώστε τον κώδικα να το διαβάζει από environment variable
# 4. Αλλάξτε το password (μην ξαναχρησιμοποιήσετε το ίδιο!)
```

## 📚 Resources

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12 Factor App - Config](https://12factor.net/config)
- [GitLeaks Documentation](https://github.com/gitleaks/gitleaks)
- [Git Secret](https://git-secret.io/)

---

**Τελευταία ενημέρωση**: Φεβρουάριος 2026
