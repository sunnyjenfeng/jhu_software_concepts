Overview And Setup
==================

This project is a Flask dashboard for GradCafe admissions analysis.

Environment Variables
---------------------

``DATABASE_URL``
    PostgreSQL connection string.

Example:

.. code-block:: bash

   export DATABASE_URL="postgresql://postgres:181818@127.0.0.1:5432/gradcafe_db_v2"

Run App
-------

.. code-block:: bash

   cd Module_4
   python src/app.py

Run Tests
---------

.. code-block:: bash

   cd Module_4
   python -m pytest