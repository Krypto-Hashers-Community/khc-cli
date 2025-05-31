"""Commandes de curation pour les listes Awesome."""

import typer
from rich.console import Console
from pathlib import Path
from typing_extensions import Annotated
from dotenv import load_dotenv

app = typer.Typer()
console = Console()
# Charger les variables d'environnement à partir du fichier .env
load_dotenv()

@app.command()
def validate(
    readme_path: Annotated[Path, typer.Argument(help="Chemin vers le fichier README.md à valider")],
):
    """Valide le format d'une liste Awesome."""
    from khc_cli.awesomecure.awesome2py import AwesomeList
    
    if not readme_path.exists():
        console.print(f"[red]Le fichier {readme_path} n'existe pas[/red]")
        raise typer.Exit(1)
    
    try:
        awesome_list = AwesomeList(str(readme_path))
        rubrics_count = len(awesome_list.rubrics)
        entries_count = sum(len(rubric.entries) for rubric in awesome_list.rubrics)
        
        console.print(f"[green]Liste Awesome valide ![/green]")
        console.print(f"[green]Nombre de rubriques: {rubrics_count}[/green]")
        console.print(f"[green]Nombre d'entrées: {entries_count}[/green]")
        
    except Exception as e:
        console.print(f"[red]Erreur lors de la validation: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def add_project(
    repo_url: Annotated[str, typer.Argument(help="URL du repository GitHub")],
    readme_path: Annotated[Path, typer.Option(help="Chemin vers le README.md")] = Path("README.md"),
    section: Annotated[str, typer.Option(help="Section où ajouter le projet")] = None,
    github_api_key: Annotated[str, typer.Option(envvar="GITHUB_API_KEY", help="GitHub API Key")] = None,
):
    """Ajoute un projet à une liste Awesome."""
    from urllib.parse import urlparse
    from khc_cli.github_client import GitHubClient
    
    if not readme_path.exists():
        console.print(f"[red]Le fichier {readme_path} n'existe pas[/red]")
        raise typer.Exit(1)
    
    # Vérifier que l'URL est bien une URL GitHub
    parsed_url = urlparse(repo_url)
    if parsed_url.netloc != "github.com":
        console.print("[red]Seuls les repositories GitHub sont supportés pour le moment[/red]")
        raise typer.Exit(1)
    
    repo_path = parsed_url.path.strip("/")
    
    # Récupérer les informations du repo
    github_client = GitHubClient(github_api_key)
    repo = github_client.client.get_repo(repo_path)
    
    if not repo:
        console.print(f"[red]Repository {repo_path} non trouvé[/red]")
        raise typer.Exit(1)
    
    # Construire la nouvelle entrée
    new_entry = f"* [{repo.name}]({repo_url}) - {repo.description or 'No description'}"
    
    # Lire le README
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Si une section est spécifiée, ajouter le projet à cette section
    if section:
        section_marker = f"## {section}"
        if section_marker not in content:
            console.print(f"[red]Section '{section}' non trouvée dans {readme_path}[/red]")
            raise typer.Exit(1)
        
        # Trouver la position d'insertion
        section_pos = content.find(section_marker)
        next_section_pos = content.find("##", section_pos + 1)
        if next_section_pos == -1:
            next_section_pos = len(content)
        
        # Insérer le projet à la fin de la section
        new_content = content[:next_section_pos] + new_entry + "\n\n" + content[next_section_pos:]
    else:
        # Ajouter à la fin du fichier
        new_content = content + "\n\n" + new_entry + "\n"
    
    # Écrire le nouveau contenu
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    console.print(f"[green]Projet {repo.name} ajouté avec succès à {readme_path}[/green]")