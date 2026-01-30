#!/usr/bin/env python
"""
Export all distinct user IDs from all tables (Users, SIP, Insurance, Portfolio).
Outputs a text file with one user_id per line.
Includes ALL users, including those with deleted == "true".
"""

import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import SIPRecord, InsuranceRecord, User, PortfolioHolding
from sqlalchemy import distinct


def export_user_ids(output_file: str = None, agent_id: str = None):
    """
    Export all distinct user IDs from all tables (Users, SIP, Insurance, Portfolio).
    Includes ALL users regardless of deleted status.
    
    Args:
        output_file: Path to output file. If None, uses default name.
        agent_id: Optional agent_id to filter by specific agent.
    """
    
    # Default output file name
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"user_ids_{timestamp}.txt"
    
    print("🔍 Extracting distinct user IDs from ALL tables...")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Get distinct user_ids from Users table
        print("   Querying Users table...")
        users_query = db.query(distinct(User.user_id)).filter(
            User.user_id.isnot(None)
        )
        
        if agent_id:
            users_query = users_query.filter(User.agent_external_id == agent_id)
        
        users_table = set([user_id for (user_id,) in users_query.all()])
        print(f"   Found {len(users_table)} unique users in Users table")
        
        # Get distinct user_ids from SIP records (NO deleted filter)
        print("   Querying SIP records...")
        sip_query = db.query(distinct(SIPRecord.user_id)).filter(
            SIPRecord.user_id.isnot(None)
        )
        
        if agent_id:
            sip_query = sip_query.filter(SIPRecord.agent_id == agent_id)
        
        sip_users = set([user_id for (user_id,) in sip_query.all()])
        print(f"   Found {len(sip_users)} unique users in SIP records")
        
        # Get distinct user_ids from Insurance records (NO deleted filter)
        print("   Querying Insurance records...")
        insurance_query = db.query(distinct(InsuranceRecord.user_id)).filter(
            InsuranceRecord.user_id.isnot(None)
        )
        
        if agent_id:
            insurance_query = insurance_query.filter(InsuranceRecord.agent_id == agent_id)
        
        insurance_users = set([user_id for (user_id,) in insurance_query.all()])
        print(f"   Found {len(insurance_users)} unique users in Insurance records")
        
        # Get distinct user_ids from Portfolio holdings
        print("   Querying Portfolio holdings...")
        portfolio_query = db.query(distinct(PortfolioHolding.user_id)).filter(
            PortfolioHolding.user_id.isnot(None)
        )
        
        # Note: Portfolio doesn't have agent_id field
        portfolio_users = set([user_id for (user_id,) in portfolio_query.all()])
        print(f"   Found {len(portfolio_users)} unique users in Portfolio holdings")
        
        # Combine and deduplicate from all sources
        all_user_ids = users_table.union(sip_users).union(insurance_users).union(portfolio_users)
        all_user_ids = sorted(list(all_user_ids))  # Sort for consistency
        
        print(f"\n✅ Total distinct users across all tables: {len(all_user_ids)}")
        print(f"   - Users table only: {len(users_table - sip_users - insurance_users - portfolio_users)}")
        print(f"   - SIP only: {len(sip_users - users_table - insurance_users - portfolio_users)}")
        print(f"   - Insurance only: {len(insurance_users - users_table - sip_users - portfolio_users)}")
        print(f"   - Portfolio only: {len(portfolio_users - users_table - sip_users - insurance_users)}")
        print(f"   - In all 4 tables: {len(users_table & sip_users & insurance_users & portfolio_users)}")
        
        # Write to file
        print(f"\n📝 Writing to file: {output_file}")
        with open(output_file, 'w') as f:
            # Write header
            f.write(f"# Distinct User IDs from ALL tables\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if agent_id:
                f.write(f"# Filtered by agent_id: {agent_id}\n")
            f.write(f"# Total users: {len(all_user_ids)}\n")
            f.write(f"# Users table: {len(users_table)}\n")
            f.write(f"# SIP records: {len(sip_users)}\n")
            f.write(f"# Insurance records: {len(insurance_users)}\n")
            f.write(f"# Portfolio holdings: {len(portfolio_users)}\n")
            f.write(f"# In all 4 tables: {len(users_table & sip_users & insurance_users & portfolio_users)}\n")
            f.write(f"# Note: Includes deleted records\n")
            f.write("#\n")
            
            # Write user IDs
            for user_id in all_user_ids:
                f.write(f"'{user_id}',")
        
        print(f"✅ Successfully exported {len(all_user_ids)} user IDs to {output_file}")
        
        # Also create a CSV with additional info
        csv_file = output_file.replace('.txt', '_detailed.csv')
        print(f"\n📊 Creating detailed CSV: {csv_file}")
        
        with open(csv_file, 'w') as f:
            f.write("user_id,in_users_table,has_sip,has_insurance,has_portfolio\n")
            for user_id in all_user_ids:
                in_users = "Yes" if user_id in users_table else "No"
                has_sip = "Yes" if user_id in sip_users else "No"
                has_insurance = "Yes" if user_id in insurance_users else "No"
                has_portfolio = "Yes" if user_id in portfolio_users else "No"
                f.write(f"{user_id},{in_users},{has_sip},{has_insurance},{has_portfolio}\n")
        
        print(f"✅ Detailed CSV created: {csv_file}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    finally:
        db.close()
    
    return 0


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Export distinct user IDs from all tables (Users, SIP, Insurance, Portfolio). Includes deleted records.'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: user_ids_TIMESTAMP.txt)',
        default=None
    )
    parser.add_argument(
        '-a', '--agent',
        help='Filter by agent_id',
        default=None
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("User ID Export Tool")
    print("=" * 60)
    print()
    
    exit_code = export_user_ids(
        output_file=args.output,
        agent_id=args.agent
    )
    
    print()
    print("=" * 60)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
