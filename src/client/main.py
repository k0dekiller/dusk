from .api import Client

c = Client("http://localhost:3050", username="test1", password="password1")
c.login()