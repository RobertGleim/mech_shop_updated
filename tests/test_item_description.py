from app import create_app
from app.models import ItemsDescription, InventoryItem, db
import unittest
from datetime import date

# python -m unittest discover tests

class TestItemDescriptions(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.item_description = ItemsDescription(
                part_name="Oil Filter",
                part_description="High quality oil filter",
                part_price=9.99
            )
            db.session.add(self.item_description)
            db.session.commit()
            self.item_description_id = self.item_description.id
            self.inventory_item = InventoryItem(
                name="Oil Filter",
                items_description_id=self.item_description_id
            )
            db.session.add(self.inventory_item)
            db.session.commit()
            self.inventory_item_id = self.inventory_item.id

            # Import and create admin and mechanic tokens
            from app.util.auth import create_admin_token, create_mechanic_token
            self.admin_token = create_admin_token(1)
            self.mechanic_token = create_mechanic_token(2)

# -------------------------------------------------------------------------------------------
        def test_mechanic_cannot_create_item_description(self):
            payload = {
                "part_name": "Cabin Filter",
                "part_description": "Mechanic should not create",
                "part_price": 19.99
            }
            headers = {"Authorization": "Bearer " + self.mechanic_token}
            response = self.client.post('/item_descriptions/', json=payload, headers=headers)
            self.assertIn(response.status_code, (401, 403))
            
        def test_mechanic_cannot_update_item_description(self):
            payload = {
                "part_name": "Should Not Update",
                "part_description": "Mechanic update attempt",
                "part_price": 15.99
            }
            headers = {"Authorization": "Bearer " + self.mechanic_token}
            response = self.client.put(f'/item_descriptions/{self.inventory_item_id}', json=payload, headers=headers)
            self.assertIn(response.status_code, (401, 403))

        def test_mechanic_cannot_delete_item_description(self):
            headers = {"Authorization": "Bearer " + self.mechanic_token}
            response = self.client.delete(f'/item_descriptions/{self.item_description_id}', headers=headers)
            self.assertIn(response.status_code, (401, 403))

        def test_admin_can_get_item_description(self):
            headers = {"Authorization": "Bearer " + self.admin_token}
            response = self.client.get(f'/item_descriptions/{self.item_description_id}', headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json['part_name'], "Oil Filter")

        def test_admin_can_get_item_descriptions(self):
            headers = {"Authorization": "Bearer " + self.admin_token}
            response = self.client.get('/item_descriptions/', headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(any(i['part_name'] == "Oil Filter" for i in response.json))

    def test_create_item_description(self):
        payload = {
            "part_name": "Air Filter",
            "part_description": "Premium air filter",
            "part_price": 14.99
        }
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.post('/item_descriptions/', json=payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['part_name'], "Air Filter")
        self.assertEqual(response.json['part_description'], "Premium air filter")
        self.assertEqual(response.json['part_price'], 14.99)
        
# -------------------------------------------------------------------------------------------

    def test_get_item_descriptions(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.get('/item_descriptions/', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(i['part_name'] == "Oil Filter" for i in response.json))
        
# -------------------------------------------------------------------------------------------

    def test_get_item_description(self):
        headers = {"Authorization": "Bearer " + self.mechanic_token}
        response = self.client.get(f'/item_descriptions/{self.item_description_id}', headers=headers)
        self.assertEqual(response.status_code, 403)
        # Optionally check for error message
        # self.assertIn('message', response.json)
        
# -------------------------------------------------------------------------------------------

    def test_update_item_description(self):
        payload = {
            "part_name": "Oil Filter Updated",
            "part_description": "Updated description",
            "part_price": 12.99
        }
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.put(f'/item_descriptions/{self.inventory_item_id}', json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['part_name'], "Oil Filter Updated")
        self.assertEqual(response.json['part_description'], "Updated description")
        self.assertEqual(response.json['part_price'], 12.99)
        
# -------------------------------------------------------------------------------------------

    def test_delete_item_description(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        with self.app.app_context():
            inv = db.session.query(InventoryItem).filter_by(items_description_id=self.item_description_id).first()
            if inv:
                db.session.delete(inv)
                db.session.commit()
        response = self.client.delete(f'/item_descriptions/{self.item_description_id}', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json)
        self.assertIn('deleted', response.json['message'])
        
        response = self.client.get(f'/item_descriptions/{self.item_description_id}', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)
        
# -------------------------------------------------------------------------------------------

    def test_get_item_description_not_found(self):
        headers = {"Authorization": "Bearer " + self.mechanic_token}
        response = self.client.get('/item_descriptions/9999', headers=headers)
        self.assertEqual(response.status_code, 403)
        # Optionally check for error message
        # self.assertIn('message', response.json)
        
# -------------------------------------------------------------------------------------------

    def test_delete_item_description_not_found(self):
        headers = {"Authorization": "Bearer " + self.admin_token}
        response = self.client.delete('/item_descriptions/9999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('message', response.json)

if __name__ == "__main__":
    unittest.main()
