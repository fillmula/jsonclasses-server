from unittest.case import TestCase
from thunderlight.client import Client
from jsonclasses_server import server

app = server()

client = Client(app)


class TestSimpleRequest(TestCase):

    async def test_create_a_song(self) -> None:
        result = client.post('simplesongs/', body={ 'name': 'song' })
