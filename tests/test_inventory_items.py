from app import create_app
from app.models import InventoryItem, ItemsDescription, db
import unittest

# python -m unittest discover tests

class TestInventoryItems(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.desc = ItemsDescription(
                part_name="Oil Filter",
                part_description="High quality oil filter",
                part_price=9.99
            )
            db.session.add(self.desc)
            db.session.commit()
            self.desc_id = self.desc.id
            self.inventory_item = InventoryItem(
                name="Oil Filter",
                items_description_id=self.desc_id
            )
            db.session.add(self.inventory_item)
            db.session.commit()
            self.inventory_item_id = self.inventory_item.id
            
# -------------------------------------------------------------------------------------------

    def test_create_inventory_item(self):
        payload = {
            "name": "Air Filter",
            "items_description_id": self.desc_id
        }
        response = self.client.post('/inventory/', json=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'], "Air Filter")
        self.assertEqual(response.json['items_description_id'], self.desc_id)
        
# -------------------------------------------------------------------------------------------

    def test_get_inventory_items(self):
        response = self.client.get('/inventory/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(i['name'] == "Oil Filter" for i in response.json))
        
# -------------------------------------------------------------------------------------------
        

    def test_get_inventory_item(self):
        response = self.client.get(f'/inventory/{self.inventory_item_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "Oil Filter")
        
# -------------------------------------------------------------------------------------------        

    def test_update_inventory_item(self):
        payload = {
            "name": "Oil Filter Updated",
            "items_description_id": self.desc_id
        }
        response = self.client.put(f'/inventory/{self.inventory_item_id}', json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "Oil Filter Updated")
        self.assertEqual(response.json['items_description_id'], self.desc_id)

# -------------------------------------------------------------------------------------------

    def test_delete_inventory_item(self):
        response = self.client.delete(f'/inventory/{self.inventory_item_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('deleted', response.json['message'])
        
        response = self.client.get(f'/inventory/{self.inventory_item_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {})

# -------------------------------------------------------------------------------------------

    def test_delete_inventory_item_not_found(self):
        response = self.client.delete('/inventory/9999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

# -------------------------------------------------------------------------------------------

    def test_update_inventory_item_not_found(self):
        payload = {"name": "Doesn't Matter", "items_description_id": self.desc_id}
        response = self.client.put('/inventory/9999', json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

# -------------------------------------------------------------------------------------------

    def test_create_inventory_item_invalid(self):
        payload = {"name": "", "items_description_id": None}
        response = self.client.post('/inventory/', json=payload)
        self.assertEqual(response.status_code, 400)



    

if __name__ == "__main__":
    unittest.main()
