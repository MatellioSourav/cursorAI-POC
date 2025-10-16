#!/bin/bash

##############################################################################
# Universal AI Code Review Installation Script
# Works with: Java, Node.js, React, PHP, Python, Go, Ruby, and ANY language!
##############################################################################

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
cat << "EOF"
   ___   ____   ______          __         ____             _               
  / _ | /  _/  / ____/__  ___  / /__      / __ \ ___  _  __(_)__ _      __
 / __ |_/ /   / /   / _ \/ _ / / -_)    / /_/ // -_)| |/ // // -_) \^/ / /
/_/ |_/___/  /_/    \___/\_,_/\__/     /_/ /_/ \__/ |___//_/ \__/\_^_/  
                                                                          
    Universal AI Code Review Tool - Powered by ChatGPT
EOF
echo -e "${NC}"

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  Works with ANY programming language!${NC}"
echo -e "${GREEN}  Java | Node | React | PHP | Python | Go | Ruby${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if running in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not a git repository${NC}"
    echo "   Please run this script from your project root (where .git folder is)"
    echo ""
    echo "   Or initialize git first:"
    echo "   ${YELLOW}git init${NC}"
    exit 1
fi

# Detect repository language(s)
echo -e "${BLUE}🔍 Detecting project language(s)...${NC}"

languages=""
[ -f "pom.xml" ] || [ -f "build.gradle" ] && languages="$languages Java"
[ -f "package.json" ] && languages="$languages Node.js/JavaScript"
[ -f "composer.json" ] && languages="$languages PHP"
[ -f "requirements.txt" ] || [ -f "setup.py" ] && languages="$languages Python"
[ -f "go.mod" ] && languages="$languages Go"
[ -f "Gemfile" ] && languages="$languages Ruby"
[ -f "Cargo.toml" ] && languages="$languages Rust"
[ -f "*.csproj" ] 2>/dev/null && languages="$languages C#"

if [ -z "$languages" ]; then
    echo -e "   ${YELLOW}⚠️  Could not auto-detect language${NC}"
    echo "   That's OK! The AI review works with ANY language."
    languages="Auto-detected from file extensions"
fi

echo -e "   ${GREEN}✓${NC} Detected: $languages"
echo ""

# Check if .github folder already exists
if [ -d ".github/workflows" ]; then
    echo -e "${YELLOW}⚠️  Warning: .github/workflows already exists${NC}"
    read -p "   Do you want to continue? This may overwrite existing workflows. (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Installation cancelled."
        exit 0
    fi
fi

# Download or copy the AI review system
echo -e "${BLUE}📥 Installing AI Code Review system...${NC}"

# Check if cursorAI-POC folder exists (local installation)
if [ -d "../cursorAI-POC/.github" ]; then
    echo "   Using local installation..."
    cp -r ../cursorAI-POC/.github ./
elif [ -d "./cursorAI-POC/.github" ]; then
    echo "   Using local installation..."
    cp -r ./cursorAI-POC/.github ./
else
    # Download from GitHub
    echo "   Downloading from GitHub..."
    TEMP_DIR=$(mktemp -d)
    
    if command -v wget &> /dev/null; then
        wget -q https://github.com/MatellioSourav/cursorAI-POC/archive/refs/heads/main.zip -O "$TEMP_DIR/ai-review.zip"
    elif command -v curl &> /dev/null; then
        curl -sL https://github.com/MatellioSourav/cursorAI-POC/archive/refs/heads/main.zip -o "$TEMP_DIR/ai-review.zip"
    else
        echo -e "${RED}❌ Error: Neither wget nor curl found${NC}"
        echo "   Please install wget or curl, or manually copy .github folder"
        exit 1
    fi
    
    unzip -q "$TEMP_DIR/ai-review.zip" -d "$TEMP_DIR"
    cp -r "$TEMP_DIR/cursorAI-POC-main/.github" ./
    rm -rf "$TEMP_DIR"
fi

if [ -d ".github/workflows/ai-code-review.yml" ]; then
    echo -e "   ${GREEN}✓${NC} AI Code Review workflow installed"
else
    echo -e "   ${RED}✗${NC} Installation failed"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get repository info
REPO_URL=$(git config --get remote.origin.url | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//')

if [ -z "$REPO_URL" ]; then
    REPO_URL="your-github-repo"
fi

echo -e "${YELLOW}📋 NEXT STEPS:${NC}"
echo ""
echo -e "${BLUE}1️⃣  Get OpenAI API Key${NC}"
echo "   → Visit: https://platform.openai.com/api-keys"
echo "   → Click 'Create new secret key'"
echo "   → Copy the key (starts with sk-proj-...)"
echo ""

echo -e "${BLUE}2️⃣  Add API Key to GitHub Secrets${NC}"
echo "   → Visit: $REPO_URL/settings/secrets/actions"
echo "   → Click 'New repository secret'"
echo "   → Name: OPENAI_API_KEY"
echo "   → Value: [paste your key]"
echo ""

echo -e "${BLUE}3️⃣  Enable GitHub Actions Permissions${NC}"
echo "   → Visit: $REPO_URL/settings/actions"
echo "   → Select 'Read and write permissions'"
echo "   → Check 'Allow GitHub Actions to create and approve pull requests'"
echo "   → Click 'Save'"
echo ""

echo -e "${BLUE}4️⃣  Commit and Push${NC}"
echo "   ${YELLOW}git add .github/${NC}"
echo "   ${YELLOW}git commit -m '🤖 Add AI code review system'${NC}"
echo "   ${YELLOW}git push origin main${NC}"
echo ""

echo -e "${BLUE}5️⃣  Test It!${NC}"
echo "   → Create a new branch"
echo "   → Make any code change"
echo "   → Create a Pull Request"
echo "   → Watch ChatGPT review your code! 🎉"
echo ""

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}💡 What You Get:${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "   ✅ Automatic code review on every PR"
echo "   ✅ Security vulnerability detection"
echo "   ✅ Bug and performance issue identification"
echo "   ✅ Best practice suggestions"
echo "   ✅ Inline comments on problematic code"
echo "   ✅ Comprehensive review summaries"
echo "   ✅ 40-60% faster code reviews"
echo ""

echo -e "${BLUE}💰 Cost: ~\$5-40/month | ⏱️  Time Saved: 40-60%${NC}"
echo ""

echo -e "${YELLOW}📖 Documentation:${NC}"
echo "   • README: .github/README.md"
echo "   • Team Lead Guide: .github/TEAM_LEAD_GUIDE.md"
echo ""

echo -e "${GREEN}🚀 Ready to revolutionize your code review process!${NC}"
echo ""

