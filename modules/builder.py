from typing import Dict
from openai import OpenAI
from .file_handler import process_all_attachments
import os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

def build_app(
    brief: str,
    checks: list = [],
    attachments: list = None,
    previous_code: str = None,
    round_num: int = 1,
) -> Dict[str, str]:
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    attached_files = process_all_attachments(attachments)
    checks = checks or []

    current_code = ""
    if previous_code and round_num > 1:
        current_code = f"""```html\n{previous_code}\n```\n\n"""

    prompt = f"""Generate a self contained single-page web application.
Existing Code:
{current_code}

App Brief: 
{brief}

Attachments:
{attached_files}

Evaluation Checks:
{'\n'.join([f'- {c}' for c in checks])}


General Instructions:
- Create a single HTML file with CSS and JavaScript included.
- Generated HTML should be ready to deploy to github pages as is.
- Make sure all checks and app requirements are satisfied.
- If existing code is given above, don't change any features unless new brief explicitly mentions it.


Only return the code with no explanations, comments or markdown formatting."""

    response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert web developer. Generate clean, functional, production-ready HTML applications that pass all specified checks.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
    html_content = response.choices[0].message.content

    if html_content is None:
        return ""

    if "```html" in html_content:
        html_content = html_content.replace('```html','').replace('```')

    return html_content


def create_readme(brief: str, repo_url: str, deployment_url: str) -> str:
    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    prompt = f"""Generate a README for the following:

Brief: {brief}
Source: {repo_url}
Deployment URL: {deployment_url}

Include the following:
1. Project title and brief description
2. Overview of Features
3. Setup & Running instructions
5. Implementation Information
6. License (MIT)

Use proper markdown formatting and only reply with the markdown content (no formatting except that in the file content)."""
    response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at writing professional technical documentation.",
                    },
                    {"role": "user", "content": prompt},
                ],
                
            )
    readme_content = response.choices[0].message.content
    if readme_content is None:
        return ""
    
    if "```markdown" in readme_content:
        readme_content = readme_content.replace('```markdown','').replace('```')

    return readme_content
