import json
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import InsuranceRecord


def clean_numeric_string(value: str) -> float:
    """Remove commas from numeric strings and convert to float"""
    if not value or value == "" or value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    return float(str(value).replace(",", ""))


def clean_integer_string(value: str) -> int:
    """Remove commas from numeric strings and convert to int"""
    if not value or value == "" or value is None:
        return 0
    if isinstance(value, int):
        return value
    return int(str(value).replace(",", ""))


def import_insurance_data(json_file_path: str):
    """Import insurance data from JSON file into PostgreSQL"""
    
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Load JSON data
    print(f"Loading data from {json_file_path}...")
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    print(f"Found {len(data)} insurance records to import")
    
    # Create database session
    db = SessionLocal()
    
    try:
        imported = 0
        skipped = 0
        errors = 0
        session_source_ids = set()  # Track source_ids in current session
        
        for record in data:
            try:
                source_id = record.get('source_id')
                
                # Check if record already exists in database
                existing = db.query(InsuranceRecord).filter(
                    InsuranceRecord.source_id == source_id
                ).first()
                
                if existing:
                    skipped += 1
                    if skipped % 50 == 0:
                        print(f"   Skipped {skipped} duplicates from database...")
                    continue
                
                # Check if already in current session
                if source_id in session_source_ids:
                    skipped += 1
                    continue
                
                # Add to session tracker
                session_source_ids.add(source_id)
                
                # Create Insurance record
                insurance_record = InsuranceRecord(
                    uid=record.get('uid'),
                    source_id=record.get('source_id'),
                    deleted=record.get('deleted'),
                    checksum=record.get('checksum'),
                    user_id=record.get('itf.user_id'),
                    name=record.get('name'),
                    mf_current_value=clean_numeric_string(record.get('mf_current_value', '0')),
                    wealth_band=record.get('wealth_band'),
                    mock_age=clean_integer_string(record.get('mock_age', '0')),
                    transaction_date=record.get('transaction_date'),
                    transaction_amount=clean_numeric_string(record.get('transaction_amount', '0')),
                    transaction_type=record.get('transaction_type'),
                    transaction_category=record.get('transaction_category'),
                    instrument_type=record.get('instrument_type'),
                    product_name=record.get('product_name'),
                    transaction_status=record.get('transaction_status'),
                    order_status=record.get('order_status'),
                    event_date=record.get('event_date'),
                    created_at=record.get('created_at'),
                    wealthy_processed_at=record.get('wealthy_processed_at'),
                    order_date=record.get('order_date'),
                    order_id=record.get('order_id'),
                    transaction_id=record.get('transaction_id'),
                    transaction_units=record.get('transaction_units'),
                    order_category=record.get('order_category'),
                    order_type=record.get('order_type'),
                    insurance_order_id=record.get('insurance_order_id'),
                    insurance_type=record.get('insurance_type'),
                    sourcing_channel=record.get('sourcing_channel'),
                    user_product_id=record.get('user_product_id'),
                    insurer=record.get('insurer'),
                    premium_frequency=record.get('premium_frequency'),
                    policy_issue_date=record.get('policy_issue_date'),
                    policy_number=record.get('policy_number'),
                    application_number=record.get('application_number'),
                    wpc=record.get('wpc'),
                    premium=clean_numeric_string(record.get('premium', '0')),
                    agent_id=record.get('agent_id'),
                    agent_external_id=record.get('itf.agent_external_id'),
                    member_id=record.get('member_id'),
                    b_agent_external_id=record.get('b.agent_external_id'),
                    total_premium=clean_numeric_string(record.get('total_premium', '0')),
                    baseline_expected_premium=clean_numeric_string(record.get('baseline_expected_premium', '0')),
                    premium_gap=clean_numeric_string(record.get('premium_gap', '0')),
                    opportunity_score=clean_integer_string(record.get('opportunity_score', '0'))
                )
                
                db.add(insurance_record)
                imported += 1
                
                # Commit in smaller batches
                if imported % 50 == 0:
                    try:
                        db.commit()
                        print(f"✅ Imported {imported} records (skipped {skipped} duplicates)...")
                        session_source_ids.clear()
                    except Exception as commit_error:
                        print(f"⚠️  Batch commit failed: {commit_error}")
                        db.rollback()
                        session_source_ids.clear()
                        errors += 1
                    
            except Exception as e:
                print(f"⚠️  Error with insurance record {record.get('source_id')}: {str(e)}")
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
        print("Usage: python import_insurance.py <path_to_json_file>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    import_insurance_data(json_file)
