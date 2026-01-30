from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import schemas
from app import services

app = FastAPI(
    title="Wealthy Partner Dashboard API",
    description="API for identifying selling opportunities in client portfolios (SIP + Insurance + Portfolio Analysis)",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "Wealthy Partner Dashboard API",
        "version": "3.0.0",
        "modules": {
            "sip": "Systematic Investment Plan opportunities",
            "insurance": "Insurance coverage and gap analysis",
            "portfolio": "Portfolio holdings and fund performance analysis"
        },
        "endpoints": {
            "sip_opportunities": {
                "all": "/api/opportunities",
                "no_increase": "/api/opportunities/no-sip-increase",
                "failed": "/api/opportunities/failed-sips",
                "inactive": "/api/opportunities/high-value-inactive",
                "stats": "/api/opportunities/stats"
            },
            "insurance_opportunities": {
                "gaps": "/api/insurance/opportunities/gaps",
                "no_coverage": "/api/insurance/opportunities/no-coverage",
                "stats": "/api/insurance/stats"
            },
            "portfolio_opportunities": {
                "all": "/api/portfolio/opportunities",
                "underperforming": "/api/portfolio/opportunities/underperforming",
                "low_rated": "/api/portfolio/opportunities/low-rated",
                "concentration": "/api/portfolio/opportunities/concentration",
                "stats": "/api/portfolio/stats"
            },
            "clients": {
                "sips": "/api/clients/{user_id}/sips",
                "insurance": "/api/clients/{user_id}/insurance",
                "portfolio": "/api/clients/{user_id}/portfolio"
            },
            "users": {
                "all": "/api/users",
                "by_id": "/api/users/{user_id}",
                "high_value": "/api/users/high-value/list",
                "by_age": "/api/users/age-range/list",
                "stats": "/api/users/stats"
            },
            "agents": "/api/agents"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/opportunities", response_model=List[schemas.OpportunityClient])
def get_all_opportunities(
    agent_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all selling opportunities across all categories"""
    return services.get_all_opportunities(db, agent_id=agent_id, limit=limit)


@app.get("/api/opportunities/no-sip-increase", response_model=List[schemas.OpportunityClient])
def get_no_sip_increase_opportunities(
    agent_id: Optional[str] = None,
    min_months: int = Query(12, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get clients who haven't increased their SIP for specified months or more.
    This identifies clients who may be ready for an investment increase.
    """
    return services.get_no_sip_increase_clients(db, agent_id=agent_id, min_months=min_months, limit=limit)


@app.get("/api/opportunities/failed-sips", response_model=List[schemas.OpportunityClient])
def get_failed_sip_opportunities(
    agent_id: Optional[str] = None,
    min_failed_amount: float = Query(5000.0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get clients with failed SIP transactions requiring intervention.
    These clients may need mandate renewal or payment resolution.
    """
    return services.get_failed_sip_clients(db, agent_id=agent_id, min_failed_amount=min_failed_amount, limit=limit)


@app.get("/api/opportunities/high-value-inactive", response_model=List[schemas.OpportunityClient])
def get_high_value_inactive_opportunities(
    agent_id: Optional[str] = None,
    min_invested_amount: float = Query(100000.0, ge=0),
    min_inactive_days: int = Query(60, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get high-value clients who have been inactive for a while.
    These are upsell/cross-sell opportunities for additional products.
    """
    return services.get_high_value_inactive_clients(
        db, agent_id=agent_id, min_invested_amount=min_invested_amount,
        min_inactive_days=min_inactive_days, limit=limit
    )


@app.get("/api/opportunities/stats", response_model=schemas.OpportunityStats)
def get_opportunity_stats(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get statistics about selling opportunities"""
    return services.get_opportunity_statistics(db, agent_id=agent_id)


@app.get("/api/agents", response_model=List[dict])
def get_agents(db: Session = Depends(get_db)):
    """Get list of all agents/advisors"""
    return services.get_all_agents(db)


@app.get("/api/clients/{user_id}/sips", response_model=List[schemas.SIPRecordResponse])
def get_client_sips(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all SIP records for a specific client"""
    return services.get_client_sip_records(db, user_id)


# ==================== Insurance Endpoints ====================

@app.get("/api/insurance/opportunities/gaps", response_model=List[schemas.InsuranceOpportunity])
def get_insurance_gap_opportunities(
    agent_id: Optional[str] = None,
    min_premium_gap: float = Query(10000.0, ge=0),
    min_opportunity_score: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get clients with insurance coverage gaps.
    These clients are paying less premium than their baseline expectation based on wealth.
    """
    return services.get_insurance_gap_opportunities(
        db, agent_id=agent_id, min_premium_gap=min_premium_gap,
        min_opportunity_score=min_opportunity_score, limit=limit
    )


@app.get("/api/insurance/opportunities/no-coverage", response_model=List[schemas.InsuranceOpportunity])
def get_no_insurance_opportunities(
    agent_id: Optional[str] = None,
    min_mf_value: float = Query(1000000.0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get high-value MF clients with NO insurance coverage.
    These are the highest priority cross-sell opportunities.
    """
    return services.get_no_insurance_clients(
        db, agent_id=agent_id, min_mf_value=min_mf_value, limit=limit
    )


@app.get("/api/insurance/stats")
def get_insurance_statistics(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get insurance portfolio statistics"""
    return services.get_insurance_statistics(db, agent_id=agent_id)


@app.get("/api/clients/{user_id}/insurance", response_model=List[schemas.InsuranceRecordResponse])
def get_client_insurance(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all insurance records for a specific client"""
    return services.get_client_insurance_records(db, user_id)


# ==================== User Endpoints ====================

@app.get("/api/users", response_model=List[schemas.UserResponse])
def get_all_users(
    agent_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get all users with pagination"""
    return services.get_all_users(db, agent_id=agent_id, limit=limit, offset=offset)


@app.get("/api/users/{user_id}", response_model=schemas.UserResponse)
def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific user by user_id"""
    user = services.get_user_by_id(db, user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/users/high-value/list", response_model=List[schemas.UserResponse])
def get_high_value_users(
    min_value: float = Query(1000000.0, ge=0),
    agent_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get high-value users based on portfolio value"""
    return services.get_high_value_users(db, min_value=min_value, agent_id=agent_id, limit=limit)


@app.get("/api/users/age-range/list", response_model=List[schemas.UserResponse])
def get_users_by_age(
    min_age: int = Query(25, ge=18, le=100),
    max_age: int = Query(70, ge=18, le=100),
    agent_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get users within a specific age range (based on mock DOB)"""
    return services.get_users_by_age_range(db, min_age=min_age, max_age=max_age, agent_id=agent_id, limit=limit)


@app.get("/api/users/stats")
def get_user_statistics(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get user and portfolio statistics"""
    return services.get_user_statistics(db, agent_id=agent_id)


# ==================== Portfolio Endpoints ====================

@app.get("/api/portfolio/opportunities", response_model=List[schemas.PortfolioOpportunity])
def get_all_portfolio_opportunities(
    user_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all portfolio optimization opportunities (underperforming, low-rated, concentrated)"""
    return services.get_all_portfolio_opportunities(db, user_id=user_id, limit=limit)


@app.get("/api/portfolio/opportunities/underperforming", response_model=List[schemas.PortfolioOpportunity])
def get_underperforming_funds(
    user_id: Optional[str] = None,
    min_current_value: float = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get underperforming mutual funds with negative alpha or XIRR performance.
    These funds are underperforming their benchmarks and should be reviewed.
    """
    return services.get_underperforming_funds(db, user_id=user_id, min_current_value=min_current_value, limit=limit)


@app.get("/api/portfolio/opportunities/low-rated", response_model=List[schemas.PortfolioOpportunity])
def get_low_rated_funds(
    user_id: Optional[str] = None,
    max_rating: float = Query(3.0, ge=0, le=5.0),
    min_current_value: float = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get low-rated funds (rating below threshold).
    Consider switching these to higher-rated alternatives.
    """
    return services.get_low_rated_funds(db, user_id=user_id, max_rating=max_rating, min_current_value=min_current_value, limit=limit)


@app.get("/api/portfolio/opportunities/concentration", response_model=List[schemas.PortfolioOpportunity])
def get_concentration_opportunities(
    user_id: Optional[str] = None,
    min_concentration: float = Query(25.0, ge=0, le=100),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get portfolios with high concentration in single funds.
    These may need rebalancing for better diversification.
    """
    return services.get_portfolio_rebalancing_opportunities(db, user_id=user_id, min_concentration=min_concentration, limit=limit)


@app.get("/api/portfolio/stats")
def get_portfolio_statistics(
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get portfolio statistics including performance metrics"""
    return services.get_portfolio_statistics(db, user_id=user_id)


@app.get("/api/clients/{user_id}/portfolio", response_model=List[schemas.PortfolioHoldingResponse])
def get_client_portfolio(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get all portfolio holdings for a specific client"""
    return services.get_user_portfolio_holdings(db, user_id, limit=limit)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8111)
