from unittest.case import TestCase
from fastapi.testclient import TestClient
from jsonclasses_pymongo import Connection
from json import loads
from .servers.server import fastapi_app, User, Article, Song

app = fastapi_app
client = TestClient(app)

class TestFastapiServer(TestCase):

    def setUp(self) -> None:
        collection = Connection.get_collection(Song)
        collection.delete_many({})
        collection = Connection.get_collection(User)
        collection.delete_many({})
        collection = Connection.get_collection(Article)
        collection.delete_many({})

    def test_fastapi_creates_a_song(self):
        result = client.post('/songs', json={"name": "song", "year": 2021}).json()
        self.assertIsNotNone(result["id"])
        self.assertIsNotNone(result["createdAt"])
        self.assertIsNotNone(result["updatedAt"])
        self.assertEqual(["song", 2021], [result["name"], result["year"]])

    def test_fastapi_gets_all_songs(self):
        client.post('/songs', json={"name": "song", "year": 2021})
        client.post('/songs', json={"name": "song2", "year": 2019})
        result = client.get('/songs').json()
        self.assertIsNotNone(result[0]["id"])
        self.assertIsNotNone(result[0]["createdAt"])
        self.assertIsNotNone(result[0]["updatedAt"])
        self.assertEqual(["song", 2021], [result[0]["name"], result[0]["year"]])
        self.assertIsNotNone(result[1]["id"])
        self.assertIsNotNone(result[1]["createdAt"])
        self.assertIsNotNone(result[1]["updatedAt"])
        self.assertEqual(["song2", 2019], [result[1]["name"], result[1]["year"]])

    def test_fastapi_gets_a_songs(self):
        song = client.post('/songs', json={"name": "song", "year": 2021}).json()
        client.post('/songs', json={"name": "song2", "year": 2019})
        song_id = song["id"]
        result = client.get(f'/songs/{song_id}').json()
        self.assertIsNotNone(result["id"])
        self.assertIsNotNone(result["createdAt"])
        self.assertIsNotNone(result["updatedAt"])
        self.assertEqual(["song", 2021], [result["name"], result["year"]])

    def test_fastapi_updates_a_song(self):
        song = client.post('/songs', json={"name": "song", "year": 2021}).json()
        client.post('/songs', json={"name": "song2", "year": 2019})
        song_id = song["id"]
        result = client.patch(f'/songs/{song_id}', json={"name": "some on you loved", "year": 2016}).json()
        self.assertIsNotNone(result["id"])
        self.assertIsNotNone(result["createdAt"])
        self.assertIsNotNone(result["updatedAt"])
        self.assertEqual(["some on you loved", 2016], [result["name"], result["year"]])

    def test_fastapi_deletes_a_song(self):
        song = client.post('/songs', json={"name": "song", "year": 2021}).json()
        client.post('/songs', json={"name": "song2", "year": 2019})
        client.post('/songs', json={"name": "song3", "year": 2017})
        song_id = song["id"]
        result = client.delete(f'/songs/{song_id}')
        songs = client.get('/songs').json()
        self.assertEqual(result.status_code, 204)
        self.assertEqual(len(songs), 2)

    def test_fastapi_sign_in(self):
        client.post('/users', json={"username": "Jack", "password": "12345678"})
        result = client.post('/users/session', json={"username": "Jack", "password": "12345678"}).json()
        self.assertIsNotNone(result["token"])

    def test_fastapi_sign_in_to_create_article(self):
        user = client.post('/users', json={"username": "Jack", "password": "12345678"}).json()
        sign_in = client.post('/users/session', json={"username": "Jack", "password": "12345678"}).json()
        token = sign_in["token"]
        auther_id = user["id"]
        article = client.post('/articles',
                              json={"title": "Python", "content": "How to learn python"},
                              headers={"Authorization": f"Bearer {token}"}).json()
        self.assertIsNotNone(article["id"])
        self.assertIsNotNone(article["createdAt"])
        self.assertIsNotNone(article["updatedAt"])
        self.assertEqual([
            "Python",
            "How to learn python",
            auther_id
        ], [
            article["title"],
            article["content"],
            article["authorId"]
        ])
