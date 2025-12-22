import datetime
import os
from typing import List

from git import GitCommandError, Repo

from .config import GitConfig


class GitManager:
    def __init__(self, config: GitConfig, repo_path: str = "."):
        self.config = config
        self.repo_path = repo_path
        self.repo = self._init_repo()

    def _init_repo(self) -> Repo:
        """Initialize GitPython Repo object."""
        try:
            return Repo(self.repo_path)
        except (GitCommandError, Exception) as e:
            # If repo doesn't exist, we might want to clone it
            # But for this script, we assume it's running inside or we clone it
            if not os.path.exists(self.repo_path) and self.config.repo_url:
                print(f"Cloning {self.config.repo_url} to {self.repo_path}...")
                return Repo.clone_from(self.config.repo_url, self.repo_path)
            raise e

    def pull_prod(self) -> None:
        """Checkout and pull the base branch."""
        print(f"Checking out {self.config.base_branch}...")
        self.repo.git.checkout(self.config.base_branch)
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
