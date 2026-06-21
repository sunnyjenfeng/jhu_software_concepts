from setuptools import setup

setup(
    name="gradcafe-dashboard",
    version="0.1.0",
    py_modules=[
        "app",
        "load_data",
        "query_data",
        "queries_2",
    ],
    package_dir={"": "src"},
    install_requires=[
        "Flask",
        "psycopg",
        "psycopg2-binary",
        "python-dotenv",
    ],
)