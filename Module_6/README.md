# Module 6 GradCafe Dashboard

This module runs the GradCafe dashboard as a Docker Compose application. It uses a Flask web app, a PostgreSQL database, RabbitMQ, and a background worker that handles scraping and analytics tasks.

## Docker Hub Images

Docker Hub registry link:

https://hub.docker.com/repositories/pandajen

Published image repositories:

- Web app: https://hub.docker.com/repository/docker/pandajen/module6-web/general
- Worker: https://hub.docker.com/repository/docker/pandajen/module_6-worker/general

Example image tags:

```text
pandajen/module6-web:v1
pandajen/module_6-worker:v1
```

## Docker Installation Assumptions

This project assumes Docker Desktop is installed and running.

On macOS, install Docker Desktop from:

```text
https://www.docker.com/products/docker-desktop/
```

Verify Docker is available:

```bash
docker --version
docker compose version
```

The app is designed to run with Docker Compose from the `Module_6` directory.

## Project Structure

```text
Module_6/
├── docker-compose.yml
├── .env
├── .env.example
├── src/
│   ├── web/
│   │   ├── app.py
│   │   ├── run.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── worker/
│   │   ├── consumer.py
│   │   ├── scrape.py
│   │   ├── clean.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── db/
│   │   ├── init.sql
│   │   └── load_data.py
│   ├── data/
│   ├── templates/
│   └── static/
└── tests/
```

## Environment Variables

Create a `.env` file in `Module_6`.

Example:

```text
POSTGRES_USER=gradcafe_app_user
POSTGRES_PASSWORD=181818
POSTGRES_DB=gradcafe_db_v2

DATABASE_URL=postgresql://gradcafe_app_user:181818@db:5432/gradcafe_db_v2
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/

FLASK_ENV=development
FLASK_SECRET=dev-secret

SEED_JSON=/data/llm_extend_applicant_data_run.jsonl
TARGET_TABLE=applicants
ID_KEY=p_id
```

## Ports

The Compose app exposes:

```text
Web dashboard: http://localhost:8080
RabbitMQ UI:   http://localhost:15672
```

RabbitMQ management login is usually:

```text
username: guest
password: guest
```

PostgreSQL runs inside Docker and is used by the web and worker services through the Compose network.

## Build and Run

From the repository root:

```bash
cd Module_6
docker compose up --build
```

Check running services:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f web
docker compose logs -f worker
```

Stop containers:

```bash
docker compose down
```

Stop containers and remove the database volume:

```bash
docker compose down -v
```

Use `docker compose down -v` only when it is okay to delete the local database data.

## Task Buttons

Open the dashboard:

```text
http://localhost:8080
```

The page has two main task buttons.

**Pull Data**

Queues a RabbitMQ task named:

```text
scrape_new_data
```

The worker consumes the task, scrapes recent GradCafe records, cleans them, and inserts new applicant rows into PostgreSQL. Duplicate URLs are skipped with `ON CONFLICT (url) DO NOTHING`, so the row count only increases when newly scraped records are not already in the database.

**Update Analysis**

Queues a RabbitMQ task named:

```text
recompute_analytics
```

The worker recomputes the SQL analysis results and stores them in the `analytics_results` table for the dashboard to display.

## Database Checks

Open a database shell:

```bash
docker compose exec db psql -U gradcafe_app_user -d gradcafe_db_v2
```

Count applicant rows:

```sql
SELECT COUNT(*) FROM applicants;
```

Check the scrape watermark:

```sql
SELECT source, last_seen, updated_at
FROM ingestion_watermarks;
```

Exit `psql`:

```sql
\q
```

## Build, Tag, and Push Images

Build local images:

```bash
docker compose build
```

Tag the web image:

```bash
docker tag module_6-web pandajen/module6-web:v1
```

Tag the worker image:

```bash
docker tag module_6-worker pandajen/module_6-worker:v1
```

Log in to Docker Hub:

```bash
docker login
```

Push images:

```bash
docker push pandajen/module6-web:v1
docker push pandajen/module_6-worker:v1
```

If Compose shows image IDs instead of image names, tag by image ID:

```bash
docker tag IMAGE_ID pandajen/module6-web:v1
docker tag IMAGE_ID pandajen/module_6-worker:v1
```

## Tests and CI

Run tests from `Module_6`:

```bash
PYTHONPATH=src python -m pytest
```

Run Pylint on Module 6 source code:

```bash
PYTHONPATH=src pylint src --fail-under=8
```

The GitHub Actions workflow should run Pylint and Pytest with `working-directory: Module_6`. 
