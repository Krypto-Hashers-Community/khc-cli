from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

# Définissez les chemins où les fichiers CSV et le cache README seront stockés par le worker Airflow.
# Ces chemins doivent être accessibles en écriture par l'utilisateur exécutant les tâches Airflow.
# Il est recommandé d'utiliser des chemins absolus.
PATH_TO_PROJECTS_CSV = "/opt/airflow/data/projects.csv"
PATH_TO_ORGS_CSV = "/opt/airflow/data/github_organizations.csv"
PATH_TO_LOCAL_README = "/opt/airflow/data/.awesome-cache.md"
AWESOME_REPO_URL = "https://github.com/Krypto-Hashers-Community/khc-cli" # Ou utilisez une Variable Airflow

with DAG(
    dag_id="awesome_cure_etl_pipeline",
    start_date=pendulum.datetime(2023, 10, 26, tz="UTC"),
    catchup=False,
    schedule_interval="@daily",  # Ou None pour manuel, ou une expression cron
    tags=["etl", "awesome-list", "github"],
    doc_md="""
    ### Awesome Cure ETL Pipeline
    Ce DAG exécute le script khc_cli pour extraire, transformer et charger
    les données d'une liste Awesome et des projets GitHub associés.
    """,
) as dag:
    run_etl = BashOperator(
        task_id="run_khc_cli_etl",
        bash_command=(
            f"source /opt/airflow/.venv/bin/activate && "
            f"khc-cli "
            f"--awesome-repo-url '{AWESOME_REPO_URL}' "
            f"--awesome-readme-filename 'README.md' "
            f"--local-readme-path '{PATH_TO_LOCAL_README}' "
            f"--projects-csv-path '{PATH_TO_PROJECTS_CSV}' "
            f"--orgs-csv-path '{PATH_TO_ORGS_CSV}' "
            f"--github-api-key '{{{{ conn.github_api.password }}}}' "
        ),

        # Vous pouvez spécifier des variables d'environnement si nécessaire
        # env={
        #     'SOME_ENV_VAR': 'value'
        # },
        # cwd='/path/to/working/directory', # Si votre script a besoin d'être dans un répertoire spécifique
    )
