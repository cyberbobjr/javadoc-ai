# Troubleshooting Guide

This guide helps you diagnose and fix common issues with Javadoc AI Automation.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Configuration Issues](#configuration-issues)
3. [Git/GitLab Issues](#gitgitlab-issues)
4. [LLM/API Issues](#llmapi-issues)
5. [Email Issues](#email-issues)
6. [Processing Issues](#processing-issues)
7. [Performance Issues](#performance-issues)
8. [Debugging Tips](#debugging-tips)

---

## Installation Issues

### Python not found
```
Error: Python is not installed
```

**Solution:**
- Install Python 3.8 or higher from https://www.python.org/
- Ensure Python is added to PATH
- Verify: `python3 --version` or `python --version`

### pip install fails
```
ERROR: Could not install packages due to an OSError
```

**Solutions:**
1. Upgrade pip: `pip install --upgrade pip`
2. Use user install: `pip install --user -r requirements.txt`
3. Check disk space: `df -h` (Linux/Mac) or `dir` (Windows)
4. Check permissions

### Git not found
```
Error: Git is not installed
```

**Solution:**
- Install Git from https://git-scm.com/
- Verify: `git --version`

---

## Configuration Issues

### Config file not found
```
Error: Configuration file 'config.yaml' not found.
```

**Solution:**
```bash
cp config.yaml.template config.yaml
# Edit config.yaml with your settings
```

### Invalid YAML syntax
```
Error parsing configuration file: ...
```

**Solution:**
- Check for proper indentation (use spaces, not tabs)
- Ensure all strings with special characters are quoted
- Validate YAML: https://www.yamllint.com/
- Common issues:
  - Tabs instead of spaces
  - Unquoted strings with colons or special characters
  - Incorrect indentation

### Missing configuration values
```
KeyError: 'access_token'
```

**Solution:**
- Ensure all required fields are filled in config.yaml
- Check template for required fields
- Don't leave placeholder values like "YOUR_TOKEN_HERE"

---

## Git/GitLab Issues

### Failed to initialize repository
```
Failed to initialize repository: ...
```

**Possible Causes & Solutions:**

1. **Invalid GitLab token**
   - Check token is valid: Go to GitLab → Settings → Access Tokens
   - Ensure token has `read_repository` and `write_repository` scopes
   - Token may have expired

2. **Incorrect repository URL**
   ```bash
   # Verify URL format
   https://gitlab.com/org/repo.git
   ```

3. **Network connectivity**
   ```bash
   # Test connection
   ping gitlab.com
   git ls-remote https://gitlab.com/org/repo.git
   ```

4. **Token authentication**
   ```bash
   # Test with token
   git ls-remote https://oauth2:YOUR_TOKEN@gitlab.com/org/repo.git
   ```

### Failed to pull latest changes
```
Failed to pull latest changes: ...
```

**Solutions:**
1. Check network connection
2. Verify branch exists: `git branch -r`
3. Check for local changes conflicts
4. Clear clone directory and retry:
   ```bash
   rm -rf ./repo_clone
   ```

### Failed to create branch
```
Failed to create documentation branch: ...
```

**Solutions:**
1. Check if branch already exists
2. Verify you have write permissions
3. Check branch naming conflicts

### Failed to push
```
Failed to commit and push: ...
```

**Solutions:**
1. Verify GitLab token has write permissions
2. Check if remote branch is protected
3. Ensure no conflicts with remote
4. Check GitLab repository settings

---

## LLM/API Issues

### Failed to generate Javadoc
```
Failed to generate Javadoc: ...
```

**Possible Causes & Solutions:**

1. **Invalid API key**
   - Verify key at https://platform.openai.com/api-keys
   - Test with curl:
     ```bash
     curl https://api.openai.com/v1/models \
       -H "Authorization: Bearer YOUR_API_KEY"
     ```

2. **Rate limit exceeded**
   ```
   Error: Rate limit exceeded
   ```
   - Wait and retry
   - Upgrade API plan
   - Reduce `max_files` or `max_methods_per_file` in config

3. **Insufficient credits/quota**
   - Check billing at https://platform.openai.com/account/billing
   - Add payment method or credits

4. **Model not available**
   ```
   Error: Model 'gpt-4' not found
   ```
   - Check model name is correct
   - Verify you have access to the model
   - Try 'gpt-3.5-turbo' instead

5. **Network timeout**
   - Increase timeout in config
   - Check network connectivity
   - Try different network

### LangChain import errors
```
ModuleNotFoundError: No module named 'langchain'
```

**Solution:**
```bash
pip install langchain langchain-openai
# Or reinstall all dependencies
pip install -r requirements.txt
```

---

## Email Issues

### Failed to send email report
```
Failed to send email report: ...
```

**Possible Causes & Solutions:**

1. **Invalid SMTP credentials**
   - Verify email and password
   - For Gmail, use App Password (not regular password):
     1. Enable 2FA on Google account
     2. Generate App Password at: Account → Security → App Passwords

2. **SMTP connection refused**
   ```
   Connection refused
   ```
   - Check SMTP server and port
   - Gmail: smtp.gmail.com:587
   - Outlook: smtp.office365.com:587
   - Test connection:
     ```bash
     telnet smtp.gmail.com 587
     ```

3. **Firewall blocking SMTP**
   - Check firewall rules
   - Try different port (465 for SSL, 587 for TLS)
   - Contact network administrator

4. **SSL/TLS errors**
   - Ensure correct port (587 for TLS, 465 for SSL)
   - Update Python SSL certificates
   - Try `smtp_ssl=True` or `smtp_ssl=False`

---

## Processing Issues

### Java parsing errors
```
Syntax error parsing file.java: ...
```

**Solutions:**
1. File may have actual syntax errors - fix in source
2. Complex Java syntax not supported by javalang
3. System will attempt regex fallback
4. Check logs for specific issues

### No files to process
```
No Java files to process
```

**Possible Causes:**
1. No changes since last run (working as intended)
2. All files excluded by patterns
3. Repository has no Java files
4. Clone directory is empty

**Solutions:**
- Check exclude_patterns in config
- Verify repository has .java files
- Check clone_dir exists and has content
- Reset state for full reprocess:
  ```bash
  rm javadoc_state.json
  ```

### Elements not being documented
```
No elements need documentation in file.java
```

**Possible Causes:**
1. All elements already have Javadoc (working as intended)
2. Parser not detecting elements correctly

**Solutions:**
- Enable DEBUG logging to see what's detected
- Check if file is excluded
- Review parser logic for edge cases

---

## Performance Issues

### Processing takes too long

**Solutions:**
1. Reduce batch size:
   ```yaml
   processing:
     max_files: 10
     max_methods_per_file: 5
   ```

2. Use faster LLM model:
   ```yaml
   llm:
     model: "gpt-3.5-turbo"  # Faster than gpt-4
   ```

3. Increase max_tokens for efficiency:
   ```yaml
   llm:
     max_tokens: 500  # Reduce for faster response
   ```

4. Process in parallel (future feature)

### High API costs

**Solutions:**
1. Use cheaper model (gpt-3.5-turbo vs gpt-4)
2. Set processing limits
3. Process only changed files (default behavior)
4. Consider local LLM (future feature)

---

## Debugging Tips

### Enable DEBUG logging

Edit config.yaml:
```yaml
logging:
  level: "DEBUG"
```

### Check logs

```bash
# View recent logs
tail -f javadoc_automation.log

# Search for errors
grep ERROR javadoc_automation.log

# View specific module logs
grep "git_operations" javadoc_automation.log
```

### Verify state

```bash
# View current state
cat javadoc_state.json | python -m json.tool

# Reset state
rm javadoc_state.json
```

### Test components individually

```python
# Test Git operations
from git_operations import GitOperations
ops = GitOperations(...)
ops.initialize_repo()

# Test Java parser
from java_parser import JavaParser
parser = JavaParser()
result = parser.parse_file("Test.java", java_code)

# Test LLM
from llm_integration import JavadocGenerator
gen = JavadocGenerator(...)
doc = gen.generate_javadoc(element, "Test.java", context)
```

### Dry run mode

Temporarily disable commit/push for testing:
```python
# In javadoc_automation.py, comment out:
# self.git_ops.commit_and_push(...)
```

### Check dependencies

```bash
# List installed packages
pip list

# Check specific package
pip show langchain

# Verify imports
python -c "import git; import yaml; import javalang; print('OK')"
```

---

## Getting More Help

If you're still experiencing issues:

1. **Check logs** for detailed error messages
2. **Search issues** on GitHub: https://github.com/cyberbobjr/javadoc-ai/issues
3. **Open new issue** with:
   - Error message
   - Log excerpt
   - Configuration (sanitized)
   - Python version
   - OS/environment
4. **Contact support** via email

## Common Error Messages Reference

| Error | Likely Cause | Quick Fix |
|-------|-------------|-----------|
| `ModuleNotFoundError` | Missing dependency | `pip install -r requirements.txt` |
| `KeyError: 'access_token'` | Config missing values | Fill in config.yaml |
| `GitCommandError` | Git/GitLab issue | Check token & URL |
| `Rate limit exceeded` | Too many API calls | Wait or upgrade plan |
| `Authentication failed` | Wrong credentials | Check token/password |
| `Connection refused` | Network/firewall | Check connectivity |
| `Syntax error` | Invalid YAML/Python | Check formatting |
| `Permission denied` | File/folder access | Check permissions |
