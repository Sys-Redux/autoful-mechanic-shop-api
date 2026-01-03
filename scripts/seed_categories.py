"""
Seed script for service categories.
Run with: python -m scripts.seed_categories
"""
import os
from app import create_app
from app.models import db, ServiceCategory

# Use ProductionConfig on Render, DevelopmentConfig locally
config = 'ProductionConfig' if os.environ.get('RENDER') else 'DevelopmentConfig'
app = create_app(config)

categories = [
    {'name': 'Oil Change', 'description': 'Standard oil and filter change', 'default_labor_hours': 0.5, 'default_labor_rate': 75.0},
    {'name': 'Brake Service', 'description': 'Brake pad/rotor replacement and inspection', 'default_labor_hours': 2.0, 'default_labor_rate': 85.0},
    {'name': 'Tire Service', 'description': 'Tire rotation, balancing, or replacement', 'default_labor_hours': 1.0, 'default_labor_rate': 75.0},
    {'name': 'Transmission', 'description': 'Transmission service and repair', 'default_labor_hours': 4.0, 'default_labor_rate': 95.0},
    {'name': 'Engine Repair', 'description': 'Engine diagnostics and repair', 'default_labor_hours': 3.0, 'default_labor_rate': 95.0},
    {'name': 'Electrical', 'description': 'Electrical system diagnostics and repair', 'default_labor_hours': 2.0, 'default_labor_rate': 85.0},
    {'name': 'A/C & Heating', 'description': 'Climate control service and repair', 'default_labor_hours': 2.0, 'default_labor_rate': 85.0},
    {'name': 'Suspension', 'description': 'Suspension and steering service', 'default_labor_hours': 2.5, 'default_labor_rate': 85.0},
    {'name': 'Exhaust', 'description': 'Exhaust system service and repair', 'default_labor_hours': 1.5, 'default_labor_rate': 75.0},
    {'name': 'General Maintenance', 'description': 'Inspections and general maintenance', 'default_labor_hours': 1.0, 'default_labor_rate': 75.0},
]

with app.app_context():
    for cat_data in categories:
        # Check if category already exists
        existing = ServiceCategory.query.filter_by(name=cat_data['name']).first()
        if not existing:
            category = ServiceCategory(**cat_data)
            db.session.add(category)
            print(f"Added: {cat_data['name']}")
        else:
            print(f"Skipped (exists): {cat_data['name']}")

    db.session.commit()
    print("\nSeeding complete!")