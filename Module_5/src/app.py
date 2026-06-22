"""
This module create flask app, connect to the DB. 
This app has two buttons: pull data and updata analysis
"""
# pylint: disable=duplicate-code

import os
import json
import subprocess
import sys

import psycopg
from psycopg2 import Error

from flask import Flask, jsonify, redirect, render_template, request, url_for
from psycopg import OperationalError

from dotenv import load_dotenv
from queries_2 import QUERIES  #Queries needs to be in .py format to be imported

load_dotenv()
# app = Flask(__name__)

MODULE_2_DIR = os.path.join(os.path.dirname(__file__), "Module_2")
PULL_DATA_RUNNING = False

def create_db_connection(database_url=None):
    """Create conenction to PostgreSQL DB"""
    connection = None

    if database_url is None:
        database_url = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

    try:
        connection = psycopg.connect(database_url)
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")

    return connection

def run_query(connection, query):
    """This function run query"""
    try:
        cur = connection.cursor()
        # cur.execute(query["sql"])
        # cur.execute(query["sql"], query.get("params", []))
        params = query.get("params")
        if params is None:
            cur.execute(query["sql"])
        else:
            cur.execute(query["sql"], params)

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

    except Error as e:
        return {
            "number": query["number"],
            "question": query["question"],
            "columns": [],
            "rows": [],
            "error": str(e),
        }


def insert_new_applicants(connection, applicant_data):
    """This function insert new applicants"""
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
    """This function uses a subprocess"""
    subprocess.run(
        [sys.executable, script_name],
        cwd=MODULE_2_DIR,
        check=True,
    )

def create_app(test_config=None):
    """This function create the flask app"""
    myapp = Flask(__name__)

    myapp.config["DATABASE_URL"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:181818@127.0.0.1:5432/gradcafe_db_v2",
    )

    if test_config:
        myapp.config.update(test_config)

    # both url goes to the same page
    @myapp.route("/")
    @myapp.route("/analysis")
    def index():
        # conn = create_db_connection("gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432")
        conn = create_db_connection(myapp.config["DATABASE_URL"])

        results = []
        pull_message = request.args.get("pull_message")

        if conn is not None:
            for query in QUERIES:
                result = run_query(conn, query)
                results.append(result)

            conn.close() # pylint: disable=no-member

        return render_template("index.html", results=results, pull_message=pull_message)


    @myapp.route("/pull-data", methods=["POST"])
    def pull_data():
        """This is the pull data button"""
        global PULL_DATA_RUNNING # pylint: disable=global-statement

        # JF modified on 06/14 for HW4
        if PULL_DATA_RUNNING:
            # return "Pull Data is currently running. Please wait", 409
            return jsonify({"busy": True}), 409
        PULL_DATA_RUNNING = True
        # conn = create_db_connection("gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432")
        conn = create_db_connection(myapp.config["DATABASE_URL"])

        if conn is None:
            PULL_DATA_RUNNING = False
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
        except Exception as error: # pylint: disable=broad-exception-caught
            return jsonify({"ok": False, "error": str(error)}), 500

        finally:
            conn.close() # pylint: disable=no-member
            PULL_DATA_RUNNING = False

        # return redirect(url_for("index", pull_message=message))
        return jsonify({"ok": True, "message": message}), 200

    @myapp.route("/update-analysis", methods=["POST"])
    def update_analysis():
        """This is the update analysis button"""
        # JF modified on 06/14 for HW4
        # return "Pull Data is currently running. Analysis cannot update yet.", 409
        if PULL_DATA_RUNNING:
            return jsonify({"busy": True}), 409
        return redirect(url_for("index",
                        pull_message="Analysis updated with the newest database results."))
    return myapp

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
