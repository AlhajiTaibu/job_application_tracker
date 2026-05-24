# Job Application Tracker

A full-stack application for managing your job search pipeline — track applications, automate status updates, and get email reminders, all in one place.

[//]: # (> Built as a portfolio project to demonstrate production-grade backend engineering: state machine design, OAuth2 integration, cursor-based pagination, and containerized deployment.)

---

## Features

- **Application pipeline management** — create and track job applications across a state machine-driven status workflow (`SAVED → APPLIED → SCREENING → INTERVIEW → OFFER → ACCEPTED / REJECTED / WITHDRAWN`)
- **Gmail OAuth2 integration** — send and receive job-related emails directly from the app using your Google account
- **Email reminders** — automated follow-up reminders for applications that have gone stale
- **Cursor-based pagination** — efficient, scalable list queries using keyset pagination (no offset drift)
- **Jinja2 email templates** — clean, professional HTML emails for follow-ups and confirmations
- **Environment-aware config** — toggle between development and production settings via pydantic-settings and `.env` files
- **Dockerized** — fully containerized with multi-stage builds and a non-root user for production safety

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.14) |
| Database | PostgreSQL |
| ORM | SQLAlchemy + Alembic (migrations) |
| Auth | Gmail OAuth2 (Google API) |
| Email | Gmail API + Jinja2 templates |
| Config | pydantic-settings |
| Containerization | Docker, Docker Compose |
| Package manager | uv |

---

## Architecture Highlights

### State Machine — Application Status

Applications move through a strict state machine rather than allowing arbitrary status updates. This prevents invalid transitions (e.g. jumping from `SAVED` directly to `OFFER`) and makes the pipeline auditable.

```
SAVED ──► APPLIED ──► SCREENING ──► INTERVIEW ──► OFFER ──► ACCEPTED
                                                         └──► REJECTED
                  └──► WITHDRAWN (from any active state)
```

This is a deliberate design choice and a good interview talking point — it mirrors how real-world workflows (order management, loan processing) enforce business rules at the domain level rather than the UI.

### Cursor-Based Pagination

List endpoints use keyset (cursor) pagination instead of `OFFSET`. This avoids the classic problem where inserting a new row shifts all subsequent pages, causing duplicates or skipped items in long-running sessions.

```python
# Example: GET /applications?cursor=<encoded_id>&limit=20
```

Each response returns a `next_cursor` that encodes the last seen record's ID, making pagination stable and performant at scale.

---

## Project Structure

```
job-application-tracker/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── applications.py    # CRUD + state transitions
│   │       ├── auth.py            # Gmail OAuth2 flow
│   │       └── interviews.py      # Manage Interviews
│   ├── alembic/                   # Database migrations
│   ├── core/
│   │   ├── config.py              # pydantic-settings config
│   │   └── celery.py              # Celery setup
│   ├── models/
│   │   └── application.py         # SQLAlchemy models
│   ├── schemas/
│   │   └── application.py         # Pydantic request/response schemas
│   ├── services/
│   │   ├── state_machine.py       # Status transition logic
│   │   └── email_services.py      # Gmail API client
│   ├── tasks/
│   │   ├── job_tasks.py           # Background job tasks
│   │   └── user_tasks.py          # Background user tasks                
│   └── main.py
├── templates/
│   └── auth/                      # Jinja2 HTML email templates
├── tests/
│   ├── test_applications.py
│   └── test_state_machine.py
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── pyproject.toml
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- A Google Cloud project with the Gmail API enabled
- OAuth2 credentials (`client_id` and `client_secret`) from Google Cloud Console

### 1. Clone the repo

```bash
git clone https://github.com/AlhajiTaibu/job-application-tracker.git
cd job-application-tracker
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://postgres:password@db:5432/jobtracker
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/callback
ENVIRONMENT=development
SECRET_KEY=your-secret-key
```

### 3. Run with Docker Compose

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

### 4. Run database migrations

```bash
docker compose exec app alembic upgrade head
```

---

## API Overview

| Method   | Endpoint                           | Description                          |
|----------|------------------------------------|--------------------------------------|
| `GET`    | `/api/v1/job_application/list`     | List applications (cursor-paginated) |
| `POST`   | `/api/v1/job_application/create`   | Create a new application             |
| `GET`    | `/api/v1/job_applications/{id}`    | Get a single application             |
| `PATCH`  | `/api/v1/job_application/transition/{id}` | Transition application status        |
| `DELETE` | `/api/v1/job_application/delete/{id}` | Delete an application                |
| `POST`   | `/api/v1/auth/login`               | Email and Password Authentication    |
| `GET`    | `/api/v1/auth/google/login`        | Start Gmail OAuth2 flow              |
| `GET`    | `/api/v1/auth/google/callback/`    | OAuth2 callback handler              |

[//]: # (| `POST` | `/api/v1/emails/send`                     | Send a follow-up email |)

[//]: # (| `GET` | `/api/v1/emails`                          | List received job-related emails |)

Full interactive documentation available via Swagger UI at `/docs`.

---

## Running Tests

```bash
docker compose exec app pytest
```

Or locally with `uv`:

```bash
uv run pytest
```

---

## Design Decisions & Trade-offs

These are the kinds of questions interviewers ask — documented here intentionally.

**Why FastAPI over Django?**
FastAPI's async-first design and automatic OpenAPI generation made it a better fit for a REST API with no server-side rendering. Django would be the right choice if the project needed a full admin interface or ORM-heavy features out of the box.

**Why cursor pagination over offset?**
Offset pagination degrades at scale and produces inconsistent results when rows are inserted between pages. Cursor-based pagination is O(log n) with the right index and is stable across requests — the same approach used by Twitter, Slack, and most production APIs.

**Why a state machine for statuses?**
An enum column with no transition rules allows the client to set any status freely, making the data unreliable. Encoding the allowed transitions as a state machine in the domain layer means invalid states are impossible by construction, not just by convention.

**Why multi-stage Docker builds?**
The builder stage installs dependencies (including build tools like `gcc` for `psycopg2`). The final stage copies only the compiled artifacts, keeping the production image lean and free of unnecessary build tooling.


---

## Author

**Abdurami Taibu** — Senior Full-Stack Software Engineer
[LinkedIn](www.linkedin.com/in/abdurami-alhaji-taibu) · [GitHub](https://github.com/AlhajiTaibu) · abdurami.taibu@gmail.com