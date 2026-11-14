# Library Management System

A Python-based library management application for maintaining books, members, inventory, loans, returns, fines, and library analytics. It includes a Tkinter desktop interface and a Flask web portal backed by SQLite.

## Features

- Maintain books, authors, publishers, members, librarians, physical copies, loans, and fines.
- Search and filter catalog records and track copy availability.
- Issue and return books, with overdue fine management.
- Review library activity through static and interactive analytics.
- Use the application from either the desktop GUI or web interface.

## Technology

- Python
- SQLite
- Tkinter
- Flask
- Pandas, NumPy, Matplotlib, Seaborn, and Plotly

## Requirements

- Python 3.10 or later
- `pip`
- Tkinter (included with most standard Python distributions; some Linux distributions package it separately)

Install the Python dependencies:

```shell
python -m pip install -r requirements.txt
```

## Run

From the project directory:

```shell
python run.py
```

The launcher presents options for the desktop application, web portal, tests, and dashboard. You can also start a component directly:

```shell
python run.py --gui
python run.py --web
python run.py --test
python run.py --dashboard
```

On Windows, the included `run_project.bat`, `run_desktop_app.bat`, and `run_website.bat` launchers can be double-clicked.

The web portal is available at `http://127.0.0.1:5000`. The database schema and sample records are initialized automatically when the application starts; the generated `library.db` file is local and is not included in the repository. Analytics charts and dashboards are generated from the current database as needed and are also excluded from version control.

For stable Flask sessions across restarts, set `FLASK_SECRET_KEY` in the environment before launching the web app. If it is not set, a random development key is generated at startup. Do not commit real keys to source control.

## Tests

Run the unit and integration test suite with:

```shell
python test_system.py
```

## Project layout

```text
.
├── analytics.py          # Data analytics and visualizations
├── app_gui.py            # Tkinter desktop application
├── app_web.py            # Flask web application
├── database.py           # SQLite schema and sample data
├── library_service.py    # Core library business logic
├── models.py             # Domain models
├── run.py                # Unified launcher
├── test_system.py        # Automated tests
├── DOCUMENTATION.md      # Detailed project documentation
├── requirements.txt      # Python dependencies
├── static/               # CSS and web assets
└── templates/            # Flask HTML templates
```

## Notes

- The desktop interface requires a Python installation with Tkinter available.
- The Flask server is intended for local development; configure and review deployment settings before exposing it to a network.
- The database is created alongside the application files, so ensure the project directory is writable.
