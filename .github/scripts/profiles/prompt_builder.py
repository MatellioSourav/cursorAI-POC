#!/usr/bin/env python3
"""
Prompt Builder
Dynamically assembles AI prompts based on enabled review categories
"""

from typing import List, Dict, Optional
from profiles.config_loader import ConfigLoader
from rules.rule_registry import RuleRegistry


class PromptBuilder:
    """Builds AI prompts dynamically from enabled rule modules"""
    
    # Fixed baseline persona - NEVER changes
    BASELINE_PERSONA = """You are a senior code reviewer with 10+ years of experience acting as a Staff/Principal Engineer.

You must review code with deep expertise in:
- Software engineering best practices and clean code
- Security vulnerabilities (OWASP Top 10)
- Authorization and data access control
- Backend and frontend architecture
- API design, database optimization, and performance
- Async/concurrency, memory, and resource management
- Logging, observability, and error handling
- Testing strategies and production readiness

You must be strict, practical, and actionable.
Do not praise code. Focus only on issues, risks, and improvements."""
    
    # Fixed priority order - NEVER changes
    PRIORITY_ORDER = """## ⚠️ CRITICAL PRIORITY ORDER (STRICT)

If token limits are reached, you MUST prioritize issues in this exact order:

1. **HIGHEST PRIORITY**: JIRA/SRS requirement violations (missing acceptance criteria, out-of-scope changes)
2. **CRITICAL**: Security vulnerabilities (SQL injection, XSS, hardcoded secrets, PII exposure, command injection)
3. **CRITICAL**: Authorization & data access issues (missing auth checks, object-level access control violations)
4. **HIGH**: Critical bugs (data corruption, crashes, logic errors that break functionality)
5. **MEDIUM**: Performance issues with real impact (N+1 queries, unbounded loops, memory leaks)

**IMPORTANT RULES:**
- If approaching token limits, STOP and report only higher-priority issues (1-3)
- NEVER omit code references - they are mandatory for all issues
- NEVER downgrade severity due to token limits - maintain accurate severity levels
- ALWAYS return valid JSON - incomplete JSON is worse than fewer issues
- Code snippets take priority over verbose descriptions"""
    
    def __init__(self, config_loader: ConfigLoader, rule_registry: RuleRegistry):
        self.config_loader = config_loader
        self.rule_registry = rule_registry
    
    def build_prompt(self, file_diff, file_content: str, 
                    srs_context: str = "", jira_context: str = "") -> str:
        """
        Build complete AI prompt from:
        - Fixed baseline persona
        - Priority order
        - Enabled rule modules
        - Code context
        - Output schema
        """
        enabled_categories = self.config_loader.get_enabled_categories()
        strictness = self.config_loader.get_strictness()
        security_level = self.config_loader.get_security_level()
        custom_rules = self.config_loader.get_custom_rules()
        
        # Start with baseline persona
        prompt = f"{self.BASELINE_PERSONA}\n\n"
        
        # Add priority order
        prompt += f"{self.PRIORITY_ORDER}\n\n"
        
        # Add SRS context if available
        if srs_context:
            prompt += f"{srs_context}\n\n"
        
        # Add JIRA context if available
        if jira_context:
            prompt += f"{jira_context}\n\n"
        
        # Add code changes context
        # Get list of all changed files for scope check (if available)
        changed_files = getattr(file_diff, '_all_file_diffs', [])
        total_additions = sum(fd.additions for fd in changed_files) if changed_files else 0
        total_deletions = sum(fd.deletions for fd in changed_files) if changed_files else 0
        total_changes = total_additions + total_deletions
        
        # PR size warning
        pr_size_warning = ""
        if len(changed_files) > 10 or total_changes > 500:
            pr_size_warning = "\n⚠️ **PR SIZE WARNING**: This PR is large. Consider breaking it into smaller, focused PRs for easier review."
        
        prompt += f"""## CODE CHANGES

**File:** {file_diff.filename}
**Status:** {file_diff.status}
**Changes:** +{file_diff.additions} -{file_diff.deletions}

**All Changed Files in PR:** ({len(changed_files) if changed_files else 1} files)
{chr(10).join(f"- {f}" for f in changed_files) if changed_files else f"- {file_diff.filename}"}

**PR Size Analysis:**
- Total files changed: {len(changed_files) if changed_files else 1}
- Total lines added: {total_additions}
- Total lines deleted: {total_deletions}
- Total changes: {total_changes} lines{pr_size_warning}

**DIFF:**
{file_diff.patch}

**FULL FILE CONTENT:**
{file_content[:8000]}

## REVIEW REQUIREMENTS

**Configuration:**
- Strictness Level: {strictness}
- Security Level: {security_level}
- Enabled Categories: {len(enabled_categories)} category(ies)

"""
        
        # Inject enabled rule modules dynamically
        prompt += "**REVIEW CATEGORIES (Enabled):**\n\n"
        
        for category in enabled_categories:
            rule_content = self.rule_registry.get_rule(category)
            if rule_content:
                prompt += f"{rule_content}\n\n"
            else:
                print(f"⚠️  Rule module not found for category: {category}")
        
        # Add custom project rules if any
        if custom_rules:
            prompt += "**CUSTOM PROJECT RULES:**\n\n"
            for rule in custom_rules:
                prompt += f"- {rule.get('description', '')}\n"
                if rule.get('checks'):
                    for check in rule['checks']:
                        prompt += f"  * {check}\n"
            prompt += "\n"
        
        # Add JIRA-specific requirements if JIRA context is available
        if jira_context:
            prompt += self._build_jira_requirements()
        
        # Add SRS-specific requirements if SRS context is available
        if srs_context:
            prompt += self._build_srs_requirements()
        
        # Add JIRA-specific requirements if JIRA context is available
        if jira_context:
            prompt += self._build_jira_requirements()
        
        # Add SRS-specific requirements if SRS context is available
        if srs_context:
            prompt += self._build_srs_requirements()
        
        # Add output format schema
        prompt += self._build_output_schema()
        
        return prompt
    
    def _build_jira_requirements(self) -> str:
        """Build JIRA-specific review requirements section"""
        return """
**CRITICAL: Code must be evaluated against JIRA ticket requirements**

1. **Requirement Compliance** (HIGHEST PRIORITY):
   - ✅ Verify implementation matches JIRA description
   - ✅ Check all acceptance criteria are met
   - ❌ Flag any missing acceptance criteria
   - ❌ Flag any out-of-scope changes
   - ⚠️  Highlight files changed that are unrelated to JIRA scope

2. **Scope Validation**:
   - Review if ALL changed files are relevant to the JIRA ticket
   - **IMPORTANT**: Files related to the ticket topic ARE IN SCOPE
   - Only flag files as out-of-scope if they are clearly unrelated (documentation, CI/CD configs, demo files, unrelated features)

3. **Acceptance Criteria Checklist**:
   - Create a checklist showing which acceptance criteria are met
   - Clearly mark any missing or incomplete criteria
   - Provide specific line references where criteria are implemented

4. **Testing Requirements**:
   - If business logic changed and no tests were added: ⚠️ WARN explicitly
   - Verify test coverage for new functionality
   - Check if acceptance criteria are testable

5. **Quality Enforcement**:
   - Warn if files changed are not aligned with JIRA scope
   - Flag business logic changes without corresponding tests
   - Apply stricter checks for critical backend changes

"""
    
    def _build_srs_requirements(self) -> str:
        """Build SRS-specific review requirements section"""
        return """
**CRITICAL: Code must align with SRS requirements**

1. **SRS Compliance** (HIGHEST PRIORITY):
   - ✅ Verify implementation matches SRS specifications
   - ✅ Check all functional requirements from SRS are met
   - ✅ Verify non-functional requirements (performance, security, scalability) are addressed
   - ❌ Flag any deviations from SRS requirements
   - ❌ Flag missing implementations required by SRS
   - ⚠️  Highlight any assumptions or interpretations that differ from SRS

2. **Architecture Alignment**:
   - Verify code follows architectural patterns specified in SRS
   - Check system design aligns with SRS architecture diagrams/descriptions
   - Flag any architectural violations

3. **Domain Knowledge**:
   - Use SRS context to understand business rules and domain logic
   - Verify business logic implementation matches SRS requirements
   - Flag incorrect business rule implementations

"""
    
    def _build_jira_requirements(self) -> str:
        """Build JIRA-specific review requirements section"""
        return """
**CRITICAL: Code must be evaluated against JIRA ticket requirements**

1. **Requirement Compliance** (HIGHEST PRIORITY):
   - ✅ Verify implementation matches JIRA description
   - ✅ Check all acceptance criteria are met
   - ❌ Flag any missing acceptance criteria
   - ❌ Flag any out-of-scope changes
   - ⚠️  Highlight files changed that are unrelated to JIRA scope

2. **Scope Validation**:
   - Review if ALL changed files are relevant to the JIRA ticket
   - **IMPORTANT**: Files related to the ticket topic ARE IN SCOPE
   - Only flag files as out-of-scope if they are clearly unrelated (documentation, CI/CD configs, demo files, unrelated features)

3. **Acceptance Criteria Checklist**:
   - Create a checklist showing which acceptance criteria are met
   - Clearly mark any missing or incomplete criteria
   - Provide specific line references where criteria are implemented

4. **Testing Requirements**:
   - If business logic changed and no tests were added: ⚠️ WARN explicitly
   - Verify test coverage for new functionality
   - Check if acceptance criteria are testable

5. **Quality Enforcement**:
   - Warn if files changed are not aligned with JIRA scope
   - Flag business logic changes without corresponding tests
   - Apply stricter checks for critical backend changes

"""
    
    def _build_srs_requirements(self) -> str:
        """Build SRS-specific review requirements section"""
        return """
**CRITICAL: Code must align with SRS requirements**

1. **SRS Compliance** (HIGHEST PRIORITY):
   - ✅ Verify implementation matches SRS specifications
   - ✅ Check all functional requirements from SRS are met
   - ✅ Verify non-functional requirements (performance, security, scalability) are addressed
   - ❌ Flag any deviations from SRS requirements
   - ❌ Flag missing implementations required by SRS
   - ⚠️  Highlight any assumptions or interpretations that differ from SRS

2. **Architecture Alignment**:
   - Verify code follows architectural patterns specified in SRS
   - Check system design aligns with SRS architecture diagrams/descriptions
   - Flag any architectural violations

3. **Domain Knowledge**:
   - Use SRS context to understand business rules and domain logic
   - Verify business logic implementation matches SRS requirements
   - Flag incorrect business rule implementations

"""
    
    def _build_output_schema(self) -> str:
        """Build JSON output schema section"""
        return """## OUTPUT FORMAT

Format your response as JSON with the following structure:
{
  "overall_assessment": "Brief summary of the changes",
  "severity": "error|critical",
  "jira_compliance": {
    "matches_requirements": true/false,
    "missing_criteria": ["List of missing acceptance criteria"],
    "out_of_scope_files": ["List of files not related to JIRA ticket"],
    "acceptance_criteria_checklist": [
      {"criteria": "Criterion text", "status": "✅ Met | ❌ Missing | ⚠️ Partial", "evidence": "Line references"}
    ],
    "subtask_coverage": [
      {"subtask_key": "PROJECT-123", "status": "✅ Covered | ❌ Missing | ⚠️ Partial", "evidence": "File/line references"}
    ],
    "final_verdict": "Approve | Changes Requested"
  },
  "issues": [
    {
      "line": <line_number or null - OPTIONAL: Only provide if 100% confident about exact location. Use null if unsure.>,
      "severity": "error|critical",
      "category": "<category name>",
      "title": "Brief issue title",
      "description": "Detailed explanation explaining WHY this is a problem. Must include exact code reference (verbatim code snippet or line number).",
      "suggestion": "Concrete fix recommendation with code example if applicable",
      "code_reference": "<REQUIRED: Exact verbatim code snippet showing the problematic code. This is mandatory - if you cannot show exact code, omit this issue entirely.>"
    }
  ],
  "positive_aspects": ["List of good practices found in the code"]
}

**IMPORTANT:**
- **ONLY REPORT CRITICAL/ERROR ISSUES**: Filter out "info" and "warning" severity issues. Only report issues with severity "error" or "critical"
- **LINE NUMBERS ARE OPTIONAL**: Only provide a line number if you are 100% confident about the exact location. If unsure, use `null`. Code snippets are the primary way to show issues.
- **IGNORE COMMENTED CODE**: Do NOT flag issues (hardcoded values, security vulnerabilities, etc.) that exist ONLY in commented-out code. Only flag issues in active, executable code
- **CODE REFERENCE IS MANDATORY**: Every issue MUST include a `code_reference` field with the exact verbatim code showing the problem. If you cannot identify exact code, DO NOT report the issue.
- **DEDUPLICATE**: Do not create multiple issues with the same title (e.g., "Large PR size" should only appear once per file or once overall)

**OUTPUT FORMAT:**
Your response must be STRICT JSON only. Do NOT include any markdown sections or formatting outside the JSON structure.
The JSON object is the complete output - no additional markdown is needed or expected.

Be constructive, specific, and helpful. Focus on meaningful improvements."""

