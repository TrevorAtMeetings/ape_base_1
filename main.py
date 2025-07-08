import os
from dotenv import load_dotenv
from app import app

# Load environment variables from .env file
load_dotenv()

if __name__ == '__main__':
    # Standardized environment variable configuration
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode
    )