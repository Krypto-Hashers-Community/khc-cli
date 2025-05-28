# ETL Orchestration with Apache Airflow

To automate, schedule, and monitor our ETL (Extract, Transform, Load) process for the "Awesome Cure" project, we leverage Apache Airflow. The core ETL logic, which fetches data from "Awesome" lists on GitHub, gathers detailed project information, and saves it to CSVs, is implemented as a Command Line Interface (CLI) using `Typer` (the `khc-cli` command, defined in `app.py` and exposed via `pyproject.toml`).

**Installation:**

1. **Install and Test the Package:**

* Install the package locally to verify it works:

```bash
uv build --wheel
```
then,

```bash
uv pip install dist/khc_cli-0.1.0-py3-none-any.whl
```

* Run tests to ensure everything behaves as expected.

2. **Check Package Metadata:**

* Verify the package information with:

```bash
uv pip show khc_cli
```

Find `khc-cli`

```bash
uv pip list | grep khc
```

Install package

```bash
uv pip install dist/khc_cli-0.1.0-py3-none-any.whl
```

**Set the API Key as Environment Variable:**

```bash
export GITHUB_API_KEY=your_secret_api_key_here
```

Run

```bash
khc-cli --help
```

Check if the package is actually installed in your virtual environment:

```bash
uv pip list | grep khc
```

If it's missing, try reinstalling it:

```bash
uv pip install dist/khc_cli-0.1.0-py3-none-any.whl
```

If it's missing, you may need to explicitly add your package to the PYTHONPATH:

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/your/package
```

**Debug with `uv pip show`:**

```bash
uv pip show khc_cli
```

Run command

```bash
khc-cli --help
```


* Ensure that dependencies, versioning, and enty points are correclty set.

3. **Pyblish to PyPI (if needed):**

* If you want to share your package, upload it to PyPI:

```bash
uv pypi upload dist/*
```

* Ensure your credentials are set up in `~/.pypirc`.

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

**Note:**

## Update Your Airflow Connection:

**Via the Airflow UI:**

- Open the Airflow Web UI and navigate to Admin → Connections.

- Click on the **"+" (Add a new record)** button to create a new connection.

- Set the **Conn Id** to `github_api`.

- Choose an appropriate **Conn Type** (for example, select "HTTP" if you expect to interact with an HTTP API).

- Fill in the **Host** field if needed (for GitHub, it might be `api.github.com` or simply leave it blank if not relevant)

- Locate the connection with the Conn Id github_api.

- Click to edit this connection.

- In the Host field, ensure you only have the hostname (e.g., replace http://api.github.com with just api.github.com).

- Past you **GitHub API** token into the **Password** field.

- Save the connection.

## Benefits of this Integration:

* **Automation:** The entire ETL pipeline can be run automatically on a schedule.
* **Reliability:** Airflow handles retries and provides alerts for failures.
* **Scalability:** Airflow can manage complex workflows and distribute tasks.
* **Monitoring & Logging:** Centralized logging and a user interface for tracking pipeline progress and history.
* **Parameterization:** Easy configuration of ETL runs through Airflow variables or DAG parameters.

## Conclusion:

This setup allows for robust and manageable deployment of our ETL process, making it easier for contributors to understand its operation and for operators to maintain it.

