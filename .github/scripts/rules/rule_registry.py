#!/usr/bin/env python3
"""
Rule Registry
Manages and loads review rule modules dynamically
"""

import os
from typing import Dict, Optional, List
from pathlib import Path


class RuleRegistry:
    """Registry for review rule modules"""
    
    def __init__(self, rules_dir: Optional[str] = None):
        if rules_dir is None:
            # Default to .github/scripts/rules relative to this file
            script_dir = Path(__file__).parent.parent
            rules_dir = script_dir / 'rules'
        self.rules_dir = Path(rules_dir)
        self._rules_cache: Dict[str, str] = {}
    
    def get_rule(self, category: str) -> Optional[str]:
        """Get rule content for a category"""
        if category in self._rules_cache:
            return self._rules_cache[category]
        
        # Try to load rule file
        rule_file = self.rules_dir / f"{category}.txt"
        
        if not rule_file.exists():
            # Try alternative naming
            rule_file = self.rules_dir / f"{category}_rule.txt"
        
        if rule_file.exists():
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    self._rules_cache[category] = content
                    return content
            except Exception as e:
                print(f"⚠️  Error loading rule {category}: {e}")
                return None
        
        return None
    
    def register_rule(self, category: str, content: str):
        """Register a rule programmatically (for testing or dynamic rules)"""
        self._rules_cache[category] = content
    
    def list_available_rules(self) -> List[str]:
        """List all available rule files"""
        if not self.rules_dir.exists():
            return []
        
        rules = []
        for rule_file in self.rules_dir.glob("*.txt"):
            category = rule_file.stem.replace('_rule', '')
            rules.append(category)
        
        return sorted(rules)

