from app import create_app
from app.models import Mechanics, Service_Ticket, db
from app.util.auth import encode_token
import unittest
from app.models import Customers
from werkzeug.security import generate_password_hash
from app.util.auth import encode_token

class TestSearch(unittest.TestCase):
   
    
    
    # python -m unittest discover tests
    
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.mechanic = Mechanics(
                first_name="Popular",
                last_name="Mechanic",
                email="popular@mech.com",
                password="123",
                salary=50000.0,
                address="123 Mechanic St"
            )
            db.session.add(self.mechanic)
            db.session.commit()
            self.mechanic_id = self.mechanic.id
            self.token = encode_token(self.mechanic_id)

            
            from app.models import ItemsDescription, InventoryItem
            desc = ItemsDescription(
                part_name="Oil Filter",
                part_description="High quality oil filter",
                part_price=9.99
            )
            db.session.add(desc)
            db.session.commit()
            item = InventoryItem(
                name="Oil Filter",
                items_description_id=desc.id
            )
            db.session.add(item)
            db.session.commit()
            
            ticket1 = Service_Ticket(
                customer_id=None,
                service_description="Oil change",
                price=50.0,
                vin="VIN1234567890"
            )
            ticket2 = Service_Ticket(
                customer_id=None,
                service_description="Tire rotation",
                price=30.0,
                vin="VIN0987654321"
            )
            ticket1.mechanics.append(self.mechanic)
            ticket2.mechanics.append(self.mechanic)
            db.session.add(ticket1)
            db.session.add(ticket2)
            db.session.commit()
            self.ticket_ids = [ticket1.id, ticket2.id]
            
# -------------------------------------------------------------------------------------------            
            
    def test_get_popular_service_tickets(self):
        from app.util.auth import create_admin_token
        admin_token = create_admin_token(self.mechanic_id)
        headers = {"Authorization": "Bearer " + admin_token}
        response = self.client.get('/service_tickets/popular', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
     
# -------------------------------------------------------------------------------------------                

    def test_search_popular_mechanic(self):
        from app.util.auth import create_admin_token
        admin_token = create_admin_token(self.mechanic_id)
        headers = {"Authorization": "Bearer " + admin_token}
        response = self.client.get('/mechanics/', headers=headers)
        self.assertEqual(response.status_code, 200)
        found = any(m.get('first_name') == 'Popular' for m in response.json)
        self.assertTrue(found)
        
# -------------------------------------------------------------------------------------------        
        
    def test_mechanic_search_tickets_by_id(self):
        headers = {"Authorization": "Bearer " + self.token}
        
        response = self.client.get(f'/service_tickets/?mechanic_id={self.mechanic_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        ticket_ids = [t['id'] for t in response.json]
        for tid in self.ticket_ids:
            self.assertIn(tid, ticket_ids)
# -------------------------------------------------------------------------------------------            
            
    def test_customer_search_tickets_by_token(self):
        with self.app.app_context():
            customer = Customers(
                first_name="Ticket",
                last_name="Customer",
                email="ticketcustomer@email.com",
                password=generate_password_hash('abc'),
                phone="5555555555",
                address="789 Main St"
            )
            db.session.add(customer)
            db.session.commit()
            customer_id = customer.id
            customer_token = encode_token(customer_id, role='customer')
           
            ticket1 = Service_Ticket(
                customer_id=customer_id,
                service_description="Brake job",
                price=120.0,
                vin="VIN1111111111"
            )
            ticket2 = Service_Ticket(
                customer_id=customer_id,
                service_description="Alignment",
                price=80.0,
                vin="VIN2222222222"
            )
            db.session.add(ticket1)
            db.session.add(ticket2)
            db.session.commit()
            ticket_ids = [ticket1.id, ticket2.id]
        headers = {"Authorization": "Bearer " + customer_token}
        response = self.client.get(f'/service_tickets/?customer_id={customer_id}', headers=headers)
        # Customer role is forbidden for this route, should be 403
        self.assertEqual(response.status_code, 403)

# ------------------------------------------------------------------------------------------- 

    def test_search_inventory_items(self):
        headers = {"Authorization": "Bearer " + self.token}
        response = self.client.get('/inventory/search?part_name=Oil', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(i['part_name'] == "Oil Filter" for i in response.json))   
            
# -------------------------------------------------------------------------------------------                    
            
    def test_search_inventory_by_description(self):
        from app.models import ItemsDescription, InventoryItem
        with self.app.app_context():
            desc = ItemsDescription(
                part_name="Cabin Filter",
                part_description="Removes dust and pollen",
                part_price=19.99
            )
            db.session.add(desc)
            db.session.commit()
            item = InventoryItem(
                name="Cabin Filter",
                items_description_id=desc.id
            )
            db.session.add(item)
            db.session.commit()
        headers = {"Authorization": "Bearer " + self.token}
        response = self.client.get('/inventory/search?part_description=dust', headers=headers)
        self.assertEqual(response.status_code, 200)
        found = any(i.get('part_name') == 'Cabin Filter' for i in response.json)
        self.assertTrue(found)            

if __name__ == "__main__":
    unittest.main()
