import os
from app import create_app

# Load the environment, default to production
env = os.environ.get('FLASK_ENV', 'production')

app = create_app(env)

if __name__ == "__main__":
    app.run()
