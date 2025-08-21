import os
from dotenv import load_dotenv
from github import Github, GithubException

load_dotenv()
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    raise SystemExit("GITHUB_TOKEN not set in environment (put it in a .env file)")
else: 
    print("GITHUB_TOKEN loaded successfully")

REPO_NAME = "SahilLamba0008/git-branching-with-PyGithub"
NEW_BRANCH = "gitPython-1"
MSG_LINE = "### edited though gitpython verison 1"

g = Github(TOKEN)
repo = g.get_repo(REPO_NAME)
base_branch = repo.default_branch
print(f"Repo: {REPO_NAME} (default branch: {base_branch})")

# get the commit sha of base branch
base = repo.get_branch(base_branch)
base_sha = base.commit.sha
print(f"Base branch {base_branch} commit sha: {base_sha}")

# create the branch if it doesn't exist
branch_exists = True
try:
    repo.get_branch(NEW_BRANCH)
    print(f"Branch '{NEW_BRANCH}' already exists — will update file on that branch.")
except GithubException as e:
    if e.status == 404:
        branch_exists = False
    else:
        raise

if not branch_exists:
    ref = repo.create_git_ref(ref=f"refs/heads/{NEW_BRANCH}", sha=base_sha)
    print(f"Created branch {NEW_BRANCH} from {base_branch} ({base_sha})")

# find the file on the new branch first (if created, it's the same as base)
print(f"Looking for file on branch {NEW_BRANCH}...")
content_file = None
file_path = None
try:
    content_file = repo.get_contents("readme.md", ref=NEW_BRANCH)
    file_path = "readme.md"
except GithubException as e:
    raise
print(f"File found: {content_file.path} (sha: {content_file.sha})")

# update existing file on NEW_BRANCH
orig = content_file.decoded_content.decode("utf-8")
print("Original content length:", len(orig))
print("Original content preview:", orig[:50] + "...")  # Preview first 50 characters

orig += "\n"
new_content = orig + MSG_LINE + "\n"
commit_message = f"Append line to {file_path} via script"
updated = repo.update_file(path=file_path, message=commit_message, content=new_content,
                            sha=content_file.sha, branch=NEW_BRANCH)
print("Updated file on branch:", updated["content"].path)
print("Commit sha:", updated["commit"].sha)
