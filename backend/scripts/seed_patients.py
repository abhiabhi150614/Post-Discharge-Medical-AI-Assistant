import sys
import os
import datetime
import json
import random

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db import SessionLocal, engine, Base
from app.models import Patient

# Create tables
Base.metadata.create_all(bind=engine)

def seed_patients():
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(Patient).count() > 0:
        print("Patients already seeded.")
        # Check for Abhishek specifically
        if not db.query(Patient).filter(Patient.name == "Abhishek B Shetty").first():
             print("Adding missing patient: Abhishek B Shetty")
             abhishek = Patient(
                name="Abhishek B Shetty",
                discharge_date=datetime.date(2024, 2, 1),
                primary_diagnosis="Chronic Kidney Disease Stage 2",
                medications=["Metformin 500mg", "Atorvastatin 20mg"],
                dietary_restrictions="Diabetic renal diet, limit sugar",
                follow_up="Endocrinology in 1 month",
                warning_signs="Dizziness, high blood sugar, swelling",
                discharge_instructions="Check blood sugar daily, maintain diet."
            )
             db.add(abhishek)
             db.commit()
        
        db.close()
        return

    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris"]

    diagnoses = [
        "Chronic Kidney Disease Stage 2",
        "Chronic Kidney Disease Stage 3a",
        "Chronic Kidney Disease Stage 3b",
        "Chronic Kidney Disease Stage 4",
        "End Stage Renal Disease (on Dialysis)"
    ]

    meds_pool = [
        "Lisinopril 10mg daily", "Furosemide 20mg twice daily", "Amlodipine 5mg daily", 
        "Metoprolol 25mg daily", "Atorvastatin 40mg daily", "Calcium Acetate 667mg with meals",
        "Sevelamer 800mg with meals", "Calcitriol 0.25mcg daily", "Allopurinol 100mg daily"
    ]

    for i in range(30):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        diagnosis = random.choice(diagnoses)
        discharge_date = datetime.date.today() - datetime.timedelta(days=random.randint(1, 60))
        
        num_meds = random.randint(2, 5)
        medications = random.sample(meds_pool, num_meds)
        
        if "Dialysis" in diagnosis:
            diet = "Fluid restriction 1L/day, Low Potassium, Low Phosphorus, High Protein"
            warning = "Missed dialysis session, shortness of breath, bleeding from access site"
        elif "Stage 4" in diagnosis:
            diet = "Low Sodium, Low Protein, Limit Potassium"
            warning = "Swelling in legs, difficulty breathing, nausea"
        else:
            diet = "Low Sodium (2g/day), DASH diet"
            warning = "Swelling, blood in urine, severe fatigue"

        patient = Patient(
            name=name,
            discharge_date=discharge_date,
            primary_diagnosis=diagnosis,
            medications=medications,
            dietary_restrictions=diet,
            follow_up="Nephrology clinic in 2 weeks",
            warning_signs=warning,
            discharge_instructions="Monitor blood pressure daily, weigh yourself daily. Call if weight increases > 2kg in 2 days."
        )
        db.add(patient)

    # Add specific requested dummy patient
    john_smith = Patient(
        name="John Smith",
        discharge_date=datetime.date(2024, 1, 15),
        primary_diagnosis="Chronic Kidney Disease Stage 3",
        medications=["Lisinopril 10mg daily", "Furosemide 20mg twice daily"],
        dietary_restrictions="Low sodium (2g/day), fluid restriction (1.5L/day)",
        follow_up="Nephrology clinic in 2 weeks",
        warning_signs="Swelling, shortness of breath, decreased urine output",
        discharge_instructions="Monitor blood pressure daily, weigh yourself daily"
    )
    db.add(john_smith)

    # Add Abhishek B Shetty
    abhishek = Patient(
        name="Abhishek B Shetty",
        discharge_date=datetime.date(2024, 2, 1),
        primary_diagnosis="Chronic Kidney Disease Stage 2",
        medications=["Metformin 500mg", "Atorvastatin 20mg"],
        dietary_restrictions="Diabetic renal diet, limit sugar",
        follow_up="Endocrinology in 1 month",
        warning_signs="Dizziness, high blood sugar, swelling",
        discharge_instructions="Check blood sugar daily, maintain diet."
    )
    db.add(abhishek)

    db.commit()
    print("Seeded 31 patients.")
    db.close()

if __name__ == "__main__":
    seed_patients()
