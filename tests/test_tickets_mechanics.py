from app import create_app
from app.models import Ticket_Mechanics, Service_Ticket, Mechanics, db
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
            # Create related Service_Ticket and Mechanic
            self.service_ticket = Service_Ticket(
                customer_id=1,
                service_description="Test Service",
                price=100.0,
                vin="VIN1234567890",
                service_date=date.today()  # Use a Python date object
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

    def test_create_ticket_mechanic(self):
        payload = {
            "service_ticket_id": self.service_ticket_id,
            "mechanic_id": self.mechanic_id
        }
       
        self.client.delete(f'/ticket_mechanics/{self.service_ticket_id}/{self.mechanic_id}')
        response = self.client.post('/ticket_mechanics/', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['service_ticket_id'], self.service_ticket_id)
        self.assertEqual(response.json['mechanic_id'], self.mechanic_id)

    def test_get_ticket_mechanics(self):
        response = self.client.get('/ticket_mechanics/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(
            t['service_ticket_id'] == self.service_ticket_id and t['mechanic_id'] == self.mechanic_id
            for t in response.json
        ))

    def test_get_ticket_mechanic(self):
        response = self.client.get(f'/ticket_mechanics/{self.service_ticket_id}/get_ticket_mechanic')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(
            t['mechanic_id'] == self.mechanic_id for t in response.json
        ))

    def test_delete_ticket_mechanic(self):
        response = self.client.delete(f'/ticket_mechanics/{self.service_ticket_id}/{self.mechanic_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('deleted', response.json['message'])
        
        response = self.client.get(f'/ticket_mechanics/{self.service_ticket_id}/get_ticket_mechanic')
        self.assertEqual(response.status_code, 404)

    def test_get_ticket_mechanic_not_found(self):
        response = self.client.get(f'/ticket_mechanics/9999/get_ticket_mechanic')
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

    def test_delete_ticket_mechanic_not_found(self):
        response = self.client.delete(f'/ticket_mechanics/9999/8888')
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

    def test_assign_new_mechanic_to_ticket(self):
        # Create a new mechanic
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
        # Assign new mechanic to the existing ticket
        payload = {
            "service_ticket_id": self.service_ticket_id,
            "mechanic_id": new_mechanic_id
        }
        response = self.client.post('/ticket_mechanics/', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['service_ticket_id'], self.service_ticket_id)
        self.assertEqual(response.json['mechanic_id'], new_mechanic_id)
        # Confirm assignment exists
        response = self.client.get(f'/ticket_mechanics/{self.service_ticket_id}/get_ticket_mechanic')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(t['mechanic_id'] == new_mechanic_id for t in response.json))

if __name__ == "__main__":
    unittest.main()
