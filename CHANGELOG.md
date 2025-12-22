# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-22

### Added
- Initial release of Javadoc AI Automation system
- Core automation script (`javadoc_automation.py`) for orchestrating Javadoc generation
- Git operations module (`git_operations.py`) for repository management
  - Support for cloning and pulling from GitLab
  - Branch creation with date-stamped naming
  - Commit and push functionality
  - Diff comparison between commits
- Java parser module (`java_parser.py`) for code analysis
  - Parse Java files to identify classes and methods
  - Detect existing Javadoc comments
  - Extract code context for LLM processing
  - Insert generated Javadoc into source files
  - Support for test file exclusion
- LLM integration module (`llm_integration.py`) for AI-powered documentation
  - LangChain provider support (OpenAI GPT-4, GPT-3.5-turbo)
  - PydanticAI provider support (experimental)
  - Configurable temperature and token limits
  - Batch processing capabilities
- Email reporter module (`email_reporter.py`) for notifications
  - HTML email reports with statistics
  - Plain text fallback
  - Customizable SMTP configuration
- State management module (`state_manager.py`) for persistence
  - Track processed commits
  - First run detection
  - Cumulative statistics
  - JSON-based state storage
- Comprehensive configuration system
  - YAML-based configuration (`config.yaml.template`)
  - Support for GitLab tokens, repository URL, and branch settings
  - LLM provider and model configuration
  - Email SMTP configuration
  - Processing options (exclude patterns, limits)
  - Logging configuration
- Documentation
  - Comprehensive README.md with features, installation, and usage
  - Quick Start Guide (QUICKSTART.md)
  - Contributing guidelines (CONTRIBUTING.md)
  - Example usage script
- Setup scripts
  - Linux/Mac setup script (`setup.sh`)
  - Windows setup script (`setup.bat`)
  - Dockerfile for containerization
- Testing infrastructure
  - Basic unit tests (`test_basic.py`)
  - Configuration validation tests
  - Requirements validation tests
- Additional files
  - `.env.example` for environment variables
  - `.gitignore` updated for project-specific files
  - Requirements file with all dependencies

### Features
- Automated nightly Javadoc generation
- Incremental processing (only modified files)
- First-run mode (document all non-test code)
- Smart test file exclusion
- Branch creation with date-stamped names (PROD_documented_YYYY-MM-DD)
- Automated commit and push to GitLab
- Detailed HTML email reports
- State persistence between runs
- Configurable processing limits
- Professional Javadoc generation with:
  - Method and class summaries
  - @param tags for parameters
  - @return tags for return values
  - @throws tags for exceptions
  - Proper formatting and indentation

### Dependencies
- PyYAML >= 6.0.1
- GitPython >= 3.1.40
- langchain >= 0.1.0
- langchain-openai >= 0.0.2
- pydantic-ai >= 0.0.1
- pydantic >= 2.5.0
- javalang >= 0.13.0
- python-dotenv >= 1.0.0
- secure-smtplib >= 0.1.1

### Notes
- Designed for GitLab repositories (GitHub support can be added)
- Requires Python 3.8 or higher
- Requires valid LLM API key (OpenAI or compatible)
- Requires SMTP server access for email reports
- First run processes entire repository, subsequent runs are incremental

## [Unreleased]

### Planned
- GitHub repository support
- Bitbucket repository support
- Additional LLM providers (Anthropic Claude, local models)
- Web UI for configuration and monitoring
- GitLab/GitHub Actions integration
- Pull request comments for review
- Configurable Javadoc templates
- Support for other programming languages (Python docstrings, JavaScript JSDoc)
- Metrics dashboard
- API endpoints for integration
- Advanced filtering options
- Custom Javadoc style guides
- Multi-repository support

### Under Consideration
- Local LLM support (Ollama, LLaMA)
- Incremental processing based on file changes only (not full diff)
- Parallel processing for large repositories
- Javadoc quality scoring
- Integration with code review tools
- Support for other documentation formats (Sphinx, Doxygen)
