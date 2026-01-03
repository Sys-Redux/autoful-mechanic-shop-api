"""
Migrate existing data to use new schema fields.
Run with: python -m scripts.migrate_existing_data

This script ensures ALL fields have values, including nullable ones.
"""
import os
from datetime import datetime
from app import create_app
from app.models import (
    db, Customer, Vehicle, ServiceCategory, ServiceTicket,
    Mechanic, Inventory, ServiceInventory
)

# Use ProductionConfig on Render, DevelopmentConfig locally
config = 'ProductionConfig' if os.environ.get('RENDER') else 'DevelopmentConfig'
app = create_app(config)

with app.app_context():
    print("=" * 60)
    print("STARTING DATA MIGRATION")
    print("=" * 60)

    # ========================================================================
    # 1. CUSTOMERS - Ensure created_at is set
    # ========================================================================
    customers = Customer.query.filter(Customer.created_at == None).all()
    for customer in customers:
        customer.created_at = datetime.now()
    print(f"[Customers] Updated {len(customers)} with created_at")

    # ========================================================================
    # 2. MECHANICS - Ensure created_at is set
    # ========================================================================
    mechanics = Mechanic.query.filter(Mechanic.created_at == None).all()
    for mechanic in mechanics:
        mechanic.created_at = datetime.now()
    print(f"[Mechanics] Updated {len(mechanics)} with created_at")

    # ========================================================================
    # 3. VEHICLES - Create from existing ticket VINs
    # ========================================================================
    # Get all unique VINs from tickets that don't have vehicles yet
    tickets_without_vehicles = ServiceTicket.query.filter(
        ServiceTicket.vehicle_id == None
    ).all()

    vehicles_created = 0
    for ticket in tickets_without_vehicles:
        # Check if vehicle with this VIN already exists
        existing_vehicle = Vehicle.query.filter_by(vin=ticket.VIN).first()

        if not existing_vehicle:
            # Create a new vehicle - we only have VIN, so use placeholders
            new_vehicle = Vehicle(
                vin=ticket.VIN,
                make='Unknown',
                model='Unknown',
                year=2020,  # Default year
                color='Unknown',
                license_plate=None,
                customer_id=ticket.customer_id,
                created_at=datetime.combine(ticket.service_date, datetime.min.time())
            )
            db.session.add(new_vehicle)
            db.session.flush()  # Get the ID
            ticket.vehicle_id = new_vehicle.id
            vehicles_created += 1
        else:
            ticket.vehicle_id = existing_vehicle.id

    print(f"[Vehicles] Created {vehicles_created} vehicles from ticket VINs")
    print(f"[Vehicles] Linked {len(tickets_without_vehicles)} tickets to vehicles")

    # ========================================================================
    # 4. SERVICE CATEGORIES - Ensure "General Maintenance" exists for default
    # ========================================================================
    general_cat = ServiceCategory.query.filter_by(name='General Maintenance').first()
    if not general_cat:
        general_cat = ServiceCategory(
            name='General Maintenance',
            description='Inspections and general maintenance',
            default_labor_hours=1.0,
            default_labor_rate=75.0
        )
        db.session.add(general_cat)
        db.session.flush()
        print("[Categories] Created 'General Maintenance' category")

    # ========================================================================
    # 5. SERVICE TICKETS - Populate all fields
    # ========================================================================
    all_tickets = ServiceTicket.query.all()
    tickets_updated = 0

    for ticket in all_tickets:
        updated = False

        # Status - normalize to capitalized form and set completed for old tickets
        if ticket.status is None or ticket.status == '' or ticket.status == 'pending':
            ticket.status = 'Completed'  # Old tickets are likely completed
            updated = True

        # Category - assign General Maintenance if missing
        if ticket.category_id is None:
            ticket.category_id = general_cat.id
            updated = True

        # Timestamps
        if ticket.created_at is None:
            ticket.created_at = datetime.combine(ticket.service_date, datetime.min.time())
            updated = True

        if ticket.updated_at is None:
            ticket.updated_at = ticket.created_at or datetime.now()
            updated = True

        if ticket.completed_at is None and ticket.status == 'Completed':
            ticket.completed_at = datetime.combine(ticket.service_date, datetime.min.time())
            updated = True

        # Labor fields - use category defaults if not set
        if ticket.labor_hours is None or ticket.labor_hours == 0:
            if ticket.category:
                ticket.labor_hours = ticket.category.default_labor_hours
            else:
                ticket.labor_hours = 1.0
            updated = True

        if ticket.labor_rate is None or ticket.labor_rate == 0:
            if ticket.category:
                ticket.labor_rate = ticket.category.default_labor_rate
            else:
                ticket.labor_rate = 75.0
            updated = True

        # Mileage - set a reasonable default if missing
        if ticket.mileage is None:
            ticket.mileage = 50000  # Reasonable average mileage
            updated = True

        # Notes - set placeholder if empty
        if ticket.notes is None or ticket.notes == '':
            ticket.notes = 'Migrated from legacy system'
            updated = True

        if updated:
            tickets_updated += 1

    print(f"[Tickets] Updated {tickets_updated} tickets with complete data")

    # ========================================================================
    # 6. INVENTORY - Populate all fields
    # ========================================================================
    all_parts = Inventory.query.all()
    parts_updated = 0

    # Category mapping based on part name keywords
    category_keywords = {
        'oil': 'Fluids',
        'filter': 'Filters',
        'brake': 'Brakes',
        'pad': 'Brakes',
        'rotor': 'Brakes',
        'tire': 'Tires',
        'battery': 'Electrical',
        'spark': 'Engine',
        'belt': 'Engine',
        'hose': 'Cooling',
        'coolant': 'Cooling',
        'wiper': 'Body',
        'light': 'Electrical',
        'bulb': 'Electrical',
    }

    for part in all_parts:
        updated = False

        # Cost - estimate as 60% of price (40% markup)
        if part.cost is None or part.cost == 0:
            part.cost = round(part.price * 0.6, 2)
            updated = True

        # Category - infer from part name
        if part.category is None or part.category == '':
            part_name_lower = part.part_name.lower()
            assigned_category = 'General'

            for keyword, category in category_keywords.items():
                if keyword in part_name_lower:
                    assigned_category = category
                    break

            part.category = assigned_category
            updated = True

        # Part number - generate if missing
        if part.part_number is None or part.part_number == '':
            # Generate a part number like "PART-001", "PART-002", etc.
            part.part_number = f"PART-{part.id:04d}"
            updated = True

        # Reorder point - set default if missing
        if part.reorder_point is None or part.reorder_point == 0:
            part.reorder_point = 5
            updated = True

        # Created at
        if part.created_at is None:
            part.created_at = datetime.now()
            updated = True

        if updated:
            parts_updated += 1

    print(f"[Inventory] Updated {parts_updated} parts with complete data")

    # ========================================================================
    # 7. SERVICE INVENTORY - Capture price/cost at time of service
    # ========================================================================
    all_service_inventory = ServiceInventory.query.all()
    si_updated = 0

    for si in all_service_inventory:
        updated = False

        # Price at service - capture current price if not set
        if si.price_at_service is None:
            si.price_at_service = si.inventory.price if si.inventory else 0.0
            updated = True

        # Cost at service - capture current cost if not set
        if si.cost_at_service is None:
            si.cost_at_service = si.inventory.cost if si.inventory else 0.0
            updated = True

        if updated:
            si_updated += 1

    print(f"[ServiceInventory] Updated {si_updated} records with price/cost snapshots")

    # ========================================================================
    # COMMIT ALL CHANGES
    # ========================================================================
    db.session.commit()

    print("=" * 60)
    print("DATA MIGRATION COMPLETE!")
    print("=" * 60)

    # Print summary
    print("\nSummary:")
    print(f"  - Customers: {Customer.query.count()}")
    print(f"  - Mechanics: {Mechanic.query.count()}")
    print(f"  - Vehicles: {Vehicle.query.count()}")
    print(f"  - Categories: {ServiceCategory.query.count()}")
    print(f"  - Tickets: {ServiceTicket.query.count()}")
    print(f"  - Inventory Parts: {Inventory.query.count()}")
    print(f"  - Parts Used Records: {ServiceInventory.query.count()}")