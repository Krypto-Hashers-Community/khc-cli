"""Commandes d'analyse de repositories GitHub."""

import typer
import logging
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from pathlib import Path
from dotenv import load_dotenv
from typing_extensions import Annotated
from urllib.parse import urlparse

from khc_cli.github_client import GitHubClient
from khc_cli.utils.helpers import crawl_github_dependents

app = typer.Typer()
console = Console()
LOGGER = logging.getLogger(__name__)
# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

@app.command()
def repo(
    repo_name: Annotated[str, typer.Argument(help="Nom du repository (ex: owner/repo)")],
    output_format: Annotated[str, typer.Option("--format", "-f", help="Format de sortie: table, json")] = "table",
    github_api_key: Annotated[str, typer.Option(envvar="GITHUB_API_KEY", help="GitHub API Key")] = None,
):
    """Analyser un repository spécifique."""
    
    with Progress() as progress:
        task = progress.add_task("Analyse du repository...", total=100)
        
        github_client = GitHubClient(github_api_key)
        
        try:
            repo = github_client.client.get_repo(repo_name)
            
            if not repo:
                console.print(f"[red]Repository {repo_name} non trouvé[/red]")
                raise typer.Exit(1)
            
            progress.update(task, advance=50)
        
            # Collecter les informations
            info = {
                "name": repo.name,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language,
                "description": repo.description,
                "last_update": repo.updated_at.isoformat() if repo.updated_at else None,
                "dependents": len(crawl_github_dependents(repo_name, 5))
            }
            
            progress.update(task, advance=50)
        except Exception as e:
            console.print(f"[red]Erreur lors de l'analyse du repository {repo_name}: {e}[/red]")
            raise typer.Exit(1)
            
        if output_format == "json":
            import json
            console.print_json(json.dumps(info))
        else:
            table = Table(title=f"Analyse de {repo_name}")
            table.add_column("Propriété", style="cyan")
            table.add_column("Valeur", style="green")
            
            for key, value in info.items():
                table.add_row(key.replace("_", " ").title(), str(value))
            
            console.print(table)

@app.command()
def etl(
    awesome_repo_url: Annotated[str, typer.Option(help="URL de la liste Awesome")] = "https://api.github.com/repos/Krypto-Hashers-Community/khc-cli/contents/README.md",
    output_dir: Annotated[Path, typer.Option(help="Répertoire de sortie")] = Path("./csv"),
    github_api_key: Annotated[str, typer.Option(envvar="GITHUB_API_KEY", help="GitHub API Key")] = None,
):
    """Exécute le pipeline ETL pour une liste Awesome."""
    from khc_cli.commands.etl import run_etl_pipeline
    
    # Extraire seulement owner/repo si une URL complète est fournie
    if "github.com" in awesome_repo_url:
        awesome_repo_path = urlparse(awesome_repo_url).path.strip("/")
    else:
        awesome_repo_path = awesome_repo_url # Déjà au format owner/repo
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    projects_csv_path = output_dir / "projects.csv"
    orgs_csv_path = output_dir / "github_organizations.csv"
    
    console.print(f"[green]Démarrage du pipeline ETL pour {awesome_repo_url}[/green]")
    console.print(f"[green]Sortie vers {projects_csv_path} et {orgs_csv_path}[/green]")
    
    run_etl_pipeline(
        awesome_repo_url=awesome_repo_url,
        awesome_readme_filename="README.md",
        local_readme_path=output_dir / ".awesome-cache.md",
        projects_csv_path=projects_csv_path,
        orgs_csv_path=orgs_csv_path,
        github_api_key=github_api_key
    )