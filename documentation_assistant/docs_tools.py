"""
Tools for documentations
"""

import os
import json
from ..database.db_loader import DatabaseLoader

loader = DatabaseLoader()

def search_documentation(query: str, doc_type: str):
    """Search through all internal documentation for relevant information"""

    try:
        results = {
            'status': 'success',
            'query': query,
            'wiki_results': [],
            'api_results': [],
            'tutorial_results': [],
            'total_found': 0
        }

        queryLower = query.lower()

        if doc_type in ['wiki', 'all']:
            wiki_data = loader.load_data('documentation/wiki_pages.json')
            for wiki in wiki_data.get('pages', []):
                if (queryLower in wiki.get('title', "").lower() or 
                    queryLower in wiki.get('content', "").lower() or
                    any(queryLower in tag.lower() for tag in wiki.get('tags', []))):
                    results['wiki_results'].append({
                        'title': wiki.get('title', ''),
                        'url': wiki.get('url', ''),
                        'summary': wiki.get('summary', ''),
                        'last_updated': wiki.get('last_updated', ''),
                        'author': wiki.get('author', ''),
                        'tags': wiki.get('tags', [])
                    })
        
        if doc_type in ['api', 'all']:
            api_data = loader.load_data('documentation/api_docs.json')
            for api in api_data.get('apis', []):
                if (queryLower in api.get('name', '') or 
                    queryLower in api.get('descriptions', '')):
                    results['api_results'].append({
                        'name': api.get('name', ''),
                        'description': api.get('description', ''),
                        'version': api.get('version', ''),
                        'base_url': api.get('base_url', ''),
                        'documentation_url': api.get('documentation_url', ''),
                        'key_endpoints': api.get('key_endpoints', [])
                    })

        if doc_type in ['tutorial', 'all']:
            tutorial_data = loader.load_data('documentation/tutorials.json')
            for tut in tutorial_data.get('title', ''):
                results['tutorial_results'].append({
                    'title': tut.get('title', ''),
                    'description': tut.get('description', ''),
                    'difficulty': tut.get('difficulty', ''),
                    'estimated_time': tut.get('estimated_time', ''),
                    'url': tut.get('url', ''),
                    'topics': tut.get('topics', [])
                })

        results['total_found'] = (len(results['wiki_results']) + len(results['api_results']) + len(results['tutorial_results']))
        return results
    
    except Exception as e:
        return {
            'status': 'error',
            'error_message': f'{e}'
        }

def find_wiki_pages(topic: str):
    try:
        wiki_data = loader.load_data('documentation/wiki_pages.json')
        topicLower = topic.lower()
        main_pages, rel_pages = [], []

        for wiki in wiki_data.get('pages', '').lower():
            rel_score = 0
            if topicLower in wiki.get('title', '').lower():
                rel_score += 3
            if topicLower in wiki.get('content', '').lower():
                rel_score += 2
            if topicLower in wiki.get('tags', []):
                rel_score += 1
        
            page_info = {
                'title': wiki.get('title', ''),
                'url': wiki.get('url', ''),
                'summary': wiki.get('summary', ''),
                'content': wiki.get('content', '')[:300] + '......' if len(wiki.get('content', '')) > 300 else wiki.get('content', ''),
                'last_updated': wiki.get('last_updated', ''),
                'author': wiki.get('author', ''),
                'tags': wiki.get('tags', []),
                'relevance_score': rel_score
            }

            if rel_score >= 3:
                main_pages.append(page_info)
            elif rel_score > 0:
                rel_pages.append(page_info)

        main_pages.sort(key=lambda x: x['relevance_score'], reverse=True)
        rel_pages.sort(key=lambda x: x['relevance_score'], reverse=True)

    except Exception as e:
        return {
            'status': 'error',
            'error_msg': f'{e}'
        }

def get_api_docs(api_name: str = "", endpoint: str = ""):
    """Get detailed API documentation and endpoint information"""
    try:
        api_data = loader.load_data('documentation/api_data.json')
        
        if not api_name:
            api_list = []
            for api in api_data.get('apis', []):
                api_list.append({
                    'name': api.get('name', ''),
                    'description': api.get('description', ''),
                    'version': api.get('version', ''),
                    'status': api.get('status', '')
                })
            return {
                "status": "success",
                "available_apis": api_list,
                "message": "Specify an api_name to get detailed information"
            }
        
        # Find specific API
        api_name_lower = api_name.lower()
        target_api = None
        for api in api_data.get("apis", []):
            if api_name_lower in api.get("name", "").lower():
                target_api = api
                break
        
        if not target_api:
            return {
                "status": "error",
                "error_message": f"API '{api_name}' not found",
                "available_apis": [api.get("name", "") for api in api_data.get("apis", [])]
            }
        
        result = {
            "status": "success",
            "api_name": target_api.get("name", ""),
            "description": target_api.get("description", ""),
            "version": target_api.get("version", ""),
            "base_url": target_api.get("base_url", ""),
            "authentication": target_api.get("authentication", {}),
            "documentation_url": target_api.get("documentation_url", ""),
            "status": target_api.get("status", ""),
            "endpoints": target_api.get("key_endpoints", [])
        }
        
        # If specific endpoint requested, filter to that
        if endpoint:
            endpoint_lower = endpoint.lower()
            matching_endpoints = []
            for ep in target_api.get("key_endpoints", []):
                if (endpoint_lower in ep.get("path", "").lower() or
                    endpoint_lower in ep.get("description", "").lower()):
                    matching_endpoints.append(ep)
            result["endpoints"] = matching_endpoints
            result["endpoint_filter"] = endpoint
        
        return result
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"Failed to get API information: {str(e)}"
        }