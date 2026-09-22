from src.server.app import app
from flask_cors import CORS

server = app("test_api.db")
CORS(server, resources={
    r"/*": {
        "origins": ["http://127.0.0.1:8080"]
    }
})
server.run("localhost", 3050, debug=True)