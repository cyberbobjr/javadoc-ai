# Quick Start Guide

Get started with Javadoc AI Automation in minutes!

## Prerequisites

Before you begin, ensure you have:
- Python 3.8 or higher
- Git
- A GitLab account with a Java repository
- An OpenAI API key (or other LLM provider)
- SMTP email credentials

## Installation (5 minutes)

### Linux/Mac

```bash
# 1. Clone the repository
git clone https://github.com/cyberbobjr/javadoc-ai.git
cd javadoc-ai

# 2. Run setup script
./setup.sh

# 3. Edit configuration
cp config.yaml.template config.yaml
nano config.yaml  # or use your preferred editor
```

### Windows

```cmd
# 1. Clone the repository
git clone https://github.com/cyberbobjr/javadoc-ai.git
cd javadoc-ai

# 2. Run setup script
setup.bat

# 3. Edit configuration
copy config.yaml.template config.yaml
notepad config.yaml
```

## Configuration (5 minutes)

Edit `config.yaml` with your credentials:

```yaml
gitlab:
  access_token: "glpat-xxxxxxxxxxxx"  # Your GitLab personal access token
  repo_url: "https://gitlab.com/yourorg/yourrepo.git"
  branch: "PROD"

llm:
  provider: "langchain"
  model: "gpt-4"
  api_key: "sk-xxxxxxxxxxxx"  # Your OpenAI API key

email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  from_email: "your-email@gmail.com"
  password: "xxxxxxxxxxxx"  # App-specific password recommended
  to_emails:
    - "recipient@example.com"
```

### Getting Required Credentials

#### GitLab Personal Access Token

1. Go to GitLab → User Settings → Access Tokens
2. Create new token with `read_repository` and `write_repository` scopes
3. Copy the token (you won't see it again!)

#### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy the key

#### Gmail App Password (if using Gmail)

1. Enable 2-factor authentication on your Google account
2. Go to Google Account → Security → 2-Step Verification → App Passwords
3. Generate app password for "Mail"
4. Use this password in config (not your regular password)

## First Run (2 minutes)

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate.bat  # Windows

# Run the automation
python javadoc_automation.py
```

**What happens on first run:**
- Clones your GitLab repository
- Scans all non-test Java files
- Generates Javadoc for classes and methods without documentation
- Creates a new branch: `PROD_documented_2024-XX-XX`
- Pushes the branch to GitLab
- Sends an email report

**Note:** First run may take longer depending on repository size and number of undocumented elements.

## Verification

After the first run, check:

1. **Logs**: View `javadoc_automation.log` for details
2. **GitLab**: Check for new branch `PROD_documented_[date]`
3. **Email**: Check your inbox for the report
4. **State**: Verify `javadoc_state.json` was created

## Daily Automation

### Linux/Mac (Cron)

```bash
# Edit crontab
crontab -e

# Add line to run at 2 AM daily
0 2 * * * cd /path/to/javadoc-ai && /path/to/javadoc-ai/venv/bin/python javadoc_automation.py >> /var/log/javadoc-ai.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Name: "Javadoc AI Automation"
4. Trigger: Daily at 2:00 AM
5. Action: Start a program
   - Program: `C:\path\to\javadoc-ai\venv\Scripts\python.exe`
   - Arguments: `javadoc_automation.py`
   - Start in: `C:\path\to\javadoc-ai`
6. Finish and enable the task

### Docker (Alternative)

```bash
# Build image
docker build -t javadoc-ai .

# Run with mounted config
docker run -v $(pwd)/config.yaml:/app/config.yaml javadoc-ai

# Schedule with cron
0 2 * * * docker run -v /path/to/config.yaml:/app/config.yaml javadoc-ai >> /var/log/javadoc-ai.log 2>&1
```

## Common Issues

### "Failed to initialize repository"
- Check GitLab token has correct permissions
- Verify repository URL is correct
- Test token: `git ls-remote https://oauth2:TOKEN@gitlab.com/org/repo.git`

### "Failed to generate Javadoc"
- Verify OpenAI API key is valid
- Check API quota/billing
- Test key: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

### "Failed to send email"
- Use app-specific password for Gmail (not regular password)
- Check SMTP port is not blocked by firewall
- Test SMTP: `telnet smtp.gmail.com 587`

### Dependencies not installing
```bash
# Update pip first
pip install --upgrade pip

# Install dependencies one by one to see which fails
pip install PyYAML
pip install GitPython
pip install langchain
pip install javalang
```

## Testing

### Dry Run (without committing)

Modify the main script temporarily to skip commit/push:

```python
# In javadoc_automation.py, comment out the commit_and_push line:
# if not self.git_ops.commit_and_push(...):
#     pass
```

### Small Repository Test

Test on a small repository first:
1. Create a test repository with 1-2 Java files
2. Configure to point to test repo
3. Run automation
4. Verify results before using on production

## Next Steps

- Review generated documentation branch
- Merge to main branch if satisfied
- Set up daily automation
- Monitor email reports
- Adjust configuration as needed

## Getting Help

- Check the full README.md for detailed documentation
- Review logs in `javadoc_automation.log`
- Open an issue on GitHub
- Review CONTRIBUTING.md for development setup

## Tips

1. **Start small**: Test on a small repository first
2. **Review output**: Always review the generated branch before merging
3. **Monitor costs**: Keep track of LLM API usage
4. **Adjust temperature**: Lower values (0.1-0.3) for more consistent output
5. **Set limits**: Use `max_files` and `max_methods_per_file` to control processing
6. **Backup state**: Keep backups of `javadoc_state.json`

Happy documenting! 🚀
