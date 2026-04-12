"""
Set of tools to available to use for codebase agent. 
"""

import json
import os
import logging
from ..database.db_loader import DatabaseLoader

# Set up logger

logger = logging.getLogger(__name__)

# Set up the DB
loader = DatabaseLoader()



def search_codebase(query: str):
    codebase_data = loader.load_data('categories/repositories.json')
    results = []

    queryLower = query.lower()

    for repo in codebase_data.get('repositories', []):
        match_score = 0
        repo_info = {
            'name': repo.get('name', ''),
            'description': repo.get('description', ''),
            'languages': repo.get('language'),
            'framework': repo.get('framework', ''),
            'key_files': repo.get('key_files', []),
            'team': repo.get('team', ''),
            'documentation': repo.get('documentation', ''),
            'examples': repo.get('examples', {})
        }

        if queryLower in repo.get('name', '').lower():
            match_score += 3
        if queryLower in repo.get('description', '').lower():
            match_score += 2
        if queryLower in str(repo.get('dependencies', [])).lower():
            match_score += 1

        if queryLower > 0:
            repo_info['match_score'] = match_score
            results.append(repo_info)

def analyze_dependencies(module_name: str):
    """Analyze dependencies between libraries"""

    deps_data = loader.load_data('codebase/dependencies.json')
    modLower = module_name.lower()
    found = None

    try:
        for mod_name, mod_data in deps_data.get('modules', {}).items():
            if modLower in mod_name.lower():
                found = mod_name
                break
        
        if found:
            mod_info = deps_data['modules'][found]

            return {
                'status': 'success',
                'name': mod_info.get('name', ''),
                'description': mod_info.get('description', ''),
                'dependencies': mod_info.get('dependencies', []),
                'dependents': mod_info.get('dependents', []),
                'architecture_layer': mod_info.get('architecture_layer', []),
                'communication_methods': mod_info.get('communication_methods', []),
                'data_flows': mod_info.get('data_flows', []),
                'integration_points': mod_info.get('integration_points', []),
            }
    except Exception as e:
        return {
            'status': 'error',
            'error_msg': f'Failed to fetch any modules: {e}'
        }
    
def check_best_practices(code_snippet: str = "", language: str = "python") -> dict:
    """Check code against internal coding standards and best practices.
    
    Args:
        code_snippet: Code to analyze (optional - if empty, returns general guidelines)
        language: Programming language for context (default: "python")
    
    Returns:
        Dict: Best practices analysis, recommendations, and coding standards
    """
    try:
        practices_data = loader.load_data("codebase/best_practices.json")
        
        # Get language-specific practices
        language_practices = practices_data.get("languages", {}).get(language, {})
        general_practices = practices_data.get("general", {})
        
        result = {
            "status": "success",
            "language": language,
            "general_guidelines": general_practices.get("guidelines", []),
            "language_specific": language_practices.get("guidelines", []),
            "code_quality_checklist": practices_data.get("quality_checklist", [])
        }
        
        if code_snippet:
            # Analyze specific code snippet
            violations = []
            recommendations = []
            
            # Check against mock rules
            for rule in practices_data.get("rules", []):
                trigger = rule.get("trigger", "").lower()
                if trigger and trigger in code_snippet.lower():
                    if rule.get("type") == "violation":
                        violations.append({
                            "rule": rule.get("rule", ""),
                            "message": rule.get("message", ""),
                            "severity": rule.get("severity", "medium")
                        })
                    else:
                        recommendations.append({
                            "rule": rule.get("rule", ""),
                            "message": rule.get("message", ""),
                            "improvement": rule.get("improvement", "")
                        })
            
            # Calculate score
            total_checks = len(practices_data.get("rules", []))
            violations_count = len(violations)
            score = max(0, int((total_checks - violations_count) / total_checks * 100))
            
            result.update({
                "code_analysis": {
                    "violations": violations,
                    "recommendations": recommendations,
                    "quality_score": score,
                    "analysis_summary": f"Found {violations_count} potential issues out of {total_checks} checks"
                }
            })
        
        return result
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to check best practices: {str(e)}"
        }

def get_tech_stack_info(component: str = "") -> dict:
    """Get information about the technology stack and tools used.
    
    Args:
        component: Specific component to get info about (optional)
    
    Returns:
        Dict: Technology stack information, tools, and frameworks
    """
    try:
        tech_data = loader.load_data("codebase/tech_stack.json")
        
        if not component:
            # Return overall tech stack
            return {
                "status": "success",
                "overview": tech_data.get("overview", ""),
                "frontend": tech_data.get("frontend", {}),
                "backend": tech_data.get("backend", {}),
                "infrastructure": tech_data.get("infrastructure", {}),
                "tools": tech_data.get("tools", {}),
                "databases": tech_data.get("databases", {})
            }
        
        # Search for specific component
        component_lower = component.lower()
        for category, items in tech_data.items():
            if isinstance(items, dict):
                for key, value in items.items():
                    if component_lower in key.lower():
                        return {
                            "status": "success",
                            "component": key,
                            "category": category,
                            "details": value
                        }
        
        return {
            "status": "error",
            "error_message": f"Component '{component}' not found in tech stack",
            "suggestion": "Try searching for frontend, backend, database, or infrastructure components"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get tech stack info: {str(e)}"
        }