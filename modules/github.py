import requests
import time
import os
from github import Github, GithubException

from .builder import create_readme
from .asset_handler import process_html_assets

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

def retrieve_file(task: str, path: str = "index.html"):
    try:
        github_client = Github(GITHUB_TOKEN)
        user = github_client.get_user()
        
        try:
            repo = user.get_repo(task)
        except GithubException as e:
            return None
        
        try:
            contents = repo.get_contents(path, ref="main")
            if hasattr(contents, "decoded_content"):
                decoded = contents.decoded_content.decode("utf-8")
                return decoded
            else:
                return None
        except GithubException as e:
            return None
        
    except Exception as e:
        return None

def mit_license_text():
    return """MIT License

Copyright (c) 2025 Krishaay Jois

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def update_repo(task: str, html_content: str, round_id: int):
    github_client = Github(GITHUB_TOKEN)
    user = github_client.get_user()
    owner = user.login
    repo = None
    try:
        repo = user.get_repo(task)
    except GithubException as e:
        if e.status == 404:
            try:
                repo = user.create_repo(
                    name=task,
                    description=f"TDS Builder",
                    private=False,
                    auto_init=False,
                )
                try:
                    repo.create_file(
                        path="LICENSE",
                        message="Add MIT License",
                        content=mit_license_text(),
                    )
                except GithubException:
                    pass

                try:
                    repo.create_file(
                        path="README.md",
                        message="Add README",
                        content=f"# {task}",
                    )
                except GithubException:
                    pass

            except GithubException:
                pass

    try:
        index_content = process_html_assets(html_content, repo, round_id)
    except Exception as e:
        pass


    update_pages(
        owner=owner,
        repo_name=task,
        html=index_content,
        commit_msg=f"Deploy pages",
    )

    return {
        "pages_url": f"https://{owner}.github.io/{task}/",
        "repo": repo,
    }


def update_pages(
    owner: str,
    repo_name: str,
    html: str,
    branch: str = "main",
    path: str = "index.html",
    commit_msg: str = "None"
) -> None:

    gh = Github(GITHUB_TOKEN)
    repo = gh.get_repo(f"{owner}/{repo_name}")

    contents = repo.get_contents(path, ref=branch)
    repo.update_file(
        path=path,
        message=commit_msg,
        content=html,
        sha=contents.sha,
        branch=branch,
    )
    print(f"{path} updated on {branch}")
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}/pages", headers=headers)
    
    if r.status_code == 200:
        body = {"source": {"branch": branch, "path": "/"}}
        requests.patch(f"https://api.github.com/repos/{owner}/{repo_name}/pages", headers=headers, json=body)
        requests.post(f"https://api.github.com/repos/{owner}/{repo_name}/pages/builds", headers=headers)
        time.sleep(130) 
   




def update_readme(repo, task: str, brief: str, repo_url: str, pages_url: str):
    readme_content = create_readme(task, brief, repo_url, pages_url)

    try:
        readme_file = repo.get_contents("README.md")
        repo.update_file(
            path="README.md",
            message="Update README",
            content=readme_content,
            sha=readme_file.sha,
        )
    except GithubException as e:
        if e.status == 404:
            repo.create_file(path="README.md", message="Add README", content=readme_content)