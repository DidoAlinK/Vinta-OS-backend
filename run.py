"""
Vinta School OS — Application Entry Point
Launches the Flask application with the appropriate configuration.
"""
import os
from app import create_app

config_name = os.getenv("FLASK_ENV", "development")
app = create_app(config_name)

if __name__ == "__main__":
    socketio = app.extensions.get("socketio")
    if socketio:
        socketio.run(app, debug=app.config.get("DEBUG", False))
    else:
        app.run(debug=app.config.get("DEBUG", False))
