from app import create_app
from app.models import Customers, db
import unittest
from werkzeug.security import  check_password_hash, generate_password_hash
from app.util.auth import encode_token

# python -m unittest discover tests 
class TestCustomers(unittest.TestCase):
    

    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            
            self.customer = Customers(
                first_name="Test",
                last_name="User",
                email="test@email.com",
                password=generate_password_hash('123'),
                phone="1234567890",
                address="123 Test St"
            )
        
            db.session.add(self.customer)
            db.session.commit()
        
            self.token = encode_token(self.customer.id)

# -------------------------------------------------------------------------------------------

    def test_create_customer(self):
        customer_payload = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test123@email.com",
            "password": "123",
            "phone": "1234567890",
            "address": "123 Main St"
        }
        
        response = self.client.post('/customers/', json=customer_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['first_name'], "John")
        self.assertEqual(response.json['last_name'], "Doe")
        self.assertEqual(response.json['email'], "test123@email.com")
        self.assertEqual(response.json['phone'], "1234567890")
        self.assertEqual(response.json['address'], "123 Main St")
        self.assertTrue(check_password_hash(response.json['password'], "123"))
        self.assertIn('id', response.json)

# -------------------------------------------------------------------------------------------

    def test_invalid_create_customer(self):
        customer_payload = {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "invalid-email",
                "password": "123",
                "phone": "1234567890",
                "address": "123 Main St"
            }
            
        response = self.client.post('/customers/', json=customer_payload)
        self.assertIn('email', response.json)
        self.assertIn('Not a valid email address.', response.json['email'][0])
        self.assertEqual(response.status_code, 400)

# -------------------------------------------------------------------------------------------

    def test_get_customers(self):
        
        response = self.client.get('/customers/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['customers'][0]['first_name'], "Test")
        self.assertEqual(response.json['customers'][0]['last_name'], "User")
    
# -------------------------------------------------------------------------------------------

    def test_get_all_customers(self):
            
            with self.app.app_context():
                customer2 = Customers(
                    first_name="Alice",
                    last_name="Smith",
                    email="alice@email.com",
                    password=generate_password_hash('abc'),
                    phone="5555555555",
                    address="456 Main St"
                )
                db.session.add(customer2)
                db.session.commit()
            response = self.client.get('/customers/')
            self.assertEqual(response.status_code, 200)
            self.assertIn('customers', response.json)
            first_names = [c['first_name'] for c in response.json['customers']]
            self.assertIn("Test", first_names)
            self.assertIn("Alice", first_names)
            
# -------------------------------------------------------------------------------------------

    def test_update_customer(self):
            headers = {"Authorization": "Bearer " + self.token}
            update_payload = {
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "newemail@email.com",
                "password": "123",
                "phone": "1234567890",
                "address": "123 Main St"
        }

            response = self.client.put('/customers', json=update_payload, headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['first_name'], "Jane")
            self.assertEqual(response.json['last_name'], "Doe")
            self.assertEqual(response.json['email'], "newemail@email.com")
            self.assertEqual(response.json['phone'], "1234567890")
            self.assertEqual(response.json['address'], "123 Main St")
            self.assertTrue(check_password_hash(response.json['password'], "123"))
            
# -------------------------------------------------------------------------------------------

    def test_delete_customer(self):
        headers = {"Authorization": "Bearer " + self.token}
        response = self.client.delete('/customers', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], f"Sorry to see you go! {self.customer.id}")

# -------------------------------------------------------------------------------------------
        
    def test_login_customer(self):
        login_creds = {
            "email": "test@email.com",
            "password": "123"
    }
        response = self.client.post('/customers/login', json=login_creds)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json)
        
# ------------------------------------------------------------------------------------------- 
   
    

    def test_unathurized_customer(self):
    
        response = self.client.delete('/customers')
        self.assertEqual(response.status_code, 401)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['message'], "Token is missing!")
        
# -------------------------------------------------------------------------------------------
        
   
        
        
                
    
    
 
             

        