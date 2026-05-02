# 🔐 Secure Vault — Encrypted File Storage

A full-stack web application for **secure, encrypted file storage** built with Flask. Users can register, log in, and upload files that are transparently encrypted at rest using Fernet symmetric encryption (AES-128-CBC). Files can only be accessed and decrypted by their rightful owner, and the application is hardened with multiple layers of security controls.

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Security Architecture](#-security-architecture)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup)
  - [Docker Setup](#docker-setup)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Routes](#-api-routes)
- [Database Models](#-database-models)
- [Running Tests](#-running-tests)
- [Security Considerations](#-security-considerations)
- [Allowed File Types](#-allowed-file-types)
- [Limitations & Future Improvements](#-limitations--future-improvements)

---

## ✨ Features

- 🔒 **Encrypted File Storage** — All uploaded files are encrypted using Fernet (AES-128-CBC with HMAC-SHA256) before being written to disk. Plaintext never touches the filesystem.
- 👤 **User Authentication** — Secure registration and login with bcrypt-hashed passwords.
- 📁 **Per-User File Isolation** — Users can only view, download, or delete their own files. Unauthorized access attempts return HTTP 403.
- 📤 **File Upload** — Upload files up to 16 MB with automatic extension validation and timestamped, collision-safe stored filenames.
- 📥 **File Download** — On-the-fly decryption: files are decrypted in memory and streamed to the user without leaving plaintext on disk.
- 🗑️ **File Deletion** — Removes both the encrypted file from disk and the database record atomically.
- 🛡️ **CSRF Protection** — All mutating forms are protected via Flask-WTF CSRF tokens.
- ⏱️ **Rate Limiting** — Login endpoint is rate-limited to 5 POST requests per minute to mitigate brute-force attacks.
- 🍪 **Secure Session Cookies** — `HttpOnly`, `SameSite=Lax`, and `Secure` flags set on session cookies.
- 🐳 **Docker Ready** — Dockerfile runs the app as a non-root user via Gunicorn.
- 🧪 **Test Suite** — Integration tests covering auth flow, encrypted upload, and decrypted download.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Flask 3.0.2 |
| **Database ORM** | Flask-SQLAlchemy 3.1.1 |
| **Database** | SQLite (dev) / any SQLAlchemy-compatible DB (prod) |
| **Authentication** | Flask-Login 0.6.3 |
| **Password Hashing** | Flask-Bcrypt 1.0.1 (bcrypt) |
| **Encryption** | `cryptography` 42.0.5 — Fernet (AES-128-CBC + HMAC-SHA256) |
| **Forms & CSRF** | Flask-WTF 1.2.1 / WTForms |
| **Rate Limiting** | Flask-Limiter 3.5.0 |
| **WSGI Server** | Gunicorn 21.2.0 |
| **Containerisation** | Docker (python:3.11-slim) |
| **Environment Config** | python-dotenv 1.0.1 |
| **Testing** | Python `unittest` |

---

## 📂 Project Structure

```
secure-file-storage-main/
│
├── app/
│   ├── __init__.py         # Application factory (create_app)
│   ├── auth.py             # Authentication blueprint (login, register, logout)
│   ├── encryption.py       # Fernet encrypt/decrypt helpers
│   ├── extensions.py       # Flask extension instances (db, bcrypt, limiter…)
│   ├── forms.py            # WTForms definitions (LoginForm, RegisterForm)
│   ├── main.py             # Main blueprint (dashboard, upload, download, delete)
│   └── models.py           # SQLAlchemy models (User, File)
│
├── templates/
│   ├── login.html          # Combined login / register page
│   └── upload.html         # Dashboard with file list + upload form
│
├── tests/
│   ├── __init__.py
│   └── test_app.py         # Integration tests (auth, upload, download)
│
├── config.py               # DevelopmentConfig / ProductionConfig / TestingConfig
├── wsgi.py                 # Gunicorn/WSGI entry point
├── Dockerfile              # Container definition (non-root, Gunicorn)
├── requirements.txt        # Python dependencies
└── .env.example            # Environment variable template
```

---

## 🔐 Security Architecture

### Encryption
Files are encrypted using the **Fernet** symmetric encryption scheme from the Python `cryptography` library. Fernet guarantees:
- **Confidentiality** via AES-128 in CBC mode.
- **Integrity & Authenticity** via HMAC-SHA256.
- **IV freshness** — a random 128-bit IV is generated per-encryption, so encrypting the same file twice yields different ciphertext.

The encryption key is loaded from the `ENCRYPTION_KEY` environment variable and **never hardcoded**. A missing or malformed key raises a `ValueError` at encryption/decryption time, preventing silent data corruption.

### Stored Filenames
Uploaded files are **never stored under their original names**. The stored filename is:
```
{user_id}_{utc_timestamp}_{original_filename}.enc
```
- Prevents filename collisions across users.
- Prevents path traversal attacks (`werkzeug.utils.secure_filename` is applied).
- The `.enc` extension signals encrypted content to any filesystem observer.

### Password Storage
Passwords are hashed with **bcrypt** (via Flask-Bcrypt) before being stored. Plaintext passwords are never written to the database.

### Authorization
Every download and delete route checks `file_record.user_id == current_user.id`. A mismatch logs a warning and returns HTTP **403 Forbidden** — users cannot access other users' files by guessing IDs.

### CSRF
All state-changing forms (upload, delete, login, register) are protected by **Flask-WTF CSRF tokens**. Requests without a valid token are rejected.

### Rate Limiting
The `/login` POST route is capped at **5 requests per minute** per IP address using Flask-Limiter (in-memory store; upgrade to Redis for multi-worker deployments).

### Secure Cookie Flags
| Flag | Value | Purpose |
|---|---|---|
| `SESSION_COOKIE_HTTPONLY` | `True` | Prevent JavaScript access to the session cookie |
| `SESSION_COOKIE_SAMESITE` | `Lax` | Mitigate CSRF via cross-site requests |
| `SESSION_COOKIE_SECURE` | `True` (prod) | Cookie only sent over HTTPS |

### Safe Redirect
The login view validates the `next` redirect parameter using an `is_safe_url()` check (same host only) to prevent **open redirect** attacks.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- `pip`
- (Optional) Docker

---

### Local Setup

**1. Clone the repository**
```bash
git clone https://github.com/your-username/secure-file-storage.git
cd secure-file-storage
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure environment variables**

Copy the example file and fill in the required values:
```bash
cp .env.example .env
```

Edit `.env`:
```env
SECRET_KEY=your_random_secret_key_here
ENCRYPTION_KEY=your_fernet_key_here
DATABASE_URL=sqlite:///database.db
FLASK_APP=wsgi.py
FLASK_ENV=development
```

> **Generating a Fernet key:**
> ```python
> from cryptography.fernet import Fernet
> print(Fernet.generate_key().decode())
> ```

**5. Run the development server**
```bash
flask run
```

The app will be available at `http://127.0.0.1:5000`.

> The database and `uploads/` folder are created automatically on first run via `db.create_all()` and `os.makedirs()`.

---

### Docker Setup

**1. Build the image**
```bash
docker build -t secure-vault .
```

**2. Run the container**
```bash
docker run -d \
  -p 8000:8000 \
  -e SECRET_KEY="your_secret_key" \
  -e ENCRYPTION_KEY="your_fernet_key" \
  -e DATABASE_URL="sqlite:///database.db" \
  -v $(pwd)/uploads:/home/vaultuser/app/uploads \
  --name secure-vault \
  secure-vault
```

The app will be available at `http://localhost:8000`.

> **Note:** The container runs as the non-root user `vaultuser` for improved security. The `uploads/` directory is mounted as a volume so data persists across container restarts.

---

## ⚙️ Configuration

Configuration is managed via `config.py` and resolved by `FLASK_ENV`:

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret — **change in production** | Hardcoded fallback (insecure) |
| `ENCRYPTION_KEY` | Fernet key (base64 url-safe, 32 bytes) — **required** | `None` (raises ValueError) |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///database.db` |
| `FLASK_ENV` | `development` / `production` / `testing` | `production` |
| `UPLOAD_FOLDER` | Path to store encrypted files | `<project_root>/uploads/` |
| `MAX_CONTENT_LENGTH` | Maximum upload size | 16 MB |

### Config Environments

| Config Class | `DEBUG` | `SESSION_COOKIE_SECURE` | `DB` |
|---|---|---|---|
| `DevelopmentConfig` | `True` | `False` | SQLite file |
| `ProductionConfig` | `False` | `True` | From `DATABASE_URL` env var |
| `TestingConfig` | — | `False` | In-memory SQLite |

---

## 🖥️ Usage

1. **Register** — Visit `/login` and fill in the register form with a username (3–150 chars) and password (min. 6 chars).
2. **Log In** — Use your credentials on the same `/login` page.
3. **Upload a File** — On the dashboard, choose a file and click Upload. The file is immediately encrypted and stored on the server.
4. **Download a File** — Click the download button next to any of your files. The server decrypts it in memory and streams it to you.
5. **Delete a File** — Click the delete button. Both the encrypted file on disk and the database record are removed.
6. **Log Out** — Click logout to destroy your session.

---

## 🗺️ API Routes

| Method | Route | Auth Required | Description |
|---|---|---|---|
| `GET` | `/` | No | Redirects to dashboard or login |
| `GET` / `POST` | `/login` | No | Login + Registration (combined) |
| `GET` | `/logout` | Yes | Logs out current user |
| `GET` | `/dashboard` | Yes | Lists user's uploaded files |
| `POST` | `/upload` | Yes | Encrypts and stores an uploaded file |
| `GET` | `/download/<file_id>` | Yes | Decrypts and downloads a file |
| `POST` | `/delete/<file_id>` | Yes | Deletes file from disk and database |

---

## 🗄️ Database Models

### `User`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `username` | String(150) | Unique, indexed |
| `password_hash` | String(256) | bcrypt hash |
| `role` | String(50) | Default `'user'`; reserved for RBAC |

### `File`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer (PK) | Auto-increment |
| `user_id` | Integer (FK → users.id) | Indexed |
| `original_filename` | String(255) | The user-provided filename |
| `stored_filename` | String(255) | Unique, timestamped `.enc` filename on disk |
| `upload_date` | DateTime | UTC timestamp, set on creation |

> The `User → File` relationship has `cascade="all, delete-orphan"`, so deleting a user also deletes all associated `File` records.

---

## 🧪 Running Tests

```bash
python -m pytest tests/
# or
python -m unittest discover -s tests
```

### What the tests cover

| Test | Description |
|---|---|
| `test_auth_flow` | Register a new user, verify redirect to dashboard; log out and log back in |
| `test_file_upload_and_download` | Upload a file; verify the on-disk ciphertext differs from plaintext; download and verify the decrypted content matches the original |

Tests use an in-memory SQLite database and a temporary `test_uploads/` directory, both cleaned up in `tearDown`. CSRF is disabled for the test environment.

---

## 🔒 Security Considerations

> These are important notes for anyone deploying this application in a real environment.

1. **Rotate the `ENCRYPTION_KEY` carefully.** Changing the key without re-encrypting existing files will make them unrecoverable. Implement a key rotation strategy before going to production.
2. **Use Redis for Flask-Limiter in multi-worker deployments.** The default in-memory store is not shared across Gunicorn workers. Set `storage_uri="redis://localhost:6379"` in `extensions.py`.
3. **Back up the `uploads/` directory.** Encrypted files are meaningless without the corresponding `ENCRYPTION_KEY`. Both must be backed up independently.
4. **Use HTTPS in production.** The `SESSION_COOKIE_SECURE` flag is set to `True` in `ProductionConfig`, which requires HTTPS. Place the app behind an Nginx or Caddy reverse proxy with a valid TLS certificate.
5. **Consider per-user encryption keys** for stronger tenant isolation. Currently all files are encrypted with a single application-level key.
6. **Set a proper `DATABASE_URL`** (e.g., PostgreSQL) for production instead of SQLite.

---

## 📎 Allowed File Types

The following extensions are accepted by the upload route:

```
txt  pdf  png  jpg  jpeg  gif  doc  docx  csv
```

Files with any other extension are rejected with an error message before they reach the encryption layer.

---

## 🔮 Limitations & Future Improvements

- [ ] **Per-user encryption keys** — Derive user-specific keys from passwords (e.g., PBKDF2) for stronger isolation.
- [ ] **File size display** — Show file sizes in the dashboard.
- [ ] **Pagination** — Paginate the file list for users with many files.
- [ ] **Admin panel** — Leverage the existing `role` column to build admin-only views.
- [ ] **Redis-backed rate limiting** — Required for horizontal scaling.
- [ ] **Key rotation utility** — CLI script to re-encrypt all files under a new key.
- [ ] **2FA / MFA** — Add TOTP-based two-factor authentication.
- [ ] **PostgreSQL support** — Production-grade database backend.
- [ ] **Audit logging** — Structured logs for all upload/download/delete events.
- [ ] **File sharing** — Allow users to securely share files with other registered users.

---

## 📄 License

This project is open source. Add a `LICENSE` file to specify terms (e.g., MIT, Apache 2.0).

---

## 👤 Author

**Gokul** — B.Tech CSE (Cyber Security), B.S. Abdur Rahman Crescent Institute of Science and Technology  
GitHub: [github.com/gokullaxman](https://github.com/gokullaxman)
