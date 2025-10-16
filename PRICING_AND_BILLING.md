# 💰 AI Code Review - Pricing & Billing Guide

## How Charging Works - Complete Breakdown

### 🎯 The Simple Answer

**You pay OpenAI directly** for ChatGPT API usage. This tool just uses their API.

```
You → OpenAI (pay for API calls) → ChatGPT analyzes your code
```

**No subscription to this tool!** It's free and open source. You only pay OpenAI for the AI.

---

## 💳 Billing Process

### Step 1: You Add Credits to OpenAI Account

```
1. Go to: https://platform.openai.com/account/billing
2. Add payment method (credit/debit card)
3. Add credits: $10, $20, $50, etc.
4. OpenAI charges you as credits are used
```

### Step 2: Tool Uses Your API Key

```
When PR is created:
  ↓
GitHub Actions runs your AI review script
  ↓
Script calls OpenAI API with YOUR API key
  ↓
OpenAI processes the request
  ↓
OpenAI deducts cost from YOUR account
  ↓
You get charged (automatically)
```

### Step 3: You Receive Invoice

```
OpenAI bills you monthly for:
  - Number of tokens used
  - Model used (GPT-4, GPT-3.5, etc.)
  - Total API calls made
```

---

## 📊 What Exactly Gets Charged?

### Pricing Model: Pay-Per-Token

OpenAI charges based on **tokens** (roughly 4 characters = 1 token)

#### Current OpenAI Pricing (as of 2024):

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| **GPT-4 Turbo (gpt-4o)** | $0.01 | $0.03 |
| GPT-4 | $0.03 | $0.06 |
| GPT-3.5 Turbo | $0.0005 | $0.0015 |
| GPT-5 (when available) | TBD | TBD |

**Your tool uses:** GPT-4 Turbo (`gpt-4o`) by default

---

## 🔢 Cost Calculation

### Per Pull Request Breakdown

#### Small PR (1-3 files, ~200 lines changed)

```
Input Tokens:
  - Code diff: ~1,000 tokens
  - Full file context: ~2,000 tokens
  - Prompt instructions: ~500 tokens
  ─────────────────────────────────────
  Total Input: ~3,500 tokens

Output Tokens:
  - AI review response: ~1,500 tokens
  ─────────────────────────────────────
  Total Output: ~1,500 tokens

Cost Calculation:
  Input:  3.5K tokens × $0.01 = $0.035
  Output: 1.5K tokens × $0.03 = $0.045
  ─────────────────────────────────────
  Total Per PR: ~$0.08
```

#### Medium PR (5-10 files, ~500 lines changed)

```
Input Tokens:  ~8,000 tokens
Output Tokens: ~3,000 tokens

Cost:
  Input:  8K × $0.01  = $0.08
  Output: 3K × $0.03  = $0.09
  ─────────────────────────────────────
  Total Per PR: ~$0.17
```

#### Large PR (15+ files, ~1000 lines changed)

```
Input Tokens:  ~15,000 tokens
Output Tokens: ~5,000 tokens

Cost:
  Input:  15K × $0.01 = $0.15
  Output: 5K × $0.03  = $0.15
  ─────────────────────────────────────
  Total Per PR: ~$0.30
```

---

## 📅 Monthly Cost Estimates

### Team Size & Activity Based

#### Small Startup (5 developers)
```
PRs per day: 5-10
PRs per month: ~200

Average PR cost: $0.10

Monthly Total: 200 × $0.10 = $20/month
```

#### Medium Team (15 developers)
```
PRs per day: 15-25
PRs per month: ~500

Average PR cost: $0.12

Monthly Total: 500 × $0.12 = $60/month
```

#### Large Team (50 developers)
```
PRs per day: 40-60
PRs per month: ~1,200

Average PR cost: $0.15

Monthly Total: 1,200 × $0.15 = $180/month
```

#### Enterprise (100+ developers)
```
PRs per day: 100-150
PRs per month: ~3,000

Average PR cost: $0.15

Monthly Total: 3,000 × $0.15 = $450/month
```

---

## 💡 What Affects the Cost?

### Factors That Increase Cost:

1. **File Size**
   - Larger files = more tokens
   - More context to analyze

2. **Number of Files**
   - Each file gets reviewed separately
   - More files = more API calls

3. **PR Frequency**
   - More PRs = more reviews = higher cost

4. **Model Choice**
   - GPT-4 Turbo: More expensive, better quality
   - GPT-3.5 Turbo: Cheaper, decent quality

5. **Detailed Responses**
   - More detailed AI responses = more output tokens
   - Can adjust verbosity in prompt

### Factors That DON'T Affect Cost:

❌ Number of developers  
❌ Number of repositories  
❌ GitHub Actions runtime  
❌ Number of comments posted  
❌ Programming language used  

---

## 🎚️ Cost Control Strategies

### Strategy 1: Set Usage Limits on OpenAI

```
OpenAI Dashboard → Usage Limits
  ├── Hard Limit: $50/month (auto-stop)
  ├── Soft Limit: $30/month (email alert)
  └── Billing Alerts: Daily/Weekly
```

### Strategy 2: Skip Certain Files

Edit `.github/scripts/ai_code_reviewer.py`:

```python
skip_patterns = [
    'package-lock.json',  # Don't review lock files
    'dist/',              # Don't review build files
    'vendor/',            # Don't review dependencies
    '*.min.js',           # Don't review minified files
    'test/',              # Skip test files (optional)
]
```

**Savings:** ~30-50% reduction in costs

### Strategy 3: Limit File Size

```python
# In ai_code_reviewer.py
MAX_FILE_SIZE = 5000  # Only review files < 5000 lines

if len(file_content.split('\n')) > MAX_FILE_SIZE:
    print(f"Skipping large file: {filename}")
    continue
```

**Savings:** ~20-40% reduction

### Strategy 4: Review Only Changed Lines

Instead of sending full file, send only the diff:

```python
# Current: Sends full file
file_content = read_file(filename)  # 10,000 tokens

# Optimized: Send only changes
file_diff = get_diff_only(filename)  # 500 tokens
```

**Savings:** ~60-80% reduction!

### Strategy 5: Use GPT-3.5 Turbo (Cheaper Model)

Edit `ai_code_reviewer.py` line 158:

```python
# Change from:
model="gpt-4o",  # $0.01 per 1K tokens

# To:
model="gpt-3.5-turbo",  # $0.0005 per 1K tokens (20x cheaper!)
```

**Savings:** ~90% cost reduction (but lower quality)

### Strategy 6: Batch Reviews

Review multiple files in one API call:

```python
# Instead of: 1 API call per file
for file in files:
    review_file(file)  # 5 files = 5 API calls

# Do: 1 API call for all files
review_all_files(files)  # 5 files = 1 API call
```

**Savings:** ~40% reduction

---

## 📊 Cost Comparison

### Your Tool vs Alternatives

| Solution | Monthly Cost (Medium Team) | Setup Time | Quality |
|----------|---------------------------|------------|---------|
| **AI Code Review (GPT-4)** | **$60** | 5 min | ⭐⭐⭐⭐⭐ |
| AI Code Review (GPT-3.5) | $3-5 | 5 min | ⭐⭐⭐⭐ |
| SonarQube Community | Free | 60 min | ⭐⭐⭐ |
| SonarQube Developer | $150+ | 60 min | ⭐⭐⭐⭐ |
| GitHub Copilot | $10/user | Instant | ⭐⭐⭐ |
| Senior Dev (30 min/PR) | ~$2000 | N/A | ⭐⭐⭐⭐⭐ |

**ROI Analysis:**
```
Senior Dev Time Saved: 30 min/PR × $100/hr = $50/PR
AI Cost: $0.10/PR

Savings Per PR: $49.90
Monthly Savings (500 PRs): $24,950

Cost: $60/month
ROI: 416x return on investment! 🚀
```

---

## 🧾 Real Invoice Example

### What Your OpenAI Invoice Looks Like

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OpenAI Invoice - November 2024
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Account: your-email@company.com
Billing Period: Nov 1 - Nov 30, 2024

Usage Summary:
─────────────────────────────────────────────
Model: GPT-4 Turbo (gpt-4o)

Input Tokens:  1,250,000 tokens
  @ $0.01 per 1K tokens         $12.50

Output Tokens: 450,000 tokens
  @ $0.03 per 1K tokens         $13.50

─────────────────────────────────────────────
Subtotal:                       $26.00
Tax (if applicable):            $2.34
─────────────────────────────────────────────
Total Amount Due:               $28.34
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Payment Method: Visa ending in 1234
Status: Paid
Date: Dec 1, 2024
```

---

## 🔍 How to Monitor Costs

### OpenAI Dashboard

1. **Login:** https://platform.openai.com/
2. **Go to:** Usage section
3. **View:**
   - Daily usage
   - Token counts
   - Cost breakdown
   - Current month spending

### Check Usage in Real-Time

```bash
# Get usage via OpenAI API
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Set Up Alerts

```
OpenAI → Settings → Billing → Usage Limits

Set alerts at:
  - $10 (10% warning)
  - $25 (25% warning)
  - $40 (40% warning)
  - $50 (Hard limit - stops)
```

---

## ⚠️ Cost Gotchas & Tips

### Common Mistakes That Increase Costs:

❌ **Reviewing generated files**
```python
# Don't review: package-lock.json, yarn.lock
# These are huge and auto-generated
```

❌ **No file size limits**
```python
# Add max file size check
if file_size > 10000:  # Skip files > 10K lines
    skip_file()
```

❌ **Reviewing every commit**
```yaml
# Don't trigger on every commit
# Only on PR events
on:
  pull_request:  # ✅ Good
  # push:        # ❌ Too frequent
```

❌ **Using wrong model**
```python
# Don't use expensive models unnecessarily
model="gpt-4"  # ❌ $0.03/1K (expensive)
model="gpt-4o"  # ✅ $0.01/1K (better value)
```

### Pro Tips to Save Money:

✅ **Exclude test files** (if not critical)
✅ **Skip documentation changes** (*.md files)
✅ **Review only changed functions** (not entire files)
✅ **Use GPT-3.5 for simple PRs** (detect complexity first)
✅ **Batch similar files** (reduce API calls)
✅ **Cache common issues** (avoid re-analyzing same patterns)

---

## 🎯 Recommended Budget

### Starting Out (First Month)

```
Start with: $10 credit on OpenAI
Expected usage: $5-20
Cushion: Safe to start

Monitor first month, then adjust.
```

### Ongoing (After First Month)

| Team Size | Recommended Monthly Budget |
|-----------|---------------------------|
| 1-5 devs | $20 |
| 6-15 devs | $50 |
| 16-30 devs | $100 |
| 31-50 devs | $150 |
| 51-100 devs | $300 |
| 100+ devs | $500+ |

---

## 🔒 Billing Security

### Protecting Your API Key

1. **Never commit API key to code**
2. **Use GitHub Secrets only**
3. **Rotate keys every 3-6 months**
4. **Set usage limits**
5. **Monitor for unusual activity**

### If Your Key is Compromised:

```
1. Immediately revoke the key on OpenAI
2. Generate new key
3. Update GitHub Secret
4. Check usage logs for unauthorized calls
5. Contact OpenAI support if needed
```

---

## 📈 Scaling Costs

### As Your Team Grows

| Team Growth | Monthly Cost | Notes |
|-------------|--------------|-------|
| **Month 1 (5 devs)** | $15 | Learning phase |
| **Month 6 (10 devs)** | $35 | Regular usage |
| **Month 12 (20 devs)** | $70 | Optimized patterns |
| **Month 24 (50 devs)** | $150 | Mature usage |

**Cost per developer decreases over time** as you optimize!

---

## 💰 Total Cost of Ownership (TCO)

### Year 1 Complete Breakdown

```
Setup Costs:
  ├── Time to setup: 0.5 hour × $0 = $0
  ├── Infrastructure: $0 (uses GitHub Actions)
  └── Training: 1 hour × $0 = $0
      Total Setup: $0

Monthly Costs (Average team - 15 devs):
  ├── OpenAI API: $60
  ├── GitHub Actions: $0 (free tier sufficient)
  └── Maintenance: 0 hours × $0 = $0
      Total Monthly: $60

Annual Costs:
  ├── Setup: $0
  ├── Monthly: $60 × 12 = $720
  └── Unexpected: $80
      Total Annual: $800

Per Developer Cost:
  $800 ÷ 15 devs = $53/dev/year = $4.40/dev/month
```

**Compared to hiring a code reviewer:**
- Junior dev salary: $60K/year
- Your tool cost: $800/year
- **Savings: $59,200/year** 🎉

---

## ✅ Summary

### How You Get Charged:

1. ✅ **Pay OpenAI directly** for API usage
2. ✅ **Pay per token** (text processed)
3. ✅ **Charged monthly** via credit card
4. ✅ **Auto-deducted** from prepaid credits
5. ✅ **No subscription** to this tool (it's free!)

### Typical Costs:

- **Per PR:** $0.08 - $0.30
- **Per Month (small team):** $15 - $30
- **Per Month (medium team):** $50 - $100
- **Per Developer:** $3 - $10/month

### Control Costs By:

1. Setting usage limits on OpenAI
2. Skipping large/generated files
3. Using GPT-3.5 for simple PRs
4. Reviewing only changed code
5. Monitoring usage weekly

---

## 🎓 Getting Started with Billing

### Quick Start Checklist:

- [ ] Create OpenAI account
- [ ] Add payment method
- [ ] Add $10 initial credit
- [ ] Set $50 hard limit
- [ ] Set $25 alert limit
- [ ] Get API key
- [ ] Add to GitHub Secrets
- [ ] Create first PR
- [ ] Monitor usage after 1 week
- [ ] Adjust limits as needed

---

**Questions about billing?** Check your OpenAI dashboard or contact OpenAI support!

**Want to optimize costs further?** See the cost control strategies above! 💡

