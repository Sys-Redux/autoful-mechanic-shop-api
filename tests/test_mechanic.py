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