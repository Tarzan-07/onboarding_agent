"""
Script to connect with postgres DB. 
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging

# Set up logger
logger = logging.getLogger(__name__)

# Set up env variables
load_dotenv()

# Class of Database actions

class DatabaseLoader():
    def __init__(self):
        """Initialize database connection."""
        
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', 5432),
            'dbname': os.getenv('DB_USERNAME', 'onboarding_db'),
            'user': os.getenv('DB_USERNAME', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres'),
        }

        self.connection = None

    def _get_connection(self):
        """Create a connection with database"""

        try:
            if self.connection is None:
                self.connection = psycopg2.connect(**self.db_config)
            return self.connection

        except Exception as e:
            logger.error(f'Facing issues with connection to DB: {e}')

    def load_data(self, path: str):
        """Load JSON data from the DB."""

        try:
            parts = path.split('/')
            if len(parts) != 2:
                raise ValueError(f"Invalid path format: {path}. Expected 'category/filename.json")
            
            cat, file = parts[0], parts[1]

            conn = self._get_connection()
            query = f"""select data from json_documents where category = %s and filename = %s limit 1"""
            

            with conn.cursor(cursor_factory = RealDictCursor) as cursor:
                cursor.execute(query, (cat, file))
                result = cursor.fetchone()

            if result:
                if result['data']:
                    return result['data']
            else:
                logger.warning(f'No data found under path: {path}')
                return {}
            
        except Exception as e:
            logger.error(f"Failed to load data from the DB: {e}")

    def load_data_by_category(self, category: str):
        """Load JSON data from the DB based on the category."""

        conn = self._get_connection()
        query = "select filename, data from json_documents where category = %s"

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            results = cursor.execute(query, (category))
            result = cursor.fetchall()

            combine_data = {}
            for row in results:
                combine_data[row['filename']] = row['data']
            return combine_data
        
    def search_all_data(self, search_term: str):
        conn = self._get_connection()
        query = "select category, subcategory, filename, data from json_documents where data::text ILIKE %s"
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            result = cursor.execute(query, (f'%{search_term}%'))
            result = cursor.fetchall()

            return result
        
    def __del__(self):
        """Close the connection to the DB."""

        if self.connection and not self.connection.closed:
            self.connection.close()
