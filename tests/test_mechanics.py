from app import create_app
from app.models import Mechanics, db
import unittest
from werkzeug.security import check_password_hash, generate_password_hash
from app.util.auth import encode_token
from app.util.auth import create_admin_token, create_mechanic_token, create_customer_token


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
            
            from app.models import Customers
            self.customer = Customers(
                first_name="Test",
                last_name="Customer",
                email="testcustomer@email.com",
                password=generate_password_hash('123'),
                phone="1234567890",
                address="123 Customer St"
            )
            db.session.add(self.customer)
            db.session.commit()
            self.mechanic_token = create_mechanic_token(self.mechanic.id)
            self.admin_token = create_admin_token(self.mechanic.id)
            self.customer_token = create_customer_token(self.customer.id)
            
# -------------------------------------------------------------------------------------------

    def test_create_mechanic(self):
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johnmech@email.com",
            "password": "123",
            "salary": 60000.0,
            "address": "456 Mechanic Ave"
        }
       
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.post('/mechanics/', json=payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['first_name'], "John")
        self.assertEqual(response.json['last_name'], "Doe")
        self.assertEqual(response.json['email'], "johnmech@email.com")
        self.assertEqual(response.json['salary'], 60000.0)
        self.assertEqual(response.json['address'], "456 Mechanic Ave")
        self.assertTrue(check_password_hash(response.json['password'], "123"))
      
        
# -------------------------------------------------------------------------------------------

    def test_create_mechanic_duplicate_email(self):
        payload = {
            "first_name": "Duplicate",
            "last_name": "Mechanic",
            "email": "testmech@email.com",  
            "password": "123",
            "salary": 60000.0,
            "address": "456 Mechanic Ave"
        }
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.post('/mechanics/', json=payload, headers=headers)
        self.assertEqual(response.status_code, 409)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], "Email already in use")
        
    def test_invalid_create_mechanic(self):
        payload = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "invalid-email",  
            "password": "123",
            "salary": 60000.0,
            "address": "123 Main St"
        }
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.post('/mechanics/', json=payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json)
        self.assertIn('Not a valid email address.', response.json['email'][0])
        
# -------------------------------------------------------------------------------------------        

    def test_get_mechanics(self):
        
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.get('/mechanics/', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(m['email'] == "testmech@email.com" for m in response.json))
       
        
    def test_search_all_mechanics(self):
        with self.app.app_context():
            mech2 = Mechanics(
                first_name="Alice",
                last_name="Smith",
                email="alice@email.com",
                password=generate_password_hash('abc'),
                salary=60000.0,
                address="456 Mechanic Ave"
            )
            db.session.add(mech2)
            db.session.commit()
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.get('/mechanics/', headers=headers)
        self.assertEqual(response.status_code, 200)
        emails = [m['email'] for m in response.json]
        self.assertIn("testmech@email.com", emails)
        self.assertIn("alice@email.com", emails)
        
# -------------------------------------------------------------------------------------------        

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
        
# -------------------------------------------------------------------------------------------        

    def test_get_mechanic_profile(self):
        headers = {"Authorization": "Bearer " + self.mechanic_token}
        response = self.client.get('/mechanics/profile', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['email'], "testmech@email.com")
       
   
        
# -------------------------------------------------------------------------------------------

    def test_update_mechanic(self):
        update_payload = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "janemech@email.com",
            "password": "456",
            "salary": 70000.0,
            "address": "789 Mechanic Blvd"
        }
        
      
# -------------------------------------------------------------------------------------------

    def test_delete_mechanic(self):
        headers = {"Authorization": "Bearer " + self.mechanic_token}
        response = self.client.delete('/mechanics', headers=headers)
       
      
        
# -------------------------------------------------------------------------------------------

    def test_unauthorized_delete_mechanic(self):
        response = self.client.delete('/mechanics')
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
