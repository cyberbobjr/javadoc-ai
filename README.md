# Javadoc AI Automation

An automated system for generating Javadoc comments for Java repositories using AI/LLM technology. This tool runs nightly, compares code changes, and generates professional Javadoc documentation for all modified classes and methods.

## Features

- **Automated Documentation**: Generates high-quality Javadoc comments using LLM technology (LangChain or PydanticAI)
- **Incremental Updates**: On first run, documents all non-test code; subsequently only documents modified files
- **Git Integration**: Automatically pulls from GitLab, creates documentation branches, and pushes changes
- **Email Reporting**: Sends detailed HTML email reports of all documented elements
- **State Management**: Tracks processed files and commits between runs
- **Configurable**: Highly customizable through YAML configuration
- **Test Exclusion**: Automatically excludes test files from documentation

## Architecture

The system consists of several modular components:

- **javadoc_automation.py**: Main orchestrator script
- **git_operations.py**: Git repository management
- **java_parser.py**: Java code parsing and analysis
- **llm_integration.py**: LLM-based Javadoc generation
- **email_reporter.py**: Email reporting functionality
- **state_manager.py**: State persistence between runs

## Installation

### Prerequisites

- Python 3.8 or higher
- Git
- Access to a GitLab repository
- API key for an LLM service (OpenAI GPT-4, GPT-3.5-turbo, etc.)
- SMTP server access for email reports

### Setup

1. Clone this repository:
```bash
git clone https://github.com/cyberbobjr/javadoc-ai.git
cd javadoc-ai
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create configuration file:
```bash
cp config.yaml.template config.yaml
```

4. Edit `config.yaml` with your settings:
```yaml
gitlab:
  access_token: "YOUR_GITLAB_ACCESS_TOKEN"
  repo_url: "https://gitlab.com/your-org/your-repo.git"
  branch: "PROD"
  clone_dir: "./repo_clone"

llm:
  provider: "langchain"
  model: "gpt-4"
  api_key: "YOUR_LLM_API_KEY"
  temperature: 0.3
  max_tokens: 1000

email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  from_email: "your-email@gmail.com"
  password: "YOUR_EMAIL_PASSWORD"
  to_emails:
    - "recipient@example.com"
```

## Usage

### Manual Run

Run the automation script manually:

```bash
python javadoc_automation.py
```

### Scheduled Execution (Nightly)

Set up a cron job to run nightly (Linux/Mac):

```bash
# Edit crontab
crontab -e

# Add this line to run at 2 AM every night
0 2 * * * cd /path/to/javadoc-ai && /usr/bin/python3 javadoc_automation.py >> /var/log/javadoc-ai.log 2>&1
```

For Windows, use Task Scheduler:
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to daily at desired time
4. Set action to run `python javadoc_automation.py`

### Docker (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "javadoc_automation.py"]
```

Build and run:
```bash
docker build -t javadoc-ai .
docker run -v $(pwd)/config.yaml:/app/config.yaml javadoc-ai
```

## Configuration

### GitLab Settings

- **access_token**: GitLab personal access token with `read_repository` and `write_repository` permissions
- **repo_url**: Full URL to your GitLab repository
- **branch**: Branch to monitor (typically "PROD", "main", or "master")
- **clone_dir**: Local directory for repository clone

### LLM Settings

- **provider**: Choose "langchain" or "pydantic-ai"
- **model**: LLM model name (e.g., "gpt-4", "gpt-3.5-turbo")
- **api_key**: API key for your LLM provider
- **temperature**: Controls randomness (0.0 = deterministic, 1.0 = creative)
- **max_tokens**: Maximum length of generated responses

### Email Settings

- **smtp_server**: SMTP server address
- **smtp_port**: SMTP port (typically 587 for TLS)
- **from_email**: Sender email address
- **password**: Email password or app-specific password
- **to_emails**: List of recipient email addresses

### Processing Options

- **exclude_tests**: Exclude test files from documentation (default: true)
- **exclude_patterns**: Glob patterns for files to exclude
- **max_files**: Maximum files to process per run (0 = unlimited)
- **max_methods_per_file**: Maximum methods per file to document (0 = unlimited)

## Workflow

1. **Initialize**: Clone or pull the latest code from the configured branch
2. **Compare**: Determine which files have changed since the last run
   - First run: All non-test Java files
   - Subsequent runs: Only modified files
3. **Parse**: Extract classes and methods that lack Javadoc comments
4. **Generate**: Use LLM to generate professional Javadoc for each element
5. **Insert**: Add generated Javadoc comments to the source files
6. **Branch**: Create a new branch named `{BRANCH}_documented_{DATE}`
7. **Commit**: Commit changes with descriptive message
8. **Push**: Push the documentation branch to GitLab
9. **Report**: Send email report with statistics and details
10. **State**: Update state file for next run

## Generated Javadoc Quality

The LLM generates Javadoc that includes:

- Clear, concise summary of functionality
- `@param` tags for all parameters
- `@return` tags for non-void methods
- `@throws` tags for declared exceptions
- Proper formatting and indentation
- Adherence to Javadoc conventions

Example generated Javadoc:
```java
/**
 * Calculates the total price including tax for a given product.
 * This method applies the current tax rate to the base price and
 * returns the final amount to be charged to the customer.
 * 
 * @param basePrice the original price of the product before tax
 * @param taxRate the tax rate as a decimal (e.g., 0.15 for 15%)
 * @return the total price including tax
 * @throws IllegalArgumentException if basePrice or taxRate is negative
 */
public double calculateTotalPrice(double basePrice, double taxRate) {
    // method implementation
}
```

## Email Reports

After each run, an HTML email report is sent containing:

- Summary statistics (files processed, classes/methods documented)
- Detailed list of all documented files
- Specific elements documented in each file
- Professional formatting with color-coded statistics

## State Management

The system maintains state in `javadoc_state.json`:

- Last run timestamp
- Last processed commit SHA
- First run flag
- Processed files list
- Cumulative statistics

This enables incremental processing and tracking over time.

## Logging

Logs are written to both console and file (`javadoc_automation.log` by default):

- INFO: Normal operation events
- WARNING: Non-critical issues (e.g., files that couldn't be parsed)
- ERROR: Critical failures
- DEBUG: Detailed debugging information

Configure log level in `config.yaml`:
```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_file: "./javadoc_automation.log"
```

## Troubleshooting

### "Failed to initialize repository"
- Check GitLab access token permissions
- Verify repository URL is correct
- Ensure network connectivity to GitLab

### "Failed to generate Javadoc"
- Verify LLM API key is valid
- Check API rate limits
- Ensure sufficient API credits/quota

### "Failed to send email report"
- Verify SMTP settings
- Check email password (use app-specific password for Gmail)
- Ensure SMTP port is not blocked by firewall

### "Syntax error parsing Java file"
- File may have syntax errors
- System will attempt regex-based fallback parsing
- Check logs for specific files with issues

## Best Practices

1. **Test First**: Run manually before scheduling to verify configuration
2. **Review Output**: Check the generated documentation branch before merging
3. **Monitor Logs**: Regularly review logs for errors or warnings
4. **Update Regularly**: Keep dependencies updated for security
5. **Backup State**: Periodically backup `javadoc_state.json`
6. **Rate Limits**: Be mindful of LLM API rate limits
7. **Cost Management**: Monitor LLM API usage and costs

## Security Considerations

- **Never commit** `config.yaml` with actual credentials
- Use environment variables for sensitive values if needed
- Restrict GitLab token permissions to minimum required
- Use app-specific passwords for email authentication
- Keep API keys secure and rotate regularly
- Review generated code before merging to production

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## License

See LICENSE file for details.

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: your-email@example.com

## Acknowledgments

- Built with [LangChain](https://github.com/langchain-ai/langchain)
- Java parsing with [javalang](https://github.com/c2nes/javalang)
- Git operations with [GitPython](https://github.com/gitpython-developers/GitPython)