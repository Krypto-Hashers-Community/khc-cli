"""Open Sustain Tech - OSS Option"""

import os
import logging
import requests
from bs4 import BeautifulSoup
import re
import time
import csv
import base64
import urllib
import traceback
from datetime import datetime, timedelta
from github import Github, StatsContributor
from urllib.parse import urlparse
from os import getenv
from dotenv import load_dotenv
from termcolor import colored
import yaml

import click
import typer
from rich import print
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.traceback import install as install_rich_traceback
from typing_extensions import Annotated
from pathlib import Path

from khc_cli.awesomecure import awesome2py
from khc_cli.awesomecure.awesome2py import AwesomeList

LOGGER = logging.getLogger(__name__)
app = typer.Typer()
install_rich_traceback()
load_dotenv()

def countdown(t):
        while t:
            mins, secs = divmod(int(t), 60)
            timeformat = "{:02d}:{:02d}".format(mins, secs)
            print(timeformat, end="\r")
            time.sleep(1)
            t -= 1
        print("\n\n\n\n\n")

class AwesomeOSSOption(AwesomeList):
    # This class is largely unused in the new structure or its methods become standalone functions.
    # crawl_dependents will become a standalone function.
    pass
def crawl_github_dependents(repo, page_num):
        url = 'https://github.com/{}/network/dependents'.format(repo)
        dependents_data = []
        list_end = False
        
        for i in range(page_num):
            #print("GET " + url)
            r = requests.get(url)
            soup = BeautifulSoup(r.content, "html.parser")

            page_data = [
                "{}/{}".format(
                    t.find('a', {"data-repository-hovercards-enabled":""}).text,
                    t.find('a', {"data-hovercard-type":"repository"}).text
                )
                for t in soup.findAll("div", {"class": "Box-row"})
            ]
            
            for dependent in page_data:
                if dependent in dependents_data:
                    list_end = True 
            
            if list_end:
                break
            else:    
                dependents_data = dependents_data + page_data
            
            try:
                paginationContainer = soup.find("div", {"class":"paginate-container"}).find_all('a')
            except:
                break
            
            try:
                if len(paginationContainer) > 1:
                    paginationContainer = paginationContainer[1]
                else:
                    paginationContainer = paginationContainer[0]
            except:
                break
            
            if paginationContainer:
                url = paginationContainer["href"]
            else:
                break
            
        return dependents_data

def fetch_awesome_readme_content(g: Github, awesome_repo_path: str, readme_filename: str, local_readme_path: Path):
    awesome_url = "https://github.com/Krypto-Hashers-Community/khc-cli"
    awesome_path = urlparse(awesome_url).path.strip("/")
    filename = "README.md"
    
    awesome_repo = g.get_repo(awesome_path)
    awesome_content_encoded = awesome_repo.get_contents(
        urllib.parse.quote(filename)
    ).content
    awesome_content = base64.b64decode(awesome_content_encoded)
    
    with open(local_readme_path, "w", encoding="utf-8") as filehandle:
        filehandle.write(awesome_content.decode("utf-8"))
    LOGGER.info(f"Awesome README saved to {local_readme_path}")
    return awesome2py.AwesomeList(str(local_readme_path))


def initialize_csv_writers(projects_csv_path: Path, orgs_csv_path: Path):
    projects_csv_path.parent.mkdir(parents=True, exist_ok=True)
    orgs_csv_path.parent.mkdir(parents=True, exist_ok=True)

    csv_fieldnames = [
        "project_name",
        "oneliner",
        "git_namespace",
        "git_url",
        "platform",
        "topics",
        "rubric",
        "last_commit_date",
        "stargazers_count",
        "number_of_dependents",
        "stars_last_year",
        "project_active",
        "dominating_language",
        "organization",
        "organization_user_name",
        "languages",
        "homepage",
        "readme_content",
        "refs",
        "project_created",
        "project_age_in_days",
        "license",
        "total_commits_last_year",
        "total_number_of_commits",
        "last_issue_closed",
        "open_issues",
        "closed_pullrequests",
        "closed_issues",
        "issues_closed_last_year",
        "days_until_last_issue_closed",
        "open_pullrequests",
        "reviews_per_pr",
        "development_distribution_score",
        "last_released_date",
        "last_release_tag_name",
        "good_first_issue",
        "contributors",
        "accepts_donations",
        "donation_platforms",
        "code_of_conduct",
        "contribution_guide",
        "dependents_repos",
        "organization_name",
        "organization_github_url",
        "organization_website",
        "organization_location",
        "organization_country",
        "organization_form",
        "organization_avatar",
        "organization_public_repos",
        "organization_created",
        "organization_last_update",
    ]

    csv_github_organizations_fieldnames = [
        "organization_name",
        "organization_user_name",
        "organization_github_url",
        "organization_website",
        "organization_location",
        "organization_country",
        "organization_form",
        "organization_avatar",
        "organization_public_repos",
        "organization_created",
        "organization_last_update",
        "organization_rubric"
    ]

    csv_projects_file = open(projects_csv_path, "w", newline="", encoding="utf-8")
    writer_projects = csv.DictWriter(csv_projects_file, fieldnames=csv_fieldnames)
    writer_projects.writeheader()

    existing_orgs = set()
    if orgs_csv_path.exists():
        with open(orgs_csv_path, "r", newline="", encoding="utf-8") as f_org_read:
            reader_github_organizations = csv.DictReader(f_org_read)
            for entry in reader_github_organizations:
                if 'organization_user_name' in entry:
                    existing_orgs.add(entry['organization_user_name'])

    csv_orgs_file = open(orgs_csv_path, "a", newline="", encoding="utf-8")
    writer_github_organizations = csv.DictWriter(csv_orgs_file, fieldnames=csv_github_organizations_fieldnames)
    # Write header only if file is new/empty
    if orgs_csv_path.stat().st_size == 0:
         writer_github_organizations.writeheader()

    return writer_projects, writer_github_organizations, existing_orgs, csv_projects_file, csv_orgs_file

def handle_github_rate_limiting(g: Github, min_requests_remaining: int = 100):
    remaining, limit = g.rate_limiting
    reset_time = g.rate_limiting_resettime
    LOGGER.info(f"GitHub API Rate Limit: {remaining}/{limit} requests remaining. Resets at {datetime.fromtimestamp(reset_time)}.")
    if remaining < min_requests_remaining:
        wait_time = max(0, (reset_time - datetime.now().timestamp()) + 5) # Add 5s buffer
        LOGGER.warning(f"Approaching GitHub rate limit. Waiting for {wait_time:.0f} seconds...")
        print(f"Waiting for {wait_time:.0f} seconds for GitHub API rate limit to reset...")
        countdown(wait_time)

def run_etl_pipeline(
    g: Github,
    awesome_repo_data: AwesomeList,
    writer_projects: csv.DictWriter,
    writer_github_organizations: csv.DictWriter,
    existing_organizations: set
):
    retry = False
    failures = []
    total_entries = sum(len(rubric.entries) for rubric in awesome_repo_data.rubrics)

    progress_columns = [
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        TimeElapsedColumn(),
    ]

    with Progress(*progress_columns, transient=False) as progress_bar:
        task = progress_bar.add_task("Processing projects...", total=total_entries)
        for r_idx, r in enumerate(awesome_repo_data.rubrics):
            for entry_idx, entry in enumerate(r.entries):
                progress_bar.update(task, advance=1, description=f"Processing: {entry.name[:30]}...")
                LOGGER.info(f"Processing project: {entry.name} ({entry.url}) from rubric: {r.key}")
            print("------------------------")
            print("Processing: %s" % entry.name)
            print("URL: %s" % entry.url)
            if urlparse(entry.url).netloc == "github.com":
                print("%s is a GitHub project" % entry.name)
                while True:
                    try:
                        handle_github_rate_limiting(g, min_requests_remaining=50)

                        # Gather project information from GitHub
                        # https://pygithub.readthedocs.io/en/latest/github_objects/Repository.html
                        repo_path = urlparse(entry.url).path.strip("/")
                        platform = "github"
                        user, project_name = os.path.split(repo_path)
                        repo = g.get_repo(repo_path)
                        contents_root = repo.get_contents("")
                        releases = repo.get_releases()
                        commits = repo.get_commits()
                        stargazers = repo.get_stargazers_with_dates()

                        # Crawel dependents
                        try:
                            dependents_repos = crawl_github_dependents(repo_path,20) # Ensure crawl_github_dependents is defined

                        except Exception as e:
                            print("Dependents not available:")
                            print(e)
                            dependents_repo = []


                        number_of_dependents = len(dependents_repos)
                        dependents_repos = ",".join(dependents_repos)

                        closed_issues = repo.get_issues(state="closed")
                        open_issues = repo.get_issues(state="open")

                        closed_pullrequests = repo.get_pulls(state="closed")
                        open_pullrequests = repo.get_pulls(state="open")


                        closed_prs = closed_pullrequests.totalCount
                        open_prs = open_pullrequests.totalCount

                        if closed_prs > 10:
                            pr_review_analyse = 10
                        else:
                            pr_review_analyse = closed_prs



                        total_reviews = 0     
                        for pull_request in closed_pullrequests[0:pr_review_analyse-1]:
                            pr_reviews = pull_request.get_reviews()
                            total_reviews = total_reviews + pr_reviews.totalCount
                        try:
                            reviews_per_pr = total_reviews/pr_review_analyse 
                        except:                   
                            reviews_per_pr = 0


                        if closed_issues.totalCount > 0:
                            last_issue_closed = closed_issues[0].updated_at
                            days_since_last_issue_closed = (datetime.now() - last_issue_closed).days


                        inactivity_time_delta = datetime.now() - timedelta(days=365)
                        issues_closed_time_delta = repo.get_issues(state="closed", since=inactivity_time_delta, sort="closed-desc")                

                        commits_time_delta = repo.get_commits(since=inactivity_time_delta)
                        last_commit_date = datetime.strptime(commits[0].last_modified, '%a, %d %b %Y %H:%M:%S GMT')


                        if (
                            issues_closed_time_delta.totalCount == 0
                            and commits_time_delta.totalCount == 0
                            or repo.archived
                        ):
                            print("%s is an inactive project" % entry.name)
                            project_active = "false"
                        else:
                            print("%s is an active project" % entry.name)
                            project_active = "true"



                        try:
                            license = repo.get_license()
                            if license.license.spdx_id == "NOASSERTION":
                                print("Custom license found")
                                license_name = "CUSTOM"
                            else:
                                license_name = license.license.spdx_id
                        except:
                            print("No license information found")
                            license_name = "UNDEFINED"

                        labels = ",".join([entry.name for entry in repo.get_labels()])
                        topics = ",".join(repo.get_topics())

                        languages_states = repo.get_languages()
                        programming_languages = ",".join(languages_states.keys())

                        try:
                            dominating_language = list(languages_states.keys())[0]

                        except:
                            dominating_language = ""
                            
                        try:
                            print("Search for references")
                            #https://stackoverflow.com/questions/27910/finding-a-doi-in-a-document-or-page
                            # some DOIs only visible in badge image
                            refs = ""
                            readme_file = repo.get_readme()
                            readme_content = base64.b64decode(readme_file.content)
                            WEB_URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""
                            matches = re.findall(WEB_URL_REGEX, str(readme_content))
                            for match in matches:
                                if urlparse(match).netloc == "doi.org" and match.find("svg") == -1:
                                    print("Found DOI URL:")
                                    print(match)
                                    refs= ','.join([refs, match])
                                if urlparse(match).netloc == "zenodo.org" and match.find("svg") == -1:
                                    print("Found Zenodo URL:")
                                    print(match)
                                    refs=','.join([refs, match])
                                if urlparse(match).netloc == "theoj.org" and match.find("svg") == -1:
                                    print("Found JOSS URL:")
                                    print(match)
                                    refs = ','.join([refs, match]) 
                                if urlparse(match).netloc == "arxiv.org" and match.find("svg") == -1:
                                    print("Found Arxiv URL:")
                                    print(match)
                                    refs = ','.join([refs, match]) 
                        except Exception as e:
                            print("No reference found")
                            print(e)

                        try:
                            print("Search for project logos")
                            PNG_PATH_REGEX = r"""[a-zA-Z0-9.]*\/.*?\.[\w:]+"""
                            matches = re.findall(PNG_PATH_REGEX, str(readme_content))
                            for match in matches:
                                if match.find(".png") > 0:
                                    pass

                        except Exception as e:
                            print("No image URLs found")
                            print(e)
                            

                        try:
                            dotfolder_file = repo.get_contents(".github")
                            for file in dotfolder_file:
                                if file.path == ".github/FUNDING.yml":
                                    print("Funding file found")
                                    funding_file = base64.b64decode(file.content)
                                    donation_platforms = ",".join(yaml.safe_load(funding_file))
                                    accepts_donations = "true"
                                    break
                                else:
                                    donation_platforms = None
                                    accepts_donations = "false"

                        except:
                            print("No funding information found")
                            donation_platforms = None
                            accepts_donations = "false"

                        try:
                            code_of_conduct = "false"
                            contribution_guide = "false"
                            for file_content in contents_root:
                                if file_content.path.lower().find("code_of_conduct") != -1:
                                    print("Code of conduct found")
                                    code_of_conduct = "true"
                                if file_content.path.lower().find("contributing") != -1:
                                    print("Contribution guide found")
                                    contribution_guide = "true"

                            for file_content in dotfolder_file:
                                if file_content.path.lower().find("code_of_conduct") != -1:
                                    print("Code of conduct found")
                                    code_of_conduct = "true"
                                if file_content.path.lower().find("contributing") != -1:
                                    print("Contribution guide found")
                                    contribution_guide = "true"

                        except Exception as e:
                            print(e)

                        contributors = repo.get_stats_contributors()
                        contributor_activity = {}
                        commits_total = 0
                        for individuum in contributors:
                            contributor_activity[individuum.author.login] = individuum.total
                            commits_total = commits_total + individuum.total

                        sorted_contributor = dict(
                            sorted(contributor_activity.items(), key=lambda item: item[1])
                        )
                        weighted_contribution = {
                            k: v / commits_total for k, v in sorted_contributor.items()
                        }

                        # Create a simple community health score that shows how much the project is focused on one developer
                        development_distribution_score = 1 - max(
                            weighted_contribution.values()
                        )

                        try:
                            last_released_date = releases[0].published_at.strftime(
                                "%Y/%m/%d, %H:%M:%S"
                            )
                            last_release_tag_name = releases[0].tag_name

                        except Exception as e:
                            print("No Release found")
                            last_released_date = ""
                            last_release_tag_name = ""
                            print(e)

                        total_number_of_commits = commits.totalCount

                        stars_last_year = 0
                        for star in stargazers:
                            starred_delta = datetime.utcnow() - star.starred_at
                            if  starred_delta < timedelta(days=365):
                                stars_last_year = stars_last_year + 1

                        # Gathering organization data
                        if repo.organization is None:
                            print("No Organization found. Project in user namespace.")
                            organization_user_name = None
                            organization_name = None
                            organization_avatar = None
                            organization_location = None
                            organization_github_url = None
                            organization_website = None
                            organization_created = None
                            organization_repos = None     
                            organization_last_update = None # Corrected typo

                        elif repo.organization.login not in existing_organizations:
                            print("Organization not in list. Gathering data.")
                            organization_user_name = repo.organization.login
                            organization_name = repo.organization.name
                            organization_avatar = repo.organization.avatar_url
                            organization_location = repo.organization.location
                            organization_github_url = repo.organization.html_url
                            organization_website = repo.organization.blog
                            organization_created = repo.organization.created_at.strftime("%Y/%m/%d, %H:%M:%S")
                            organization_repos = g.search_repositories(query='user:'+organization_user_name, sort='updated')     
                            organization_last_update = organization_repos[0].updated_at.strftime("%Y/%m/%d, %H:%M:%S")


                            organization_data = {
                                "organization_name": organization_name,
                                "organization_user_name":organization_user_name,
                                "organization_github_url":organization_github_url,
                                "organization_website":organization_website,
                                "organization_avatar": organization_avatar,
                                "organization_location": organization_location,
                                "organization_country": "",
                                "organization_form": "",
                                "organization_public_repos": organization_repos.totalCount,
                                "organization_created": organization_created,
                                "organization_last_update": organization_last_update,
                                "organization_rubric": r.key
                            }

                            existing_organizations.add(organization_user_name)
                            print("Organization Data:")
                            print(organization_data)
                            writer_github_organizations.writerow(organization_data)

                        else:
                            organization_user_name = repo.organization.login
                            organization_name = repo.organization.name
                            organization_avatar = repo.organization.avatar_url
                            organization_location = repo.organization.location
                            organization_github_url = repo.organization.html_url
                            organization_website = repo.organization.blog                    

                        project_data = {
                            "project_name": entry.name,
                            "git_namespace": user,
                            "git_url": repo.clone_url,
                            "rubric": r.key,
                            "oneliner": entry.text[2:],
                            "topics": topics,
                            "organization": organization_name,
                            "organization_user_name": organization_user_name,
                            "project_created": repo.created_at.strftime("%Y/%m/%d, %H:%M:%S"),
                            "project_age_in_days": (datetime.now() - repo.created_at).days,
                            "last_commit_date": last_commit_date.strftime("%Y/%m/%d, %H:%M:%S"),
                            "project_active": project_active,
                            "last_issue_closed": last_issue_closed.strftime(
                                "%Y/%m/%d, %H:%M:%S"
                            ),
                            "last_released_date": last_released_date,
                            "last_release_tag_name": last_release_tag_name,
                            "total_number_of_commits": total_number_of_commits,
                            "total_commits_last_year": commits_time_delta.totalCount,
                            "development_distribution_score": development_distribution_score,
                            "stargazers_count": repo.stargazers_count,
                            "number_of_dependents": number_of_dependents,
                            "dependents_repos": dependents_repos,
                            "stars_last_year": stars_last_year,
                            "dominating_language": dominating_language,
                            "languages": programming_languages,
                            "homepage": repo.homepage,
                            "refs": refs,
                            "closed_issues": closed_issues.totalCount,
                            "issues_closed_last_year": issues_closed_time_delta.totalCount,
                            "days_until_last_issue_closed": days_since_last_issue_closed,
                            "open_issues": open_issues.totalCount,
                            "closed_pullrequests": closed_prs,
                            "open_pullrequests": open_prs,
                            "reviews_per_pr": reviews_per_pr,
                            "good_first_issue": repo.get_issues(state="open", labels=["good first issue"]).totalCount,
                            "license": license_name,
                            "contributors": repo.get_contributors().totalCount,
                            "accepts_donations": accepts_donations,
                            "donation_platforms": donation_platforms,
                            "code_of_conduct": code_of_conduct,
                            "contribution_guide": contribution_guide,
                            "organization_avatar":organization_avatar,
                            "platform":platform,
                            "organization_github_url":organization_github_url,
                            "organization_website":organization_website,
                            "organization_avatar": organization_avatar,
                            "organization_location": organization_location,
                            "readme_content": readme_content,
                        }



                        print("Project Data:")
                        print(project_data)
                        writer_projects.writerow(project_data)
                        break

                    except Exception as e:
                        print(colored("Failed to gather project information:"))
                        print(colored(e, "red"))
                        print(traceback.format_exc())
                        
                        if retry == False:
                            print(colored("Now try it one more time"))
                            retry = True
                            continue
                        else:
                            retry = False
                            print(colored("Last try. Now Quit"))
                            failures.append(entry.url)
                            break

            elif urlparse(entry.url).netloc == "gitlab.com":
                print("%s is a Gitlab project" % entry.name)
                repo_path = urlparse(entry.url).path.strip("/")
                user, project_name = os.path.split(repo_path)
                platform = "gitlab"

                project_data = {
                    "project_name": entry.name,
                    "git_namespace": user,
                    "git_url": entry.url,
                    "rubric": r.key,
                    "oneliner": entry.text[2:],
                    "platform":platform
                }
                print("Project Data:")
                print(project_data)
                writer_projects.writerow(project_data)

            else:
                print("%s is hosted on custom platform" % entry.name)
                repo_path = urlparse(entry.url).path.strip("/")
                user, project_name = os.path.split(repo_path)
                platform = "custom"

                project_data = {
                    "project_name": entry.name,
                    "git_namespace": user,
                    "homepage": entry.url,
                    "rubric": r.key,
                    "oneliner": entry.text[2:],
                    "platform":platform
                }

                print("Project Data:")
                print(project_data)
                writer_projects.writerow(project_data)

    return failures

@app.command()
def main(
    awesome_repo_url: Annotated[str, typer.Option(help="URL of the Awesome list GitHub repository.")] = "https://github.com/protontypes/open-sustainable-technology",
    awesome_readme_filename: Annotated[str, typer.Option(help="Filename of the README in the Awesome list repository.")] = "README.md",
    local_readme_path: Annotated[Path, typer.Option(help="Local path to save/read the Awesome README.", dir_okay=False, writable=True)] = Path("./.awesome-cache.md"),
    projects_csv_path: Annotated[Path, typer.Option(help="Output path for the projects CSV file.", dir_okay=False, writable=True)] = Path("./csv/projects.csv"),
    orgs_csv_path: Annotated[Path, typer.Option(help="Output path for the GitHub organizations CSV file.", dir_okay=False, writable=True)] = Path("./csv/github_organizations.csv"),
    github_api_key: Annotated[str, typer.Option(envvar="GITHUB_API_KEY", help="GitHub API Key. Can also be set via GITHUB_API_KEY environment variable.")] = None,
):
    """
    ETL pipeline to analyze an Awesome list, collect project data (especially from GitHub),
    and save it to CSV files.
    """
    if not github_api_key:
        print(colored("Error: GitHub API Key is required. Set GITHUB_API_KEY environment variable or use --github-api-key option.", "red"))
        raise typer.Exit(code=1)

    print(f"Starting ETL pipeline for Awesome list: {awesome_repo_url}")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Setup ---
    g = Github(github_api_key)
    awesome_repo_path_in_url = urlparse(awesome_repo_url).path.strip("/")

    # --- Extract Phase ---
    print("Step 1: Fetching and parsing Awesome list README...")
    try:
        awesome_repo_data = fetch_awesome_readme_content(g, awesome_repo_path_in_url, awesome_readme_filename, local_readme_path)
    except Exception as e:
        print(colored(f"Error fetching or parsing Awesome README: {e}", "red"))
        LOGGER.error(f"Error fetching or parsing Awesome README: {e}", exc_info=True)
        raise typer.Exit(code=1)
    print(f"Found {sum(len(r.entries) for r in awesome_repo_data.rubrics)} projects in {len(awesome_repo_data.rubrics)} rubrics.")

    # --- Initialize Load Phase (Writers) ---
    print(f"Step 2: Initializing CSV output files (Projects: {projects_csv_path}, Orgs: {orgs_csv_path})...")
    try:
        writer_projects, writer_github_organizations, existing_orgs, csv_projects_file, csv_orgs_file = initialize_csv_writers(projects_csv_path, orgs_csv_path)
    except Exception as e:
        print(colored(f"Error initializing CSV writers: {e}", "red"))
        LOGGER.error(f"Error initializing CSV writers: {e}", exc_info=True)
        raise typer.Exit(code=1)

    # --- Transform and Load per project (Core ETL loop) ---
    print("Step 3: Processing individual projects...")
    failures = run_etl_pipeline(g, awesome_repo_data, writer_projects, writer_github_organizations, existing_orgs)

    # --- Finalize Load Phase ---
    csv_projects_file.close()
    csv_orgs_file.close()

    print("------------------------")
    print(colored("ETL Processing finished.", "green"))
    if failures:
        print(colored(f"Failed to process {len(failures)} projects:", "yellow"))
        for failed_url in failures:
            print(f"  - {failed_url}")
    else:
        print(colored("All projects processed successfully.", "green"))

if __name__ == "__main__":
    typer.run(app)