# Contributing to AI Code Review System

Thank you for your interest in improving the AI Code Review system! This document provides guidelines for contributing.

## 🎯 Ways to Contribute

1. **Bug Reports**: Found an issue? Open a GitHub issue
2. **Feature Requests**: Have an idea? Suggest it in issues
3. **Code Improvements**: Submit pull requests
4. **Documentation**: Improve README, guides, or comments
5. **Testing**: Help test new features

## 🚀 Development Setup

### Local Testing

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/cursorAI-POC.git
cd cursorAI-POC
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r .github/scripts/requirements.txt
```

4. Set up environment variables:
```bash
export OPENAI_API_KEY="your-api-key"
export GITHUB_TOKEN="your-github-token"
export PR_NUMBER="123"
export REPO_NAME="username/repo"
export BASE_SHA="abc123"
export HEAD_SHA="def456"
```

5. Test locally:
```bash
python .github/scripts/ai_code_reviewer.py
```

## 📝 Pull Request Process

1. **Fork** the repository
2. **Create a branch** for your feature: `git checkout -b feature/amazing-feature`
3. **Make your changes** with clear, descriptive commits
4. **Test thoroughly** - ensure nothing breaks
5. **Update documentation** if needed
6. **Submit PR** with description of changes

### PR Guidelines

- ✅ Clear description of what the PR does
- ✅ Reference any related issues
- ✅ Include tests if applicable
- ✅ Update README if adding features
- ✅ Follow existing code style
- ❌ Don't include unrelated changes

## 🎨 Code Style

### Python
- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to functions
- Keep functions focused and small

### YAML (GitHub Actions)
- Use 2-space indentation
- Add comments for complex workflows
- Keep workflows modular

### Documentation
- Use clear, concise language
- Include examples where helpful
- Add emoji for visual scanning (but don't overdo it)

## 🧪 Testing

Before submitting:

1. Test with different file types (Python, JavaScript, etc.)
2. Test with various PR sizes (small, medium, large)
3. Verify inline comments appear correctly
4. Check summary format is readable

## 🐛 Reporting Bugs

When reporting bugs, include:

1. **Description**: What happened vs. what you expected
2. **Steps to reproduce**: Exact steps to trigger the bug
3. **Environment**: OS, Python version, repository details
4. **Logs**: GitHub Actions logs or error messages
5. **Screenshots**: If applicable

Example:
```markdown
## Bug: AI review not posting comments

**Expected**: Comments appear on PR lines
**Actual**: No comments posted, only summary

**Steps**:
1. Created PR with 5 Python files
2. Workflow ran successfully
3. Summary posted but no inline comments

**Environment**: Ubuntu 22.04, Public repo, GPT-4o

**Logs**: [Paste relevant GitHub Actions logs]
```

## 💡 Feature Requests

When requesting features:

1. **Use case**: Describe why this would be useful
2. **Proposed solution**: How you envision it working
3. **Alternatives**: Other approaches you considered
4. **Impact**: Who would benefit?

## 🔍 Code Review Focus Areas

When reviewing code, pay attention to:

### For AI Reviewer Script
- **Accuracy**: Does it correctly identify issues?
- **Performance**: Is it efficient with API calls?
- **Error handling**: Does it gracefully handle failures?
- **Configurability**: Can users customize behavior?

### For GitHub Actions
- **Reliability**: Does it work consistently?
- **Security**: Are secrets handled properly?
- **Permissions**: Minimal required permissions?
- **Clarity**: Are steps well-documented?

## 🏗️ Architecture Decisions

### Current Design

```
GitHub Actions Workflow
    ↓
Python Script (ai_code_reviewer.py)
    ↓
OpenAI API (GPT-4/GPT-5)
    ↓
GitHub API (post comments)
```

When proposing changes:
- Consider backward compatibility
- Think about different repository types
- Account for rate limiting
- Plan for error scenarios

## 📚 Documentation Standards

- **README.md**: User-facing documentation
- **SETUP.md**: Quick start guide
- **CONTRIBUTING.md**: This file
- **Code comments**: Explain "why", not "what"
- **Docstrings**: Function purpose, params, returns

## 🎯 Priority Areas

Current focus areas for improvement:

1. **Multi-language support**: Better handling of different languages
2. **Performance**: Reduce API calls and execution time
3. **Cost optimization**: Minimize OpenAI API usage
4. **Customization**: More configuration options
5. **Testing**: Automated tests for the reviewer

## ⚖️ License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## 🤝 Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on the code, not the person
- Assume positive intent
- Give credit where due

## 📞 Questions?

- Open a GitHub issue for questions
- Tag issues appropriately (bug, enhancement, question)
- Be patient - this is maintained by volunteers

## 🙏 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- README acknowledgments section

---

Thank you for helping make code reviews better for everyone! 🚀

