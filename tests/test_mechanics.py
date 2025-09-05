from app import create_app
from app.models import Mechanics, db
import unittest
from werkzeug.security import check_password_hash, generate_password_hash
from app.util.auth import encode_token


# python -m unittest discover tests

class TestMechanics(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.mechanic = Mechanics(
                first_name="Test",
                last_name="Mechanic",
                email="testmech@email.com",
                password=generate_password_hash('123'),
                salary=50000.0,
                address="123 Mechanic St"
            )
            db.session.add(self.mechanic)
            db.session.commit()
            self.token = encode_token(self.mechanic.id, "mechanic")

    def test_create_mechanic(self):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johnmech@email.com",
            "password": "123",
            "salary": 60000.0,
            "address": "456 Mechanic Ave"
        }
        response = self.client.post('/mechanics/', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['first_name'], "John")
        self.assertEqual(response.json['last_name'], "Doe")
        self.assertEqual(response.json['email'], "johnmech@email.com")
        self.assertEqual(response.json['salary'], 60000.0)
        self.assertEqual(response.json['address'], "456 Mechanic Ave")
        self.assertTrue(check_password_hash(response.json['password'], "123"))

    def test_create_mechanic_duplicate_email(self):
        payload = {
            "first_name": "Duplicate",
            "last_name": "Mechanic",
            "email": "testmech@email.com",  
            "password": "123",
            "salary": 60000.0,
            "address": "456 Mechanic Ave"
        }
        response = self.client.post('/mechanics/', json=payload)
        self.assertEqual(response.status_code, 409)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], "Email already in use")

    def test_invalid_create_mechanic(self):
        payload = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "invalid-email",  # Invalid email format
            "password": "123",
            "salary": 60000.0,
            "address": "123 Main St"
        }
        response = self.client.post('/mechanics/', json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json)
        self.assertIn('Not a valid email address.', response.json['email'][0])

    def test_get_mechanics(self):
        response = self.client.get('/mechanics/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(m['email'] == "testmech@email.com" for m in response.json))

    def test_login_mechanic_success(self):
        creds = {
            "email": "testmech@email.com",
            "password": "123"
        }
        response = self.client.post('/mechanics/login', json=creds)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json)
        self.assertIn('message', response.json)
        self.assertTrue(response.json['message'].startswith("Login successful"))

    def test_login_mechanic_invalid_password(self):
        creds = {
            "email": "testmech@email.com",
            "password": "wrongpassword"
        }
        response = self.client.post('/mechanics/login', json=creds)
        self.assertEqual(response.status_code, 403)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], "Invalid email or password")

    def test_login_mechanic_invalid_email(self):
        creds = {
            "email": "notfound@email.com",
            "password": "123"
        }
        response = self.client.post('/mechanics/login', json=creds)
        self.assertEqual(response.status_code, 403)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], "Invalid email or password")

    def test_get_mechanic_profile(self):
        headers = {"Authorization": "Bearer " + self.token}
        response = self.client.get('/mechanics/profile', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['email'], "testmech@email.com")

    def test_update_mechanic(self):
        headers = {"Authorization": "Bearer " + self.token}
        update_payload = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "janemech@email.com",
            "password": "456",
            "salary": 70000.0,
            "address": "789 Mechanic Blvd"
        }
        response = self.client.put('/mechanics/', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['first_name'], "Jane")
        self.assertEqual(response.json['last_name'], "Smith")
        self.assertEqual(response.json['email'], "janemech@email.com")
        self.assertEqual(response.json['salary'], 70000.0)
        self.assertEqual(response.json['address'], "789 Mechanic Blvd")
        self.assertTrue(check_password_hash(response.json['password'], "456"))

    def test_delete_mechanic(self):
        headers = {"Authorization": "Bearer " + self.token}
        response = self.client.delete('/mechanics', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)

    def test_unauthorized_delete_mechanic(self):
        response = self.client.delete('/mechanics')
        self.assertEqual(response.status_code, 401)

if __name__ == "__main__":
    unittest.main()
