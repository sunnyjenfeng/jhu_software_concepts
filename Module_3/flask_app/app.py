import os


import psycopg

from flask import Flask, render_template
from psycopg import OperationalError

# from queries import QUERIES


app = Flask(__name__)


def create_db_connection(db_name, db_user, db_password, db_host, db_port):

    """
    create conenction to my db
    """

    connection = None
    try:
        connection = psycopg.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


# def run_query(connection, query_info):
#     result = dict(query_info)

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute(query_info["sql"])
#             rows = cursor.fetchall()
#             result["columns"] = [desc.name for desc in cursor.description]
#     except Exception as error:
#         result["error"] = str(error)
#         result["columns"] = []
#         result["rows"] = []
#         result["value"] = "Error"
#         return result

#     return result


@app.route("/")
def index():
    # error = None
    # results = []

    # connect to db
    conn = create_db_connection("gradcafe_db_v2", "postgres", "181818", "127.0.0.1", "5432")
    cur = conn.cursor()

    cur.execute("SELECT * FROM applicants LIMIT 5;")
    applicants = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', applicants=applicants) 


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
