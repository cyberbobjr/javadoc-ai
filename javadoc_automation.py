#!/usr/bin/env python3
"""
Javadoc AI Automation - Main Script

This script automates the generation of Javadoc comments for Java repositories.
It runs nightly, pulls the PROD branch, compares with the previous day,
and updates Javadoc for all modified classes and methods.

On the first run, it documents all non-test code.
Uses config.yaml for GitLab tokens, repo URL, and branch settings.
Generates Javadoc via an LLM agent (LangChain or PydanticAI).
Creates a branch PROD_documented_[date], pushes it, and emails a report.
"""

import os
import sys
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from git_operations import GitOperations
from java_parser import JavaParser
from llm_integration import JavadocGenerator
from email_reporter import EmailReporter
from state_manager import StateManager


# Configure logging
def setup_logging(config: Dict):
    """Set up logging configuration."""
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_file = log_config.get('log_file', 'javadoc_automation.log')
    log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config(config_path: str = 'config.yaml') -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
    
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        print("Please copy config.yaml.template to config.yaml and fill in your values.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}")
        sys.exit(1)


class JavadocAutomation:
    """Main automation orchestrator."""
    
    def __init__(self, config: Dict):
        """
        Initialize automation with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.git_ops = GitOperations(
            repo_url=config['gitlab']['repo_url'],
            clone_dir=config['gitlab']['clone_dir'],
            branch=config['gitlab']['branch'],
            access_token=config['gitlab']['access_token']
        )
        
        self.java_parser = JavaParser(
            exclude_patterns=config['processing']['exclude_patterns']
        )
        
        self.javadoc_gen = JavadocGenerator(
            provider=config['llm']['provider'],
            model=config['llm']['model'],
            api_key=config['llm']['api_key'],
            temperature=config['llm']['temperature'],
            max_tokens=config['llm']['max_tokens']
        )
        
        self.email_reporter = EmailReporter(
            smtp_server=config['email']['smtp_server'],
            smtp_port=config['email']['smtp_port'],
            from_email=config['email']['from_email'],
            password=config['email']['password'],
            to_emails=config['email']['to_emails'],
            subject_template=config['email']['subject_template']
        )
        
        self.state_manager = StateManager(
            state_file=config['state']['state_file'],
            enabled=config['state']['enabled']
        )
        
        self.date_str = datetime.now().strftime('%Y-%m-%d')
    
    def run(self):
        """Execute the main automation workflow."""
        self.logger.info("=" * 60)
        self.logger.info(f"Starting Javadoc automation - {self.date_str}")
        self.logger.info("=" * 60)
        
        try:
            # Step 1: Initialize and pull repository
            if not self._initialize_repository():
                return False
            
            # Step 2: Get current commit
            current_commit = self.git_ops.get_current_commit()
            if not current_commit:
                self.logger.error("Failed to get current commit")
                return False
            
            self.logger.info(f"Current commit: {current_commit}")
            
            # Step 3: Determine which files to process
            previous_commit = self.state_manager.get_last_commit()
            is_first_run = self.state_manager.is_first_run()
            
            if is_first_run:
                self.logger.info("First run: will document all non-test Java files")
            else:
                self.logger.info(f"Incremental run: comparing with previous commit {previous_commit}")
            
            modified_files = self.git_ops.get_modified_java_files(previous_commit)
            
            if not modified_files:
                self.logger.info("No Java files to process")
                return True
            
            self.logger.info(f"Found {len(modified_files)} files to process")
            
            # Step 4: Create documentation branch
            if not self.git_ops.create_documentation_branch(self.date_str):
                self.logger.error("Failed to create documentation branch")
                return False
            
            # Step 5: Process files and generate Javadoc
            stats, documented_files = self._process_files(modified_files)
            
            # Step 6: Commit and push changes
            if stats['total_elements'] > 0:
                if not self.git_ops.commit_and_push(
                    self.date_str,
                    f"Automated Javadoc generation - {self.date_str}\n\n"
                    f"Files: {stats['total_files']}\n"
                    f"Classes: {stats['total_classes']}\n"
                    f"Methods: {stats['total_methods']}"
                ):
                    self.logger.error("Failed to commit and push changes")
                    return False
            else:
                self.logger.info("No changes to commit")
            
            # Step 7: Send email report
            self._send_report(stats, documented_files)
            
            # Step 8: Update state
            self.state_manager.update_after_run(
                current_commit,
                modified_files,
                stats
            )
            
            self.logger.info("=" * 60)
            self.logger.info("Javadoc automation completed successfully")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Automation failed: {e}", exc_info=True)
            return False
    
    def _initialize_repository(self) -> bool:
        """Initialize and update the repository."""
        self.logger.info("Initializing repository...")
        
        if not self.git_ops.initialize_repo():
            self.logger.error("Failed to initialize repository")
            return False
        
        self.logger.info("Pulling latest changes...")
        if not self.git_ops.pull_latest():
            self.logger.error("Failed to pull latest changes")
            return False
        
        return True
    
    def _process_files(self, file_paths: List[str]) -> tuple:
        """
        Process files and generate Javadoc.
        
        Args:
            file_paths: List of file paths to process
        
        Returns:
            Tuple of (stats dict, documented files list)
        """
        stats = {
            'total_files': 0,
            'total_classes': 0,
            'total_methods': 0,
            'total_elements': 0
        }
        
        documented_files = []
        
        max_files = self.config['processing']['max_files']
        files_to_process = file_paths[:max_files] if max_files > 0 else file_paths
        
        for i, file_path in enumerate(files_to_process, 1):
            self.logger.info(f"Processing file {i}/{len(files_to_process)}: {file_path}")
            
            file_info = self._process_single_file(file_path)
            
            if file_info['elements_documented'] > 0:
                stats['total_files'] += 1
                stats['total_classes'] += file_info['classes']
                stats['total_methods'] += file_info['methods']
                stats['total_elements'] += file_info['elements_documented']
                documented_files.append(file_info)
        
        self.logger.info(f"Processing complete: {stats['total_elements']} elements documented")
        
        return stats, documented_files
    
    def _process_single_file(self, file_path: str) -> Dict:
        """
        Process a single Java file.
        
        Args:
            file_path: Relative path to the file
        
        Returns:
            Dictionary with file processing information
        """
        file_info = {
            'file_path': file_path,
            'classes': 0,
            'methods': 0,
            'elements_documented': 0,
            'elements': []
        }
        
        try:
            # Get file content
            content = self.git_ops.get_file_content(file_path)
            if not content:
                self.logger.warning(f"Empty or unreadable file: {file_path}")
                return file_info
            
            # Parse file to find elements needing documentation
            elements = self.java_parser.get_elements_needing_documentation(file_path, content)
            
            if not elements:
                self.logger.debug(f"No elements need documentation in {file_path}")
                return file_info
            
            self.logger.info(f"Found {len(elements)} elements needing documentation")
            
            # Generate Javadoc for each element
            max_methods = self.config['processing']['max_methods_per_file']
            elements_to_process = elements[:max_methods] if max_methods > 0 else elements
            
            modified_content = content
            
            # Process elements in reverse order (bottom to top) to maintain line numbers
            for element in sorted(elements_to_process, key=lambda e: e.line_number, reverse=True):
                self.logger.info(f"Generating Javadoc for {element.element_type} {element.name}")
                
                code_context = self.java_parser.extract_code_context(content, element)
                javadoc = self.javadoc_gen.generate_javadoc(element, file_path, code_context)
                
                if javadoc:
                    modified_content = self.java_parser.insert_javadoc(
                        modified_content, element, javadoc
                    )
                    
                    if element.element_type == 'class':
                        file_info['classes'] += 1
                    else:
                        file_info['methods'] += 1
                    
                    file_info['elements_documented'] += 1
                    file_info['elements'].append(f"{element.element_type}: {element.name} (line {element.line_number})")
            
            # Write modified content back to file
            if file_info['elements_documented'] > 0:
                self.git_ops.write_file_content(file_path, modified_content)
                self.logger.info(f"Updated {file_path} with {file_info['elements_documented']} Javadoc comments")
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}", exc_info=True)
        
        return file_info
    
    def _send_report(self, stats: Dict, documented_files: List[Dict]):
        """
        Send email report.
        
        Args:
            stats: Statistics dictionary
            documented_files: List of documented file information
        """
        try:
            self.logger.info("Sending email report...")
            success = self.email_reporter.send_report(
                self.date_str,
                stats,
                documented_files
            )
            
            if success:
                self.logger.info("Email report sent successfully")
            else:
                self.logger.warning("Failed to send email report")
        except Exception as e:
            self.logger.error(f"Error sending email report: {e}")


def main():
    """Main entry point."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config)
    
    # Run automation
    automation = JavadocAutomation(config)
    success = automation.run()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
