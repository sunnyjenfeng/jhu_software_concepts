

1. File structures: 

Module_3/
├── .DS_Store
├── README.md
├── app.py
├── app_test.py
├── app_test.ipynb
├── queries.py
├── static/
│   └── styles.css
├── templates/
│   ├── base.html
│   └── index.html
├── llm_extend_applicant_data_run.jsonl
├── load_data.py
└── query_data.py

2. Steps to install postgresql to my local MAC. (Note: not in virtual venv!) 
    2a. /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    2b. brew update
    2c. # Install PostgreSQL
        brew install postgresql.      
    2d. # Start PostgreSQL service
        brew services start postgresql

3. Install psycopg Under virtual venv:     
    pip install psycopg
    pip install psycopg-binary


4. Start postgressql db: 
    psql postgres        

    create the postgres role:  
    CREATE ROLE postgres WITH SUPERUSER CREATEDB CREATEROLE LOGIN PASSWORD '181818';
    \q


5. How to run: 

    5a: Enter venv
    5b: cd /Users/jennifer/Documents/software_concept_python_class/jhu_software_concepts/Module_3
    5c: python app.py
    5d: Ctrl + C to close the app

6. # Open the browser: 
    http://localhost:8080

