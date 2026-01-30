from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta, date
from dateutil import parser as date_parser
from typing import List, Optional
from app.models import SIPRecord, InsuranceRecord, User, PortfolioHolding
from app.schemas import OpportunityClient, OpportunityStats, SIPRecordResponse, InsuranceOpportunity, InsuranceRecordResponse, UserResponse, PortfolioOpportunity, PortfolioHoldingResponse


def parse_date_safe(date_string: str) -> Optional[datetime]:
    """Safely parse date string to datetime object"""
    if not date_string or date_string == "":
        return None
    try:
        return date_parser.parse(date_string)
    except:
        return None


def get_days_since_date(date_string: str) -> Optional[int]:
    """Calculate days since a given date string"""
    parsed_date = parse_date_safe(date_string)
    if not parsed_date:
        return None
    return (datetime.now() - parsed_date).days


def get_months_since_date(date_string: str) -> Optional[int]:
    """Calculate months since a given date string"""
    days = get_days_since_date(date_string)
    if days is None:
        return None
    return days // 30


def get_no_sip_increase_clients(
    db: Session,
    agent_id: Optional[str] = None,
    min_months: int = 12,
    limit: int = 100
) -> List[OpportunityClient]:
    """
    Find clients who haven't increased their SIP for specified months or more.
    Criteria:
    - Active SIPs
    - Last success was long ago but no increment has happened
    - Has increment period configured but hasn't increased
    """
    query = db.query(SIPRecord).filter(
        SIPRecord.is_active == "true",
        SIPRecord.current_sip_status == "Success",
        SIPRecord.deleted == "false",
        SIPRecord.latest_success_order_date.isnot(None),
        SIPRecord.increment_percentage > 0
    )
    
    if agent_id:
        query = query.filter(SIPRecord.agent_id == agent_id)
    
    records = query.all()
    
    opportunities = []
    for record in records:
        months_since_last = get_months_since_date(record.latest_success_order_date)
        months_since_start = get_months_since_date(record.start_date)
        
        if months_since_last and months_since_start and months_since_last >= min_months:
            # Calculate expected increments based on increment_period
            increment_period = record.increment_period
            expected_increments = 0
            
            if increment_period == "6M" and months_since_start >= 6:
                expected_increments = months_since_start // 6
            elif increment_period == "1Y" and months_since_start >= 12:
                expected_increments = months_since_start // 12
            
            # Check if amount is still same (no increments happened)
            # This is a simplified check - in real scenario, you'd track historical changes
            if expected_increments > 0:
                potential_increase = record.amount * (record.increment_percentage / 100)
                
                opportunities.append(OpportunityClient(
                    user_id=record.user_id,
                    agent_id=record.agent_id or "0",
                    agent_external_id=record.agent_external_id or "unassigned",
                    opportunity_type="No SIP Increase",
                    opportunity_description=f"Client hasn't increased SIP for {months_since_last} months. Expected {expected_increments} increments based on {increment_period} period.",
                    current_sip_amount=record.amount,
                    potential_increase=potential_increase,
                    last_activity_date=record.latest_success_order_date,
                    days_since_activity=get_days_since_date(record.latest_success_order_date),
                    total_invested=record.success_amount,
                    risk_score=min(10.0, months_since_last / 6.0)
                ))
    
    # Sort by potential increase and limit
    opportunities.sort(key=lambda x: x.potential_increase or 0, reverse=True)
    return opportunities[:limit]


def get_failed_sip_clients(
    db: Session,
    agent_id: Optional[str] = None,
    min_failed_amount: float = 5000.0,
    limit: int = 100
) -> List[OpportunityClient]:
    """
    Find clients with failed SIP transactions requiring intervention.
    Criteria:
    - Has significant failed amount
    - Currently active or recently failed
    """
    query = db.query(SIPRecord).filter(
        SIPRecord.deleted == "false",
        SIPRecord.failed_amount >= min_failed_amount
    )
    
    if agent_id:
        query = query.filter(SIPRecord.agent_id == agent_id)
    
    records = query.order_by(desc(SIPRecord.failed_amount)).limit(limit * 2).all()
    
    opportunities = []
    for record in records:
        # Calculate failure rate
        total_attempted = record.success_amount + record.failed_amount
        failure_rate = (record.failed_amount / total_attempted * 100) if total_attempted > 0 else 0
        
        opportunities.append(OpportunityClient(
            user_id=record.user_id,
            agent_id=record.agent_id or "0",
            agent_external_id=record.agent_external_id or "unassigned",
            opportunity_type="Failed SIP Transactions",
            opportunity_description=f"Failed amount: ₹{record.failed_amount:,.0f} ({failure_rate:.1f}% failure rate). Status: {record.current_sip_status}. May need mandate renewal or payment issue resolution.",
            current_sip_amount=record.amount,
            potential_increase=record.failed_amount,  # Recovering failed amount
            last_activity_date=record.latest_success_order_date,
            days_since_activity=get_days_since_date(record.latest_success_order_date),
            total_invested=record.success_amount,
            failed_amount=record.failed_amount,
            risk_score=min(10.0, failure_rate / 10.0)
        ))
    
    return opportunities[:limit]


def get_high_value_inactive_clients(
    db: Session,
    agent_id: Optional[str] = None,
    min_invested_amount: float = 100000.0,
    min_inactive_days: int = 60,
    limit: int = 100
) -> List[OpportunityClient]:
    """
    Find high-value clients who have been inactive.
    These are good candidates for upsell/cross-sell opportunities.
    Criteria:
    - High total invested amount
    - No recent activity
    - Currently active but no recent transactions
    """
    query = db.query(SIPRecord).filter(
        SIPRecord.deleted == "false",
        SIPRecord.success_amount >= min_invested_amount,
        SIPRecord.latest_success_order_date.isnot(None)
    )
    
    if agent_id:
        query = query.filter(SIPRecord.agent_id == agent_id)
    
    records = query.order_by(desc(SIPRecord.success_amount)).limit(limit * 3).all()
    
    opportunities = []
    for record in records:
        days_since_activity = get_days_since_date(record.latest_success_order_date)
        
        if days_since_activity and days_since_activity >= min_inactive_days:
            # Calculate potential based on current portfolio
            potential_increase = record.amount * 1.5  # Suggest 50% increase or new product
            
            opportunities.append(OpportunityClient(
                user_id=record.user_id,
                agent_id=record.agent_id or "0",
                agent_external_id=record.agent_external_id or "unassigned",
                opportunity_type="High-Value Inactive Client",
                opportunity_description=f"High-value client (₹{record.success_amount:,.0f} invested) inactive for {days_since_activity} days. Good candidate for portfolio review, additional products, or insurance cross-sell.",
                current_sip_amount=record.amount,
                potential_increase=potential_increase,
                last_activity_date=record.latest_success_order_date,
                days_since_activity=days_since_activity,
                total_invested=record.success_amount,
                risk_score=min(10.0, days_since_activity / 30.0)
            ))
    
    opportunities.sort(key=lambda x: x.total_invested or 0, reverse=True)
    return opportunities[:limit]


def get_all_opportunities(
    db: Session,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[OpportunityClient]:
    """Get all opportunities combined"""
    all_opps = []
    
    # Get opportunities from each category (smaller limits)
    all_opps.extend(get_no_sip_increase_clients(db, agent_id, limit=limit//3))
    all_opps.extend(get_failed_sip_clients(db, agent_id, limit=limit//3))
    all_opps.extend(get_high_value_inactive_clients(db, agent_id, limit=limit//3))
    
    # Sort by risk score and potential
    all_opps.sort(key=lambda x: (x.risk_score or 0) + (x.potential_increase or 0) / 10000, reverse=True)
    
    return all_opps[:limit]


def get_opportunity_statistics(
    db: Session,
    agent_id: Optional[str] = None
) -> OpportunityStats:
    """Get statistics about opportunities"""
    
    # Get all opportunities
    no_increase = get_no_sip_increase_clients(db, agent_id, limit=1000)
    failed_sips = get_failed_sip_clients(db, agent_id, limit=1000)
    high_value = get_high_value_inactive_clients(db, agent_id, limit=1000)
    
    total_potential = sum([
        sum(o.potential_increase or 0 for o in no_increase),
        sum(o.potential_increase or 0 for o in failed_sips),
        sum(o.potential_increase or 0 for o in high_value)
    ])
    
    return OpportunityStats(
        total_opportunities=len(no_increase) + len(failed_sips) + len(high_value),
        total_potential_revenue=total_potential,
        breakdown_by_type={
            "no_sip_increase": {
                "count": len(no_increase),
                "potential_revenue": sum(o.potential_increase or 0 for o in no_increase)
            },
            "failed_sips": {
                "count": len(failed_sips),
                "potential_revenue": sum(o.potential_increase or 0 for o in failed_sips)
            },
            "high_value_inactive": {
                "count": len(high_value),
                "potential_revenue": sum(o.potential_increase or 0 for o in high_value)
            }
        }
    )


def get_all_agents(db: Session) -> List[dict]:
    """Get list of all agents with their stats"""
    agents = db.query(
        SIPRecord.agent_id,
        SIPRecord.agent_external_id,
        func.count(SIPRecord.id).label('total_sips'),
        func.sum(SIPRecord.success_amount).label('total_aum')
    ).filter(
        SIPRecord.deleted == "false"
    ).group_by(
        SIPRecord.agent_id,
        SIPRecord.agent_external_id
    ).order_by(
        desc('total_aum')
    ).all()
    
    return [
        {
            "agent_id": agent.agent_id,
            "agent_external_id": agent.agent_external_id,
            "total_sips": agent.total_sips,
            "total_aum": agent.total_aum or 0
        }
        for agent in agents
    ]


def get_client_sip_records(db: Session, user_id: str) -> List[SIPRecordResponse]:
    """Get all SIP records for a specific client"""
    records = db.query(SIPRecord).filter(
        SIPRecord.user_id == user_id,
        SIPRecord.deleted == "false"
    ).all()
    
    return records


# ==================== Insurance Services ====================

def get_insurance_gap_opportunities(
    db: Session,
    agent_id: Optional[str] = None,
    min_premium_gap: float = 10000.0,
    min_opportunity_score: int = 0,
    limit: int = 100
) -> List[InsuranceOpportunity]:
    """
    Find clients with insurance coverage gaps.
    These are clients paying less premium than their baseline expectation.
    """
    query = db.query(InsuranceRecord).filter(
        InsuranceRecord.deleted == "false",
        InsuranceRecord.premium_gap >= min_premium_gap,
        InsuranceRecord.opportunity_score >= min_opportunity_score
    )
    
    if agent_id:
        query = query.filter(InsuranceRecord.agent_id == agent_id)
    
    records = query.order_by(desc(InsuranceRecord.opportunity_score)).limit(limit * 2).all()
    
    # Group by user to get unique clients
    client_insurance = {}
    for record in records:
        user_id = record.user_id
        if user_id not in client_insurance:
            client_insurance[user_id] = {
                'record': record,
                'insurance_types': set(),
                'total_premium': 0
            }
        client_insurance[user_id]['insurance_types'].add(record.insurance_type or 'Unknown')
        client_insurance[user_id]['total_premium'] += record.premium or 0
    
    opportunities = []
    for user_id, data in client_insurance.items():
        record = data['record']
        insurance_types = data['insurance_types']
        
        # Identify missing coverage types
        all_types = {'Health', 'Term', 'ULIP', 'Traditional'}
        missing_types = list(all_types - insurance_types)
        
        description = f"Client has ₹{record.premium_gap:,.0f} premium gap. "
        description += f"Current coverage: {', '.join(insurance_types)}. "
        if missing_types:
            description += f"Consider adding: {', '.join(missing_types)}."
        
        opportunities.append(InsuranceOpportunity(
            user_id=user_id,
            name=record.name or "Unknown",
            agent_id=record.agent_id or "0",
            agent_external_id=record.agent_external_id or "unassigned",
            opportunity_type="Insurance Coverage Gap",
            opportunity_description=description,
            wealth_band=record.wealth_band or "Unknown",
            age=record.mock_age,
            mf_current_value=record.mf_current_value or 0,
            total_premium=data['total_premium'],
            baseline_expected_premium=record.baseline_expected_premium or 0,
            premium_gap=record.premium_gap or 0,
            opportunity_score=record.opportunity_score or 0,
            missing_coverage_types=missing_types
        ))
    
    # Sort by opportunity score
    opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
    return opportunities[:limit]


def get_no_insurance_clients(
    db: Session,
    agent_id: Optional[str] = None,
    min_mf_value: float = 1000000.0,
    limit: int = 100
) -> List[InsuranceOpportunity]:
    """
    Find clients with high MF investments but no insurance.
    These are high-priority cross-sell opportunities.
    """
    # Get all SIP clients with high investments
    sip_query = db.query(
        SIPRecord.user_id,
        func.sum(SIPRecord.success_amount).label('total_invested')
    ).filter(
        SIPRecord.deleted == "false"
    )
    
    if agent_id:
        sip_query = sip_query.filter(SIPRecord.agent_id == agent_id)
    
    sip_clients = sip_query.group_by(SIPRecord.user_id).having(
        func.sum(SIPRecord.success_amount) >= min_mf_value
    ).all()
    
    # Get all clients with insurance
    insured_clients = set([
        r.user_id for r in db.query(InsuranceRecord.user_id).filter(
            InsuranceRecord.deleted == "false"
        ).distinct().all()
    ])
    
    opportunities = []
    for sip_client in sip_clients:
        if sip_client.user_id not in insured_clients:
            # Get client details from SIP record
            sip_record = db.query(SIPRecord).filter(
                SIPRecord.user_id == sip_client.user_id,
                SIPRecord.deleted == "false"
            ).first()
            
            if sip_record:
                # Estimate expected premium based on investment
                expected_premium = min(100000, sip_client.total_invested * 0.02)  # 2% of investment
                
                opportunities.append(InsuranceOpportunity(
                    user_id=sip_client.user_id,
                    name="Unknown",  # SIP data doesn't have name
                    agent_id=sip_record.agent_id or "0",
                    agent_external_id=sip_record.agent_external_id or "unassigned",
                    opportunity_type="No Insurance Coverage",
                    opportunity_description=f"High-value client (₹{sip_client.total_invested:,.0f} MF investment) with NO insurance coverage. High-priority cross-sell opportunity.",
                    wealth_band="5Cr+" if sip_client.total_invested >= 5000000 else "1Cr-5Cr",
                    age=None,
                    mf_current_value=sip_client.total_invested,
                    total_premium=0,
                    baseline_expected_premium=expected_premium,
                    premium_gap=expected_premium,
                    opportunity_score=100,  # Highest priority
                    missing_coverage_types=['Health', 'Term', 'ULIP', 'Traditional']
                ))
    
    # Sort by MF value
    opportunities.sort(key=lambda x: x.mf_current_value, reverse=True)
    return opportunities[:limit]


def get_insurance_renewal_opportunities(
    db: Session,
    agent_id: Optional[str] = None,
    months_until_renewal: int = 3,
    limit: int = 100
) -> List[InsuranceOpportunity]:
    """
    Find insurance policies due for renewal soon.
    Good for proactive client engagement.
    """
    # This would require policy expiry dates in the data
    # For now, return empty list as policy_issue_date doesn't have expiry
    return []


def get_client_insurance_records(db: Session, user_id: str) -> List[InsuranceRecordResponse]:
    """Get all insurance records for a specific client"""
    records = db.query(InsuranceRecord).filter(
        InsuranceRecord.user_id == user_id,
        InsuranceRecord.deleted == "false"
    ).all()
    
    return records


def get_insurance_statistics(
    db: Session,
    agent_id: Optional[str] = None
) -> dict:
    """Get insurance statistics"""
    
    query = db.query(InsuranceRecord).filter(
        InsuranceRecord.deleted == "false"
    )
    
    if agent_id:
        query = query.filter(InsuranceRecord.agent_id == agent_id)
    
    total_policies = query.count()
    total_premium = query.with_entities(func.sum(InsuranceRecord.premium)).scalar() or 0
    total_gap = query.with_entities(func.sum(InsuranceRecord.premium_gap)).scalar() or 0
    
    # Group by insurance type
    by_type = query.with_entities(
        InsuranceRecord.insurance_type,
        func.count(InsuranceRecord.id).label('count'),
        func.sum(InsuranceRecord.premium).label('total_premium')
    ).group_by(InsuranceRecord.insurance_type).all()
    
    type_breakdown = {
        item.insurance_type or 'Unknown': {
            'count': item.count,
            'total_premium': item.total_premium or 0
        }
        for item in by_type
    }
    
    return {
        'total_policies': total_policies,
        'total_premium_collected': total_premium,
        'total_premium_gap': total_gap,
        'potential_additional_revenue': total_gap,
        'breakdown_by_type': type_breakdown
    }


# ==================== User Services ====================

def get_all_users(
    db: Session,
    agent_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[UserResponse]:
    """Get all users with optional filtering"""
    query = db.query(User)
    
    if agent_id:
        query = query.filter(User.agent_external_id == agent_id)
    
    users = query.order_by(desc(User.total_current_value)).offset(offset).limit(limit).all()
    return users


def get_user_by_id(db: Session, user_id: str) -> Optional[UserResponse]:
    """Get a specific user by user_id"""
    return db.query(User).filter(User.user_id == user_id).first()


def get_high_value_users(
    db: Session,
    min_value: float = 1000000.0,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[UserResponse]:
    """Get high-value users based on total current value"""
    query = db.query(User).filter(
        User.total_current_value >= min_value
    )
    
    if agent_id:
        query = query.filter(User.agent_external_id == agent_id)
    
    return query.order_by(desc(User.total_current_value)).limit(limit).all()


def get_users_by_age_range(
    db: Session,
    min_age: int = 25,
    max_age: int = 70,
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[UserResponse]:
    """Get users within a specific age range"""
    current_year = datetime.now().year
    max_birth_year = current_year - min_age
    min_birth_year = current_year - max_age
    
    query = db.query(User).filter(
        User.date_of_birth.isnot(None),
        func.extract('year', User.date_of_birth) >= min_birth_year,
        func.extract('year', User.date_of_birth) <= max_birth_year
    )
    
    if agent_id:
        query = query.filter(User.agent_external_id == agent_id)
    
    return query.order_by(desc(User.total_current_value)).limit(limit).all()


def get_user_statistics(
    db: Session,
    agent_id: Optional[str] = None
) -> dict:
    """Get user statistics"""
    query = db.query(User)
    
    if agent_id:
        query = query.filter(User.agent_external_id == agent_id)
    
    total_users = query.count()
    total_aum = query.with_entities(func.sum(User.total_current_value)).scalar() or 0
    total_invested = query.with_entities(func.sum(User.total_invested_value)).scalar() or 0
    avg_portfolio = total_aum / total_users if total_users > 0 else 0
    
    # Count by product
    users_with_mf = query.filter(User.mf_current_value > 0).count()
    users_with_fd = query.filter(User.fd_current_value > 0).count()
    users_with_pms = query.filter(User.pms_current_value > 0).count()
    users_with_aif = query.filter(User.aif_current_value > 0).count()
    users_with_preipo = query.filter(User.preipo_current_value > 0).count()
    
    return {
        'total_users': total_users,
        'total_aum': total_aum,
        'total_invested': total_invested,
        'average_portfolio_value': avg_portfolio,
        'total_returns': total_aum - total_invested,
        'overall_return_percentage': ((total_aum - total_invested) / total_invested * 100) if total_invested > 0 else 0,
        'product_penetration': {
            'mutual_funds': users_with_mf,
            'fixed_deposits': users_with_fd,
            'pms': users_with_pms,
            'aif': users_with_aif,
            'preipo': users_with_preipo
        }
    }


# ==================== Portfolio Services ====================

def get_underperforming_funds(
    db: Session,
    user_id: Optional[str] = None,
    min_current_value: float = 0,
    limit: int = 100
) -> List[PortfolioOpportunity]:
    """
    Find underperforming mutual funds based on negative alpha and XIRR performance.
    These are funds that should be reviewed for switching/redemption.
    """
    query = db.query(PortfolioHolding).filter(
        or_(
            PortfolioHolding.three_year_returns_alpha < 0,
            PortfolioHolding.five_year_returns_alpha < 0,
            PortfolioHolding.xirr_performance < 0
        ),
        PortfolioHolding.current_value >= min_current_value
    )
    
    if user_id:
        query = query.filter(PortfolioHolding.user_id == user_id)
    
    holdings = query.order_by(desc(PortfolioHolding.current_value)).limit(limit).all()
    
    opportunities = []
    for holding in holdings:
        # Determine opportunity type based on performance
        issues = []
        if holding.three_year_returns_alpha and holding.three_year_returns_alpha < 0:
            issues.append(f"3Y alpha: {holding.three_year_returns_alpha:.2f}%")
        if holding.five_year_returns_alpha and holding.five_year_returns_alpha < 0:
            issues.append(f"5Y alpha: {holding.five_year_returns_alpha:.2f}%")
        if holding.xirr_performance and holding.xirr_performance < 0:
            issues.append(f"XIRR underperformance: {holding.xirr_performance:.2f}%")
        
        opportunities.append(PortfolioOpportunity(
            user_id=holding.user_id,
            scheme_name=holding.scheme_name,
            wpc=holding.wpc,
            category=holding.category,
            amc_name=holding.amc_name,
            current_value=holding.current_value,
            portfolio_weight=holding.portfolio_weight,
            opportunity_type="Underperforming Fund",
            opportunity_description=f"Fund showing negative performance. {', '.join(issues)}. {holding.comment or 'Consider switching to better performing alternatives.'}",
            w_rating=holding.w_rating,
            xirr_performance=holding.xirr_performance,
            three_year_returns_alpha=holding.three_year_returns_alpha,
            five_year_returns_alpha=holding.five_year_returns_alpha,
            rolling_12q_beat_percentage=holding.rolling_12q_beat_percentage
        ))
    
    return opportunities


def get_low_rated_funds(
    db: Session,
    user_id: Optional[str] = None,
    max_rating: float = 3.0,
    min_current_value: float = 0,
    limit: int = 100
) -> List[PortfolioOpportunity]:
    """
    Find low-rated funds (rating < 3.0) that should be reviewed.
    """
    query = db.query(PortfolioHolding).filter(
        PortfolioHolding.w_rating.isnot(None),
        PortfolioHolding.current_value >= min_current_value
    )
    
    if user_id:
        query = query.filter(PortfolioHolding.user_id == user_id)
    
    holdings = query.all()
    
    # Filter by rating (convert string to float)
    low_rated = []
    for holding in holdings:
        try:
            rating = float(holding.w_rating)
            if rating < max_rating:
                low_rated.append(holding)
        except (ValueError, TypeError):
            continue
    
    # Sort by current value and limit
    low_rated.sort(key=lambda x: x.current_value, reverse=True)
    low_rated = low_rated[:limit]
    
    opportunities = []
    for holding in low_rated:
        opportunities.append(PortfolioOpportunity(
            user_id=holding.user_id,
            scheme_name=holding.scheme_name,
            wpc=holding.wpc,
            category=holding.category,
            amc_name=holding.amc_name,
            current_value=holding.current_value,
            portfolio_weight=holding.portfolio_weight,
            opportunity_type="Low Rated Fund",
            opportunity_description=f"Fund has low rating of {holding.w_rating}. {holding.comment or 'Consider reviewing and switching to higher rated alternatives.'}",
            w_rating=holding.w_rating,
            xirr_performance=holding.xirr_performance,
            three_year_returns_alpha=holding.three_year_returns_alpha,
            five_year_returns_alpha=holding.five_year_returns_alpha,
            rolling_12q_beat_percentage=holding.rolling_12q_beat_percentage
        ))
    
    return opportunities


def get_portfolio_rebalancing_opportunities(
    db: Session,
    user_id: Optional[str] = None,
    min_concentration: float = 25.0,
    limit: int = 100
) -> List[PortfolioOpportunity]:
    """
    Find portfolios with high concentration in single funds (>25% weight).
    These may need rebalancing for better diversification.
    """
    query = db.query(PortfolioHolding).filter(
        PortfolioHolding.portfolio_weight >= min_concentration
    )
    
    if user_id:
        query = query.filter(PortfolioHolding.user_id == user_id)
    
    holdings = query.order_by(desc(PortfolioHolding.portfolio_weight)).limit(limit).all()
    
    opportunities = []
    for holding in holdings:
        opportunities.append(PortfolioOpportunity(
            user_id=holding.user_id,
            scheme_name=holding.scheme_name,
            wpc=holding.wpc,
            category=holding.category,
            amc_name=holding.amc_name,
            current_value=holding.current_value,
            portfolio_weight=holding.portfolio_weight,
            opportunity_type="Portfolio Concentration",
            opportunity_description=f"Fund represents {holding.portfolio_weight:.1f}% of portfolio. Consider rebalancing for better diversification across multiple funds and categories.",
            w_rating=holding.w_rating,
            xirr_performance=holding.xirr_performance,
            three_year_returns_alpha=holding.three_year_returns_alpha,
            five_year_returns_alpha=holding.five_year_returns_alpha,
            rolling_12q_beat_percentage=holding.rolling_12q_beat_percentage
        ))
    
    return opportunities


def get_all_portfolio_opportunities(
    db: Session,
    user_id: Optional[str] = None,
    limit: int = 100
) -> List[PortfolioOpportunity]:
    """Get all portfolio opportunities combined"""
    all_opps = []
    
    # Get opportunities from each category
    all_opps.extend(get_underperforming_funds(db, user_id, limit=limit//3))
    all_opps.extend(get_low_rated_funds(db, user_id, limit=limit//3))
    all_opps.extend(get_portfolio_rebalancing_opportunities(db, user_id, limit=limit//3))
    
    # Sort by current value
    all_opps.sort(key=lambda x: x.current_value, reverse=True)
    
    return all_opps[:limit]


def get_user_portfolio_holdings(
    db: Session,
    user_id: str,
    limit: int = 100
) -> List[PortfolioHoldingResponse]:
    """Get all portfolio holdings for a specific user"""
    holdings = db.query(PortfolioHolding).filter(
        PortfolioHolding.user_id == user_id
    ).order_by(desc(PortfolioHolding.current_value)).limit(limit).all()
    
    return holdings


def get_portfolio_statistics(
    db: Session,
    user_id: Optional[str] = None
) -> dict:
    """Get portfolio statistics"""
    query = db.query(PortfolioHolding)
    
    if user_id:
        query = query.filter(PortfolioHolding.user_id == user_id)
    
    total_holdings = query.count()
    total_value = query.with_entities(func.sum(PortfolioHolding.current_value)).scalar() or 0
    avg_holding_value = total_value / total_holdings if total_holdings > 0 else 0
    
    # Get underperforming counts
    underperforming_count = query.filter(
        or_(
            PortfolioHolding.three_year_returns_alpha < 0,
            PortfolioHolding.xirr_performance < 0
        )
    ).count()
    
    # Get low rated count
    low_rated_count = 0
    for holding in query.all():
        try:
            if holding.w_rating and float(holding.w_rating) < 3.0:
                low_rated_count += 1
        except (ValueError, TypeError):
            continue
    
    # Get concentrated holdings
    concentrated_count = query.filter(
        PortfolioHolding.portfolio_weight >= 25.0
    ).count()
    
    # Category breakdown
    category_breakdown = query.with_entities(
        PortfolioHolding.category,
        func.count(PortfolioHolding.id).label('count'),
        func.sum(PortfolioHolding.current_value).label('total_value')
    ).group_by(PortfolioHolding.category).all()
    
    category_dict = {
        item.category or 'Unknown': {
            'count': item.count,
            'total_value': item.total_value or 0
        }
        for item in category_breakdown
    }
    
    return {
        'total_holdings': total_holdings,
        'total_portfolio_value': total_value,
        'average_holding_value': avg_holding_value,
        'underperforming_funds_count': underperforming_count,
        'low_rated_funds_count': low_rated_count,
        'concentrated_holdings_count': concentrated_count,
        'category_breakdown': category_dict
    }
