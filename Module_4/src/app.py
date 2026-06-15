import os
import json
import subprocess
import sys


import psycopg

from flask import Flask, jsonify, redirect, render_template, request, url_for
from psycopg import OperationalError

from queries import QUERIES  #Queries needs to be in .py format to be imported


# app = Flask(__name__)

MODULE_2_DIR = os.path.join(os.path.dirname(__file__), "Module_2")
pull_data_running = False


# def create_db_connection(db_name, db_user, db_password, db_host, db_port):

#     """
#     create conenction to my db
#     """
#     connection = None
#     try:
#         connection = psycopg.connect(
#             dbname=db_name,
#             user=db_user,
#             password=db_password,
#             host=db_host,
#             port=db_port,
#         )
#         print("Connection to PostgreSQL DB successful")
#     except OperationalError as e:
#         print(f"The error '{e}' occurred")
#     return connection

def create_db_connection(database_url=None):
    connection = None

    if database_url is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:181818@127.0.0.1:5432/gradcafe_db_v2",
        )

    try:
        connection = psycopg.connect(database_url)
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")

    return connection

def run_query(connection, query):
    try:
        cur = connection.cursor()
        cur.execute(query["sql"])

        rows = cur.fetchall() # rows is results of the query

        # Get the names of the columns returned by the SQL query.
        columns = [desc.name for desc in cur.description]

        cur.close()

        return {
            "number": query["number"],
            "question": query["question"],
            "columns": columns,
            "rows": rows,
            "error": None,
        }

    except Exception as e:
        return {
            "number": query["number"],
            "question": query["question"],
            "columns": [],
            "rows": [],
            "error": str(e),
        }


def insert_new_applicants(connection, applicant_data):
    inserted_count = 0

    insert_sql = """
        INSERT INTO applicants (
            program,
            comments,
            date_added,
            url,
            status,
            term,
            us_or_international,
            gpa,
            gre,
            gre_v,
            gre_aw,
            degree,
            llm_generated_program,
            llm_generated_university
        )
        SELECT
            %(program)s,
            %(comments)s,
            %(date_added)s,
            %(url)s,
            %(status)s,
            %(term)s,
            %(us_or_international)s,
            %(gpa)s,
            %(gre)s,
            %(gre_v)s,
            %(gre_aw)s,
            %(degree)s,
            %(llm_generated_program)s,
            %(llm_generated_university)s
        WHERE NOT EXISTS (
            SELECT 1
            FROM applicants
            WHERE url = %(url)s
        );
    """

    cur = connection.cursor()

    for applicant in applicant_data:
        program_name = applicant.get("Program Name")
        university = applicant.get("University")

        if program_name and university:
            program = program_name + ", " + university
        else:
            program = program_name or university

        row = {
            "program": program,
            "comments": applicant.get("Comments"),
            "date_added": applicant.get("Date of Information Added to Grad Cafe"),
            "url": applicant.get("URL link to applicant entry"),
            "status": applicant.get("Applicant Status"),
            "term": applicant.get("Semester and Year of Program Start"),
            "us_or_international": applicant.get("International / American Student"),
            "gpa": applicant.get("GPA"),
            "gre": applicant.get("GRE Score"),
            "gre_v": applicant.get("GRE V Score"),
            "gre_aw": applicant.get("GRE AW"),
            "degree": applicant.get("Masters or PhD"),
            "llm_generated_program": program_name,
            "llm_generated_university": university,
        }

        cur.execute(insert_sql, row)

        if cur.rowcount == 1:
            inserted_count += 1

    connection.commit()
    cur.close()

    return inserted_count


def run_module_2_script(script_name):
    subprocess.run(
        [sys.executable, script_name],
        cwd=MODULE_2_DIR,
        check=True,
    )

def create_app(test_config=None):
    app = Flask(__name__)

    app.config["DATABASE_URL"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:181818@127.0.0.1:5432/gradcafe_db_v2",
    )

    if test_config:
        app.config.update(test_config)

    # both url goes to the same page
    @app.route("/")
    @app.route("/analysis") 
   
    def index():
        # conn = create_db_connection("gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432")
        conn = create_db_connection(app.config["DATABASE_URL"])

        results = []
        pull_message = request.args.get("pull_message")

        if conn is not None:
            for query in QUERIES:
                result = run_query(conn, query)
                results.append(result)

            conn.close()

        return render_template("index.html", results=results, pull_message=pull_message)


    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        global pull_data_running

        # if pull_data_running:
        #     return redirect(url_for("index", pull_message="Pull Data is already running. Please wait."))
        
        # JF modified on 06/14 for HW4
        if pull_data_running:
            # return "Pull Data is currently running. Please wait", 409
            return jsonify({"busy": True}), 409
        
        pull_data_running = True
        # conn = create_db_connection("gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432")
        conn = create_db_connection(app.config["DATABASE_URL"])

        if conn is None:
            pull_data_running = False
            return redirect(url_for("index", pull_message="Could not connect to the database."))

        try:
            run_module_2_script("scrape.py")
            run_module_2_script("clean.py")

            applicant_data_file = os.path.join(MODULE_2_DIR, "applicant_data.json")

            with open(applicant_data_file, "r", encoding="utf-8") as f:
                applicant_data = json.load(f)

            inserted_count = insert_new_applicants(conn, applicant_data)
            message = f"Pull complete. Added {inserted_count} new applicants to the database."

        # except Exception as error:
        #     message = f"Pull failed: {error}"
        except Exception as error:
            return jsonify({"ok": False, "error": str(error)}), 500

        finally:
            conn.close()
            pull_data_running = False

        # return redirect(url_for("index", pull_message=message))
        return jsonify({"ok": True, "message": message}), 200

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        # if pull_data_running:
        #     return redirect(url_for("index", pull_message="Pull Data is currently running. Analysis cannot update yet."))
        
        # JF modified on 06/14 for HW4
        if pull_data_running:
            # return "Pull Data is currently running. Analysis cannot update yet.", 409
            return jsonify({"busy": True}), 409
        
        return redirect(url_for("index", pull_message="Analysis updated with the newest database results."))

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
