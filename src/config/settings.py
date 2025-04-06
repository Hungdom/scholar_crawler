import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Database settings
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'scholar_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Crawler settings
CRAWLER_CONFIG = {
    'max_results': int(os.getenv('MAX_RESULTS', '10')),
    'search_query': os.getenv('SEARCH_QUERY', 'mathematics'),
    'delay_between_requests': float(os.getenv('DELAY_BETWEEN_REQUESTS', '2.0'))
} 