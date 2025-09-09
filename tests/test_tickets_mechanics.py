from app import create_app
from app.models import Ticket_Mechanics, Service_Ticket, Mechanics, db
from app.util.auth import create_admin_token
import unittest
from datetime import date
from werkzeug.security import generate_password_hash

# python -m unittest discover tests

class TestTicketMechanics(unittest.TestCase):

    
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            # Create a test admin user (simulate user_id=1)
            self.admin_user_id = 1
            # Create a service ticket and mechanic
            self.service_ticket = Service_Ticket(
                customer_id=1,
                service_description="Test Service",
                price=100.0,
                vin="VIN1234567890",
                service_date=date.today() 
            )
            self.mechanic = Mechanics(
                first_name="Test",
                last_name="Mechanic",
                email="mech@email.com",
                password="hashed",
                salary=50000.0,
                address="123 Mechanic St"
            )
            db.session.add(self.service_ticket)
            db.session.add(self.mechanic)
            db.session.commit()
            self.service_ticket_id = self.service_ticket.id
            self.mechanic_id = self.mechanic.id
            self.ticket_mechanic = Ticket_Mechanics(
                service_ticket_id=self.service_ticket_id,
                mechanic_id=self.mechanic_id
            )
            db.session.add(self.ticket_mechanic)
            db.session.commit()
        # Generate admin token for all requests
        self.admin_token = create_admin_token(self.admin_user_id)
        self.auth_header = {"Authorization": f"Bearer {self.admin_token}"}
            
# -------------------------------------------------------------------------------------------         

    def test_create_ticket_mechanic(self):
        payload = {
            "service_ticket_id": self.service_ticket_id,
            "mechanic_id": self.mechanic_id
        }
        self.client.delete(f'/ticket_mechanics/{self.service_ticket_id}/{self.mechanic_id}', headers=self.auth_header)
        response = self.client.post('/ticket_mechanics/', json=payload, headers=self.auth_header)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['service_ticket_id'], self.service_ticket_id)
        self.assertEqual(response.json['mechanic_id'], self.mechanic_id)
        
# -------------------------------------------------------------------------------------------        

    def test_get_ticket_mechanics(self):
        response = self.client.get('/ticket_mechanics/', headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(
            t['service_ticket_id'] == self.service_ticket_id and t['mechanic_id'] == self.mechanic_id
            for t in response.json
        ))
        
# -------------------------------------------------------------------------------------------        

    def test_get_ticket_mechanic(self):
        response = self.client.get(f'/ticket_mechanics/{self.service_ticket_id}/get_ticket_mechanic', headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(
            t['mechanic_id'] == self.mechanic_id for t in response.json
        ))
        
    def test_get_ticket_mechanic_not_found(self):
        response = self.client.get(f'/ticket_mechanics/9999/get_ticket_mechanic', headers=self.auth_header)
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)
        
# -------------------------------------------------------------------------------------------

    def test_delete_ticket_mechanic(self):
        response = self.client.delete(f'/ticket_mechanics/{self.service_ticket_id}/{self.mechanic_id}', headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('deleted', response.json['message'])
        response = self.client.get(f'/ticket_mechanics/{self.service_ticket_id}/get_ticket_mechanic', headers=self.auth_header)
        if response.status_code == 404:
            self.assertIn('message', response.json)
        elif response.status_code == 200:
            self.assertTrue(response.json == [] or response.json == {} or response.json is None)
        else:
            self.fail(f"Unexpected status code: {response.status_code}")
      
    def test_delete_ticket_mechanic_not_found(self):
        response = self.client.delete(f'/ticket_mechanics/9999/8888', headers=self.auth_header)
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

# -------------------------------------------------------------------------------------------

    def test_assign_new_mechanic_to_ticket(self):
        with self.app.app_context():
            new_mechanic = Mechanics(
                first_name="Jane",
                last_name="Smith",
                email="jane@email.com",
                password=generate_password_hash('123'),
                salary=60000.0,
                address="456 Mechanic Ave"
            )
            db.session.add(new_mechanic)
            db.session.commit()
            new_mechanic_id = new_mechanic.id
        payload = {
            "service_ticket_id": self.service_ticket_id,
            "mechanic_id": new_mechanic_id
        }
        response = self.client.post('/ticket_mechanics/', json=payload, headers=self.auth_header)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['service_ticket_id'], self.service_ticket_id)
        self.assertEqual(response.json['mechanic_id'], new_mechanic_id)
        response = self.client.get(f'/ticket_mechanics/{self.service_ticket_id}/get_ticket_mechanic', headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(t['mechanic_id'] == new_mechanic_id for t in response.json))
        
# -------------------------------------------------------------------------------------------
        
    def test_unassign_mechanic_to_ticket(self):
        response = self.client.get(f'/ticket_mechanics/{self.service_ticket_id}/get_ticket_mechanic', headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(t['mechanic_id'] == self.mechanic_id for t in response.json))
        response = self.client.delete(f'/ticket_mechanics/{self.service_ticket_id}/{self.mechanic_id}', headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('deleted', response.json['message'])
        response = self.client.get(f'/ticket_mechanics/{self.service_ticket_id}/get_ticket_mechanic', headers=self.auth_header)
        if response.status_code == 404:
            self.assertIn('message', response.json)
        elif response.status_code == 200:
            self.assertTrue(
                response.json == [] or
                response.json == {} or
                response.json is None or
                (isinstance(response.json, dict) and 'message' in response.json) or
                (isinstance(response.json, list) and len(response.json) == 1 and isinstance(response.json[0], dict) and 'message' in response.json[0])
            , f"Unexpected 200 response: {response.json}")
        else:
            self.fail(f"Unexpected status code: {response.status_code}, response: {response.json}")

if __name__ == "__main__":
    unittest.main()
