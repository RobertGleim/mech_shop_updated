from app import create_app
from app.models import Customer, db
import unittest
from werkzeug.security import  check_password_hash, generate_password_hash
from app.util.auth import generate_token, encode_token


class TestCustomer(unittest.TestCase):

    def setUp(self):
        self.app = create_app('TestingConfig')
        self.customer = Customer(
            first_name="Test",
            last_name="User",
            email="test@email.com",
            password=generate_password_hash('123'),
            phone="1234567890",
            address="123 Test St"
        )
        
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(self.customer)
            db.session.commit()
        self.token = encode_token(1,"customer")    
        self.client = self.app.test_client()
        
    def test_create_customer(self):
        customer_payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test@email.com",
            "password": "123",
            "phone": "1234567890",
            "address": "123 Main St"
        }
        
        response = self.client.post('/customers', json=customer_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['first_name'], "John")
        self.assertEqual(response.json['last_name'], "Doe")
        self.assertEqual(response.json['email'], "test@email.com")
        self.assertEqual(response.json['phone'], "1234567890")
        self.assertEqual(response.json['address'], "123 Main St")
        self.assertTrue(check_password_hash(response.json['password'], "123"))
        
def test_invalid_create_customer(self):
        customer_payload = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "invalid-email",
            "password": "123",
            "phone": "1234567890",
            "address": "123 Main St"
        }
        
        response = self.client.post('/customers', json=customer_payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid email format', response.json['error'])   
        
def test_get_customers(self):
    response = self.client.get('/customers')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.jsaon[0]['first_name'], "Test")
    
    
def test_login_customer(self):
    login_creds = {
        "email": "test@email.com"
        "password": "123"
    }
    response = self.client.post('/customers/login', json=login_creds)
    self.assertEqual(response.status_code, 200)
    self.assertin('token', response.json)
    
def test_delete_customer(self):
    headers = {"authorization": "Bearer" + self.token}
    
    response = self.client.delete('/customers', headers=headers)
    self.assertEqual(response.status_code, 200)
    self.assertIn(response.json['message'],'Sorry to see you go customer 1 ' ) 
    
def test_unathurized_customer(self):
   
    response = self.client.delete('/customers')
    self.assertEqual(response.status_code, 401)
    
def test_update_customer(self):
    headers = {"authorization": "Bearer" + self.token}
    update_payload = {
        "first_name": "Jane",
            "last_name": "Doe",
            "email": "newemail@email.com",
            "password": "123",
            "phone": "1234567890",
            "address": "123 Main St"
        }
     
    response = self.client.put('/customers', headers=headers,json=update_payload)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json["email"] "newemail@email.com")
    
    
   
             

        