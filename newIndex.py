import os 
import base64
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise SystemExit("GITHUB_TOKEN not set in environment (put it in a .env file)")
else:
    print("GITHUB_TOKEN loaded successfully")

class GitHubRepo:
    HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    BASE_URL = "https://api.github.com"

    def __init__(self, owner, repo):
        self.owner = owner
        self.repo = repo
        self.repo_name = f"{owner}/{repo}"
    
    def get_base_branch(self):
        repo_url = f"{self.BASE_URL}/repos/{self.repo_name}"
        repo_resp = requests.get(repo_url, headers=self.HEADERS)
        repo_resp.raise_for_status()
        repo_data = repo_resp.json()
        print(f"Default branch : '{repo_data['default_branch']}'")
        return repo_data["default_branch"]

    def create_new_branch_with_updated_file(self, new_branch, file_path, msg_line):
        # --- Get base branch commit sha ---
        base_branch = self.get_base_branch()
        branch_url = f"{self.BASE_URL}/repos/{self.repo_name}/git/ref/heads/{base_branch}"
        branch_resp = requests.get(branch_url, headers=self.HEADERS)
        branch_resp.raise_for_status()
        print(f"Base branch sha: {branch_resp.json()['object']['sha']}")
        base_sha = branch_resp.json()["object"]["sha"]

        # --- Check if NEW_BRANCH exists ---
        branch_url = f"{self.BASE_URL}/repos/{self.repo_name}/git/ref/heads/{new_branch}"
        branch_exists = True
        branch_resp = requests.get(branch_url, headers=self.HEADERS)
        if branch_resp.status_code == 404:
            branch_exists = False
        elif branch_resp.status_code != 200:
            branch_resp.raise_for_status()

        source_branch = ""
        if not branch_exists:
            # --- Create NEW_BRANCH from base_branch ---
            file_url = f"{self.BASE_URL}/repos/{self.repo_name}/contents/{file_path}?ref={base_branch}" # to get file from base branch
            data = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
            create_branch_url = f"{self.BASE_URL}/repos/{self.repo_name}/git/refs"
            create_branch_resp = requests.post(create_branch_url, headers=self.HEADERS, json=data)
            create_branch_resp.raise_for_status()
            source_branch = base_branch
            print(f"✅ Branch '{new_branch}' created from '{base_branch}'")
        else:
           print(f"⚠️ Branch '{new_branch}' already exists, updating file directly...")
           source_branch = new_branch

        file_url = f"{self.BASE_URL}/repos/{self.repo_name}/contents/{file_path}?ref={source_branch}"
        file_resp = requests.get(file_url, headers=self.HEADERS)
        file_resp.raise_for_status()
        file_data = file_resp.json()
        file_sha = file_data["sha"]
        file_content = base64.b64decode(file_data["content"]).decode("utf-8")

        # --- Update file content ---
        updated_content = file_content + "\n" + msg_line
        encoded_content = base64.b64encode(updated_content.encode("utf-8")).decode("utf-8")

        # --- Commit updated file to NEW_BRANCH ---
        commit_msg = f"Update {file_path} with a new line"
        update_data = {
            "message": commit_msg,
            "content": encoded_content,
            "sha": file_sha,
            "branch": new_branch,
        }
        update_file_url = f"{self.BASE_URL}/repos/{self.repo_name}/contents/{file_path}"
        update_resp = requests.put(update_file_url, headers=self.HEADERS, json=update_data)
        update_resp.raise_for_status()
        if update_resp.status_code == 200 or update_resp.status_code == 201:
            print(f"✅ File '{file_path}' updated on branch '{new_branch}'")
        else:
            print(f"⚠️ Unexpected status code {update_resp.status_code} when updating file.")


    def create_pull_request(self, new_branch, base_branch, title, body=""):
        pr_url = f"{self.BASE_URL}/repos/{self.repo_name}/pulls"
        data = {
            "title": title,         # PR title
            "head": new_branch,     # branch with your changes
            "base": base_branch,    # where you want to merge the PR
            "body": body,           # optional PR description
        }

        pr_resp = requests.post(pr_url, headers=self.HEADERS, json=data)
        if pr_resp.status_code == 422:
            # This happens if a PR for the same branch already exists
            print(f"⚠️ A PR for branch '{new_branch}' already exists.")
            existing_prs_url = f"{self.BASE_URL}/repos/{self.repo_name}/pulls?head={self.owner}:{new_branch}&state=open"
            prs_resp = requests.get(existing_prs_url, headers=self.HEADERS)
            prs_resp.raise_for_status()
            prs = prs_resp.json()

            if prs:
                pr_url = prs[0]["html_url"]
                pr_number = prs[0]["number"]
                print(f"🔄 Found existing PR #{pr_number}: {pr_url}")
                return pr_url
            else:
                print(f"⚠️ No open PRs found for branch '{new_branch}', but 422 was returned. Something inconsistent.")
                return None
            
        pr_resp.raise_for_status()
        pr_data = pr_resp.json()
        pr_url = pr_data["html_url"]
        pr_number = pr_data["number"]
        print(f"🔄 created new PR #{pr_number}: {pr_url}")
        return pr_url

    def comment_on_pr(self, pr_url_to_comment, comment_body):
        pr_number = pr_url_to_comment.split("/")[-1]
        comment_url = f"{self.BASE_URL}/repos/{self.repo_name}/issues/{pr_number}/comments"
        data = {"body": comment_body}
        comment_resp = requests.post(comment_url, headers=self.HEADERS, json=data)
        comment_resp.raise_for_status()
        comment_data = comment_resp.json()
        print(f"💬 Comment added to PR #{pr_number}")
        return comment_data["html_url"]

repo = GitHubRepo("Sahillamba0008", "git-branching-with-PyGithub")
base_branch = repo.get_base_branch()

# --- create new branch with updated file ---
new_branch = "feature/add-line-to-index"
file_path = "readme.md"
msg_line = "This is a new line added to the file."
repo.create_new_branch_with_updated_file(new_branch, file_path, msg_line)

# --- create a PR, from the new branch created with updated file ---
pr_title = "Add a new line to readme.md"
pr_desc = "This PR adds a new line to the readme.md file."
pr_url = repo.create_pull_request(new_branch, base_branch, pr_title, pr_desc)

# --- create a new Fix branch with updated file ---
fix_new_branch = "fix/add-line-to-index-fix"
fix_file_path = "readme.md"
fix_msg_line = "This is a fix line added to the file."
repo.create_new_branch_with_updated_file(fix_new_branch, fix_file_path, fix_msg_line)

# --- create a PR, from the new Fix branch created with updated file ---
fix_pr_title = "Fix: Add a new line to readme.md"
fix_pr_desc = "This PR adds a new fix line to the readme.md file."
fix_pr_url = repo.create_pull_request(fix_new_branch, base_branch, pr_title, pr_desc)

# --- comment fix PR link on the feature PR ---
repo.comment_on_pr(pr_url, f"Fix PR created: {fix_pr_url}")