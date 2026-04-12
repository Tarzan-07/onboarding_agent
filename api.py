"""
REST api wrapper for the ADK onboarding agent
Exposes the agent via HTTP endpoints
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging
import time
import requests
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from .agent import root_agent
from .database.db_loader import DatabaseLoader

load_dotenv()

app = Flask(__name__)
CORS(app)

loader = DatabaseLoader()

APP_NAME = 'onboarding_agent'
DEFAULT_USER_ID = 'local_user'
session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

@app.route('/health', methods=['GET'])
def health():
    """Health check point"""
    app.logger.info('Health check called')
    return jsonify({'status':'healthy', 'service':'onboarding-agent-api'})

@app.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint

    Expects: {'message': 'user message'}
    Returns: {'response': 'agent response', 'session_id':'.....'}
    """

    try:
        data = request.get_json()
        user_message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        app.logger.info('Incoming chat request session_id=%s message=%s', session_id, user_message[:120])

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        if not session_service.get_session(
            app_name=APP_NAME, user_id=DEFAULT_USER_ID, session_id=session_id
        ):
            session_service.create_session(
                app_name=APP_NAME,
                user_id=DEFAULT_USER_ID,
                session_id=session_id
            )

        new_message = types.Content(
            role='user',
            parts=[types.Part(text=user_message)]
        )

        events = list(
            Runner.run(
                user_id=DEFAULT_USER_ID,
                session_id=session_id,
                new_message=new_message
            )
        )

        response_text = ""
        for event in reversed(events):
            if event.author == 'user' or not event.content or not event.content.parts:
                continue
            
            if not event.is_final_response():
                continue
            
            parts_text = [part.text for part in event.content.parts if getattr(part, 'text', None)]
            if parts_text:
                response_text = '\n'.join(parts_text)
                break

        agent_resp = response_text or "I could not generate a response. Please try again !"
        app.logger.info('Outgoing chat response session_id=%s, length=%d', session_id, len(agent_resp))

        return jsonify({
            'response': agent_resp,
            'session_id': session_id,
            'success': True,
            'metadata': {
                'model': os.getenv('MODEL_NAME', 'gemini-2.5-flash'),
                'agent': 'onboarding_orchestrator'
            }
        })

    except Exception as e:
        app.logger.exception('Chat endpoint failed')
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/documents', methods=['GET'])
def get_documents():
    """
    Get all cached onboarding documents
    """

    try:
        category = request.args.get('category')

        if category:
            docs = loader.load_data_by_category(category=category)
        else:
            docs = loader.load_data_by_category(category='')

        return jsonify({
            'documents': docs,
            'count': len(docs) if isinstance(docs, []) else 1,
            'success': True
        }), 500
    
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        })

@app.route('/search', methods=['GET'])
def search_documents():
    """
    Search all documents by keyword
    """

    try:
        query = request.args.get('q', '')

        if not query:
            return jsonify({
                'error': 'No search query provided'
            }), 400
        
        results = loader.search_all_data(query)

        return jsonify ({
            'results': results,
            'query': query,
            'count': len(results),
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        })
    
@app.route('/capabilities', methods=['GET'])
def get_capabilities():
    """
    Get agent capabilities and sub-agents
    """

    return jsonify({
        'agent': 'onboarding_agent',
        'description': 'Central coordinator for new hire onboarding',
        'model': os.getenv('MODEL_NAME', 'gemini-2.5-flash'),
        'sub_agents': [
            {
                'name': 'codebase_navigator',
                'description': 'Specialized in finding and explaining documentation'
            }
        ],
        'documentation_categories': [
            'codebase',
            'documentation'
        ],
        'success': True
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)