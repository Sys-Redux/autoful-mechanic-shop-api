from app import create_app
from app.models import Mechanic, Inventory, ServiceInventory, db
from datetime import date
from app.utils.util import encode_mechanic_token
from bcrypt import hashpw, gensalt
import unittest

class TestInventory(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        hashed_password = hashpw('mechanicpass'.encode('utf-8'), gensalt()).decode('utf-8')
        self.mechanic = Mechanic(name='test_mechanic', email='test_mechanic@email.com', phone='1234567890', salary=50000.0, password=hashed_password)
        self.inventory_item = Inventory(part_name='Brake Pad', price=49.99, quantity_in_stock=100)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(self.mechanic)
            db.session.add(self.inventory_item)
            db.session.commit()
            self.token = encode_mechanic_token(1)
            self.client = self.app.test_client()

    def test_create_inventory(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        inventory_payload = {
            'part_name': 'Oil Filter',
            'price': 15.99,
            'quantity_in_stock': 50
        }
        response = self.client.post('/inventory/', json=inventory_payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('Oil Filter', str(response.data))

    def test_invalid_create_inventory(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        inventory_payload = {
            'part_name': '',
            'price': -10.00,
            'quantity_in_stock': -5
        }
        response = self.client.post('/inventory/', json=inventory_payload, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_get_all_inventory(self):
        response = self.client.get('/inventory/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Brake Pad', str(response.data))

    def test_get_single_inventory(self):
        response = self.client.get('/inventory/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Brake Pad', str(response.data))

    def test_get_single_inventory_not_found(self):
        response = self.client.get('/inventory/999')
        self.assertEqual(response.status_code, 404)
        self.assertIn('Inventory part not found', str(response.data))

    def test_update_inventory(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        update_payload = {
            'part_name': 'Brake Pad - Updated',
            'price': 54.99,
            'quantity_in_stock': 80
        }
        response = self.client.put('/inventory/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Brake Pad - Updated', str(response.data))

    def test_update_inventory_not_found(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        update_payload = {
            'part_name': 'Nonexistent Part',
            'price': 20.00,
            'quantity_in_stock': 10
        }
        response = self.client.put('/inventory/999', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Inventory part not found', str(response.data))

    def test_invalid_update_inventory(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        update_payload = {
            'part_name': '',
            'price': -5.00,
            'quantity_in_stock': -10
        }
        response = self.client.put('/inventory/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Length must be between 1 and 255.', str(response.data))

    def test_delete_inventory(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.delete('/inventory/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Inventory part deleted successfully', str(response.data))

    def test_delete_inventory_not_found(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.delete('/inventory/999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Inventory part not found', str(response.data))

    def test_unauthorized_delete_inventory(self):
        response = self.client.delete('/inventory/1')
        self.assertEqual(response.status_code, 401)

    def test_search_inventory(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.get('/inventory/search?part_name=Brake', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Brake Pad', str(response.data))

    def test_search_inventory_no_results(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.get('/inventory/search?part_name=Nonexistent', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Brake Pad', str(response.data))

    def test_search_inventory_unauthorized(self):
        response = self.client.get('/inventory/search?part_name=Brake')
        self.assertEqual(response.status_code, 401)

    def test_low_stock_inventory(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        # First, reduce stock to below threshold
        update_payload = {
            'quantity_in_stock': 3
        }
        self.client.put('/inventory/1', json=update_payload, headers=headers)

        response = self.client.get('/inventory/low-stock?threshold=5', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Brake Pad', str(response.data))

    def test_low_stock_inventory_no_results(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.get('/inventory/low-stock?threshold=2', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Brake Pad', str(response.data))

    def test_low_stock_inventory_unauthorized(self):
        response = self.client.get('/inventory/low-stock?threshold=5')
        self.assertEqual(response.status_code, 401)