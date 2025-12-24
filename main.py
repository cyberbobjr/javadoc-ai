import argparse
import logging
import os
import shutil
import tempfile
from typing import List

from dotenv import load_dotenv

from src.agent import JavaDocAgent
from src.config import load_config
from src.git_manager import GitManager
from src.notifier import Notifier
from src.progress_manager import ProgressManager

# Configure logging
# Default to INFO, will change if verbose is set
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Javadoc Automation Agent")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--first-run", action="store_true", help="Run on all files (excluding tests)")
    parser.add_argument("--dry-run", action="store_true", help="Do not push changes")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging (overrides config)")
    parser.add_argument("--work-dir", default=None, help="Directory to use for the repository (required for resume)")
    parser.add_argument("--resume", action="store_true", help="Resume from previous run (skips already processed files)")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Load Configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    # Set Log Level
    # Priority: CLI > Config.verbose > Config.level > Default INFO
    log_level = logging.INFO
    
    if args.verbose:
        log_level = logging.DEBUG
    elif config.logging.verbose:
        log_level = logging.DEBUG
    else:
        # Parse level string to int
        level_str = config.logging.level.upper()
        if hasattr(logging, level_str):
            log_level = getattr(logging, level_str)
    
    logger.setLevel(log_level)
    logging.getLogger().setLevel(log_level)
    
    if log_level == logging.DEBUG:
         logger.debug("Verbose logging enabled")

    # Set API Key for PydanticAI if provided in config
    if config.llm.api_key:
        os.environ["OPENAI_API_KEY"] = config.llm.api_key.get_secret_value()
        # Also set OPENAI_API_KEY if the model requires it, 
        # but here we assume Gemini or generic usage.
    
    # Initialize components
    if args.work_dir:
        repo_path = args.work_dir
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)
        logger.info(f"Using persistent working directory: {repo_path}")
        is_temp_dir = False
    else:
        repo_path = tempfile.mkdtemp(prefix="javadoc-ai-repo-")
        logger.info(f"Using temporary directory: {repo_path}")
        is_temp_dir = True

    try:
        git_manager = GitManager(config.git, repo_path=repo_path)
        agent = JavaDocAgent(config.llm)
        notifier = Notifier(config.email, config.teams)
        progress_manager = ProgressManager(repo_path) if args.resume or args.work_dir else None
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        if is_temp_dir:
            shutil.rmtree(repo_path, ignore_errors=True)
        return

    # Git Operations
    try:
        git_manager.pull_prod()
        modified_files = git_manager.get_diff_files(first_run=args.first_run)
        
        if not modified_files:
            logger.info("No modified .java files found. Exiting.")
            return

        logger.info(f"Found {len(modified_files)} files to document.")

        # Create branch
        branch_name = git_manager.create_branch()
        
        documented_files = []
        failed_files = []

        # Process files
        for file_path in modified_files:
            # Check for resume
            if args.resume and progress_manager and progress_manager.is_processed(file_path):
                logger.info(f"Skipping {file_path} (already processed).")
                documented_files.append(file_path) # Treat as success for reporting purposes if we want to show full scope, or maybe just skip
                # Actually, for reporting "Documented Files", we might want to distinguish "New" vs "Skipped".
                # But to keep logic simple for now, we process it.
                continue

            full_path = os.path.join(git_manager.repo_path, file_path)
            logger.info(f"Processing {file_path}...")
            
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Generate Javadoc
                new_content = agent.generate_javadoc(content)

                # Write back
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                
                documented_files.append(file_path)
                
                # Update progress
                if progress_manager:
                    progress_manager.mark_processed(file_path)
            
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                failed_files.append(f"{file_path} ({str(e)})")

        # Commit and Push
        if documented_files:
            if not args.dry_run:
                try:
                    git_manager.commit_and_push(branch_name)
                    logger.info("Changes pushed successfully.")
                except Exception as e:
                    logger.error(f"Failed to push changes: {e}")
            else:
                logger.info("Dry run: Skipping push.")

            # Auto-Merge Request
            mr_url = None
            if not args.dry_run:
                try:
                    mr_url = git_manager.create_merge_request(branch_name)
                except Exception as e:
                    logger.error(f"Failed to create MR: {e}")
            
            # Notifications
            summary = (
                f"Javadoc Automation ran successfully.\n"
                f"Branch: {branch_name}\n"
                f"Documented Files: {len(documented_files)}\n"
            )
            if mr_url:
                summary += f"Merge Request: {mr_url}\n"

            if failed_files:

                summary += f"Failed Files: {len(failed_files)}\n"
                summary += "\n".join(failed_files)
            
            # Email
            notifier.send_email(
                subject=f"Javadoc Automation Report - {branch_name}",
                body=summary + "\n\nFiles:\n" + "\n".join(documented_files)
            )

            # Teams
            notifier.send_teams_notification(
                title=f"Javadoc Updated in {branch_name}",
                message=summary
            )
        else:
            logger.info("No files were successfully documented.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    finally:
        # Cleanup temp dir if needed. 
        if 'repo_path' in locals() and os.path.exists(repo_path):
            if is_temp_dir:
                if args.dry_run:
                     logger.info(f"Dry run: Keeping temp directory at {repo_path} for inspection.")
                else:
                    logger.info("Cleaning up temporary directory...")
                    shutil.rmtree(repo_path, ignore_errors=True)
            else:
                logger.info("Keeping working directory (user specified).")



if __name__ == "__main__":
    main()
