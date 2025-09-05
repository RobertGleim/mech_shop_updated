from app import create_app
from app.models import Service_Ticket, db
import unittest
from werkzeug.security import generate_password_hash
from datetime import date

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

    def test_create_service_ticket(self):
        payload = {
            "customer_id": 2,
            "service_description": "Tire Rotation",
            "price": 19.99,
            "vin": "1HGCM82633A004353",
            "service_date": str(date.today())
        }
        response = self.client.post('/service_tickets/', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['service_description'], "Tire Rotation")
        self.assertEqual(response.json['price'], 19.99)
        self.assertEqual(response.json['vin'], "1HGCM82633A004353")

    def test_get_service_tickets(self):
        response = self.client.get('/service_tickets/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(t['service_description'] == "Oil Change" for t in response.json))

    def test_get_service_ticket(self):
        response = self.client.get(f'/service_tickets/{self.ticket_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['service_description'], "Oil Change")

    def test_update_service_ticket(self):
        update_payload = {
            "customer_id": 1,
            "service_description": "Brake Inspection",
            "price": 39.99,
            "vin": "1HGCM82633A004352",
            "service_date": str(date.today())
        }
        response = self.client.put(f'/service_tickets/{self.ticket_id}', json=update_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['service_description'], "Brake Inspection")
        self.assertEqual(response.json['price'], 39.99)

    def test_delete_service_ticket(self):
        response = self.client.delete(f'/service_tickets/{self.ticket_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('deleted', response.json['message'])

    def test_get_popular_service_tickets(self):
        response = self.client.get('/service_tickets/popular')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

if __name__ == "__main__":
    unittest.main()
