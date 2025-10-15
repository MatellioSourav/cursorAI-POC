# Quick Setup Guide

## 🚀 5-Minute Setup

Follow these steps to get AI Code Review running on your repository:

### 1. Get Your OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the API key (you won't see it again!)
5. **Important**: Ensure you have billing set up and credits available

### 2. Add API Key to GitHub

1. Go to your repository: `https://github.com/YOUR_USERNAME/YOUR_REPO`
2. Click **Settings** (top navigation)
3. In left sidebar: **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Fill in:
   - **Name**: `OPENAI_API_KEY`
   - **Secret**: Paste your OpenAI API key
6. Click **Add secret**

### 3. Enable GitHub Actions Permissions

1. Still in Settings, go to **Actions** → **General** (left sidebar)
2. Scroll to **Workflow permissions**
3. Select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

### 4. Push This Code to Your Repository

```bash
# If you haven't already cloned your repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO

# Add and commit the AI review files
git add .
git commit -m "🤖 Add AI code review automation"
git push origin main
```

### 5. Test It!

Create a test pull request:

```bash
# Create a new branch
git checkout -b test-ai-review

# Make a simple change (create a test file)
echo "print('Hello, World!')" > test.py

# Commit and push
git add test.py
git commit -m "Test AI review"
git push origin test-ai-review
```

Then:
1. Go to your repository on GitHub
2. Click **Pull requests** → **New pull request**
3. Select `test-ai-review` branch
4. Click **Create pull request**
5. Wait 1-2 minutes...
6. See the AI review comments appear! 🎉

## ✅ Verification Checklist

- [ ] OpenAI API key added to GitHub Secrets
- [ ] GitHub Actions permissions set to Read/Write
- [ ] Files pushed to repository
- [ ] Workflow file exists at `.github/workflows/ai-code-review.yml`
- [ ] Python script exists at `.github/scripts/ai_code_reviewer.py`
- [ ] Test PR created and AI review appears

## 🎯 What to Expect

When you create a PR, you'll see:

1. **GitHub Actions check** runs (yellow dot → green check)
2. **Inline comments** on specific lines of code
3. **Summary comment** with overall assessment

## ⚙️ Customization (Optional)

### Change Target Branches

Edit `.github/workflows/ai-code-review.yml`:

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
      - staging  # Add more branches here
```

### Adjust Review Focus

Edit `.github/config/review-config.json` to enable/disable review categories:

```json
{
  "review_categories": {
    "code_quality": true,
    "potential_bugs": true,
    "security": true,
    "performance": false,  // Disable if not needed
    "boilerplate_reduction": true
  }
}
```

### Use GPT-5 (When Available)

When OpenAI releases GPT-5 API access, update the model in `.github/scripts/ai_code_reviewer.py`:

```python
response = self.client.chat.completions.create(
    model="gpt-5",  # Change from gpt-4o to gpt-5
    ...
)
```

Or update `.github/config/review-config.json`:
```json
{
  "model": "gpt-5"
}
```

## 💰 Cost Estimation

Approximate OpenAI API costs:

- **Small PR** (1-3 files, <500 lines): $0.01 - $0.05
- **Medium PR** (4-10 files, <2000 lines): $0.05 - $0.20
- **Large PR** (10+ files, >2000 lines): $0.20 - $1.00

**Tip**: Set up billing alerts in your OpenAI dashboard!

## 🔧 Troubleshooting

### "Error: OPENAI_API_KEY not found"
→ Make sure you added the secret correctly in GitHub Settings → Secrets

### "Permission denied" or "403 Forbidden"
→ Check GitHub Actions permissions are set to Read/Write

### "Workflow not running"
→ Ensure the PR targets `main` or `develop` branch

### AI comments not appearing
→ Check the Actions tab for error logs

### High costs
→ Reduce files reviewed by adding more skip patterns in config

## 📞 Need Help?

1. Check the main [README.md](README.md) for detailed documentation
2. Review [GitHub Actions logs](../../actions) for error messages
3. Verify your OpenAI API key is valid and has credits
4. Check OpenAI API status page

## 🎓 Next Steps

Once working:

1. **Educate your team** about the AI reviewer
2. **Customize prompts** to match your coding standards
3. **Monitor costs** in OpenAI dashboard
4. **Gather feedback** from team on usefulness
5. **Iterate and improve** the prompts and configuration

---

**Ready to save hours of code review time!** ⏱️✨

