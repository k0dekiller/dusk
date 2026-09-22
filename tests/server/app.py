from src.server.app import app
from flask_cors import CORS

server = app("test_api.db")
CORS(server, resources={
    r"/*": {
        "origins": ["http://localhost:8080"]
    }
})
server.run("localhost", 8080, debug=True)