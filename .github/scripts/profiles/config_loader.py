#!/usr/bin/env python3
"""
Project Review Profile Resolver
Loads and validates project-specific review configuration
"""

import os
import json
from typing import Dict, List, Optional
from pathlib import Path


class ConfigLoader:
    """Loads and resolves project review configuration"""
    
    # Mandatory safety categories that cannot be disabled
    MANDATORY_CATEGORIES = [
        'secrets',           # Hardcoded secrets detection
        'authorization',     # Object-level access control
        'security',          # Basic security vulnerabilities
        'error_leakage'     # Internal error exposure
    ]
    
    # Default enabled categories (safe defaults if config missing)
    DEFAULT_ENABLED = [
        'security', 'authorization', 'secrets', 'pii', 'error_leakage',
        'sql_injection', 'xss', 'input_validation', 'error_handling',
        'performance', 'database', 'api', 'logging', 'testing'
    ]
    
    def __init__(self, repo_root: str = '.'):
        self.repo_root = Path(repo_root).resolve()
        self.config_path = self.repo_root / '.ai-review.json'
        self.config = None
    
    def load_config(self) -> Dict:
        """Load project configuration from .ai-review.json"""
        if self.config is not None:
            return self.config
        
        if not self.config_path.exists():
            print("ℹ️  No .ai-review.json found - using default configuration")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Validate and normalize config
            self.config = self._validate_config(self.config)
            print(f"✅ Loaded review configuration from {self.config_path}")
            return self.config
        except json.JSONDecodeError as e:
            print(f"⚠️  Invalid JSON in .ai-review.json: {e}")
            return self._get_default_config()
        except Exception as e:
            print(f"⚠️  Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return safe default configuration"""
        return {
            'enabled_categories': self.DEFAULT_ENABLED.copy(),
            'strictness': 'standard',
            'security_level': 'high',
            'custom_rules': []
        }
    
    def _validate_config(self, config: Dict) -> Dict:
        """Validate and normalize configuration"""
        # Ensure enabled_categories exists
        if 'enabled_categories' not in config:
            config['enabled_categories'] = self.DEFAULT_ENABLED.copy()
        
        # Force-enable mandatory categories
        for mandatory in self.MANDATORY_CATEGORIES:
            if mandatory not in config['enabled_categories']:
                config['enabled_categories'].append(mandatory)
                print(f"⚠️  Force-enabled mandatory category: {mandatory}")
        
        # Remove duplicates
        config['enabled_categories'] = list(set(config['enabled_categories']))
        
        # Set defaults for optional fields
        config.setdefault('strictness', 'standard')
        config.setdefault('security_level', 'high')
        config.setdefault('custom_rules', [])
        
        return config
    
    def get_enabled_categories(self) -> List[str]:
        """Get list of enabled review categories"""
        config = self.load_config()
        return config.get('enabled_categories', self.DEFAULT_ENABLED)
    
    def get_strictness(self) -> str:
        """Get strictness level: 'lenient', 'standard', 'strict'"""
        config = self.load_config()
        return config.get('strictness', 'standard')
    
    def get_security_level(self) -> str:
        """Get security level: 'low', 'medium', 'high'"""
        config = self.load_config()
        return config.get('security_level', 'high')
    
    def get_custom_rules(self) -> List[Dict]:
        """Get custom project-specific rules"""
        config = self.load_config()
        return config.get('custom_rules', [])

