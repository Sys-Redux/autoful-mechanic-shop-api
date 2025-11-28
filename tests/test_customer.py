from app import create_app
from app.models import Customer, ServiceTicket, db
from datetime import date
from app.utils.util import encode_customer_token
from bcrypt import hashpw, gensalt
import unittest

class TestCustomer(unittest.TestCase):
    def setUp(self):
        self.app = create_app('TestingConfig')
        # Hashing the password like the route does
        hashed_password = hashpw('password123'.encode('utf-8'), gensalt()).decode('utf-8')
        self.customer = Customer(name='test_user', email='test@email.com', phone='1234567890', password=hashed_password)
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            db.session.add(self.customer)
            db.session.commit()
            self.token = encode_customer_token(1)
            self.client = self.app.test_client()

    def test_create_customer(self):
        customer_payload = {
            'name': 'John Doe',
            'email': 'john.doe@email.com',
            'phone': '0987654321',
            'password': 'securepassword'
        }
        response = self.client.post('/customers/', json=customer_payload)
        self.assertEqual(response.status_code, 201)
        self.assertIn('John Doe', str(response.data))

    def test_invalid_create_customer(self):
        customer_payload = {
            'name': '',
            'email': 'invalidemail',
            'phone': '0987654321',
            'password': 'securepassword'
        }
        response = self.client.post('/customers/', json=customer_payload)
        self.assertEqual(response.status_code, 400)

    def test_login_customer(self):
        credentials = {
            'email': 'test@email.com',
            'password': 'password123'
        }
        response = self.client.post('/customers/login', json=credentials)
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth_token', response.json)
        self.assertEqual(response.json['status'], 'success')

    def test_invalid_login_customer(self):
        credentials = {
            'email': 'test@email.com',
            'password': 'wrongpassword'
        }
        response = self.client.post('/customers/login', json=credentials)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['message'], 'Invalid email or password.')

    def test_get_all_customers(self):
        response = self.client.get('/customers/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('test_user', str(response.data))

    def test_get_specific_customer(self):
        response = self.client.get('/customers/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn('test_user', str(response.data))

    def test_get_nonexistent_customer(self):
        response = self.client.get('/customers/999')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['message'], 'Customer not found.')

    def test_get_customer_service_tickets(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.get('/customers/my-tickets', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_get_customer_service_tickets_no_token(self):
        response = self.client.get('/customers/my-tickets')
        self.assertEqual(response.status_code, 401)

    def test_update_customer(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        update_payload = {
            'name': 'updated_user',
            'phone': '1112223333'
        }
        response = self.client.put('/customers/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('updated_user', str(response.data))

    def test_invalid_update_customer(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        update_payload = {
            'email': 'notanemail'
        }
        response = self.client.put('/customers/1', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_delete_customer(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.delete('/customers/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Customer deleted successfully')

    def test_unauthorized_delete_customer(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        response = self.client.delete('/customers/2', headers=headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json['error'], 'Unauthorized')

    def test_get_top_customers(self):
        # Create additional customers with different numbers of service tickets
        with self.app.app_context():
            hashed_pw = hashpw('password'.encode('utf-8'), gensalt()).decode('utf-8')

            # Customer with 3 tickets (most)
            customer1 = Customer(name='top_customer', email='top@email.com', phone='1111111111', password=hashed_pw)
            db.session.add(customer1)
            db.session.commit()
            for i in range(3):
                ticket = ServiceTicket(VIN=f'VIN00000000000{i}', service_date=date.today(), service_desc=f'Service {i}', customer_id=customer1.id)
                db.session.add(ticket)

            # Customer with 2 tickets
            customer2 = Customer(name='second_customer', email='second@email.com', phone='2222222222', password=hashed_pw)
            db.session.add(customer2)
            db.session.commit()
            for i in range(2):
                ticket = ServiceTicket(VIN=f'VIN10000000000{i}', service_date=date.today(), service_desc=f'Service {i}', customer_id=customer2.id)
                db.session.add(ticket)

            # Customer with 1 ticket
            customer3 = Customer(name='third_customer', email='third@email.com', phone='3333333333', password=hashed_pw)
            db.session.add(customer3)
            db.session.commit()
            ticket = ServiceTicket(VIN='VIN2000000000001', service_date=date.today(), service_desc='Service', customer_id=customer3.id)
            db.session.add(ticket)

            db.session.commit()

        response = self.client.get('/customers/top')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertLessEqual(len(response.json), 3)

        # Verify order
        self.assertEqual(response.json[0]['name'], 'top_customer')
        self.assertEqual(response.json[1]['name'], 'second_customer')
        self.assertEqual(response.json[2]['name'], 'third_customer')
        # At most 3 customers returned
        self.assertLessEqual(len(response.json), 3)