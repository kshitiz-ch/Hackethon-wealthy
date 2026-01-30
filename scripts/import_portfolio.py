#!/usr/bin/env python3
"""
Import portfolio holdings data from JSON file into the database.
This script processes mutual fund portfolio data including holdings, performance metrics,
and opportunity analysis.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import PortfolioHolding, Base


def import_portfolio_data(json_file_path: str):
    """Import portfolio data from JSON file"""
    
    print(f"📊 Starting portfolio data import from {json_file_path}")
    
    # Create tables if they don't exist
    print("📋 Creating tables if needed...")
    Base.metadata.create_all(bind=engine)
    
    # Load JSON data
    print("📖 Loading JSON data...")
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File not found at {json_file_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format - {e}")
        return
    
    print(f"✅ Loaded data for {data.get('total_users', 0)} users")
    print(f"   Successful: {data.get('successful', 0)}, Failed: {data.get('failed', 0)}")
    
    db = SessionLocal()
    
    try:
        imported_count = 0
        skipped_count = 0
        users_processed = 0
        
        results = data.get('results', [])
        total_users = len(results)
        
        for idx, result in enumerate(results, 1):
            user_id = result.get('user_id')
            pan_number = result.get('pan_number')
            client_details = result.get('client_details', {})
            as_on_date = client_details.get('as_on_date')
            
            print(f"\n[{idx}/{total_users}] Processing user: {user_id} ({client_details.get('name', 'Unknown')})")
            
            holdings_count = 0
            
            # Process each holding in top_holdings_bucket
            for holding in result.get('top_holdings_bucket', []):
                try:
                    # Extract rolling returns data
                    rolling_4q = holding.get('rolling_4_quarter_returns_comparison', {})
                    rolling_12q = holding.get('rolling_12_quarter_returns_comparison', {})
                    
                    portfolio_holding = PortfolioHolding(
                        user_id=user_id,
                        pan_number=pan_number,
                        as_on_date=as_on_date,
                        wpc=holding.get('wpc'),
                        scheme_name=holding.get('scheme_name'),
                        category=holding.get('category'),
                        amc_name=holding.get('amc_name'),
                        nav=holding.get('nav'),
                        nav_as_on=holding.get('nav_as_on'),
                        current_value=holding.get('current_value'),
                        portfolio_weight=holding.get('portfolio_weight'),
                        benchmark_name=holding.get('benchmark_name'),
                        live_xirr=holding.get('live_xirr'),
                        benchmark_xirr=holding.get('benchmark_xirr'),
                        xirr_performance=holding.get('xirr_performance'),
                        one_year_returns=holding.get('one_year_returns'),
                        three_year_returns_cagr=holding.get('three_year_returns_cagr'),
                        benchmark_three_year_returns_cagr=holding.get('benchmark_three_year_returns_cagr'),
                        three_year_returns_alpha=holding.get('three_year_returns_alpha'),
                        five_year_returns_cagr=holding.get('five_year_returns_cagr'),
                        benchmark_five_year_returns_cagr=holding.get('benchmark_five_year_returns_cagr'),
                        five_year_returns_alpha=holding.get('five_year_returns_alpha'),
                        rolling_4q_beat_count=rolling_4q.get('beat_quarters_count'),
                        rolling_4q_total_count=rolling_4q.get('total_quarters'),
                        rolling_4q_beat_percentage=rolling_4q.get('beat_percentage'),
                        rolling_12q_beat_count=rolling_12q.get('beat_quarters_count'),
                        rolling_12q_total_count=rolling_12q.get('total_quarters'),
                        rolling_12q_beat_percentage=rolling_12q.get('beat_percentage'),
                        realized_stcg=holding.get('realized_stcg'),
                        realized_ltcg=holding.get('realized_ltcg'),
                        unrealized_stu=holding.get('unrealized_stu'),
                        unrealized_ltu=holding.get('unrealized_ltu'),
                        cost_of_unrealized_stu=holding.get('cost_of_unrealized_stu'),
                        cost_of_unrealized_ltu=holding.get('cost_of_unrealized_ltu'),
                        unrealized_stcg=holding.get('unrealized_stcg'),
                        unrealized_ltcg=holding.get('unrealized_ltcg'),
                        comment=holding.get('comment'),
                        w_rating=holding.get('w_rating')
                    )
                    
                    db.add(portfolio_holding)
                    imported_count += 1
                    holdings_count += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Error importing holding {holding.get('wpc')} for user {user_id}: {e}")
                    skipped_count += 1
                    continue
            
            print(f"   ✅ Imported {holdings_count} holdings for this user")
            users_processed += 1
            
            # Commit every 10 users to avoid memory issues
            if users_processed % 10 == 0:
                try:
                    print(f"\n💾 Committing batch... ({users_processed}/{total_users} users processed)")
                    db.commit()
                except Exception as commit_error:
                    print(f"⚠️  Batch commit failed: {commit_error}")
                    db.rollback()
        
        # Final commit
        try:
            print(f"\n💾 Final commit...")
            db.commit()
            
            print(f"\n{'='*60}")
            print(f"✅ Import Complete!")
            print(f"{'='*60}")
            print(f"Users processed: {users_processed}")
            print(f"Holdings imported: {imported_count}")
            print(f"Holdings skipped: {skipped_count}")
            if (imported_count + skipped_count) > 0:
                print(f"Success rate: {imported_count / (imported_count + skipped_count) * 100:.1f}%")
        except Exception as final_commit_error:
            print(f"⚠️  Final commit had issues: {final_commit_error}")
            db.rollback()
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        print(f"Rolling back transaction...")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    # Default file path
    default_path = "/Users/rishurajsinha/Downloads/portfolio_data.json"
    
    # Check if custom path provided
    if len(sys.argv) > 1:
        json_file_path = sys.argv[1]
    else:
        json_file_path = default_path
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║         Portfolio Data Import Script                      ║
║         Wealthy Partner Dashboard                         ║
╚════════════════════════════════════════════════════════════╝
""")
    
    import_portfolio_data(json_file_path)
