# 📂 File Structure & Branch Strategy Guide

## Where Files Live - Complete Explanation

### 🏠 Two Separate Repositories

#### Repository A: Your AI Code Review Tool (This Repo)
```
github.com/MatellioSourav/cursorAI-POC/

├── install.sh                          ← Universal installer script
├── README.md                           ← Tool documentation
├── UNIVERSAL_INTEGRATION.md            ← Integration guide
├── TEAM_LEAD_GUIDE.md                  ← For team leads
├── QUICK_START.md                      ← Quick reference
├── example_test.py                     ← Demo files
├── api_handler.py                      ← Demo files
├── data_validator.js                   ← Demo files
└── .github/                            ← THE CORE SYSTEM (gets copied)
    ├── workflows/
    │   └── ai-code-review.yml         ← GitHub Actions workflow
    ├── scripts/
    │   ├── ai_code_reviewer.py        ← Main AI review logic
    │   ├── requirements.txt            ← Python dependencies
    │   └── test_reviewer.py            ← Testing script
    └── config/
        └── review-config.json          ← Configuration settings
```

**This repo is PUBLIC** - Users download/clone it to get the AI review system.

---

#### Repository B: User's Project (Any Language)
```
github.com/username/their-java-app/    (or Node/PHP/Python/etc)

AFTER running install.sh:

├── .github/                            ← COPIED from your tool
│   ├── workflows/
│   │   └── ai-code-review.yml         ← Reviews their code now
│   ├── scripts/
│   │   ├── ai_code_reviewer.py
│   │   └── requirements.txt
│   └── config/
│       └── review-config.json
├── src/                                ← Their actual code
├── pom.xml                             ← Their Java project
└── ...                                 ← Their other files
```

---

## 🌿 Branch Strategy

### In Your Tool Repository (cursorAI-POC)

```
main                                    ← Stable release
  ├── install.sh (v1.0)
  └── .github/ (stable version)

develop                                 ← Active development
  ├── install.sh (v1.1-beta)
  └── .github/ (new features)

feature/gpt5-support                    ← New features
feature/custom-rules                    ← New features
```

**Users download from:** `main` branch (stable)

---

### In User's Project Repository

```
main branch (production)
  ├── .github/                          ← AI review system installed
  │   └── workflows/ai-code-review.yml  ← Active on PRs to main
  └── src/                              ← Their code

develop branch
  ├── .github/                          ← Same AI review system
  │   └── workflows/ai-code-review.yml  ← Active on PRs to develop
  └── src/                              ← Their code

feature/add-login
  ├── .github/                          ← Inherited from main/develop
  │   └── workflows/ai-code-review.yml  ← Active when PR created
  └── src/LoginController.java          ← Their new code
      ↑
      When they create PR: main ← feature/add-login
      AI automatically reviews LoginController.java!

feature/fix-bug-123
  ├── .github/                          ← Inherited from main
  └── src/BugFix.java                   ← Their fix
      ↑
      When PR created: AI reviews automatically!
```

---

## 🔄 Complete Installation Flow

### Step-by-Step: What Happens

#### 1. User Discovers Your Tool
```bash
# They find your GitHub repo
https://github.com/MatellioSourav/cursorAI-POC
```

#### 2. User Runs Installer in Their Project
```bash
# In their Java/Node/PHP project
cd ~/projects/my-java-app

# Download and run your install.sh
curl -sSL https://raw.githubusercontent.com/MatellioSourav/cursorAI-POC/main/install.sh | bash
```

#### 3. Install Script Copies Files
```bash
# Copies from YOUR repo → THEIR project
cursorAI-POC/.github/  →  my-java-app/.github/
```

#### 4. User Commits to Main Branch
```bash
cd ~/projects/my-java-app
git add .github/
git commit -m "Add AI code review"
git push origin main
```

**Result:** `.github/` is now in their main branch

#### 5. User Creates Feature Branch
```bash
git checkout -b feature/new-api
# .github/ folder automatically exists (inherited from main)
# Makes code changes
git add src/NewAPI.java
git commit -m "Add new API endpoint"
git push origin feature/new-api
```

#### 6. User Creates Pull Request
```
GitHub: Create PR
  Base: main ← Compare: feature/new-api
```

#### 7. AI Review Triggers
```
GitHub Actions reads: .github/workflows/ai-code-review.yml
  ↓
Runs: .github/scripts/ai_code_reviewer.py
  ↓
Analyzes: src/NewAPI.java (the changes)
  ↓
Posts: AI review comments on PR
```

---

## 📍 Key Points

### ✅ `install.sh` Location
- **Lives in:** Your tool repository (cursorAI-POC)
- **Not copied** to user's project
- **Used once** during installation
- **Users access via:** Direct download or clone

### ✅ `.github/` Location
- **Lives in:** User's project repository
- **Installed once** on main branch
- **Inherited** by all feature branches automatically
- **Active on:** Every pull request

---

## 🎯 Real-World Example

### Your Tool Repo (MatellioSourav/cursorAI-POC)
```
Branches:
  • main          ← install.sh (stable) ← Users download this
  • develop       ← New features being tested
  • feature/*     ← Experimental features

Users interact with this repo by:
  1. Downloading install.sh
  2. OR cloning the entire repo
  3. Then running install.sh in THEIR project
```

### User's Project (acme-corp/ecommerce-platform)
```
Branches BEFORE installation:
  • main
    ├── src/
    ├── pom.xml
    └── README.md

Branches AFTER running install.sh:
  • main
    ├── .github/          ← NEW! AI review system
    ├── src/
    ├── pom.xml
    └── README.md

  • feature/add-payment   ← Inherits .github/ from main
  • feature/fix-checkout  ← Inherits .github/ from main
  • develop               ← Inherits .github/ from main

ALL branches now have AI review active!
```

---

## 🚀 Distribution Strategy

### Option 1: GitHub Template Repository
Make cursorAI-POC a template:
- Users click "Use this template"
- Get a copy with .github/ folder
- Merge it into their project

### Option 2: Direct Download (Recommended)
```bash
# Users run one command
curl -sSL https://raw.githubusercontent.com/MatellioSourav/cursorAI-POC/main/install.sh | bash
```

### Option 3: Manual Copy
```bash
# Users clone and copy manually
git clone https://github.com/MatellioSourav/cursorAI-POC.git
cp -r cursorAI-POC/.github my-project/
```

---

## 🔧 Updating the AI Review System

### If You Release Updates (v2.0)

Users can update by:

```bash
# In their project, remove old version
rm -rf .github/workflows/ai-code-review.yml
rm -rf .github/scripts/ai_code_reviewer.py

# Re-run installer (gets latest)
curl -sSL https://raw.githubusercontent.com/MatellioSourav/cursorAI-POC/main/install.sh | bash

# Commit update
git add .github/
git commit -m "Update AI review to v2.0"
git push
```

Or provide an update script:
```bash
# update-ai-review.sh
curl -sSL https://raw.githubusercontent.com/MatellioSourav/cursorAI-POC/main/install.sh | bash
```

---

## 📊 Summary

| File/Folder | Your Tool Repo | User's Project | In Branches |
|-------------|---------------|----------------|-------------|
| `install.sh` | ✅ Lives here | ❌ Not copied | ❌ Not needed |
| `.github/workflows/` | ✅ Source | ✅ Copied once | ✅ Inherited |
| `.github/scripts/` | ✅ Source | ✅ Copied once | ✅ Inherited |
| `.github/config/` | ✅ Source | ✅ Copied once | ✅ Inherited |
| Documentation | ✅ Lives here | ⚠️ Optional | ⚠️ Optional |
| User's code | ❌ | ✅ Lives here | ✅ Lives here |

---

## 💡 Best Practices

### For Your Tool Repository:
1. Keep `install.sh` on main branch only
2. Version your releases (v1.0, v1.1, v2.0)
3. Maintain CHANGELOG.md
4. Tag stable releases
5. Keep main branch stable, use develop for new features

### For User's Projects:
1. Install .github/ on main branch first
2. Push to main before creating feature branches
3. Feature branches automatically inherit .github/
4. AI review works on all PRs automatically
5. Update periodically by re-running install.sh

---

## ✅ Quick Reference

**Your Tool:**
- Repository: github.com/MatellioSourav/cursorAI-POC
- Contains: install.sh + .github/ + docs
- Users: Download install.sh only

**User's Project:**
- Gets: .github/ folder only (copied)
- Location: Project root, all branches
- Active: On every pull request

**install.sh:**
- Location: Your repo only
- Purpose: One-time installer
- Not needed: After installation

---

**Think of it like npm or composer:**
- Your tool repo = npm registry (source of packages)
- install.sh = npm install command
- .github/ = node_modules (installed dependency)
- User's project = app using the dependency

🎉 **Simple, reusable, universal!**

