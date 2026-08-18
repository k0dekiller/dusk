from .api import Client

c = Client("http://localhost:8080", username="test1", password="password1")
c.login()