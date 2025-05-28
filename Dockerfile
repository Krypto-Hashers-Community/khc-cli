FROM python:3.10 AS builder

ENV PYTHONUNBUFFERED=1

WORKDIR /opt/src

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/opt/src/.venv/bin:$PATH"

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Copy project definition and lock file
# These files are located in src/khc_cli/ relative to the build context
COPY src/khc_cli/pyproject.toml src/khc_cli/uv.lock ./

# Copy application source code
# The source code is in src/khc_cli/ relative to the build context.
# Copy its contents to /opt/src/ so pyproject.toml (now in /opt/src) can find the source files.
COPY src/khc_cli/ ./

# Create virtual environment, install build tool (build), and project dependencies from uv.lock in a single layer
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv && \
    uv sync && \
    uv pip install build

# Build the wheel
# The output directory will be /opt/src/dist
# Ensure your /opt/src/pyproject.toml (copied from src/khc_cli/pyproject.toml)
# For example, [project] name = "khc_cli", version = "0.1.0"
# And [tool.setuptools.packages.find] where = ["app"] if khc_cli package is in app/khc_cli
RUN uv run python -m build --wheel --outdir dist/
FROM apache/airflow:2.5.3-python3.10 AS runtime

# Install necessary dependencies for compiling pymssql
USER root
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    unixodbc-dev \
    freetds-dev \
    libgssapi-krb5-2 \
    libkrb5-dev \
    libldap2-dev \
    libpq-dev \
    libssl-dev \
    libcrypto++-dev \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Switch to airflow user to install Python packages
USER airflow
ENV PATH="/home/airflow/.local/bin:${PATH}"

# Upgrade pip and wheel
RUN python -m pip install --upgrade pip wheel

# Create data directory needed by the DAG
RUN mkdir -p /opt/airflow/data

# Install Python packages in a single layer
RUN pip install \
    dbt-postgres==1.0.0 \
    markupsafe==2.0.1 \
    apache-airflow-providers-discord \
    apache-airflow-providers-http \
    apache-airflow-providers-odbc \
    pyodbc \
    apache-airflow-providers-microsoft-mssql \
    apache-airflow-providers-microsoft-mssql[odbc] \
    apache-airflow-providers-microsoft-azure \
    gitpython \
    apache-airflow-providers-airbyte[http] \
    airflow-dbt \
    plyvel \
    "pyarrow<10.1.0,>=10.0.1" \
    pdfplumber \
    pandas \
    markdown \
    beautifulsoup4 \
    requests \
    feedparser \
    schedule \
    xmltodict \
    python-dotenv \
    pygithub \
    termcolor \
    pycountry \
    dateparser \
    pyyaml \
    handcalcs

WORKDIR /opt/airflow

# Copy the built wheel from the builder stage
COPY --from=builder --chown=airflow:root /opt/src/dist/*.whl /opt/airflow/khc_cli_app.whl

# Install the package and remove the wheel to save space
RUN pip install /opt/airflow/khc_cli_app.whl && \
    rm /opt/airflow/khc_cli_app.whl

COPY --chown=airflow:root dags/awesome_cure_dag.py /opt/airflow/dags/awesome_cure_dag.py