from unittest.case import TestCase
from jsonclasses_pymongo.connection import Connection
from thunderlight.client import Client
from .classes.server import app, User, Article, Song


client = Client(app)


class TestServer(TestCase):

    def setUp(self) -> None:
        collection = Connection.get_collection(Song)
        collection.delete_many({})
        collection = Connection.get_collection(User)
        collection.delete_many({})
        collection = Connection.get_collection(Article)
        collection.delete_many({})

    def test_fastapi_creates_a_song(self):
        result = client.post('/songs', body={"name": "song", "year": 2021}).json()['data']
        self.assertIsNotNone(result["data"]["id"])
        self.assertIsNotNone(result["data"]["createdAt"])
        self.assertIsNotNone(result["data"]["updatedAt"])
        self.assertEqual(["song", 2021], [result["name"], result["year"]])

    def test_fastapi_gets_all_songs(self):
        client.post('/songs', body={"name": "song", "year": 2021})
        client.post('/songs', body={"name": "song2", "year": 2019})
        result = client.get('/songs').json()['data']
        self.assertIsNotNone(result[0]["id"])
        self.assertIsNotNone(result[0]["createdAt"])
        self.assertIsNotNone(result[0]["updatedAt"])
        self.assertEqual(["song", 2021], [result[0]["name"], result[0]["year"]])
        self.assertIsNotNone(result[1]["id"])
        self.assertIsNotNone(result[1]["createdAt"])
        self.assertIsNotNone(result[1]["updatedAt"])
        self.assertEqual(["song2", 2019], [result[1]["name"], result[1]["year"]])

    def test_fastapi_gets_a_songs(self):
        song = client.post('/songs', body={"name": "song", "year": 2021}).json()['data']
        client.post('/songs', body={"name": "song2", "year": 2019})
        song_id = song["id"]
        result = client.get(f'/songs/{song_id}').json()['data']
        self.assertIsNotNone(result["id"])
        self.assertIsNotNone(result["createdAt"])
        self.assertIsNotNone(result["updatedAt"])
        self.assertEqual(["song", 2021], [result["name"], result["year"]])

    def test_fastapi_updates_a_song(self):
        song = client.post('/songs', body={"name": "song", "year": 2021}).json()["data"]
        client.post('/songs', body={"name": "song2", "year": 2019})
        song_id = song["id"]
        result = client.patch(f'/songs/{song_id}', body={"name": "some on you loved", "year": 2016}).json()["data"]
        self.assertIsNotNone(result["id"])
        self.assertIsNotNone(result["createdAt"])
        self.assertIsNotNone(result["updatedAt"])
        self.assertEqual(["some on you loved", 2016], [result["name"], result["year"]])

    def test_fastapi_deletes_a_song(self):
        song = client.post('/songs', body={"name": "song", "year": 2021}).json()
        client.post('/songs', body={"name": "song2", "year": 2019})
        client.post('/songs', body={"name": "song3", "year": 2017})
        song_id = song["data"]["id"]
        result = client.delete(f'/songs/{song_id}')
        songs = client.get('/songs').json()
        self.assertEqual(result.status_code, 204)
        self.assertEqual(len(songs["data"]), 2)

    def test_fastapi_sign_in(self):
        client.post('/users', body={"username": "Jack", "password": "12345678"})
        result = client.post('/users/session', body={"username": "Jack", "password": "12345678"}).json()
        self.assertIsNotNone(result["data"]["token"])

    def test_fastapi_sign_in_to_create_article(self):
        user = client.post('/users', body={"username": "Jack", "password": "12345678"}).json()
        sign_in = client.post('/users/session', body={"username": "Jack", "password": "12345678"}).json()
        token = sign_in["data"]["token"]
        auther_id = user["data"]["id"]
        article = client.post('/articles',
                              body={"title": "Python", "content": "How to learn python"},
                              headers={"Authorization": f"Bearer {token}"}).json()
        self.assertIsNotNone(article["data"]["id"])
        self.assertIsNotNone(article["data"]["createdAt"])
        self.assertIsNotNone(article["data"]["updatedAt"])
        self.assertEqual([
            "Python",
            "How to learn python",
            auther_id
        ], [
            article["data"]["title"],
            article["data"]["content"],
            article["data"]["authorId"]
        ])
