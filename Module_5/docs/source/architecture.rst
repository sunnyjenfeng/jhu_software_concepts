Architecture
============

Web
---

``src/app.py`` defines the Flask app factory, routes, database connection, and analysis rendering.

ETL
---

``src/Module_2/scrape.py`` scrapes raw GradCafe records.

``src/Module_2/clean.py`` cleans raw records.

Database
--------

PostgreSQL stores applicant records in the ``applicants`` table.

Analysis
--------

``src/queries.py`` stores SQL queries.

``src/query_data.py`` runs analysis queries.