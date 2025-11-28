from app import create_app
from app.models import Mechanic, ServiceTicket, Inventory, ServiceInventory, db
from datetime import date
from app.utils.util import encode_mechanic_token
from bcrypt import hashpw, gensalt
import unittest

class TestServiceTicket(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        hashed_pw = hashpw('mechanicpass'.encode('utf-8'), gensalt()).decode('utf-8')
        service = ServiceTicket(VIN='1HGCM82633A123456', service_date=date(2024, 10, 1), service_desc='Initial service', customer_id=1)
        mechanic = Mechanic(name='service_mechanic', email='service_mechanic@email.com', phone='1234567890', salary=50000.0, password=hashed_pw)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(mechanic)
            db.session.add(service)
            db.session.commit()
            self.token = encode_mechanic_token(1)
            self.client = self.app.test_client()

    def test_create_service_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        ticket_payload = {
            'VIN': '1HGCM82633A654321',
            'service_date': '2024-11-01',
            'service_desc': 'Oil change and tire rotation',
            'customer_id': 1
        }
        response = self.client.post('/service_tickets/', json=ticket_payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('Oil change and tire rotation', str(response.data))

    def test_invalid_create_service_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        ticket_payload = {
            'VIN': '',
            'service_date': 'invalid-date',
            'service_desc': '',
            'customer_id': 1
        }
        response = self.client.post('/service_tickets/', json=ticket_payload, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_get_service_tickets(self):
        response = self.client.get('/service_tickets/')
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json), 1)

    def test_get_specific_service_ticket(self):
        response = self.client.get('/service_tickets/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Initial service', str(response.data))

    def test_assign_mechanic_to_service_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.put('/service_tickets/1/assign-mechanic/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('service_mechanic', str(response.data))

    def test_assign_mechanic_to_nonexistent_service_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.put('/service_tickets/999/assign-mechanic/1', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Service Ticket not found', str(response.data))

    def test_assign_nonexistent_mechanic_to_service_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.put('/service_tickets/1/assign-mechanic/999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Mechanic not found', str(response.data))

    def test_assign_mechanic_already_assigned(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        # First assignment
        self.client.put('/service_tickets/1/assign-mechanic/1', headers=headers)
        # Second assignment (should fail)
        response = self.client.put('/service_tickets/1/assign-mechanic/1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Mechanic already assigned to this service ticket', str(response.data))

    def test_remove_mechanic_from_service_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        # First assign mechanic
        self.client.put('/service_tickets/1/assign-mechanic/1', headers=headers)
        # Now remove mechanic
        response = self.client.put('/service_tickets/1/remove-mechanic/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('service_mechanic', str(response.data))

    def test_remove_mechanic_not_assigned(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.put('/service_tickets/1/remove-mechanic/1', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Mechanic not assigned to this service ticket', str(response.data))

    def test_delete_service_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.delete('/service_tickets/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Service Ticket deleted successfully', str(response.data))

    def test_delete_nonexistent_service_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.delete('/service_tickets/999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Service Ticket not found', str(response.data))

    def test_edit_service_ticket_mechanics(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        # Assign mechanic first
        self.client.put('/service_tickets/1/assign-mechanic/1', headers=headers)
        # Edit mechanics (remove all)
        edit_payload = {
            'add_ids': [],
            'remove_ids': [1]
        }
        response = self.client.put('/service_tickets/1/edit-mechanics', json=edit_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('service_mechanic', str(response.data))

    def test_invalid_edit_service_ticket_mechanics(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        edit_payload = {
            'add_ids': 'not-a-list',
            'remove_ids': []
        }
        response = self.client.put('/service_tickets/1/edit-mechanics', json=edit_payload, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_add_inventory_to_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}

        with self.app.app_context():
            inventory = Inventory(part_name='Brake Pad', price=29.99, quantity_in_stock=10)
            db.session.add(inventory)
            db.session.commit()

        inventory_payload = {
            'inventory_id': 1,
            'quantity_used': 2
        }
        response = self.client.post('/service_tickets/1/add-inventory', json=inventory_payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        self.assertIn('Brake Pad', str(response.data))

    def test_add_inventory_to_ticket_insufficient_stock(self):
        headers = {'Authorization': f'Bearer {self.token}'}

        with self.app.app_context():
            inventory = Inventory(part_name='Oil Filter', price=15.99, quantity_in_stock=1)
            db.session.add(inventory)
            db.session.commit()

        inventory_payload = {
            'inventory_id': 1,
            'quantity_used': 5
        }
        response = self.client.post('/service_tickets/1/add-inventory', json=inventory_payload, headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Insufficient stock', str(response.data))

    def test_add_inventory_to_nonexistent_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        inventory_payload = {
            'inventory_id': 1,
            'quantity_used': 1
        }
        response = self.client.post('/service_tickets/999/add-inventory', json=inventory_payload, headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Service Ticket not found', str(response.data))

    def test_add_nonexistent_inventory_to_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        inventory_payload = {
            'inventory_id': 999,
            'quantity_used': 1
        }
        response = self.client.post('/service_tickets/1/add-inventory', json=inventory_payload, headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Inventory Part not found', str(response.data))

    def test_remove_inventory_from_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}

        with self.app.app_context():
            inventory = Inventory(part_name='Air Filter', price=19.99, quantity_in_stock=5)
            db.session.add(inventory)
            db.session.commit()

            service_inventory = ServiceInventory(service_ticket_id=1, inventory_id=inventory.id, quantity_used=1)
            db.session.add(service_inventory)
            db.session.commit()

        response = self.client.put('/service_tickets/1/remove-inventory/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Air Filter', str(response.data))
        self.assertIn('restored stock', str(response.data))

    def test_remove_nonexistent_inventory_from_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.put('/service_tickets/1/remove-inventory/999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Service Inventory record not found', str(response.data))

    def test_remove_inventory_from_nonexistent_ticket(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.put('/service_tickets/999/remove-inventory/1', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Service Inventory record not found', str(response.data))

    def test_remove_inventory_unauthorized(self):
        response = self.client.put('/service_tickets/1/remove-inventory/1')
        self.assertEqual(response.status_code, 401)