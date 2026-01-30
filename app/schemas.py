from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class UserBase(BaseModel):
    uid: Optional[str] = None
    user_id: Optional[str] = None
    crn: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    agent_external_id: Optional[str] = None
    agent_name: Optional[str] = None
    agent_email: Optional[str] = None
    agent_phone_number: Optional[str] = None
    member_id: Optional[str] = None
    total_current_value: Optional[float] = None
    mf_current_value: Optional[float] = None
    fd_current_value: Optional[float] = None
    aif_current_value: Optional[float] = None
    deb_current_value: Optional[float] = None
    pms_current_value: Optional[float] = None
    preipo_current_value: Optional[float] = None
    total_invested_value: Optional[float] = None
    mf_invested_value: Optional[float] = None
    fd_invested_value: Optional[float] = None
    aif_invested_value: Optional[float] = None
    deb_invested_value: Optional[float] = None
    pms_invested_value: Optional[float] = None
    preipo_invested_value: Optional[float] = None
    trak_cob_opportunity_value: Optional[float] = None
    latest_as_on_date: Optional[str] = None
    first_active_at: Optional[str] = None
    first_active_mf: Optional[str] = None
    first_active_fd: Optional[str] = None
    first_active_insurance: Optional[str] = None
    first_active_mld: Optional[str] = None
    first_active_ncd: Optional[str] = None
    first_active_aif: Optional[str] = None
    first_active_pms: Optional[str] = None
    first_active_preipo: Optional[str] = None
    first_active_mf_sip: Optional[str] = None
    inserted_at: Optional[str] = None
    event_date: Optional[str] = None
    created_at: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_in_db: Optional[datetime] = None
    updated_in_db: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InsuranceRecordBase(BaseModel):
    uid: Optional[str] = None
    source_id: Optional[str] = None
    deleted: Optional[str] = None
    checksum: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None
    mf_current_value: Optional[float] = None
    wealth_band: Optional[str] = None
    mock_age: Optional[int] = None
    transaction_date: Optional[str] = None
    transaction_amount: Optional[float] = None
    transaction_type: Optional[str] = None
    transaction_category: Optional[str] = None
    instrument_type: Optional[str] = None
    product_name: Optional[str] = None
    transaction_status: Optional[str] = None
    order_status: Optional[str] = None
    event_date: Optional[str] = None
    created_at: Optional[str] = None
    wealthy_processed_at: Optional[str] = None
    order_date: Optional[str] = None
    order_id: Optional[str] = None
    transaction_id: Optional[str] = None
    transaction_units: Optional[str] = None
    order_category: Optional[str] = None
    order_type: Optional[str] = None
    insurance_order_id: Optional[str] = None
    insurance_type: Optional[str] = None
    sourcing_channel: Optional[str] = None
    user_product_id: Optional[str] = None
    insurer: Optional[str] = None
    premium_frequency: Optional[str] = None
    policy_issue_date: Optional[str] = None
    policy_number: Optional[str] = None
    application_number: Optional[str] = None
    wpc: Optional[str] = None
    premium: Optional[float] = None
    agent_id: Optional[str] = None
    agent_external_id: Optional[str] = None
    member_id: Optional[str] = None
    b_agent_external_id: Optional[str] = None
    total_premium: Optional[float] = None
    baseline_expected_premium: Optional[float] = None
    premium_gap: Optional[float] = None
    opportunity_score: Optional[int] = None


class InsuranceRecordResponse(InsuranceRecordBase):
    id: int
    created_in_db: Optional[datetime] = None
    updated_in_db: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InsuranceOpportunity(BaseModel):
    user_id: str
    name: str
    agent_id: str
    agent_external_id: str
    opportunity_type: str
    opportunity_description: str
    wealth_band: str
    age: Optional[int] = None
    mf_current_value: float
    total_premium: float
    baseline_expected_premium: float
    premium_gap: float
    opportunity_score: int
    missing_coverage_types: Optional[list] = None
    
    class Config:
        from_attributes = True


class SIPRecordBase(BaseModel):
    uid: Optional[str] = None
    sip_meta_id: Optional[str] = None
    user_id: Optional[str] = None
    goal_id: Optional[str] = None
    agent_id: Optional[str] = None
    agent_external_id: Optional[str] = None
    member_id: Optional[str] = None
    amount: Optional[float] = None
    sip_days: Optional[str] = None
    num_days: Optional[int] = None
    scheme_name: Optional[str] = None
    goal_name: Optional[str] = None
    created_at: Optional[str] = None
    sip_meta_date: Optional[str] = None
    sip_meta_month: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    event_date: Optional[str] = None
    inserted_at: Optional[str] = None
    increment_percentage: Optional[float] = None
    increment_amount: Optional[float] = None
    increment_period: Optional[str] = None
    paused_from: Optional[str] = None
    paused_till: Optional[str] = None
    paused_reason: Optional[str] = None
    is_active: Optional[str] = None
    sip_sales_status: Optional[str] = None
    current_sip_status: Optional[str] = None
    had_mandate_at_creation: Optional[str] = None
    has_current_mandate: Optional[str] = None
    mandate_tracking_status: Optional[str] = None
    mandate_confirmed_date: Optional[str] = None
    first_order_nav_allocated_at: Optional[str] = None
    first_success_order_date: Optional[str] = None
    latest_success_order_date: Optional[str] = None
    first_success_order_month: Optional[str] = None
    latest_success_order_month: Optional[str] = None
    success_amount: Optional[float] = None
    pending_amount: Optional[float] = None
    failed_amount: Optional[float] = None
    in_progress_amount: Optional[float] = None
    paused_amount: Optional[float] = None
    success_count: Optional[int] = None
    stepper_enabled: Optional[str] = None
    deleted: Optional[str] = None


class SIPRecordResponse(SIPRecordBase):
    id: int
    created_in_db: Optional[datetime] = None
    updated_in_db: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OpportunityClient(BaseModel):
    user_id: str
    agent_id: str
    agent_external_id: str
    opportunity_type: str
    opportunity_description: str
    current_sip_amount: float
    potential_increase: Optional[float] = None
    last_activity_date: Optional[str] = None
    days_since_activity: Optional[int] = None
    risk_score: Optional[float] = None
    total_invested: Optional[float] = None
    failed_amount: Optional[float] = None
    
    class Config:
        from_attributes = True


class OpportunityStats(BaseModel):
    total_opportunities: int
    total_potential_revenue: float
    breakdown_by_type: dict
    
    class Config:
        from_attributes = True


class PortfolioHoldingBase(BaseModel):
    user_id: Optional[str] = None
    pan_number: Optional[str] = None
    as_on_date: Optional[str] = None
    wpc: Optional[str] = None
    scheme_name: Optional[str] = None
    category: Optional[str] = None
    amc_name: Optional[str] = None
    nav: Optional[float] = None
    nav_as_on: Optional[str] = None
    current_value: Optional[float] = None
    portfolio_weight: Optional[float] = None
    benchmark_name: Optional[str] = None
    live_xirr: Optional[float] = None
    benchmark_xirr: Optional[float] = None
    xirr_performance: Optional[float] = None
    one_year_returns: Optional[float] = None
    three_year_returns_cagr: Optional[float] = None
    benchmark_three_year_returns_cagr: Optional[float] = None
    three_year_returns_alpha: Optional[float] = None
    five_year_returns_cagr: Optional[float] = None
    benchmark_five_year_returns_cagr: Optional[float] = None
    five_year_returns_alpha: Optional[float] = None
    rolling_4q_beat_count: Optional[int] = None
    rolling_4q_total_count: Optional[int] = None
    rolling_4q_beat_percentage: Optional[float] = None
    rolling_12q_beat_count: Optional[int] = None
    rolling_12q_total_count: Optional[int] = None
    rolling_12q_beat_percentage: Optional[float] = None
    realized_stcg: Optional[float] = None
    realized_ltcg: Optional[float] = None
    unrealized_stu: Optional[float] = None
    unrealized_ltu: Optional[float] = None
    cost_of_unrealized_stu: Optional[float] = None
    cost_of_unrealized_ltu: Optional[float] = None
    unrealized_stcg: Optional[float] = None
    unrealized_ltcg: Optional[float] = None
    comment: Optional[str] = None
    w_rating: Optional[str] = None


class PortfolioHoldingResponse(PortfolioHoldingBase):
    id: int
    created_in_db: Optional[datetime] = None
    updated_in_db: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PortfolioOpportunity(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    scheme_name: str
    wpc: str
    category: str
    amc_name: str
    current_value: float
    portfolio_weight: float
    opportunity_type: str
    opportunity_description: str
    w_rating: Optional[str] = None
    xirr_performance: Optional[float] = None
    three_year_returns_alpha: Optional[float] = None
    five_year_returns_alpha: Optional[float] = None
    rolling_12q_beat_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True
