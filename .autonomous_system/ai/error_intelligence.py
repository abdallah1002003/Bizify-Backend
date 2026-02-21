#!/usr/bin/env python3
"""
Error Intelligence System
Analyzes errors and determines when to search the web for solutions
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorIntelligence:
    """
    Intelligent error analysis system that determines when web research is needed.
    """
    
    def __init__(self):
        logger.info('Initializing Error Intelligence System')
        
        # Known error patterns that typically need web research
        self.research_triggers = {
            'ModuleNotFoundError': 'high',
            'ImportError': 'high',
            'AttributeError': 'medium',
            'TypeError': 'medium',
            'ValueError': 'low',
            'NameError': 'low',
            'SyntaxError': 'low',
            'IndentationError': 'low',
            'KeyError': 'medium',
            'IndexError': 'low',
            'FileNotFoundError': 'medium',
            'PermissionError': 'high',
            'ConnectionError': 'high',
            'TimeoutError': 'high',
        }
        
        # Patterns that indicate external dependencies
        self.external_dependency_patterns = [
            r'No module named [\'"](\w+)[\'"]',
            r'cannot import name [\'"](\w+)[\'"]',
            r'pip install (\w+)',
            r'npm install (\w+)',
            r'apt-get install (\w+)',
        ]
    
    def analyze_error(self, error_msg: str, context: Dict = None) -> Dict:
        """
        Analyze an error message and determine if web research is needed.
        
        Args:
            error_msg: The error message to analyze
            context: Additional context (file, line, code snippet, etc.)
        
        Returns:
            Dict with analysis results including:
            - error_type: Type of error
            - severity: How critical is it
            - needs_research: Boolean indicating if web research is needed
            - confidence: Confidence level (0-1)
            - search_query: Suggested search query if research is needed
        """
        logger.info(f'Analyzing error: {error_msg[:100]}...')
        
        context = context or {}
        
        # Extract error type
        error_type = self._extract_error_type(error_msg)
        
        # Determine severity
        severity = self._determine_severity(error_type, error_msg)
        
        # Check if it's an external dependency issue
        is_external = self._is_external_dependency(error_msg)
        
        # Determine if research is needed
        needs_research = self._should_search_web(error_type, severity, is_external, context)
        
        # Generate search query if needed
        search_query = None
        if needs_research:
            search_query = self._generate_search_query(error_msg, error_type, context)
        
        # Calculate confidence
        confidence = self._calculate_confidence(error_type, is_external, context)
        
        analysis = {
            'error_type': error_type,
            'severity': severity,
            'needs_research': needs_research,
            'is_external_dependency': is_external,
            'confidence': confidence,
            'search_query': search_query,
            'timestamp': datetime.now().isoformat(),
            'original_error': error_msg
        }
        
        logger.info(f'Analysis complete: needs_research={needs_research}, confidence={confidence:.2f}')
        
        return analysis
    
    def _extract_error_type(self, error_msg: str) -> str:
        """Extract the error type from the error message."""
        # Try to find Python exception type
        match = re.search(r'(\w+Error|\w+Exception):', error_msg)
        if match:
            return match.group(1)
        
        # Check for common error keywords
        if 'not found' in error_msg.lower():
            return 'NotFoundError'
        if 'permission denied' in error_msg.lower():
            return 'PermissionError'
        if 'timeout' in error_msg.lower():
            return 'TimeoutError'
        if 'connection' in error_msg.lower():
            return 'ConnectionError'
        
        return 'UnknownError'
    
    def _determine_severity(self, error_type: str, error_msg: str) -> str:
        """Determine the severity of the error."""
        # Check research triggers
        if error_type in self.research_triggers:
            return self.research_triggers[error_type]
        
        # Check for critical keywords
        critical_keywords = ['critical', 'fatal', 'cannot continue', 'system']
        if any(kw in error_msg.lower() for kw in critical_keywords):
            return 'high'
        
        return 'medium'
    
    def _is_external_dependency(self, error_msg: str) -> bool:
        """Check if the error is related to external dependencies."""
        for pattern in self.external_dependency_patterns:
            if re.search(pattern, error_msg, re.IGNORECASE):
                return True
        return False
    
    def _should_search_web(self, error_type: str, severity: str, 
                          is_external: bool, context: Dict) -> bool:
        """
        Determine if web research is needed for this error.
        
        Logic:
        - Always search for external dependency issues
        - Search for high severity errors
        - Search for medium severity if no local solution found
        - Don't search for simple syntax errors
        """
        # Always search for external dependencies
        if is_external:
            logger.info('External dependency detected - research needed')
            return True
        
        # Always search for high severity
        if severity == 'high':
            logger.info('High severity error - research needed')
            return True
        
        # Don't search for simple syntax errors
        if error_type in ['SyntaxError', 'IndentationError', 'NameError']:
            logger.info('Simple syntax error - no research needed')
            return False
        
        # For medium severity, check if we have context
        if severity == 'medium':
            # If we have tried before and failed, search
            if context.get('retry_count', 0) > 0:
                logger.info('Retry detected - research needed')
                return True
            
            # If it's a known complex error, search
            if error_type in ['AttributeError', 'KeyError', 'FileNotFoundError']:
                logger.info('Complex error type - research needed')
                return True
        
        logger.info('No research needed for this error')
        return False
    
    def _generate_search_query(self, error_msg: str, error_type: str, 
                               context: Dict) -> str:
        """
        Generate an intelligent search query for the error.
        
        Strategies:
        1. For module errors: "how to install [module] python"
        2. For specific errors: "[error_type] [key_part] python solution"
        3. Include language/framework from context
        """
        # Extract module name for import errors
        module_match = re.search(r'No module named [\'"](\w+)[\'"]', error_msg)
        if module_match:
            module_name = module_match.group(1)
            return f"how to install {module_name} python pip"
        
        # Extract import name
        import_match = re.search(r'cannot import name [\'"](\w+)[\'"]', error_msg)
        if import_match:
            name = import_match.group(1)
            return f"python {error_type} cannot import {name} solution"
        
        # For other errors, extract key information
        # Remove file paths and line numbers
        clean_msg = re.sub(r'File ".*?", line \d+', '', error_msg)
        clean_msg = re.sub(r'line \d+', '', clean_msg)
        
        # Take first line of error (usually most relevant)
        first_line = clean_msg.split('\n')[0].strip()
        
        # Limit length
        if len(first_line) > 100:
            first_line = first_line[:100]
        
        # Add language context
        language = context.get('language', 'python')
        
        query = f"{language} {error_type} {first_line} solution"
        
        logger.info(f'Generated search query: {query}')
        
        return query
    
    def _calculate_confidence(self, error_type: str, is_external: bool, 
                             context: Dict) -> float:
        """
        Calculate confidence level for the analysis.
        
        Higher confidence means we're more sure about needing research.
        """
        confidence = 0.5  # Base confidence
        
        # High confidence for external dependencies
        if is_external:
            confidence += 0.3
        
        # Adjust based on error type
        if error_type in self.research_triggers:
            severity = self.research_triggers[error_type]
            if severity == 'high':
                confidence += 0.2
            elif severity == 'medium':
                confidence += 0.1
        
        # Increase confidence if we have good context
        if context.get('file_path'):
            confidence += 0.05
        if context.get('code_snippet'):
            confidence += 0.05
        if context.get('stack_trace'):
            confidence += 0.1
        
        # Cap at 1.0
        confidence = min(confidence, 1.0)
        
        return confidence
    
    def extract_solution_from_results(self, search_results: List[Dict]) -> Optional[Dict]:
        """
        Extract the best solution from search results.
        
        Args:
            search_results: List of search results with title, snippet, url
        
        Returns:
            Dict with solution information or None
        """
        logger.info(f'Extracting solution from {len(search_results)} results')
        
        # Look for Stack Overflow results (usually high quality)
        stackoverflow_results = [
            r for r in search_results 
            if 'stackoverflow.com' in r.get('url', '').lower()
        ]
        
        # Look for official documentation
        doc_results = [
            r for r in search_results
            if any(kw in r.get('url', '').lower() 
                  for kw in ['docs.python.org', 'readthedocs', 'github.com'])
        ]
        
        # Prioritize: official docs > stackoverflow > others
        prioritized = doc_results + stackoverflow_results + search_results
        
        if not prioritized:
            return None
        
        # Take the top result
        top_result = prioritized[0]
        
        solution = {
            'source': top_result.get('url', 'unknown'),
            'title': top_result.get('title', ''),
            'snippet': top_result.get('snippet', ''),
            'confidence': self._rate_solution_quality(top_result),
            'type': self._identify_solution_type(top_result)
        }
        
        logger.info(f'Solution extracted from: {solution["source"]}')
        
        return solution
    
    def _rate_solution_quality(self, result: Dict) -> float:
        """Rate the quality of a solution based on the source."""
        url = result.get('url', '').lower()
        
        # Official documentation = highest quality
        if any(kw in url for kw in ['docs.python.org', 'readthedocs.io']):
            return 0.9
        
        # Stack Overflow = high quality
        if 'stackoverflow.com' in url:
            return 0.8
        
        # GitHub = good quality
        if 'github.com' in url:
            return 0.7
        
        # Other sources
        return 0.5
    
    def _identify_solution_type(self, result: Dict) -> str:
        """Identify the type of solution."""
        snippet = result.get('snippet', '').lower()
        
        if 'pip install' in snippet or 'npm install' in snippet:
            return 'installation'
        
        if 'import' in snippet:
            return 'import_fix'
        
        if any(kw in snippet for kw in ['def ', 'class ', 'function']):
            return 'code_fix'
        
        if 'config' in snippet or 'setting' in snippet:
            return 'configuration'
        
        return 'general'

# CLI for testing
if __name__ == "__main__":
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    ei = ErrorIntelligence()
    
    # Test cases
    test_errors = [
        "ModuleNotFoundError: No module named 'requests'",
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "SyntaxError: invalid syntax",
        "AttributeError: 'NoneType' object has no attribute 'get'",
    ]
    
    print("🧪 Testing Error Intelligence System\n")
    print("=" * 60)
    
    for error in test_errors:
        print(f"\n📋 Error: {error}")
        analysis = ei.analyze_error(error)
        print(f"   Type: {analysis['error_type']}")
        print(f"   Severity: {analysis['severity']}")
        print(f"   Needs Research: {analysis['needs_research']}")
        print(f"   Confidence: {analysis['confidence']:.2f}")
        if analysis['search_query']:
            print(f"   Search Query: {analysis['search_query']}")
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
