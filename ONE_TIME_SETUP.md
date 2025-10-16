# ⚡ One-Time Setup Guide - Automate Everything!

## 🎯 Goal: Commit Once, Automated Forever!

After this one-time setup, **every pull request will automatically get AI review** - no manual action needed!

---

## 📋 Complete Checklist

### ✅ Step 1: Copy Files to Your Repository (One Time)

You need to commit **only ONE folder** to your repo:

```bash
# Navigate to your project
cd /path/to/your/project

# Copy the .github folder from this tool repo
cp -r /path/to/cursorAI-POC/.github ./

# That's it! This is the only folder you need.
```

**What you're copying:**
```
your-project/
  └── .github/                          ← COMMIT THIS
      ├── workflows/
      │   └── ai-code-review.yml       ← GitHub Actions workflow
      ├── scripts/
      │   ├── ai_code_reviewer.py      ← AI review logic
      │   ├── requirements.txt          ← Dependencies
      │   └── test_reviewer.py          ← Optional testing
      └── config/
          └── review-config.json        ← Configuration
```

---

## 📝 Step-by-Step: Commit Once

### 1. Copy the .github Folder

```bash
# If you have the cursorAI-POC repo locally:
cd ~/my-java-app                # Your actual project
cp -r ~/cursorAI-POC/.github ./

# OR download directly:
curl -sL https://github.com/MatellioSourav/cursorAI-POC/archive/main.zip -o ai-review.zip
unzip ai-review.zip
cp -r cursorAI-POC-main/.github ./
rm -rf cursorAI-POC-main ai-review.zip
```

### 2. Commit to Your Repository

```bash
# Add the .github folder
git add .github/

# Commit it
git commit -m "🤖 Add AI code review automation"

# Push to main branch
git push origin main
```

**That's the ONE commit!** ✅

---

## 🔑 Step 2: Add OpenAI API Key (One Time in GitHub)

This is done **on GitHub website**, not in code:

### A. Get OpenAI API Key

1. Go to: https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Copy the key (starts with `sk-proj-...`)

### B. Add to GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** (top navigation)
3. In sidebar: **Secrets and variables** → **Actions**
4. Click **"New repository secret"**
5. Fill in:
   - **Name:** `OPENAI_API_KEY` (exact name, all caps)
   - **Secret:** Paste your OpenAI API key
6. Click **"Add secret"**

**Screenshot guide:**
```
https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions
                                          ↑
                                    Go here
```

---

## ⚙️ Step 3: Enable GitHub Actions (One Time)

Still on GitHub website:

1. Go to **Settings** → **Actions** → **General** (left sidebar)
2. Scroll to **"Workflow permissions"**
3. Select: ✅ **"Read and write permissions"**
4. Check: ✅ **"Allow GitHub Actions to create and approve pull requests"**
5. Click **"Save"**

---

## 🎉 DONE! Everything is Now Automated

After these 3 one-time steps, **everything happens automatically:**

```
From now on, whenever ANYONE creates a PR:
  ↓
GitHub Actions automatically triggers
  ↓
AI analyzes the code changes
  ↓
AI posts review comments on the PR
  ↓
NO manual action needed! ✨
```

---

## 🔄 What Happens Automatically After Setup

### Scenario 1: Developer Creates Feature Branch

```bash
# Developer's workflow (they don't do anything special!)
git checkout -b feature/new-login
# ... make changes to LoginController.java
git add .
git commit -m "Add new login feature"
git push origin feature/new-login
```

### On GitHub: Create Pull Request

```
Developer clicks: "Create Pull Request"
  Base: main ← Compare: feature/new-login

Automatically happens:
  1. ✅ GitHub detects PR created
  2. ✅ GitHub Actions workflow triggers
  3. ✅ Runs ai-code-review.yml
  4. ✅ Python script analyzes code
  5. ✅ Calls OpenAI API
  6. ✅ ChatGPT reviews the code
  7. ✅ AI posts comments on PR
  8. ✅ Team lead sees AI review

Developer does: NOTHING extra! 🎉
```

---

## 📂 Complete File Structure After Setup

### Your Repository Structure:

```
your-project/                        ← Your actual project
├── .github/                         ← Committed ONCE
│   ├── workflows/
│   │   └── ai-code-review.yml      ← Triggers on every PR
│   ├── scripts/
│   │   ├── ai_code_reviewer.py     ← Does the AI review
│   │   ├── requirements.txt
│   │   └── test_reviewer.py
│   └── config/
│       └── review-config.json      ← Settings (optional)
│
├── src/                             ← Your code
│   ├── main/
│   └── ...
│
├── pom.xml / package.json / etc     ← Your project files
└── README.md
```

### What's in Each Branch:

```
main branch:
  ├── .github/        ← Your one commit is here
  └── src/            ← Your code

feature/new-api:
  ├── .github/        ← Automatically inherited from main
  └── src/            ← Developer's changes
      └── NewAPI.java

feature/bug-fix:
  ├── .github/        ← Automatically inherited from main
  └── src/            ← Developer's changes
      └── BugFix.java
```

**Every branch automatically has `.github/` folder** because it's in main!

---

## 🎯 The ONE Commit Explained

### What You Committed:

```bash
git add .github/
git commit -m "🤖 Add AI code review automation"
git push
```

### What This Enables:

✅ **Automatic trigger** - Runs on every PR  
✅ **Zero manual work** - No one does anything  
✅ **Works for all branches** - Every PR to main/develop  
✅ **Works for all developers** - Everyone gets reviews  
✅ **Works forever** - Until you remove it  

---

## 🔧 Optional: Customize Settings (Optional)

If you want to customize behavior, edit these files (after committing):

### 1. Change Review Focus

Edit `.github/config/review-config.json`:

```json
{
  "review_categories": {
    "security": true,          ← Keep
    "potential_bugs": true,    ← Keep
    "performance": false,      ← Disable if not needed
    "code_quality": true,
    "boilerplate_reduction": true
  }
}
```

### 2. Skip Certain File Types

Edit `.github/scripts/ai_code_reviewer.py` (line ~70):

```python
skip_patterns = [
    '.lock',
    'node_modules/',
    'vendor/',
    'test/',           # Add: Skip test files
    'docs/',           # Add: Skip documentation
]
```

### 3. Change Target Branches

Edit `.github/workflows/ai-code-review.yml` (line ~8):

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
      - staging      # Add more branches here
```

**Then commit changes:**
```bash
git add .github/
git commit -m "Customize AI review settings"
git push
```

---

## ✅ Verification: Check It's Working

### After Your One Commit:

1. **Check GitHub Actions is enabled:**
   - Go to: `https://github.com/YOUR_REPO/actions`
   - Should see: "AI Code Review" workflow

2. **Check Secret is added:**
   - Go to: Settings → Secrets → Actions
   - Should see: `OPENAI_API_KEY`

3. **Check Permissions:**
   - Go to: Settings → Actions → General
   - Should be: "Read and write permissions" ✅

---

## 🧪 Test It: Create Your First PR

### Quick Test:

```bash
# Create test branch
git checkout -b test-ai-review

# Make a simple change
echo "// Test comment" >> src/main/Test.java

# Commit and push
git add .
git commit -m "Test AI review"
git push origin test-ai-review
```

### On GitHub:

1. Create Pull Request: `main ← test-ai-review`
2. Wait 1-2 minutes
3. Check for:
   - ✅ GitHub Actions running (yellow/green check)
   - ✅ AI comments on the PR
   - ✅ AI summary comment

**If you see comments = IT'S WORKING! 🎉**

---

## 🎓 Developer Workflow (After Your Setup)

Your developers don't need to know anything! Their workflow stays the same:

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
vim src/MyCode.java

# 3. Commit
git add .
git commit -m "My changes"

# 4. Push
git push origin feature/my-feature

# 5. Create PR on GitHub

# 6. AI review appears automatically! ✨
#    (They don't do anything!)
```

---

## 📊 Summary: The One Commit

| What | Where | When |
|------|-------|------|
| **Copy** `.github/` folder | To your repo root | Once |
| **Commit** `.github/` folder | To main branch | Once |
| **Add** `OPENAI_API_KEY` | GitHub Secrets | Once |
| **Enable** Actions permissions | GitHub Settings | Once |
| **Total time** | 5 minutes | Once |
| **Future PRs** | Automatic! | Forever! |

---

## 🚀 Quick Start Commands

### The Complete One-Time Setup (Copy-Paste):

```bash
# 1. Navigate to your project
cd /path/to/your/project

# 2. Download and extract AI review system
curl -sL https://github.com/MatellioSourav/cursorAI-POC/archive/main.zip -o ai.zip
unzip -q ai.zip
cp -r cursorAI-POC-main/.github ./
rm -rf cursorAI-POC-main ai.zip

# 3. Commit it
git add .github/
git commit -m "🤖 Add AI code review automation"
git push origin main

echo "✅ Done! Now add OPENAI_API_KEY to GitHub Secrets"
echo "👉 Go to: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/settings/secrets/actions"
```

### Then on GitHub:

1. Add `OPENAI_API_KEY` secret
2. Enable Actions permissions
3. Create a test PR
4. Watch the magic! ✨

---

## ❓ FAQs

### Q: Do I commit the API key?
**A: NO! Never!** API key goes in GitHub Secrets only, never in code.

### Q: Do developers need to do anything?
**A: NO!** They just create PRs normally. AI review happens automatically.

### Q: What if I update the AI tool?
**A: Just copy `.github/` folder again and commit.**

### Q: Does it work on all branches?
**A: YES!** Any branch that creates a PR to main/develop gets reviewed.

### Q: What if I want to turn it off temporarily?
**A: Disable the workflow in `.github/workflows/ai-code-review.yml` (add `if: false`)**

### Q: Can I customize the review?
**A: YES!** Edit `.github/config/review-config.json` or the Python script.

---

## 🎉 Congratulations!

After your **one commit**, you have:

✅ **Automated code reviews** on every PR  
✅ **Zero manual work** for developers  
✅ **AI-powered** suggestions  
✅ **Works forever** until you remove it  
✅ **Saves hours** of review time  
✅ **Costs pennies** per PR  

**Your team will thank you!** 🙌

---

## 📞 Need Help?

If something doesn't work:

1. Check GitHub Actions logs: `/actions` tab
2. Verify API key is added: Settings → Secrets
3. Check permissions: Settings → Actions → General
4. See README.md for detailed troubleshooting

**Everything automated with just ONE commit!** 🚀

