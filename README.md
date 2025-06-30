# Poultry Farm Management Dashboard

A comprehensive web application built with Python, Dash, and Plotly for managing and visualizing poultry farm data. This dashboard provides a user-friendly interface for operators to log key metrics and track operational activities, helping to streamline farm management and improve production analysis.

## Features

  - **Tabbed Interface**: A clean, organized layout allowing easy navigation between different data entry and visualization modules.
  - **Weekly Production Logging**: A detailed form to enter weekly flock data, including:
      - Daily and total mortality counts.
      - Average body weight (min, max, and average).
      - Real and standard feed consumption.
  - **Daily Egg Production**: A simple form to log daily egg counts from up to four different sheds, with automatic calculation of the daily production percentage.
  - **Interactive KPI Dashboards**: Visualize the performance of each flock over time with interactive graphs for:
      - Average Body Weight per Week.
      - Weekly Mortality.
      - Accumulated Mortality.
      - Weekly Feed Consumption (Real).
      - Cumulative Feed Consumption (Real vs. Standard).
  - **Operational Records**: Dedicated forms for logging other essential farm activities:
      - **Bedding Management**: Track bedding material, installation/removal dates, and disposal.
      - **Bait Station Inspection**: Record details of rodent bait station checks.
      - **Visitor Log**: Maintain a record of all visitors to the facility.
      - **Treatment Records**: Log all medical treatments administered to the flocks.
  - **Persistent Storage**: All data is saved to a relational database (MySQL/MariaDB), ensuring data integrity and availability.

## Tech Stack

  - **Backend & Frontend**: Python
  - **Web Framework**: [Dash](https://dash.plotly.com/)
  - **UI Components**: [Dash Bootstrap Components](https://dash-bootstrap-components.opensource.faculty.ai/)
  - **Data Manipulation**: [Pandas](https://pandas.pydata.org/)
  - **Charting**: [Plotly Express](https://plotly.com/python/plotly-express/)
  - **Database ORM**: [SQLAlchemy](https://www.sqlalchemy.org/)
  - **Database Driver**: [PyMySQL](https://pypi.org/project/PyMySQL/)
  - **Database**: [MariaDB](https://mariadb.org/) or [MySQL](https://www.mysql.com/)

-----

## Getting Started

Follow these instructions to set up and run the application on your local machine.

### 1\. Prerequisites

  - Python 3.8 or newer
  - [Docker](https://www.docker.com/products/docker-desktop/) and Docker Compose (Recommended for database setup)

### 2\. Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-folder>
```

### 3\. Create a Virtual Environment

It's recommended to create a virtual environment to manage project dependencies.

```bash
# For Windows
python -m venv venv
.\venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4\. Install Dependencies

Create a file named `requirements.txt` with the following content:

```txt
dash
dash-bootstrap-components
plotly
pandas
sqlalchemy
pymysql
```

Then, install the packages:

```bash
pip install -r requirements.txt
```

### 5\. Set Up the Database

The application is configured to connect to a MariaDB/MySQL database. The easiest way to get a database running is with Docker.

1.  Create a file named `docker-compose.yml` in the root of your project with the following content:

    ```yaml
    version: '3.8'
    services:
      mariadb:
        image: mariadb:10.6
        restart: always
        environment:
          MYSQL_ROOT_PASSWORD: 'rootpass'
          MYSQL_DATABASE: 'criacao_aves'
        ports:
          - '3306:3306'
        volumes:
          - 'mariadb_data:/var/lib/mysql'

    volumes:
      mariadb_data:
    ```

2.  Start the database container:

    ```bash
    docker-compose up -d
    ```

3.  Modify the database connection string. Since the Python application will be running on your host machine and the database is in a Docker container, you need to connect via `localhost`.

      - Open the `db.py` file.
      - Find the `get_engine()` function.
      - Change the `DB_URL` from `mariadb` to `localhost`:

    <!-- end list -->

    ```python
    # in db.py
    def get_engine():
        DB_URL = os.getenv(
            "DATABASE_URL",
            # Change 'mariadb' to 'localhost' here
            "mysql+pymysql://root:rootpass@localhost:3306/criacao_aves" 
        )
        return create_engine(DB_URL, pool_pre_ping=True)
    ```

### 6\. Address Table Name Inconsistencies (Important)

There are minor inconsistencies between the table names defined in the schema (`db.py`) and the names used in the SQL queries (`callbacks.py`). **You must correct these for the application to work.**

Open `callbacks.py` and make the following changes:

1.  In the `insert_bait` function, change `INSERT INTO iscas` to `INSERT INTO inspecao_iscas`.
2.  In the `insert_visits` function, change `INSERT INTO visitas` to `INSERT INTO registro_visitas`.
3.  In the `insert_treatments` function, change `INSERT INTO tratamentos` to `INSERT INTO registro_tratamentos`.

The application's `init_db()` function will automatically create all the necessary tables in the `criacao_aves` database the first time it is run.

### 7\. Run the Application

Once the database is running and the dependencies are installed, you can start the Dash server.

```bash
python app.py
```

The application will be available at [link suspeito removido] in your web browser.

-----

## File Structure

```
.
├── app.py              # Main application entry point, initializes the Dash app.
├── callbacks.py        # Contains all Dash callback logic for interactivity.
├── db.py               # Defines the database connection and schema.
├── layout.py           # Defines the UI layout and components for all tabs.
├── requirements.txt    # Lists all Python dependencies.
└── docker-compose.yml  # Defines the MariaDB service for easy setup.
```
