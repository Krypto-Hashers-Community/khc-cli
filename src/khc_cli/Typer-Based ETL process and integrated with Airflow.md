# ETL Orchestration with Apache Airflow

To automate, schedule, and monitor our ETL (Extract, Transform, Load) process for the "Awesome Cure" project, we leverage Apache Airflow. The core ETL logic, which fetches data from "Awesome" lists on GitHub, gathers detailed project information, and saves it to CSVs, is implemented as a Command Line Interface (CLI) using `Typer` (the `khc-cli` command, defined in `app.py` and exposed via `pyproject.toml`).

**How it Works:**

1. **Core ETL CLI (khc-cli):**

* **Extract:** Fetches the content of an "Awesome" list's README from a specified GitHub repository.
* **Transform:** Parses the README, then for each GitHub project found, it queries the GitHub API to collect metadata (stars, commits, issues, organization details, license, etc.).
* **Load:** Writes the processed project and organization data into separate CSV files.

2. **Apache Airflow DAG (awesome_cure_dag.py):**

* We define an Airflow Directed Acyclic Graph (DAG) in a separate Python file (e.g., `awesome_cure_dag.py`) located in Airflow's `dags` folder.
* This DAG uses Airflow's `BashOperator` to execute our `khc-cli` command.
* Parameters for the ETL (like the Awesome list URL, output CSV paths) are passed as command-line arguments to `khc-cli` within the `BashOperator`.
* Sensitive information, such as the `GITHUB_API_KEY`, is managed securely using Airflow Connections (e.g., a connection named `github_api` stores the key, which is then templated into the bash command: `{{ conn.github_api.password }}`).

## Deployment & Execution:

* The `khc_awesome_cure` Python package (containing `app.py` and its CLI) must be installed in the Python environment where Airflow workers run.
* The DAG file is placed in Airflow's `dags` directory.
* Airflow then discovers the DAG, allowing users to:
    - **Schedule** regular runs (e.g., daily, weekly).
    - **Trigger** runs manually.
    - **Monitor** execution status, logs, and retries through the Airflow UI.

## Benefits of this Integration:

* **Automation:** The entire ETL pipeline can be run automatically on a schedule.
* **Reliability:** Airflow handles retries and provides alerts for failures.
* **Scalability:** Airflow can manage complex workflows and distribute tasks.
* **Monitoring & Logging:** Centralized logging and a user interface for tracking pipeline progress and history.
* **Parameterization:** Easy configuration of ETL runs through Airflow variables or DAG parameters.

## Conclusion:

This setup allows for robust and manageable deployment of our ETL process, making it easier for contributors to understand its operation and for operators to maintain it.

