
<!-- markdownlint-disable MD033 MD041 MD001 MD022 MD032 MD024 MD040 MD031 -->

<div align="center">

# 🔧 Autoful - Auto Shop Management API

### *A Modern REST API for Auto Repair Shop Management*

[![GitHub](https://img.shields.io/badge/GitHub-Sys--Redux-D91A5F?style=for-the-badge&logo=github&logoColor=00DD88)](https://github.com/Sys-Redux)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-T--Edge-00A3CC?style=for-the-badge&logo=linkedin&logoColor=000000)](https://www.linkedin.com/in/t-edge/)
[![X](https://img.shields.io/badge/X-@sys__redux-7C3AED?style=for-the-badge&logo=x&logoColor=00DD88)](https://x.com/sys_redux)
[![Portfolio](https://img.shields.io/badge/Portfolio-sysredux.xyz-00CC66?style=for-the-badge&logo=googlechrome&logoColor=000000)](https://www.sysredux.xyz/)

![Flask](https://img.shields.io/badge/Flask-D91A5F?style=flat-square&logo=flask&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-00A3CC?style=flat-square&logo=sqlalchemy&logoColor=000000)
![MySQL](https://img.shields.io/badge/MySQL-CC9400?style=flat-square&logo=mysql&logoColor=000000)
![Python](https://img.shields.io/badge/Python-7C3AED?style=flat-square&logo=python&logoColor=FFD43B)
![Marshmallow](https://img.shields.io/badge/Marshmallow-00CC66?style=flat-square&logoColor=000000)

</div>

---

## 📋 Overview

A production-ready RESTful API for managing an auto repair shop! This project showcases modern Flask development with SQLAlchemy 2.0, Marshmallow schemas, and complex many-to-many relationships - built to handle real-world auto shop operations efficiently.

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 👥 Customer Management
- Complete CRUD operations
- Email uniqueness validation
- Automatic relationship tracking
- Nested service ticket data

</td>
<td width="50%">

### 🎫 Service Tickets
- VIN tracking & validation
- Service date & description
- Customer association
- Multi-mechanic assignments

</td>
</tr>
<tr>
<td width="50%">

### 🔧 Mechanic System
- Skill & certification tracking
- Multi-ticket assignments
- Workload visibility
- Partial update support

</td>
<td width="50%">

### 🔗 Smart Relationships
- Many-to-many associations
- Duplicate prevention
- Circular reference handling
- Nested serialization

</td>
</tr>
</table>

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| **Flask** | Lightweight web framework for REST API |
| **SQLAlchemy 2.0** | Modern ORM with declarative mapping & type hints |
| **Marshmallow** | Schema validation & serialization/deserialization |
| **MySQL** | Relational database for persistent storage |
| **Flask-SQLAlchemy** | Flask integration for SQLAlchemy ORM |

## 📁 Project Structure

```file-structure
autoful/
├── app/
│   ├── blueprints/
│   │   ├── customers/
|   |   |   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── mechanics/
|   |   |   ├── __init__.py
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   └── service_tickets/
|   |       ├── __init__.py
│   │       ├── routes.py
│   │       └── schemas.py
|   ├── __init__.py
│   ├── models.py
│   └── extensions.py
├── app.py
└── config.py
```

## 🎯 API Endpoints

### 👥 Customers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/customers/` | Create a new customer |
| `GET` | `/customers/` | Get all customers (includes service tickets) |
| `GET` | `/customers/<id>` | Get a specific customer |
| `PUT` | `/customers/<id>` | Update customer info (partial updates supported) |
| `DELETE` | `/customers/<id>` | Delete a customer |

### 🔧 Mechanics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/mechanics/` | Create a new mechanic |
| `GET` | `/mechanics/` | Get all mechanics (includes assigned tickets) |
| `GET` | `/mechanics/<id>` | Get a specific mechanic |
| `PUT` | `/mechanics/<id>` | Update mechanic info (partial updates supported) |
| `DELETE` | `/mechanics/<id>` | Delete a mechanic |

### 🎫 Service Tickets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/service_tickets/` | Create a new service ticket |
| `GET` | `/service_tickets/` | Get all service tickets |
| `GET` | `/service_tickets/<id>` | Get specific ticket (shows customer & mechanics) |
| `PUT` | `/service_tickets/<ticket_id>/assign-mechanic/<mechanic_id>` | Assign a mechanic to a ticket |
| `DELETE` | `/service_tickets/<ticket_id>/remove-mechanic/<mechanic_id>` | Remove a mechanic from a ticket |
| `DELETE` | `/service_tickets/<id>` | Delete a service ticket |

## 💡 Technical Highlights

> **Built with best practices and production-ready patterns**

```
🎯 Smart Relationship Handling
   └─ dump_only=True on nested fields for clean API design
   └─ Pass IDs on creation, get full objects on retrieval

🛡️ Data Integrity
   └─ Duplicate prevention for mechanic assignments
   └─ Email uniqueness constraints
   └─ Foreign key relationships enforced

🔄 Flexible Updates
   └─ Partial update support on all PUT endpoints
   └─ Send only the fields you want to change

🔗 Intelligent Serialization
   └─ Automatic nested object inclusion
   └─ Circular reference prevention
   └─ load_instance=True for cleaner code patterns
```

## 🔥 Skills Demonstrated

<details>
<summary><b>🏗️ Architecture & Design</b></summary>

- Modular Flask application structure with blueprints
- Clean separation of concerns (routes, schemas, models)
- RESTful API design principles
- Scalable project organization

</details>

<details>
<summary><b>💾 Database & ORM</b></summary>

- SQLAlchemy 2.0 modern declarative mapping
- Complex many-to-many relationship management
- Association tables and foreign key constraints
- Migration-ready database schema design

</details>

<details>
<summary><b>🔧 API Development</b></summary>

- Marshmallow schema validation & serialization
- `load_instance=True` pattern implementation
- Nested relationship serialization
- Circular reference prevention
- Partial update support

</details>

<details>
<summary><b>✅ Best Practices</b></summary>

- Type hints throughout codebase
- Error handling & validation
- DRY (Don't Repeat Yourself) principles
- Production-ready code structure

</details>

## � Quick Start

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip package manager

### Installation

1️⃣ **Clone the repository**

```bash
git clone https://github.com/Sys-Redux/autoful.git
cd autoful
```

2️⃣ **Set up virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3️⃣ **Install dependencies**

```bash
pip install -r requirements.txt
```

4️⃣ **Configure database**

Update `config.py` with your MySQL credentials:

```python
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://user:password@localhost/autoful'
```

5️⃣ **Run the application**

```bash
python app.py
```

🎉 **API is live at** `http://localhost:5000`

## 🎨 Example Usage

### Create a Customer

```bash
curl -X POST http://localhost:5000/customers/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-1234"
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "555-1234",
  "service_tickets": []
}
```

### Create a Service Ticket

```bash
curl -X POST http://localhost:5000/service_tickets/ \
  -H "Content-Type: application/json" \
  -d '{
    "VIN": "1HGBH41JXMN109186",
    "service_date": "2025-11-15",
    "service_desc": "Brake replacement",
    "customer_id": 1
  }'
```

### Assign Mechanic to Ticket

```bash
curl -X PUT http://localhost:5000/service_tickets/1/assign-mechanic/1
```

**Response:**
```json
{
  "message": "Mechanic successfully assigned to service ticket"
}
```

---

<div align="center">

### 🌟 Connect With Me

[![GitHub](https://img.shields.io/badge/GitHub-Follow-D91A5F?style=for-the-badge&logo=github&logoColor=00DD88)](https://github.com/Sys-Redux)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-00A3CC?style=for-the-badge&logo=linkedin&logoColor=000000)](https://www.linkedin.com/in/t-edge/)
[![X](https://img.shields.io/badge/X-Follow-7C3AED?style=for-the-badge&logo=x&logoColor=00DD88)](https://x.com/sys_redux)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-00CC66?style=for-the-badge&logo=googlechrome&logoColor=000000)](https://www.sysredux.xyz/)

**Built with ❤️ by [T-Edge](https://www.sysredux.xyz/) | Coding Temple Backend Specialization**

*If you found this project helpful, consider giving it a ⭐️!*

</div>
