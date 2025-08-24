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

HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
BASE_URL = "https://api.github.com"


def update_file_on_branch(owner, repo, new_branch, file_path, msg_line):
    repo_name = f"{owner}/{repo}"

    # --- Get repository info ---
    repo_url = f"{BASE_URL}/repos/{repo_name}"
    repo_resp = requests.get(repo_url, headers=HEADERS)
    repo_resp.raise_for_status()
    repo_data = repo_resp.json()
    base_branch = repo_data["default_branch"]

    # --- Get base branch commit sha ---
    branch_url = f"{BASE_URL}/repos/{repo_name}/git/ref/heads/{base_branch}"
    branch_resp = requests.get(branch_url, headers=HEADERS)
    branch_resp.raise_for_status()
    base_sha = branch_resp.json()["object"]["sha"]

    # --- Check if NEW_BRANCH exists ---
    branch_url = f"{BASE_URL}/repos/{repo_name}/git/ref/heads/{new_branch}"
    branch_exists = True
    branch_resp = requests.get(branch_url, headers=HEADERS)
    if branch_resp.status_code == 404:
        branch_exists = False
    elif branch_resp.status_code != 200:
        branch_resp.raise_for_status()

    # --- Create branch if not exists ---
    if not branch_exists:
        ref_url = f"{BASE_URL}/repos/{repo_name}/git/refs"
        data = {"ref": f"refs/heads/{new_branch}", "sha": base_sha}
        ref_resp = requests.post(ref_url, headers=HEADERS, json=data)
        ref_resp.raise_for_status()

    # --- Get file contents ---
    contents_url = f"{BASE_URL}/repos/{repo_name}/contents/{file_path}?ref={new_branch}"
    file_resp = requests.get(contents_url, headers=HEADERS)
    file_resp.raise_for_status()
    file_data = file_resp.json()
    file_sha = file_data["sha"]

    orig_content = base64.b64decode(file_data["content"]).decode("utf-8")

    # --- Update file ---
    new_content = orig_content + "\n" + msg_line + "\n"
    b64_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

    update_url = f"{BASE_URL}/repos/{repo_name}/contents/{file_path}"
    commit_message = f"Append line to {file_path} via script"
    update_data = {
        "message": commit_message,
        "content": b64_content,
        "sha": file_sha,
        "branch": new_branch,
    }

    update_resp = requests.put(update_url, headers=HEADERS, json=update_data)
    update_resp.raise_for_status()
    update_result = update_resp.json()

    commit_url = update_result["commit"]["html_url"]
    print("✅ File updated on branch:", update_result["content"]["path"])
    print("✅ Commit sha:", update_result["commit"]["sha"])
    print("✅ Commit URL:", commit_url)

    return commit_url  # return commit link


def comment_on_pr_for_branch(owner, repo, branch, comment_msg):
    """
    Finds an open PR for the given branch and posts a comment.
    """
    repo_name = f"{owner}/{repo}"

    # Find PR for the branch
    prs_url = f"{BASE_URL}/repos/{repo_name}/pulls?head={owner}:{branch}&state=open"
    prs_resp = requests.get(prs_url, headers=HEADERS)
    prs_resp.raise_for_status()
    prs = prs_resp.json()

    if not prs:
        print(f"⚠️ No open PR found for branch {branch}")
        return None

    pr_number = prs[0]["number"]

    # Post comment
    comment_url = f"{BASE_URL}/repos/{repo_name}/issues/{pr_number}/comments"
    data = {"body": comment_msg}
    comment_resp = requests.post(comment_url, headers=HEADERS, json=data)
    comment_resp.raise_for_status()
    comment_data = comment_resp.json()

    print(f"💬 Comment added to PR #{pr_number}: {comment_data['html_url']}")
    return comment_data["html_url"]


# ---- Example Usage ----

commit_link = update_file_on_branch(
    owner="SahilLamba0008",
    repo="git-branching-with-PyGithub",
    new_branch="gitVanilla-1-method-comment",  # <-- branch to create/update
    file_path="readme.md",
    msg_line="### edited through vanilla GitHub API version 1",
)

comment_on_pr_for_branch(
    owner="SahilLamba0008",
    repo="git-branching-with-PyGithub",
    branch="gitVanilla-1",   # <-- PR branch name
    comment_msg=f"Automated update made here: {commit_link}",
)
