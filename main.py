import argparse
import logging
import os
from typing import List

from dotenv import load_dotenv

from src.agent import JavaDocAgent
from src.config import load_config
from src.git_manager import GitManager
from src.notifier import Notifier

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Javadoc Automation Agent")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--first-run", action="store_true", help="Run on all files (excluding tests)")
    parser.add_argument("--dry-run", action="store_true", help="Do not push changes")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Load Configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return

    # Set API Key for PydanticAI if provided in config
    if config.llm.api_key:
        os.environ["OPENAI_API_KEY"] = config.llm.api_key.get_secret_value()
        # Also set OPENAI_API_KEY if the model requires it, 
        # but here we assume Gemini or generic usage.
    
    # Initialize components
    try:
        git_manager = GitManager(config.git)
        agent = JavaDocAgent(config.llm)
        notifier = Notifier(config.email, config.teams)
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
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

            # Notifications
            summary = (
                f"Javadoc Automation ran successfully.\n"
                f"Branch: {branch_name}\n"
                f"Documented Files: {len(documented_files)}\n"
            )
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
        # Notify failure? (Optional enhancement)

if __name__ == "__main__":
    main()
