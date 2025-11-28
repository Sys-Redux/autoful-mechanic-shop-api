from app import create_app
from app.models import Mechanic, ServiceTicket, db
from datetime import date
from app.utils.util import encode_mechanic_token
from bcrypt import hashpw, gensalt
import unittest

class TestMechanic(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        hashed_password = hashpw('mechanicpass'.encode('utf-8'), gensalt()).decode('utf-8')
        self.mechanic = Mechanic(name='test_mechanic', email='test_mechanic@email.com', phone='1234567890', salary=50000.0, password=hashed_password)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(self.mechanic)
            db.session.commit()
            self.token = encode_mechanic_token(1)
            self.client = self.app.test_client()

    def test_create_mechanic(self):
        mechanic_payload = {
            'name': 'Jane Smith',
            'email': 'jane.smith@email.com',
            'phone': '0987654321',
            'salary': 60000.0,
            'password': 'strongpassword'
        }
        response = self.client.post('/mechanics/', json=mechanic_payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn('Jane Smith', str(response.data))

    def test_invalid_create_mechanic(self):
        mechanic_payload = {
            'name': '',
            'email': 'invalidemail',
            'phone': '0987654321',
            'salary': -1000.0,
            'password': 'strongpassword'
        }
        response = self.client.post('/mechanics/', json=mechanic_payload)
        self.assertEqual(response.status_code, 400)

    def test_login_mechanic(self):
        credentials = {
            'email': 'test_mechanic@email.com',
            'password': 'mechanicpass'
        }
        response = self.client.post('/mechanics/login', json=credentials)
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth_token', response.json)
        self.assertEqual(response.json['status'], 'success')

    def test_invalid_login_mechanic(self):
        credentials = {
            'email': 'wrong_email@email.com',
            'password': 'wrongpassword'
        }
        response = self.client.post('/mechanics/login', json=credentials)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['message'], 'Invalid email or password.')

    def test_get_all_mechanics(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.get('/mechanics/', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('test_mechanic', str(response.data))

    def test_get_specific_mechanic(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.get('/mechanics/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('test_mechanic', str(response.data))

    def test_get_nonexistent_mechanic(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.get('/mechanics/999', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['message'], 'Mechanic not found.')

    def test_update_mechanic(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        update_payload = {
            'name': 'updated_mechanic',
            'email': 'updated_mechanic@email.com',
        }
        response = self.client.put('/mechanics/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('updated_mechanic', str(response.data))
        self.assertIn('updated_mechanic@email.com', str(response.data))

    def test_update_mechanic_unauthorized(self):
        update_payload = {
            'name': 'hacker_mechanic',
        }
        response = self.client.put('/mechanics/1', json=update_payload)
        self.assertEqual(response.status_code, 401)

    def test_invalid_update_mechanic(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        update_payload = {
            'email': 'notanemail',
        }
        response = self.client.put('/mechanics/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_delete_mechanic(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.delete('/mechanics/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Mechanic deleted successfully')

    def test_unauthorized_delete_mechanic(self):
        response = self.client.delete('/mechanics/1')
        self.assertEqual(response.status_code, 401)

    def test_delete_nonexistent_mechanic(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.delete('/mechanics/999', headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_top_three_mechanics(self):
        with self.app.app_context():
            hashed_pw = hashpw('anotherpass'.encode('utf-8'), gensalt()).decode('utf-8')

            top_mechanic1 = Mechanic(name='Top Mechanic 1', email='top1@email.com', phone='1111111111', salary=50000.0, password=hashed_pw)
            db.session.add(top_mechanic1)
            db.session.commit()
            for i in range(3):
                ticket = ServiceTicket(VIN=f'VIN00000000000{i}', service_date=date.today(), service_desc=f'Service {i}', customer_id=1)
                ticket.mechanics.append(top_mechanic1)
                db.session.add(ticket)

            top_mechanic2 = Mechanic(name='Top Mechanic 2', email='top2@email.com', phone='2222222222', salary=60000.0, password=hashed_pw)
            db.session.add(top_mechanic2)
            db.session.commit()
            for i in range(2):
                ticket = ServiceTicket(VIN=f'VIN11111111111{i}', service_date=date.today(), service_desc=f'Service {i}', customer_id=1)
                ticket.mechanics.append(top_mechanic2)
                db.session.add(ticket)

            top_mechanic3 = Mechanic(name='Top Mechanic 3', email='top3@email.com', phone='3333333333', salary=70000.0, password=hashed_pw)
            db.session.add(top_mechanic3)
            db.session.commit()
            ticket = ServiceTicket(VIN='VIN222222222220', service_date=date.today(), service_desc='Service 0', customer_id=1)
            ticket.mechanics.append(top_mechanic3)
            db.session.add(ticket)

            db.session.commit()

        response = self.client.get('/mechanics/top')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertLessEqual(len(response.json), 3)

        # Verify order: Top Mechanic 1 should be first (most tickets)
        self.assertEqual(response.json[0]['name'], 'Top Mechanic 1')
        self.assertEqual(response.json[1]['name'], 'Top Mechanic 2')
        self.assertEqual(response.json[2]['name'], 'Top Mechanic 3')