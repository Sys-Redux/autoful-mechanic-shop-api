from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import date, datetime
from typing import List


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class = Base)

# ============================================================================
# CUSTOMER
# ============================================================================

class Customer(Base):
    __tablename__ = 'customers'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)
    firebase_uid: Mapped[str | None] = mapped_column(db.String(128), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    # Relationships
    service_tickets: Mapped[List["ServiceTicket"]] = db.relationship(back_populates='customer', cascade='all, delete-orphan')
    vehicles: Mapped[List["Vehicle"]] = db.relationship(back_populates='customer', cascade='all, delete-orphan')

# ============================================================================
# VEHICLE
# ============================================================================

class Vehicle(Base):
    __tablename__ = 'vehicles'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vin: Mapped[str] = mapped_column(db.String(17), unique=True, nullable=False)
    make: Mapped[str] = mapped_column(db.String(50), nullable=False)
    model: Mapped[str] = mapped_column(db.String(50), nullable=False)
    year: Mapped[int] = mapped_column(db.Integer, nullable=False)
    color: Mapped[str | None] = mapped_column(db.String(30), nullable=True)
    license_plate: Mapped[str | None] = mapped_column(db.String(15), nullable=True)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    # Relationships
    customer: Mapped['Customer'] = db.relationship(back_populates='vehicles')
    service_tickets: Mapped[List['ServiceTicket']] = db.relationship(back_populates='vehicle')

# ============================================================================
# SERVICE CATEGORY
# ============================================================================

class ServiceCategory(Base):
    __tablename__ = 'service_categories'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(db.String(255), nullable=True)
    default_labor_hours: Mapped[float] = mapped_column(db.Float, default=1.0)
    default_labor_rate: Mapped[float] = mapped_column(db.Float, default=75.0)

    # Relationships
    service_tickets: Mapped[List['ServiceTicket']] = db.relationship(back_populates='category')

# ============================================================================
# SERVICE TICKET
# ============================================================================

# Junction table for many-to-many relationship between ServiceTicket and Mechanic
service_mechanics = db.Table(
    'service_mechanics',
    Base.metadata,
    db.Column('service_ticket_id', db.ForeignKey('service_tickets.id')),
    db.Column('mechanic_id', db.ForeignKey('mechanics.id'))
)

class ServiceTicket(Base):
    __tablename__ = 'service_tickets'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    VIN: Mapped[str] = mapped_column(db.String(17), nullable=False)
    service_date: Mapped[date] = mapped_column(db.Date, nullable=False)
    service_desc: Mapped[str] = mapped_column(db.String(360), nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'))
    vehicle_id: Mapped[int | None] = mapped_column(db.ForeignKey('vehicles.id'), nullable=True)
    category_id: Mapped[int | None] = mapped_column(db.ForeignKey('service_categories.id'), nullable=True)
    status: Mapped[str] = mapped_column(db.String(20), default='Pending')
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at: Mapped[datetime | None] = mapped_column(db.DateTime, nullable=True)
    labor_hours: Mapped[float] = mapped_column(db.Float, default=0.0)
    labor_rate: Mapped[float] = mapped_column(db.Float, default=75.0)
    mileage: Mapped[int | None] = mapped_column(db.Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(db.Text, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = db.relationship(back_populates='service_tickets')
    vehicle: Mapped['Vehicle'] = db.relationship(back_populates='service_tickets')
    category: Mapped['ServiceCategory'] = db.relationship(back_populates='service_tickets')
    mechanics: Mapped[List['Mechanic']] = db.relationship(secondary=service_mechanics, back_populates='service_tickets')
    service_inventories: Mapped[List['ServiceInventory']] = db.relationship(back_populates='service_ticket', cascade='all, delete-orphan')

# ============================================================================
# MECHANIC
# ============================================================================

class Mechanic(Base):
    __tablename__ = 'mechanics'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    salary: Mapped[float] = mapped_column(db.Float, nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)
    firebase_uid: Mapped[str | None] = mapped_column(db.String(128), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    # Relationships
    service_tickets: Mapped[List['ServiceTicket']] = db.relationship(secondary=service_mechanics, back_populates='mechanics')

# ============================================================================
# INVENTORY
# ============================================================================

class Inventory(Base):
    __tablename__ = 'inventory'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    part_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)
    quantity_in_stock: Mapped[int] = mapped_column(db.Integer, nullable=False, default=0)
    cost: Mapped[float] = mapped_column(db.Float, default=0.0)
    category: Mapped[str | None] = mapped_column(db.String(50), nullable=True)
    part_number: Mapped[str | None] = mapped_column(db.String(100), unique=True, nullable=True)
    reorder_point: Mapped[int] = mapped_column(db.Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    # Relationships
    service_inventories: Mapped[List['ServiceInventory']] = db.relationship(back_populates='inventory')

# ============================================================================
# SERVICE INVENTORY (Junction: Ticket <-> Parts Used)
# ============================================================================

class ServiceInventory(Base):
    __tablename__ = 'service_inventories'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service_ticket_id: Mapped[int] = mapped_column(db.ForeignKey('service_tickets.id'), nullable=False)
    inventory_id: Mapped[int] = mapped_column(db.ForeignKey('inventory.id'), nullable=False)
    quantity_used: Mapped[int] = mapped_column(db.Integer, nullable=False, default=1)
    price_at_service: Mapped[float | None] = mapped_column(db.Float, nullable=True)
    cost_at_service: Mapped[float | None] = mapped_column(db.Float, nullable=True)

    # Relationships
    service_ticket: Mapped['ServiceTicket'] = db.relationship(back_populates='service_inventories')
    inventory: Mapped['Inventory'] = db.relationship(back_populates='service_inventories')