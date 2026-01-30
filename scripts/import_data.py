import json
import sys
import os
from dateutil import parser as date_parser
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import SIPRecord


def clean_numeric_string(value: str) -> float:
    """Remove commas from numeric strings and convert to float"""
    if not value or value == "":
        return 0.0
    return float(value.replace(",", ""))


def clean_integer_string(value: str) -> int:
    """Remove commas from numeric strings and convert to int"""
    if not value or value == "":
        return 0
    return int(value.replace(",", ""))


def import_sip_data(json_file_path: str):
    """Import SIP data from JSON file into PostgreSQL"""
    
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Load JSON data
    print(f"Loading data from {json_file_path}...")
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} records to import")
    
    # Create database session
    db = SessionLocal()
    
    try:
        imported = 0
        skipped = 0
        errors = 0
        session_sip_ids = set()  # Track sip_meta_ids in current session
        
        for record in data:
            try:
                sip_meta_id = record.get('sip_meta_id')
                
                # Check if record already exists in database
                existing = db.query(SIPRecord).filter(
                    SIPRecord.sip_meta_id == sip_meta_id
                ).first()
                
                if existing:
                    skipped += 1
                    if skipped % 50 == 0:
                        print(f"   Skipped {skipped} duplicates from database...")
                    continue
                
                # Check if already in current session
                if sip_meta_id in session_sip_ids:
                    skipped += 1
                    continue
                
                # Add to session tracker
                session_sip_ids.add(sip_meta_id)
                
                # Create SIP record
                sip_record = SIPRecord(
                    uid=record.get('uid'),
                    sip_meta_id=record.get('sip_meta_id'),
                    user_id=record.get('user_id'),
                    goal_id=record.get('goal_id'),
                    agent_id=record.get('agent_id'),
                    agent_external_id=record.get('agent_external_id'),
                    member_id=record.get('member_id'),
                    amount=clean_numeric_string(record.get('amount', '0')),
                    sip_days=record.get('sip_days'),
                    num_days=clean_integer_string(record.get('num_days', '0')),
                    scheme_name=record.get('scheme_name'),
                    goal_name=record.get('goal_name'),
                    created_at=record.get('created_at'),
                    sip_meta_date=record.get('sip_meta_date'),
                    sip_meta_month=record.get('sip_meta_month'),
                    start_date=record.get('start_date'),
                    end_date=record.get('end_date'),
                    event_date=record.get('event_date'),
                    inserted_at=record.get('inserted_at'),
                    increment_percentage=clean_numeric_string(record.get('increment_percentage', '0')),
                    increment_amount=clean_numeric_string(record.get('increment_amount', '0')),
                    increment_period=record.get('increment_period'),
                    paused_from=record.get('paused_from'),
                    paused_till=record.get('paused_till'),
                    paused_reason=record.get('paused_reason'),
                    is_active=record.get('is_active'),
                    sip_sales_status=record.get('sip_sales_status'),
                    current_sip_status=record.get('currentSipStatus'),
                    had_mandate_at_creation=record.get('had_mandate_at_creation'),
                    has_current_mandate=record.get('has_current_mandate'),
                    mandate_tracking_status=record.get('mandate_tracking_status'),
                    mandate_confirmed_date=record.get('mandate_confirmed_date'),
                    first_order_nav_allocated_at=record.get('first_order_nav_allocated_at'),
                    first_success_order_date=record.get('first_success_order_date'),
                    latest_success_order_date=record.get('latest_success_order_date'),
                    first_success_order_month=record.get('first_success_order_month'),
                    latest_success_order_month=record.get('latest_success_order_month'),
                    success_amount=clean_numeric_string(record.get('success_amount', '0')),
                    pending_amount=clean_numeric_string(record.get('pending_amount', '0')),
                    failed_amount=clean_numeric_string(record.get('failed_amount', '0')),
                    in_progress_amount=clean_numeric_string(record.get('in_progress_amount', '0')),
                    paused_amount=clean_numeric_string(record.get('paused_amount', '0')),
                    success_count=clean_integer_string(record.get('success_count', '0')),
                    stepper_enabled=record.get('stepper_enabled'),
                    deleted=record.get('deleted')
                )
                
                db.add(sip_record)
                imported += 1
                
                # Commit in smaller batches
                if imported % 50 == 0:
                    try:
                        db.commit()
                        print(f"✅ Imported {imported} records (skipped {skipped} duplicates)...")
                        session_sip_ids.clear()
                    except Exception as commit_error:
                        print(f"⚠️  Batch commit failed: {commit_error}")
                        db.rollback()
                        session_sip_ids.clear()
                        errors += 1
                    
            except Exception as e:
                print(f"⚠️  Error with SIP record {record.get('sip_meta_id')}: {str(e)}")
                db.rollback()
                errors += 1
                continue
        
        # Final commit
        try:
            db.commit()
            print(f"\n✅ Import completed!")
            print(f"Total imported: {imported}")
            print(f"Total skipped (duplicates): {skipped}")
            print(f"Total errors: {errors}")
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
        print("Usage: python import_data.py <path_to_json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    import_sip_data(json_file)
