# Module 4

This project is a Flask web app for analyzing GradCafe admissions data. It includes scraping and cleaning scripts, PostgreSQL loading/querying code, a Flask dashboard, pytest tests, GitHub Actions, and Sphinx documentation.

## Repository

GitHub SSH URL:

```text
git@github.com:sunnyjenfeng/jhu_software_concepts.git
```

## Project Structure

```text
Module_4/
├── src/
│   ├── app.py
│   ├── load_data.py
│   ├── query_data.py
│   ├── queries.py
│   ├── Module_2/
│   │   ├── scrape.py
│   │   └── clean.py
│   ├── templates/
│   └── static/
├── tests/
├── docs/
├── pytest.ini
└── coverage_summary.txt
```

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv /Users/jennifer/Documents/software_concept_python_class/venv
source /Users/jennifer/Documents/software_concept_python_class/venv/bin/activate
```

Install dependencies:

```bash
cd Module_4
python -m pip install --upgrade pip
python -m pip install -r src/requirements.txt
python -m pip install pytest pytest-cov sphinx
```

## Configure PostgreSQL

Create the PostgreSQL role if needed:

```sql
CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD '181818';
```

Create the database:

```sql
CREATE DATABASE gradcafe_db_v2;
```

Set the database URL:

```bash
export DATABASE_URL="postgresql://postgres:181818@127.0.0.1:5432/gradcafe_db_v2"
```

Create the applicants table:

```sql
CREATE TABLE IF NOT EXISTS applicants (
    p_id SERIAL PRIMARY KEY,
    program TEXT,
    comments TEXT,
    date_added date,
    url TEXT,
    status TEXT,
    term TEXT,
    us_or_international TEXT,
    gpa FLOAT,
    gre FLOAT,
    gre_v FLOAT,
    gre_aw FLOAT,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);
```

## Run The Flask App

From `Module_4`:

```bash
python src/app.py
```

Open:

```text
http://localhost:8080/analysis
```

## Run Tests

Run the full test suite:

```bash
python -m pytest
```

Run tests by marker:

```bash
python -m pytest -m web
python -m pytest -m buttons
python -m pytest -m analysis
python -m pytest -m db
python -m pytest -m integration
```

Run all marked tests:

```bash
python -m pytest -m "web or buttons or analysis or db or integration"
```

## Coverage

Coverage is configured in:

```text
pytest.ini
```

Save the terminal coverage summary:

```bash
python -m pytest > coverage_summary.txt
```

## Documentation

Sphinx documentation source files are in:

```text
docs/source/
```

Build docs locally:

```bash
cd docs
make clean
make html
```
Link to sphinx read the docs documentation: 
https://jhu-software-concepts-hw4.readthedocs.io/en/latest/

Open local HTML docs:

```text
docs/build/html/index.html
```

Published documentation:

```text
Add your Read the Docs URL here.
```

## GitHub Actions

The workflow file is located at:

```text
../.github/workflows/tests.yml
```

