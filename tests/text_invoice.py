from app import create_app
from app.models import Invoice, Invoice_Inventory_Link, InventoryItem, ItemsDescription, Customers, Service_Ticket, db
import unittest
from datetime import datetime

class TestInvoices(unittest.TestCase):
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
                password="123",
                phone="1234567890",
                address="123 Test St"
            )
            db.session.add(self.customer)
            db.session.commit()
            self.ticket = Service_Ticket(
                customer_id=self.customer.id,
                service_description="Oil change",
                price=50.0,
                vin="VIN1234567890"
            )
            db.session.add(self.ticket)
            db.session.commit()
            self.desc = ItemsDescription(
                part_name="Oil Filter",
                part_description="High quality oil filter",
                part_price=9.99
            )
            db.session.add(self.desc)
            db.session.commit()
            self.inventory_item = InventoryItem(
                name="Oil Filter",
                items_description_id=self.desc.id
            )
            db.session.add(self.inventory_item)
            db.session.commit()
            self.invoice = Invoice(
                customer_id=self.customer.id,
                service_ticket_id=self.ticket.id,
                price=100.0,
                invoice_date=datetime.now(),
                submitted=False
            )
            db.session.add(self.invoice)
            db.session.commit()
            self.invoice_id = self.invoice.id
            self.inventory_item_id = self.inventory_item.id

    def test_create_invoice(self):
        payload = {
            "customer_id": self.customer.id,
            "service_ticket_id": self.ticket.id,
            "price": 200.0,
            "invoice_date": datetime.now().isoformat(),
            "submitted": False
        }
        response = self.client.post('/invoice/', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['customer_id'], self.customer.id)
        self.assertEqual(response.json['service_ticket_id'], self.ticket.id)
        self.assertEqual(response.json['price'], 200.0)

    def test_get_invoices(self):
        response = self.client.get('/invoice/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(i['id'] == self.invoice_id for i in response.json))

    def test_get_invoice(self):
        response = self.client.get(f'/invoice/{self.invoice_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['id'], self.invoice_id)

    def test_update_invoice(self):
        payload = {"price": 150.0, "submitted": True}
        response = self.client.put(f'/invoice/{self.invoice_id}', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['price'], 150.0)
        self.assertEqual(response.json['submitted'], True)

    def test_delete_invoice(self):
        response = self.client.delete(f'/invoice/{self.invoice_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('deleted', response.json['message'])
        # Confirm deletion returns not found (API returns empty dict)
        response = self.client.get(f'/invoice/{self.invoice_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {})

    def test_delete_invoice_not_found(self):
        response = self.client.delete('/invoice/9999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

    def test_update_invoice_not_found(self):
        payload = {"price": 999.0}
        response = self.client.put('/invoice/9999', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

    def test_create_invoice_invalid(self):
        payload = {"customer_id": None, "service_ticket_id": None, "price": None}
        response = self.client.post('/invoice/', json=payload)
        self.assertEqual(response.status_code, 400)

    def test_add_invoice_item(self):
        payload = {"inventory_item_id": self.inventory_item_id, "quantity": 2}
        response = self.client.post(f'/invoice/{self.invoice_id}/add_invoice_item', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn('message', response.json)
        self.assertEqual(response.json['quantity'], 2)

    def test_add_invoice_item_not_found(self):
        payload = {"inventory_item_id": 9999, "quantity": 1}
        response = self.client.post(f'/invoice/{self.invoice_id}/add_invoice_item', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

    def test_delete_invoice_item(self):
        # First add the item
        payload = {"inventory_item_id": self.inventory_item_id, "quantity": 1}
        self.client.post(f'/invoice/{self.invoice_id}/add_invoice_item', json=payload)
        # Now delete
        response = self.client.delete(f'/invoice/{self.invoice_id}/delete_invoice_item/{self.inventory_item_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)

    def test_delete_invoice_item_not_found(self):
        response = self.client.delete(f'/invoice/{self.invoice_id}/delete_invoice_item/9999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

    def test_update_invoice_item(self):
        # Add an item
        payload = {"inventory_item_id": self.inventory_item_id, "quantity": 1}
        self.client.post(f'/invoice/{self.invoice_id}/add_invoice_item', json=payload)
        # Create a new inventory item to update to
        new_desc = ItemsDescription(
            part_name="Air Filter",
            part_description="Premium air filter",
            part_price=14.99
        )
        db.session.add(new_desc)
        db.session.commit()
        new_item = InventoryItem(
            name="Air Filter",
            items_description_id=new_desc.id
        )
        db.session.add(new_item)
        db.session.commit()
        payload = {"inventory_item_id": new_item.id}
        response = self.client.put(f'/invoice/{self.invoice_id}/update_invoice_item/{self.inventory_item_id}', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)

    def test_update_invoice_item_not_found(self):
        payload = {"inventory_item_id": 9999}
        response = self.client.put(f'/invoice/{self.invoice_id}/update_invoice_item/9999', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

if __name__ == "__main__":
    unittest.main()
