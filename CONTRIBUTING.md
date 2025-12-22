# Contributing to Javadoc AI Automation

Thank you for your interest in contributing to this project! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/javadoc-ai.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes thoroughly
6. Commit with clear messages: `git commit -m "Add feature: description"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

1. Run the setup script:
   ```bash
   # Linux/Mac
   ./setup.sh
   
   # Windows
   setup.bat
   ```

2. Activate virtual environment:
   ```bash
   # Linux/Mac
   source venv/bin/activate
   
   # Windows
   venv\Scripts\activate.bat
   ```

3. Install development dependencies:
   ```bash
   pip install pytest black flake8 mypy
   ```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Use meaningful variable and function names
- Keep functions focused and concise

### Formatting

Use `black` for code formatting:
```bash
black *.py
```

### Linting

Use `flake8` for linting:
```bash
flake8 *.py
```

### Type Checking

Use `mypy` for type checking:
```bash
mypy *.py
```

## Testing

- Write tests for new features
- Ensure all tests pass before submitting PR
- Aim for high test coverage

Run tests:
```bash
pytest tests/
```

## Documentation

- Update README.md if adding new features
- Add docstrings to all new functions and classes
- Update configuration examples if needed
- Include usage examples for new features

## Commit Messages

Write clear, concise commit messages:

- Use present tense: "Add feature" not "Added feature"
- First line: brief summary (50 chars or less)
- Blank line after summary
- Detailed description if needed
- Reference issues: "Fixes #123"

Example:
```
Add support for custom LLM providers

- Implement provider interface
- Add configuration options
- Update documentation
- Add tests for new providers

Fixes #123
```

## Pull Request Process

1. Update documentation as needed
2. Ensure all tests pass
3. Update CHANGELOG.md
4. Request review from maintainers
5. Address review feedback
6. Squash commits if requested
7. Wait for approval and merge

## Code Review

All submissions require code review. We look for:

- Code quality and style
- Test coverage
- Documentation
- Performance considerations
- Security implications

## Bug Reports

When reporting bugs, include:

- Clear, descriptive title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python version, etc.)
- Logs or error messages
- Screenshots if applicable

## Feature Requests

When suggesting features:

- Clear, descriptive title
- Use case and motivation
- Proposed solution
- Alternative solutions considered
- Impact on existing features

## Areas for Contribution

We welcome contributions in:

- **LLM Providers**: Add support for new LLM providers
- **Git Platforms**: Extend beyond GitLab (GitHub, Bitbucket)
- **Parsing**: Improve Java parsing accuracy
- **Testing**: Add more test coverage
- **Documentation**: Improve guides and examples
- **Performance**: Optimize processing speed
- **UI**: Create web interface or CLI improvements
- **Integrations**: CI/CD pipeline integrations

## Questions?

- Open an issue with the "question" label
- Contact maintainers via email
- Check existing issues and discussions

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards others

Thank you for contributing! 🎉
