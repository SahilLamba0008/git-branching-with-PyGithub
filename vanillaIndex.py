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

# Config
OWNER = "SahilLamba0008"
REPO = "git-branching-with-PyGithub"
REPO_NAME = f"{OWNER}/{REPO}"
NEW_BRANCH = "gitVanilla-1"
MSG_LINE = "### edited through vanilla GitHub API version 1"
FILE_PATH = "readme.md"

# Headers for GitHub API
HEADERS = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}

# Base URL
BASE_URL = "https://api.github.com"

# --- Get repository info ---
repo_url = f"{BASE_URL}/repos/{REPO_NAME}"
repo_resp = requests.get(repo_url, headers=HEADERS)
repo_resp.raise_for_status()
repo_data = repo_resp.json()
base_branch = repo_data["default_branch"]
print(f"Repo: {REPO_NAME} (default branch: {base_branch})")

# --- Get base branch commit sha ---
branch_url = f"{BASE_URL}/repos/{REPO_NAME}/git/ref/heads/{base_branch}"
branch_resp = requests.get(branch_url, headers=HEADERS)
branch_resp.raise_for_status()
base_sha = branch_resp.json()["object"]["sha"]
print(f"Base branch {base_branch} commit sha: {base_sha}")

# --- Check if NEW_BRANCH exists ---
branch_url = f"{BASE_URL}/repos/{REPO_NAME}/git/ref/heads/{NEW_BRANCH}"
branch_exists = True
branch_resp = requests.get(branch_url, headers=HEADERS)
if branch_resp.status_code == 404:
    branch_exists = False
elif branch_resp.status_code != 200:
    branch_resp.raise_for_status()

# --- Create branch if not exists ---
if not branch_exists:
    ref_url = f"{BASE_URL}/repos/{REPO_NAME}/git/refs"
    data = {"ref": f"refs/heads/{NEW_BRANCH}", "sha": base_sha}
    ref_resp = requests.post(ref_url, headers=HEADERS, json=data)
    ref_resp.raise_for_status()
    print(f"Created branch {NEW_BRANCH} from {base_branch} ({base_sha})")
else:
    print(f"Branch '{NEW_BRANCH}' already exists — will update file on that branch.")

# --- Get file contents ---
contents_url = f"{BASE_URL}/repos/{REPO_NAME}/contents/{FILE_PATH}?ref={NEW_BRANCH}"
file_resp = requests.get(contents_url, headers=HEADERS)
file_resp.raise_for_status()
file_data = file_resp.json()
file_sha = file_data["sha"]

orig_content = base64.b64decode(file_data["content"]).decode("utf-8")
print("Original content length:", len(orig_content))
print("Original content preview:", orig_content[:50] + "...")

# --- Update file ---
new_content = orig_content + "\n" + MSG_LINE + "\n"
b64_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

update_url = f"{BASE_URL}/repos/{REPO_NAME}/contents/{FILE_PATH}"
commit_message = f"Append line to {FILE_PATH} via script"
update_data = {
    "message": commit_message,
    "content": b64_content,
    "sha": file_sha,
    "branch": NEW_BRANCH,
}

update_resp = requests.put(update_url, headers=HEADERS, json=update_data)
update_resp.raise_for_status()
update_result = update_resp.json()

print("Updated file on branch:", update_result["content"]["path"])
print("Commit sha:", update_result["commit"]["sha"])
