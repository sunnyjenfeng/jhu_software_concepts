# GradCafe Dashboard

This project is a Flask dashboard for viewing and updating GradCafe admissions data stored in a PostgreSQL database. 

## Project Structure

```text
.
├── src/
│   ├── app.py                  # Flask application entry point
│   ├── queries_2.py            # SQL analysis queries
│   ├── load_data.py            # Database loading helpers
│   ├── query_data.py           # Query helpers
│   ├── templates/              # Flask HTML templates
│   ├── static/                 # CSS files
│   └── Module_2/               # Scraping and cleaning scripts used by Pull Data
├── tests/                      # Pytest test suite
├── docs/                       # Sphinx documentation
├── .github/workflows/ci.yml    # CI checks 
├── .env.example                # Example environment variable file
├── requirements.txt            # Full development dependency list
├── setup.py                    # Editable package configuration
└── pytest.ini                  # Pytest and coverage settings
└── README.md                   # Readme file
└── dependency.svg              # Dependency graph
├── snyk-analysis.png.          # screenshot
├── Module_5_report.pdf         # Module 5 Report
├── coverage_summary.txt        # Test coverage      
```

## Fresh Install with pip

Run these commands from the project root.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
pip install -e .
```

### Using uv

```bash
uv venv
source .venv/bin/activate
uv pip sync src/requirements.txt
uv pip install -e .
```

## Environment Variables

Create a local `.env` file from the example file:

```bash
cp .env.example .env
```

Update `.env` with your real PostgreSQL settings:

```text
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=gradcafe_db_v2
DB_USER=gradcafe_app_user
DB_PASSWORD=replace_with_real_password
```

The application can also use a full PostgreSQL connection string through `DATABASE_URL`:

```bash
export DATABASE_URL="postgresql://USER:PASSWORD@127.0.0.1:5432/gradcafe_db_v2"
```

Do not commit `.env` because it contains database credentials.

## Database Setup

The app expects a running PostgreSQL database. On macOS, PostgreSQL can be installed with Homebrew:

```bash
brew install postgresql
brew services start postgresql
```

Create a database and user that match your `.env` values. Example:

```sql
CREATE DATABASE gradcafe_db_v2;
CREATE USER gradcafe_app_user WITH PASSWORD 'replace_with_real_password';
GRANT ALL PRIVILEGES ON DATABASE gradcafe_db_v2 TO gradcafe_app_user;
```

## Running the Application

Activate your environment, then run the Flask app:

```bash
source venv/bin/activate
python src/app.py
```

If you used `uv`, activate `.venv` instead:

```bash
source .venv/bin/activate
python src/app.py
```

Open the dashboard in a browser:

```text
http://localhost:8080
```

The main routes are:

- `/` and `/analysis`: display the analysis dashboard.
- `/pull-data`: runs the scrape and clean scripts, then inserts new applicants.
- `/update-analysis`: refreshes the analysis view.

## Running Tests

Run the full test suite:

```bash
pytest
```

The project uses `pytest.ini` to require 100 percent coverage:

```text
--cov=src --cov-report=term-missing --cov-fail-under=100
```

## Pylint

Command to Run Pylint on all files inside src folder: 
pylint Module_5/src

This is the same command documented in the GitHub Actions CI workflow.

## Security Tooling

This project uses Snyk in CI to scan Python dependencies for known vulnerabilities. The documented command is:

```bash
snyk test --file=src/requirements.txt --package-manager=pip
```

To run Snyk locally, install the Snyk CLI and authenticate first:

```bash
npm install -g snyk
snyk auth
snyk test --file=src/requirements.txt --package-manager=pip
```

Security-related project practices:

- Database credentials are stored in `.env` or `DATABASE_URL`, not hard-coded in source files.
- `.env.example` documents required settings without real secrets.
- Snyk scans dependencies in CI.
- Pylint runs in CI to catch code quality issues.
- Pytest with coverage runs in CI to verify behavior.

## CI Workflow

GitHub Actions runs these checks on push and pull request:

- Pylint: `pylint src tests --fail-under=10`
- Pytest: `pytest`
- Dependency graph generation with `pydeps`
- Snyk dependency scanning

