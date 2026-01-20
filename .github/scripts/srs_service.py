#!/usr/bin/env python3
"""
SRS (Software Requirements Specification) Service
Reads and provides SRS documents for AI code review context
"""

import os
import glob
from typing import List, Optional


class SRSService:
    """Service for reading and providing SRS documents"""
    
    def __init__(self):
        # SRS document locations (configurable via environment variable)
        self.srs_paths = os.getenv('SRS_PATHS', 'docs/srs/,docs/requirements/,docs/').split(',')
        self.srs_paths = [p.strip() for p in self.srs_paths if p.strip()]
        
        # Supported SRS file extensions
        self.srs_extensions = ['.md', '.txt', '.rst']
        
        # Maximum SRS content to include (to avoid token limits)
        self.max_srs_length = int(os.getenv('MAX_SRS_LENGTH', '10000'))  # 10k chars default
        
        self.enabled = True
    
    def find_srs_documents(self) -> List[str]:
        """
        Find all SRS documents in configured paths
        
        Returns:
            List of file paths to SRS documents
        """
        srs_files = []
        
        for srs_path in self.srs_paths:
            # Check if path exists
            if not os.path.exists(srs_path):
                continue
            
            # Search for SRS files
            for ext in self.srs_extensions:
                # Pattern: docs/srs/**/*.md, docs/requirements/**/*.md, etc.
                pattern = os.path.join(srs_path, '**', f'*{ext}')
                files = glob.glob(pattern, recursive=True)
                srs_files.extend(files)
        
        # Also check for common SRS file names
        common_names = ['SRS.md', 'srs.md', 'requirements.md', 'REQUIREMENTS.md', 
                       'software_requirements.md', 'project_requirements.md',
                       'SRS.txt', 'requirements.txt']
        
        for name in common_names:
            for srs_path in self.srs_paths:
                file_path = os.path.join(srs_path, name)
                if os.path.exists(file_path) and file_path not in srs_files:
                    srs_files.append(file_path)
        
        # Remove duplicates and sort
        srs_files = sorted(list(set(srs_files)))
        
        return srs_files
    
    def read_srs_content(self, file_path: str) -> Optional[str]:
        """
        Read content from an SRS file
        
        Args:
            file_path: Path to SRS file
            
        Returns:
            File content or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return content
        except Exception as e:
            print(f"⚠️  Error reading SRS file {file_path}: {str(e)}")
            return None
    
    def get_srs_context(self) -> str:
        """
        Get SRS context for AI prompt
        
        Returns:
            Formatted SRS context string
        """
        srs_files = self.find_srs_documents()
        
        if not srs_files:
            print("ℹ️  No SRS documents found in configured paths")
            return ""
        
        print(f"📚 Found {len(srs_files)} SRS document(s)")
        
        srs_contexts = []
        total_length = 0
        
        for srs_file in srs_files:
            print(f"   📄 Reading: {srs_file}")
            content = self.read_srs_content(srs_file)
            
            if not content:
                continue
            
            # Truncate if too long
            if len(content) > self.max_srs_length:
                content = content[:self.max_srs_length] + "\n... (truncated)"
                print(f"   ⚠️  Truncated {srs_file} to {self.max_srs_length} chars")
            
            # Check if adding this would exceed total limit
            if total_length + len(content) > self.max_srs_length:
                print(f"   ⚠️  SRS content limit reached, skipping remaining files")
                break
            
            # Get relative path for display
            rel_path = os.path.relpath(srs_file, os.getcwd())
            
            srs_contexts.append(f"""
## SRS Document: {rel_path}

{content}
""")
            total_length += len(content)
        
        if not srs_contexts:
            return ""
        
        # Combine all SRS contexts
        combined_context = f"""
## 📋 SOFTWARE REQUIREMENTS SPECIFICATION (SRS)

The following SRS documents provide project requirements and specifications:

{''.join(srs_contexts)}

---
**Note:** Code changes should align with the above SRS requirements. Flag any deviations or missing implementations.
"""
        
        print(f"✅ SRS context prepared ({total_length} chars from {len(srs_contexts)} document(s))")
        return combined_context
    
    def get_srs_summary(self) -> str:
        """
        Get a brief summary of available SRS documents
        
        Returns:
            Summary string
        """
        srs_files = self.find_srs_documents()
        
        if not srs_files:
            return "No SRS documents found"
        
        rel_paths = [os.path.relpath(f, os.getcwd()) for f in srs_files]
        return f"Found {len(srs_files)} SRS document(s): {', '.join(rel_paths[:3])}{'...' if len(rel_paths) > 3 else ''}"

