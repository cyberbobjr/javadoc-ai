import datetime
import os
from typing import List

import requests
from git import GitCommandError, Repo

from .config import GitConfig


class GitManager:
    def __init__(self, config: GitConfig, repo_path: str = "."):
        self.config = config
        self.repo_path = repo_path
        self.repo = self._init_repo()
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration, specifically for GitLab."""
        if self.config.provider.lower() == "gitlab":
            if not self.config.project_id:
                raise ValueError("GitLab provider requires 'project_id' to be set in config.yaml.")
            
            # Verify project_id existence via API
            print(f"Validating GitLab project ID: {self.config.project_id}...")
            
            if self.config.api_url:
                api_url = self.config.api_url
            else:
                 # Auto-detect from repo_url
                 from urllib.parse import urlparse
                 parsed = urlparse(self.config.repo_url)
                 api_url = f"{parsed.scheme}://{parsed.netloc}/api/v4"

            url = f"{api_url}/projects/{self.config.project_id}"
            headers = {"PRIVATE-TOKEN": self.config.token.get_secret_value()}
            
            try:
                # Use HEAD or GET just to check existence. GET is safer for info.
                response = requests.get(url, headers=headers, verify=self.config.ssl_verify)
                if response.status_code == 404:
                     raise ValueError(f"GitLab project ID '{self.config.project_id}' not found (404). Check your configuration.")
                elif response.status_code == 401:
                     raise PermissionError(f"Unauthorized (401) accessing GitLab project '{self.config.project_id}'. Check your token.")
                response.raise_for_status()
                print("GitLab project ID validated successfully.")
            except requests.RequestException as e:
                # If we can't reach the server or other error
                raise ConnectionError(f"Failed to validate GitLab project ID: {e}")


    def _init_repo(self) -> Repo:
        """Initialize GitPython Repo object."""
        # Configure Git environment for SSL if necessary, before any git operation
        if isinstance(self.config.ssl_verify, str):
             os.environ["GIT_SSL_CAINFO"] = self.config.ssl_verify
        elif self.config.ssl_verify is False:
             os.environ["GIT_SSL_NO_VERIFY"] = "true"

        try:
            return Repo(self.repo_path)
        except (GitCommandError, Exception) as e:
            # Check if directory exists and is empty (or we are allowed to clone into it)
            # If so, clone the repo
            if os.path.exists(self.repo_path) and not os.listdir(self.repo_path) and self.config.repo_url:
                 # It's an empty directory, safe to clone
                 pass
            elif not os.path.exists(self.repo_path) and self.config.repo_url:
                 # Directory doesn't exist, will be created by clone
                 pass
            else:
                # Directory exists and is not empty, and not a git repo
                # OR no repo_url. Re-raise exception.
                # Use a specific message error to help debugging
                if os.path.exists(self.repo_path) and os.listdir(self.repo_path):
                     raise Exception(f"Directory {self.repo_path} exists, is not empty, and is not a git repository.") from e
                
                # If we are here, we probably failed to init a generic path without URL, or obscure error
                raise e

            print(f"Cloning {self.config.repo_url} to {self.repo_path}...")
            return Repo.clone_from(self.config.repo_url, self.repo_path)

    def pull_prod(self) -> None:
        """Checkout and pull the base branch."""
        print("Fetching latest changes...")
        self.repo.git.fetch()

        branch = self.config.base_branch
        
        # Check if branch exists locally or in remote
        # We can look at remote refs to be sure what exists on origin
        try:
            # List remote branches to simplify checking
            remote_output = self.repo.git.branch("-r")
            remote_branches = [line.strip().replace("origin/", "").split("->")[0].strip() for line in remote_output.splitlines()]
            
            if branch not in remote_branches:
                print(f"config.base_branch '{branch}' not found in remote branches.")
                
                # Check for fallbacks
                if branch == "master" and "main" in remote_branches:
                    print("Found 'main', using that instead of 'master'.")
                    branch = "main"
                elif branch == "main" and "master" in remote_branches:
                    print("Found 'master', using that instead of 'main'.")
                    branch = "master"
                else:
                    # If we can't find it and can't fallback, list what we have
                    raise Exception(f"Branch '{branch}' not found. Remote branches: {remote_branches}")
        except Exception as e:
            # If listing fails, we might just try checking out and let it fail naturally or warn
             print(f"Warning: Could not verify remote branches: {e}")

        print(f"Checking out {branch}...")
        self.repo.git.checkout(branch)
        print(f"Pulling latest changes...")
        self.repo.git.pull()

    def get_diff_files(self, first_run: bool = False) -> List[str]:
        """
        Get list of modified .java files.
        If first_run is True, returns all .java files excluding tests.
        Otherwise, returns files changed in the last 24 hours.
        """
        modified_files = []
        
        if first_run:
            print("First run mode: Scanning all Java files...")
            # Use git ls-files to get all tracked files
            all_files = self.repo.git.ls_files().splitlines()
            for f in all_files:
                if f.endswith(".java") and "src/test/" not in f:
                    modified_files.append(f)
        else:
            print("Daily mode: Checking for changes in the last 24 hours...")
            # diff against 1 day ago. 
            # Note: This relies on reflog or commit dates. 
            # Safest is probably 'HEAD@{1 day ago}' if available, else since 1 day ago.
            try:
                # Get files changed since 1 day ago
                # We use log with name-only
                files = self.repo.git.log('--since=1.day', '--name-only', '--pretty=format:').splitlines()
                # filter empty lines and duplicates
                files = list(set([f for f in files if f]))
                
                for f in files:
                    if f.endswith(".java") and "src/test/" not in f:
                         # verify file still exists (it might have been deleted)
                        if os.path.exists(os.path.join(self.repo_path, f)):
                            modified_files.append(f)
            except GitCommandError as e:
                print(f"Error getting diff: {e}")
                # Fallback or strict error handling?
                # If 'HEAD@{1 day ago}' fails, it might be a fresh clone.
                # In that case, maybe we should just look at the latest commit?
                # User req: "checks for changes... compared to the previous day"
                pass

        return modified_files

    def create_branch(self) -> str:
        """Create a new branch for the documentation update."""
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        branch_name = f"PROD_documented_{date_str}"
        print(f"Creating branch {branch_name}...")
        
        # Check if branch exists
        if branch_name in self.repo.heads:
            # Check it out if it exists
            self.repo.git.checkout(branch_name)
        else:
            self.repo.git.checkout('-b', branch_name)
            
        return branch_name

    def commit_and_push(self, branch_name: str, message: str = "Auto-generated Javadoc") -> None:
        """Commit changes and push to remote."""
        if self.repo.is_dirty():
            print("Committing changes...")
            self.repo.git.add(update=True) # Stage modified files
            self.repo.git.commit('-m', message)
            
            print(f"Pushing {branch_name}...")
            # Set upstream if pushing for first time
            origin = self.repo.remote(name='origin')
            # Authentication should be handled by the environment (ssh agent or credential helper)
            # or by embedding token in URL if using https
            
            # If token is provided in config and we are using HTTPS, we might need to adjust remote URL
            # But assuming environment is set up for now as per standard gitpython usage
            
            try:
                self.repo.git.push('--set-upstream', 'origin', branch_name)
                print("Push successful.")
            except GitCommandError as e:
                print(f"Failed to push: {e}")
        else:
            print("No changes to commit.")

    def create_merge_request(self, branch_name: str, title: str = "Javadoc Update", body: str = "Automated Javadoc updates.") -> str:
        """Create a Merge Request/Pull Request."""
        if not self.config.token:
            print("No token provided, skipping MR creation.")
            return None

        token = self.config.token.get_secret_value()
        base_branch = self.config.base_branch
        
        # Determine API interaction based on provider
        if self.config.provider.lower() == "github":
            return self._create_github_pr(branch_name, base_branch, title, body, token)
        elif self.config.provider.lower() == "gitlab":
            return self._create_gitlab_mr(branch_name, base_branch, title, body, token)
        else:
            print(f"Unknown provider {self.config.provider}, skipping MR creation.")
            return None

    def _create_github_pr(self, branch: str, base: str, title: str, body: str, token: str) -> str:
        # Extract owner/repo from URL or config
        # Assumption: repo_url is like https://github.com/owner/repo.git
        if self.config.project_id:
            owner_repo = self.config.project_id
        else:
            # Simple parse attempt
            parts = self.config.repo_url.rstrip(".git").split("/")
            owner_repo = f"{parts[-2]}/{parts[-1]}"
        
        api_url = self.config.api_url or "https://api.github.com"
        url = f"{api_url}/repos/{owner_repo}/pulls"
        
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": title,
            "body": body,
            "head": branch,
            "base": base
        }
        
        try:
            print(f"Creating GitHub PR on {owner_repo}...")
            response = requests.post(url, json=data, headers=headers, verify=self.config.ssl_verify)
            response.raise_for_status()
            pr_url = response.json().get("html_url")
            print(f"PR created: {pr_url}")
            return pr_url
        except Exception as e:
            print(f"Failed to create GitHub PR: {e}")
            if response.text:
                print(f"Response: {response.text}")
            return None

    def _create_gitlab_mr(self, branch: str, base: str, title: str, body: str, token: str) -> str:
        # Strict usage of project_id, validated at startup
        project_id = self.config.project_id
        
        if self.config.api_url:
            api_url = self.config.api_url
        else:
             # Auto-detect from repo_url
             from urllib.parse import urlparse
             parsed = urlparse(self.config.repo_url)
             api_url = f"{parsed.scheme}://{parsed.netloc}/api/v4"
             
        url = f"{api_url}/projects/{project_id}/merge_requests"
        
        headers = {
            "PRIVATE-TOKEN": token
        }

        data = {
            "source_branch": branch,
            "target_branch": base,
            "title": title,
            "description": body
        }
        
        try:
            print(f"Creating GitLab MR for project {project_id}...")
            response = requests.post(url, json=data, headers=headers, verify=self.config.ssl_verify)
            response.raise_for_status()
            mr_url = response.json().get("web_url")
            print(f"MR created: {mr_url}")
            return mr_url
        except Exception as e:
            print(f"Failed to create GitLab MR: {e}")
            if response.text:
                print(f"Response: {response.text}")
            return None

