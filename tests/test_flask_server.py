from flask_unittest import ClientTestCase
from jsonclasses_pymongo import Connection
from json import loads
from .servers.server import flask_app, fastapi_app, User, Article, Song

class TestFlaskServer(ClientTestCase):

    app = flask_app

    def setUp(self, _) -> None:
        collection = Connection.get_collection(Song)
        collection.delete_many({})
        collection = Connection.get_collection(User)
        collection.delete_many({})
        collection = Connection.get_collection(Article)
        collection.delete_many({})

    def test_create_creates_a_song(self, client):
        rv = client.post('/songs', json={"name": "song", "year": 2021}).data
        result = loads(rv)["data"]
        self.assertIsNotNone(result["id"])
        self.assertIsNotNone(result["createdAt"])
        self.assertIsNotNone(result["updatedAt"])
        self.assertEqual(["song", 2021], [result["name"], result["year"]])

    def test_get_gets_all_songs(self, client):
        client.post('/songs', json={"name": "song", "year": 2021})
        client.post('/songs', json={"name": "song2", "year": 2019})
        rv = client.get('/songs').data
        result = loads(rv)["data"]
        self.assertIsNotNone(result[0]["id"])
        self.assertIsNotNone(result[0]["createdAt"])
        self.assertIsNotNone(result[0]["updatedAt"])
        self.assertEqual(["song", 2021], [result[0]["name"], result[0]["year"]])
        self.assertIsNotNone(result[1]["id"])
        self.assertIsNotNone(result[1]["createdAt"])
        self.assertIsNotNone(result[1]["updatedAt"])
        self.assertEqual(["song2", 2019], [result[1]["name"], result[1]["year"]])

    def test_get_gets_a_songs(self, client):
        song = client.post('/songs', json={"name": "song", "year": 2021}).data
        client.post('/songs', json={"name": "song2", "year": 2019})
        song_id = loads(song)["data"]["id"]
        rv = client.get(f'/songs/{song_id}').data
        result = loads(rv)["data"]
        self.assertIsNotNone(result["id"])
        self.assertIsNotNone(result["createdAt"])
        self.assertIsNotNone(result["updatedAt"])
        self.assertEqual(["song", 2021], [result["name"], result["year"]])

    def test_update_updates_a_song(self, client):
        song = client.post('/songs', json={"name": "song", "year": 2021}).data
        client.post('/songs', json={"name": "song2", "year": 2019})
        song_id = loads(song)["data"]["id"]
        rv = client.patch(f'/songs/{song_id}', json={"name": "some on you loved", "year": 2016}).data
        result = loads(rv)["data"]
        self.assertIsNotNone(result["id"])
        self.assertIsNotNone(result["createdAt"])
        self.assertIsNotNone(result["updatedAt"])
        self.assertEqual(["some on you loved", 2016], [result["name"], result["year"]])

    def test_delete_deletes_a_song(self, client):
        song = client.post('/songs', json={"name": "song", "year": 2021}).data
        client.post('/songs', json={"name": "song2", "year": 2019})
        client.post('/songs', json={"name": "song3", "year": 2017})
        song_id = loads(song)["data"]["id"]
        rv = client.delete(f'/songs/{song_id}')
        songs = client.get('/songs').data
        self.assertStatus(rv, 204)
        self.assertEqual(len(loads(songs)["data"]), 2)
