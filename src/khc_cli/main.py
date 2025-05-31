"""Point d'entrée principal de la CLI khc."""

import typer
from rich.console import Console
from rich.table import Table
import logging
from typing_extensions import Annotated

from khc_cli.github_client import GitHubClient
from khc_cli.commands import analyze, curate
from dotenv import load_dotenv

# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

# Initialisation de l'application Typer
app = typer.Typer(
    name="khc-cli",
    help="CLI tool for curating and analyzing Awesome lists, focusing on Open Sustainable Technology.",
    rich_help_panel=True
)

# Console Rich pour des affichages améliorés
console = Console()

# Ajouter les sous-commandes
app.add_typer(analyze.app, name="analyze", help="Analyze awesome lists and repositories")
app.add_typer(curate.app, name="curate", help="Curate awesome lists")

@app.command()
def status(
    github_api_key: Annotated[str, typer.Option(envvar="GITHUB_API_KEY", help="GitHub API Key")] = None,
):
    """Vérifier le statut de l'API GitHub."""
    try:
        github_client = GitHubClient(github_api_key)
        rate_limit = github_client.get_rate_limit()
        
        table = Table(title="GitHub API Status")
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="green")
        
        table.add_row("Requêtes restantes", str(rate_limit["remaining"]))
        table.add_row("Limite totale", str(rate_limit["total"]))
        table.add_row("Reset à", str(rate_limit["reset_time"]))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Erreur: {e}[/red]")
        raise typer.Exit(1)

@app.callback()
def main():
    """
    KHC CLI - Outil pour analyser et organiser les listes Awesome
    axées sur les technologies durables et open source.
    """
    pass

def run(prog_name="khc-cli"):
    """Fonction de point d'entrée pour exécuter l'application."""
    app(prog_name=prog_name)

if __name__ == "__main__":
    run()