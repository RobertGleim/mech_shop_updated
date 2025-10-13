from app import create_app
from app.models import Customers, db
import unittest
from werkzeug.security import  check_password_hash, generate_password_hash
from app.util.auth import encode_token
from app.util.auth import create_admin_token, create_mechanic_token, create_customer_token

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
            self.customer_token = create_customer_token(self.customer.id)
            self.mechanic_token = create_mechanic_token(self.customer.id)
            self.admin_token = create_admin_token(self.customer.id)

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

    def test_get_customers_role_access(self):
       
        headers = {"Authorization": "Bearer " + self.mechanic_token}
        response = self.client.get('/customers/', headers=headers)
        self.assertEqual(response.status_code, 200)
       
       
    
# -------------------------------------------------------------------------------------------

    def test_get_all_customers(self):
       
        with self.app.app_context():
            from werkzeug.security import generate_password_hash
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
        
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.get('/customers/', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('customers', response.json)
        first_names = [c['first_name'] for c in response.json['customers']]
        self.assertIn("Test", first_names)
        self.assertIn("Alice", first_names)
            
# -------------------------------------------------------------------------------------------

    def test_update_customer_role_access(self):
        update_payload = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "newemail@email.com",
            "password": "123",
            "phone": "1234567890",
            "address": "123 Main St"
        }
       
        headers = {"Authorization": "Bearer " + self.customer_token}
        response = self.client.put('/customers', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
       

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
        
if __name__ == "__main__":
    unittest.main()

    # Additional admin endpoint tests
    class TestAdminCustomerActions(unittest.TestCase):
        def setUp(self):
            self.app = create_app('TestingConfig')
            self.client = self.app.test_client()
            with self.app.app_context():
                db.drop_all()
                db.create_all()
                # create an admin user
                admin = Customers(
                    first_name="Admin",
                    last_name="User",
                    email="admin@email.com",
                    password=generate_password_hash('adminpass'),
                    phone="1111111111",
                    address="1 Admin St"
                )
                db.session.add(admin)
                db.session.commit()
                self.admin_token = create_admin_token(admin.id)

                # create another customer to act on
                other = Customers(
                    first_name="Target",
                    last_name="User",
                    email="target@email.com",
                    password=generate_password_hash('target'),
                    phone="2222222222",
                    address="2 Target St"
                )
                db.session.add(other)
                db.session.commit()
                self.other_id = other.id

        def test_admin_update_customer_by_id(self):
            headers = {"Authorization": "Bearer " + self.admin_token}
            payload = {"first_name": "Updated", "phone": "9999999999"}
            response = self.client.put(f"/customers/{self.other_id}", json=payload, headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['first_name'], 'Updated')
            self.assertEqual(response.json['phone'], '9999999999')

        def test_admin_delete_customer_by_id(self):
            headers = {"Authorization": "Bearer " + self.admin_token}
            # delete target
            response = self.client.delete(f"/customers/{self.other_id}", headers=headers)
            self.assertIn(response.status_code, (200,204))

        def test_admin_cannot_delete_self(self):
            headers = {"Authorization": "Bearer " + self.admin_token}
            # extract admin id from token payload using helper not available here; we created admin with id in DB
            # we'll attempt to delete id 1 which is admin in this setup
            response = self.client.delete(f"/customers/1", headers=headers)
            self.assertEqual(response.status_code, 403)


    
 
             

        