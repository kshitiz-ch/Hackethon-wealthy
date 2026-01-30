#!/usr/bin/env python
"""
Import user data from JSON file into PostgreSQL.
Generates mock date_of_birth for each user (ages 25-70).
"""

import json
import sys
import os
from datetime import datetime, date
from random import randint

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import User


def clean_numeric_string(value: str) -> float:
    """Remove commas from numeric strings and convert to float"""
    if not value or value == "" or value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(",", ""))


def generate_mock_dob() -> date:
    """
    Generate a realistic mock date of birth.
    Ages range from 25 to 70 years old.
    """
    current_year = datetime.now().year
    age = randint(25, 70)
    birth_year = current_year - age
    birth_month = randint(1, 12)
    
    # Handle different month lengths
    if birth_month in [4, 6, 9, 11]:
        birth_day = randint(1, 30)
    elif birth_month == 2:
        birth_day = randint(1, 28)
    else:
        birth_day = randint(1, 31)
    
    return date(birth_year, birth_month, birth_day)


def import_user_data(json_file_path: str):
    """Import user data from JSON file into PostgreSQL"""
    
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Load JSON data
    print(f"Loading data from {json_file_path}...")
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} user records to import")
    
    # Create database session
    db = SessionLocal()
    
    try:
        imported = 0
        skipped = 0
        errors = 0
        session_user_ids = set()  # Track user_ids in current session to avoid duplicates within batch
        
        for record in data:
            try:
                user_id = record.get('user_id')
                
                # Check if record already exists in database
                existing = db.query(User).filter(
                    User.user_id == user_id
                ).first()
                
                if existing:
                    skipped += 1
                    if skipped % 50 == 0:
                        print(f"   Skipped {skipped} duplicates from database...")
                    continue
                
                # Check if user_id already added in current session (before commit)
                if user_id in session_user_ids:
                    skipped += 1
                    if skipped % 50 == 0:
                        print(f"   Skipped {skipped} duplicates (including in-session)...")
                    continue
                
                # Add to session tracker
                session_user_ids.add(user_id)
                
                # Generate mock DOB
                mock_dob = generate_mock_dob()
                
                # Create User record
                user = User(
                    uid=record.get('uid'),
                    user_id=user_id,
                    crn=record.get('crn'),
                    name=record.get('name'),
                    email=record.get('email'),
                    phone_number=record.get('phone_number'),
                    date_of_birth=mock_dob,
                    agent_external_id=record.get('agent_external_id'),
                    agent_name=record.get('agent_name'),
                    agent_email=record.get('agent_email'),
                    agent_phone_number=record.get('agent_phone_number'),
                    member_id=record.get('member_id'),
                    total_current_value=clean_numeric_string(record.get('total_current_value', '0')),
                    mf_current_value=clean_numeric_string(record.get('mf_current_value', '0')),
                    fd_current_value=clean_numeric_string(record.get('fd_current_value', '0')),
                    aif_current_value=clean_numeric_string(record.get('aif_current_value', '0')),
                    deb_current_value=clean_numeric_string(record.get('deb_current_value', '0')),
                    pms_current_value=clean_numeric_string(record.get('pms_current_value', '0')),
                    preipo_current_value=clean_numeric_string(record.get('preipo_current_value', '0')),
                    total_invested_value=clean_numeric_string(record.get('total_invested_value', '0')),
                    mf_invested_value=clean_numeric_string(record.get('mf_invested_value', '0')),
                    fd_invested_value=clean_numeric_string(record.get('fd_invested_value', '0')),
                    aif_invested_value=clean_numeric_string(record.get('aif_invested_value', '0')),
                    deb_invested_value=clean_numeric_string(record.get('deb_invested_value', '0')),
                    pms_invested_value=clean_numeric_string(record.get('pms_invested_value', '0')),
                    preipo_invested_value=clean_numeric_string(record.get('preipo_invested_value', '0')),
                    trak_cob_opportunity_value=clean_numeric_string(record.get('trak_cob_opportunity_value', '0')),
                    latest_as_on_date=record.get('latest_as_on_date'),
                    first_active_at=record.get('first_active_at'),
                    first_active_mf=record.get('first_active_mf'),
                    first_active_fd=record.get('first_active_fd'),
                    first_active_insurance=record.get('first_active_insurance'),
                    first_active_mld=record.get('first_active_mld'),
                    first_active_ncd=record.get('first_active_ncd'),
                    first_active_aif=record.get('first_active_aif'),
                    first_active_pms=record.get('first_active_pms'),
                    first_active_preipo=record.get('first_active_preipo'),
                    first_active_mf_sip=record.get('first_active_mf_sip'),
                    inserted_at=record.get('inserted_at'),
                    event_date=record.get('event_date'),
                    created_at=record.get('created_at')
                )
                
                db.add(user)
                imported += 1
                
                # Commit in smaller batches to isolate potential errors
                if imported % 50 == 0:
                    try:
                        db.commit()
                        print(f"✅ Imported {imported} records (skipped {skipped} duplicates)...")
                        # Clear session tracker after successful commit
                        session_user_ids.clear()
                    except Exception as commit_error:
                        print(f"⚠️  Batch commit failed: {commit_error}")
                        db.rollback()
                        session_user_ids.clear()  # Clear tracker on rollback too
                        errors += 1
                    
            except Exception as e:
                print(f"⚠️  Error with user {record.get('user_id')}: {str(e)}")
                db.rollback()
                errors += 1
                continue
        
        # Final commit for remaining records
        try:
            db.commit()
            print(f"\n✅ Import completed!")
            print(f"Total imported: {imported}")
            print(f"Total skipped (duplicates): {skipped}")
            print(f"Total errors: {errors}")
            print(f"\n📅 Note: Mock date_of_birth generated for all users (ages 25-70)")
            print(f"   You can update these later with actual DOB data.")
        except Exception as final_commit_error:
            print(f"⚠️  Final commit had issues: {final_commit_error}")
            db.rollback()
        
    except Exception as e:
        print(f"❌ Error during import: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_users.py <path_to_json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    import_user_data(json_file)
