"""
Git operations module for Javadoc automation.
Handles repository cloning, pulling, and diff operations.
"""

import os
import logging
from typing import List, Dict, Set
from git import Repo, GitCommandError
from pathlib import Path


logger = logging.getLogger(__name__)


class GitOperations:
    """Manages Git repository operations for Javadoc automation."""
    
    def __init__(self, repo_url: str, clone_dir: str, branch: str, access_token: str = None):
        """
        Initialize Git operations.
        
        Args:
            repo_url: URL of the Git repository
            clone_dir: Local directory for cloning
            branch: Branch name to monitor
            access_token: GitLab access token for authentication
        """
        self.repo_url = repo_url
        self.clone_dir = Path(clone_dir)
        self.branch = branch
        self.access_token = access_token
        self.repo = None
        
        # Inject access token into URL if provided
        if access_token and "https://" in repo_url:
            parts = repo_url.split("https://")
            self.auth_url = f"https://oauth2:{access_token}@{parts[1]}"
        else:
            self.auth_url = repo_url
    
    def initialize_repo(self) -> bool:
        """
        Initialize or clone the repository.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.clone_dir.exists() and (self.clone_dir / ".git").exists():
                logger.info(f"Repository already exists at {self.clone_dir}")
                self.repo = Repo(self.clone_dir)
                return True
            else:
                logger.info(f"Cloning repository from {self.repo_url}")
                self.clone_dir.mkdir(parents=True, exist_ok=True)
                self.repo = Repo.clone_from(self.auth_url, self.clone_dir)
                logger.info("Repository cloned successfully")
                return True
        except GitCommandError as e:
            logger.error(f"Failed to initialize repository: {e}")
            return False
    
    def pull_latest(self) -> bool:
        """
        Pull the latest changes from the remote branch.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.repo:
                logger.error("Repository not initialized")
                return False
            
            # Checkout the target branch
            if self.branch not in self.repo.heads:
                logger.info(f"Creating local branch {self.branch}")
                origin = self.repo.remotes.origin
                origin.fetch()
                self.repo.create_head(self.branch, origin.refs[self.branch])
            
            # Checkout and pull
            self.repo.heads[self.branch].checkout()
            origin = self.repo.remotes.origin
            origin.pull(self.branch)
            logger.info(f"Pulled latest changes from {self.branch}")
            return True
        except GitCommandError as e:
            logger.error(f"Failed to pull latest changes: {e}")
            return False
    
    def get_modified_java_files(self, previous_commit: str = None) -> List[str]:
        """
        Get list of modified Java files since the previous commit.
        
        Args:
            previous_commit: SHA of the previous commit to compare against.
                           If None, returns all Java files.
        
        Returns:
            List of modified Java file paths
        """
        try:
            if not self.repo:
                logger.error("Repository not initialized")
                return []
            
            java_files = []
            
            if previous_commit:
                # Get diff between commits
                current_commit = self.repo.head.commit
                logger.info(f"Comparing {previous_commit} with {current_commit.hexsha}")
                
                try:
                    diff = self.repo.commit(previous_commit).diff(current_commit)
                    for diff_item in diff:
                        if diff_item.b_path and diff_item.b_path.endswith('.java'):
                            full_path = self.clone_dir / diff_item.b_path
                            if full_path.exists():
                                java_files.append(str(diff_item.b_path))
                except GitCommandError as e:
                    logger.warning(f"Failed to get diff, will process all files: {e}")
                    previous_commit = None
            
            if not previous_commit:
                # First run: get all Java files
                logger.info("First run: collecting all Java files")
                for root, dirs, files in os.walk(self.clone_dir):
                    # Skip .git directory
                    if '.git' in root:
                        continue
                    for file in files:
                        if file.endswith('.java'):
                            full_path = Path(root) / file
                            rel_path = full_path.relative_to(self.clone_dir)
                            java_files.append(str(rel_path))
            
            logger.info(f"Found {len(java_files)} Java files to process")
            return java_files
        except Exception as e:
            logger.error(f"Error getting modified Java files: {e}")
            return []
    
    def create_documentation_branch(self, date_str: str) -> bool:
        """
        Create a new branch for documented code.
        
        Args:
            date_str: Date string to append to branch name
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.repo:
                logger.error("Repository not initialized")
                return False
            
            branch_name = f"{self.branch}_documented_{date_str}"
            
            # Check if branch already exists
            if branch_name in self.repo.heads:
                logger.info(f"Branch {branch_name} already exists, checking out")
                self.repo.heads[branch_name].checkout()
            else:
                # Create new branch from current position
                logger.info(f"Creating new branch {branch_name}")
                new_branch = self.repo.create_head(branch_name)
                new_branch.checkout()
            
            return True
        except GitCommandError as e:
            logger.error(f"Failed to create documentation branch: {e}")
            return False
    
    def commit_and_push(self, date_str: str, message: str = None) -> bool:
        """
        Commit changes and push to remote.
        
        Args:
            date_str: Date string for branch name
            message: Commit message
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.repo:
                logger.error("Repository not initialized")
                return False
            
            # Add all modified Java files
            # A=True: add all files including untracked
            # u=True: update tracked files
            self.repo.git.add(A=True, u=True)
            
            # Check if there are changes to commit
            if not self.repo.is_dirty() and not self.repo.untracked_files:
                logger.info("No changes to commit")
                return True
            
            # Commit
            if not message:
                message = f"Automated Javadoc generation - {date_str}"
            self.repo.index.commit(message)
            logger.info(f"Committed changes: {message}")
            
            # Push to remote
            branch_name = f"{self.branch}_documented_{date_str}"
            origin = self.repo.remotes.origin
            origin.push(branch_name)
            logger.info(f"Pushed branch {branch_name} to remote")
            
            return True
        except GitCommandError as e:
            logger.error(f"Failed to commit and push: {e}")
            return False
    
    def get_current_commit(self) -> str:
        """
        Get the SHA of the current commit.
        
        Returns:
            Current commit SHA or None if error
        """
        try:
            if self.repo:
                return self.repo.head.commit.hexsha
            return None
        except Exception as e:
            logger.error(f"Failed to get current commit: {e}")
            return None
    
    def get_file_content(self, file_path: str) -> str:
        """
        Get the content of a file in the repository.
        
        Args:
            file_path: Relative path to the file
        
        Returns:
            File content as string
        """
        try:
            full_path = self.clone_dir / file_path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return ""
    
    def write_file_content(self, file_path: str, content: str) -> bool:
        """
        Write content to a file in the repository.
        
        Args:
            file_path: Relative path to the file
            content: Content to write
        
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.clone_dir / file_path
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False
