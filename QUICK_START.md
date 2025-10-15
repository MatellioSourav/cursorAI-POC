# ⚡ Quick Start - ChatGPT Integration in 10 Minutes

## 🎯 Goal
Get AI-powered code reviews working on your GitHub repository using ChatGPT.

---

## 📋 Checklist (Follow in Order)

### ☐ Step 1: Get OpenAI API Key (3 min)
1. Visit: https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-...`)
4. **Save it temporarily** - you'll need it in Step 3

### ☐ Step 2: Add Billing to OpenAI (2 min)
1. Visit: https://platform.openai.com/account/billing
2. Add payment method
3. Add $10 in credits
4. Set usage limit: $20/month

### ☐ Step 3: Add Key to GitHub (1 min)
1. Go to your repo: **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"**
3. Name: `OPENAI_API_KEY`
4. Value: [paste your key from Step 1]
5. Click **"Add secret"**

### ☐ Step 4: Enable Permissions (1 min)
1. Still in Settings: **Actions** → **General**
2. Scroll to "Workflow permissions"
3. Select: ✅ **"Read and write permissions"**
4. Check: ✅ **"Allow GitHub Actions to create and approve pull requests"**
5. Click **"Save"**

### ☐ Step 5: Push Code (1 min)
```bash
git add .
git commit -m "🤖 Add AI code review"
git push origin main
```

### ☐ Step 6: Test It! (2 min)
```bash
# Create test branch
git checkout -b test-ai

# Add the example file
git add example_test.py
git commit -m "Test AI review"
git push origin test-ai
```

Then create a PR on GitHub and watch the magic! ✨

---

## 🎉 Success Indicators

Within 2 minutes of creating a PR, you should see:

✅ GitHub Actions workflow running (yellow dot, then green check)  
✅ AI bot posts inline comments on code issues  
✅ AI bot posts a summary comment with all findings  

---

## 🚨 If Something's Wrong

| Problem | Quick Fix |
|---------|-----------|
| "API key not found" | Check Step 3 - verify secret name is exactly `OPENAI_API_KEY` |
| "Insufficient quota" | Add credits in OpenAI billing (Step 2) |
| "Permission denied" | Check Step 4 - enable write permissions |
| Workflow not running | PR must target `main` or `develop` branch |

---

## 📖 Full Documentation

- **Complete Guide**: [README.md](README.md)
- **Detailed Integration**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **For Team Leads**: [TEAM_LEAD_GUIDE.md](TEAM_LEAD_GUIDE.md)

---

## 💰 Pricing Estimate

- **Per PR**: $0.01 - $0.20
- **Per Month**: $5 - $40 (depending on team size)
- **Time Saved**: 40-60% reduction in review time

---

**Ready? Let's go! Start with Step 1 above.** 🚀

