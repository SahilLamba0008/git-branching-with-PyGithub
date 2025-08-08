from github import Github

def create_branch_github(repo_name, new_branch, base_branch):
    g = Github("YOUR_GITHUB_PERSONAL_ACCESS_TOKEN")
    repo = g.get_repo(repo_name)

    # Get the commit SHA of the base branch
    base = repo.get_branch(base_branch)
    sha = base.commit.sha

    # Create new branch
    ref = f"refs/heads/{new_branch}"
    repo.create_git_ref(ref=ref, sha=sha)
    print(f"Branch '{new_branch}' created on GitHub from '{base_branch}'.")

create_branch_github("username/repo", "feature/my-new-branch", "main")