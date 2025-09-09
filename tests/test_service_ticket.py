from app import create_app
from app.models import Service_Ticket, db
import unittest
from werkzeug.security import generate_password_hash
from datetime import date
from app.util.auth import create_admin_token, create_mechanic_token

#  python -m unittest discover tests

class TestServiceTickets(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.ticket = Service_Ticket(
                customer_id=1,
                service_description="Oil Change",
                price=29.99,
                vin="1HGCM82633A004352",
                service_date=date.today()
            )
            db.session.add(self.ticket)
            db.session.commit()
            self.ticket_id = self.ticket.id  

            self.admin_token = create_admin_token(1)
            self.mechanic_token = create_mechanic_token(2)

    def test_create_service_ticket(self):
        payload = {
            "customer_id": 2,
            "service_description": "Tire Rotation",
            "price": 19.99,
            "vin": "1HGCM82633A004353",
            "service_date": str(date.today())
        }
        headers = {"Authorization": "Bearer " + self.mechanic_token}
        response = self.client.post('/service_tickets/', json=payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['service_description'], "Tire Rotation")
        self.assertEqual(response.json['price'], 19.99)
        self.assertEqual(response.json['vin'], "1HGCM82633A004353")
        
# ------------------------------------------------------------------------------------------- 

    def test_get_service_tickets(self):
        headers = {"Authorization": "Bearer " + self.mechanic_token}
        response = self.client.get('/service_tickets/', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(t['service_description'] == "Oil Change" for t in response.json))
        
# -------------------------------------------------------------------------------------------         

    def test_get_service_ticket(self):
        headers = {"Authorization": "Bearer " + self.mechanic_token}
        response = self.client.get(f'/service_tickets/{self.ticket_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['service_description'], "Oil Change")
        self.assertEqual(response.json['price'], 29.99)
        self.assertEqual(response.json['vin'], "1HGCM82633A004352")
        
# ------------------------------------------------------------------------------------------- 

    def test_update_service_ticket(self):
        update_payload = {
            "customer_id": 1,
            "service_description": "Brake Inspection",
            "price": 39.99,
            "vin": "1HGCM82633A004352",
            "service_date": str(date.today())
        }
        headers = {"Authorization": "Bearer " + self.mechanic_token}
        response = self.client.put(f'/service_tickets/{self.ticket_id}', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['service_description'], "Brake Inspection")
        self.assertEqual(response.json['price'], 39.99)
        self.assertEqual(response.json['vin'], "1HGCM82633A004352")

# -------------------------------------------------------------------------------------------

    def test_delete_service_ticket(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.delete(f'/service_tickets/{self.ticket_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('deleted', response.json['message'])
        response = self.client.get(f'/service_tickets/{self.ticket_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json is None or response.json == {})
    
# ------------------------------------------------------------------------------------------- 

    

if __name__ == "__main__":
    unittest.main()
