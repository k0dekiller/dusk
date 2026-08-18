from src.server.app import app

server = app("test_api.db")
server.run("localhost", 8080, debug=True)