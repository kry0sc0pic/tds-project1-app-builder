from flask import Flask, request, jsonify
from modules.builder import build_app
from modules.github import update_repo, update_readme, retrieve_file
import time
import requests
import os

app = Flask(__name__)


def ping_eval_api(eval_url: str, payload: dict):
    delay = 1
    while delay <= 8:
        try:
            response = requests.post(eval_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30)

            if response.status_code == 200:
                print(f"Pinged API")
                continue
            else:
                print(
                    f"Ping Failed"
                )

        except requests.RequestException as e:
            time.sleep(delay)
            delay *= 2

    print("Eval API is down")


def validate_request(data):
    return data.get("secret", "") == os.environ.get('SECRET')


@app.route("/api-endpoint", methods=["POST"])
def handle_build_request():
    data = None

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error"}), 400

        if not validate_request(data):
            return jsonify({"status": "error"}), 403

        email = data.get("email", "")
        task = data.get("task", "")
        round_id = data.get("round", 1)
        nonce = data.get("nonce", "")
        brief = data.get("brief", "")
        checks = data.get("checks", [])
        evaluation_url = data.get("evaluation_url", "")
        attachments = data.get("attachments", [])

        print(f"Processing request for ask: {task}, round: {round_id}")


        if round_id > 1:
            prev_code = retrieve_file(task)
        else:
            prev_code = ""
       
        html_content = build_app(brief, checks, attachments, prev_code, round_id)
    
        repo = update_repo(task, {'index.html': html_content}, round_id)
        update_readme(
            repo["repo"],
            task,
            brief,
            repo["repo"].html_url,
            repo["pages_url"],
        )
        
        commits = repo["repo"].get_commits()
        commit_hash = commits[0].sha

        eval_data = {
            "email": email,
            "task": task,
            "round": round_id,
            "nonce": nonce,
            "repo_url": repo["repo_url"],
            "commit_sha": commit_hash,
            "pages_url": repo["pages_url"],
        }

    
        ping_eval_api(evaluation_url, eval_data)
 
        return jsonify({"status": "done"}), 200

    except Exception as e:
        return jsonify({"status": "error"}), 500


@app.route("/", methods=["GET"])
def ping():
    return jsonify({"ping": "pong"}), 200


def main():
    app.run(host="0.0.0.0", port=os.environ.get("PORT", 8000), debug=True)


if __name__ == "__main__":
    main()
