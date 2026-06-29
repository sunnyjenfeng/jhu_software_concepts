# Module 6 Docker Compose Summary

## Architecture Overview

Module 6 is a multi-container Docker Compose application for the GradCafe dashboard. The system separates the web interface, background processing, message queue, and database into independent services.

The Compose stack contains four services:

```text
web       Flask dashboard and task publisher
worker    Background task consumer for scraping and analytics
db        PostgreSQL database
rabbitmq  RabbitMQ message broker with management UI
```

This design keeps long-running work out of the Flask request cycle. The web app responds quickly to button clicks by publishing tasks to RabbitMQ, while the worker performs scraping, cleaning, inserts, and analytics updates in the background.

## Service Roles

**web**

The `web` service builds from `src/web/Dockerfile` using `./src` as the Docker build context. It runs the Flask app with:

```text
python -m web.run
```

The web app serves the dashboard at:

```text
http://localhost:8080
```

It connects to PostgreSQL through `DATABASE_URL` and publishes tasks to RabbitMQ through `RABBITMQ_URL`.

**worker**

The `worker` service builds from `src/worker/Dockerfile` using `./src` as the Docker build context. It starts by loading the seed JSONL data, then starts the RabbitMQ consumer:

```text
python /db/load_data.py && python -m worker.consumer
```

The worker mounts:

```text
./src/data:/data:ro
./src/db:/db:ro
```

This gives the worker read-only access to the seed data and database loader script.

**db**

The `db` service uses:

```text
postgres:16
```

It initializes the schema from:

```text
src/db/init.sql
```

Database data is stored in the named Docker volume:

```text
pgdata
```

This keeps data across container restarts unless the volume is removed.

**rabbitmq**

The `rabbitmq` service uses:

```text
rabbitmq:3.13-management
```

It provides the queue used by the web app and worker. The management UI is exposed at:

```text
http://localhost:15672
```

## RabbitMQ Message Flow

The web app has two task buttons.

**Pull Data**

The `/pull-data` route publishes this task:

```json
{
  "kind": "scrape_new_data",
  "payload": {}
}
```

The message is published to:

```text
exchange: tasks
queue: tasks_q
routing key: tasks
```

The worker consumes the message and routes it to `handle_scrape_new_data`.

**Update Analysis**

The `/update-analysis` route publishes this task:

```json
{
  "kind": "recompute_analytics",
  "payload": {}
}
```

The worker consumes the message and routes it to `handle_recompute_analytics`.

## Database Initialization

PostgreSQL runs the schema file on first database initialization:

```text
src/db/init.sql
```

The schema creates three main tables:

```text
applicants
ingestion_watermarks
analytics_results
```

The `applicants` table stores GradCafe applicant records. The `url` column is unique, which prevents duplicate applicant rows:

```sql
url TEXT UNIQUE
```

The `ingestion_watermarks` table stores the most recent scraped GradCafe result ID for a source file or scrape process.

The `analytics_results` table stores cached results from the worker's analytics queries so the web dashboard can display them quickly.

When the worker starts, it runs:

```text
python /db/load_data.py
```

This loads the seed JSONL file from:

```text
/data/llm_extend_applicant_data_run.jsonl
```

The loader uses conflict-safe inserts, so if the seed data already exists, it may print:

```text
Inserted 0 new applicants.
```

That is expected when the data has already been loaded.

## Worker Behavior

After loading seed data, the worker starts consuming RabbitMQ messages:

```text
Worker waiting for tasks...
```

For `scrape_new_data`, the worker:

1. Scrapes recent GradCafe pages.
2. Cleans the raw scraped data.
3. Inserts cleaned records into `applicants`.
4. Skips duplicate URLs with `ON CONFLICT (url) DO NOTHING`.
5. Updates `ingestion_watermarks` with the largest scraped result ID.

The row count only increases when the scraper finds URLs that are not already in the database.

For `recompute_analytics`, the worker:

1. Runs the SQL analysis queries from `worker.queries_2`.
2. Converts result rows into JSON-compatible values.
3. Stores the output in `analytics_results`.
4. Updates existing query results with `ON CONFLICT (query_number) DO UPDATE`.

Messages are acknowledged only after successful processing. If an error occurs, the worker rolls back the database transaction and negatively acknowledges the message without requeueing it.

## Verification Steps

Start the stack from `Module_6`:

```bash
docker compose up --build
```

Check service status:

```bash
docker compose ps
```

Expected services:

```text
db
rabbitmq
web
worker
```

Open the dashboard:

```text
http://localhost:8080
```

Open RabbitMQ management:

```text
http://localhost:15672
```

Check worker logs:

```bash
docker compose logs -f worker
```

Check web logs:

```bash
docker compose logs -f web
```

Confirm the database row count:

```bash
docker compose exec db psql -U gradcafe_app_user -d gradcafe_db_v2
```

Then run:

```sql
SELECT COUNT(*) FROM applicants;
```

Check latest applicant rows:

```sql
SELECT p_id, program, status, url
FROM applicants
ORDER BY p_id DESC
LIMIT 10;
```

Check the scrape watermark:

```sql
SELECT source, last_seen, updated_at
FROM ingestion_watermarks;
```

Check RabbitMQ queue status:

```bash
docker compose exec rabbitmq rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers
```

For a healthy queue after tasks are processed, `tasks_q` should usually show no ready messages and one consumer.

## Notes

If clicking **Pull Data** does not increase the applicant count, it may still be working correctly. The scraper may be finding URLs that already exist in the database, and duplicate rows are intentionally skipped.

If the web app returns a `202` response for `/pull-data`, RabbitMQ shows a consumer on `tasks_q`, and the watermark updates, then the task pipeline is working.
