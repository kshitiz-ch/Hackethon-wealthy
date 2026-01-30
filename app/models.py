from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Date
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identifiers
    uid = Column(String, index=True, unique=True)
    user_id = Column(String, index=True, unique=True)
    crn = Column(String, index=True)
    
    # Personal Information
    name = Column(String, index=True)
    email = Column(String, index=True)
    phone_number = Column(String)
    date_of_birth = Column(Date, index=True)  # Mock data, to be updated later
    
    # Agent Information
    agent_external_id = Column(String, index=True)
    agent_name = Column(String)
    agent_email = Column(String)
    agent_phone_number = Column(String)
    member_id = Column(String, index=True)
    
    # Portfolio Values - Current
    total_current_value = Column(Float, index=True)
    mf_current_value = Column(Float)
    fd_current_value = Column(Float)
    aif_current_value = Column(Float)
    deb_current_value = Column(Float)
    pms_current_value = Column(Float)
    preipo_current_value = Column(Float)
    
    # Portfolio Values - Invested
    total_invested_value = Column(Float, index=True)
    mf_invested_value = Column(Float)
    fd_invested_value = Column(Float)
    aif_invested_value = Column(Float)
    deb_invested_value = Column(Float)
    pms_invested_value = Column(Float)
    preipo_invested_value = Column(Float)
    
    # Opportunity Tracking
    trak_cob_opportunity_value = Column(Float)
    
    # Activity Dates
    latest_as_on_date = Column(String)
    first_active_at = Column(String, index=True)
    first_active_mf = Column(String)
    first_active_fd = Column(String)
    first_active_insurance = Column(String)
    first_active_mld = Column(String)
    first_active_ncd = Column(String)
    first_active_aif = Column(String)
    first_active_pms = Column(String)
    first_active_preipo = Column(String)
    first_active_mf_sip = Column(String)
    
    # Record Metadata
    inserted_at = Column(String)
    event_date = Column(String)
    created_at = Column(String, index=True)
    
    # Database Metadata
    created_in_db = Column(DateTime(timezone=True), server_default=func.now())
    updated_in_db = Column(DateTime(timezone=True), onupdate=func.now())


class InsuranceRecord(Base):
    __tablename__ = "insurance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identifiers
    uid = Column(String, index=True)
    source_id = Column(String, index=True, unique=True)
    deleted = Column(String)
    checksum = Column(String)
    
    # Client Information
    user_id = Column(String, index=True)  # itf.user_id
    name = Column(String, index=True)
    mf_current_value = Column(Float)
    wealth_band = Column(String, index=True)
    mock_age = Column(Integer)
    
    # Transaction Details
    transaction_date = Column(String, index=True)
    transaction_amount = Column(Float)
    transaction_type = Column(String)
    transaction_category = Column(String)
    instrument_type = Column(String)
    product_name = Column(String)
    transaction_status = Column(String, index=True)
    order_status = Column(String, index=True)
    
    # Dates
    event_date = Column(String)
    created_at = Column(String)
    wealthy_processed_at = Column(String)
    order_date = Column(String)
    
    # Order Information
    order_id = Column(String)
    transaction_id = Column(String)
    transaction_units = Column(String)
    order_category = Column(String)
    order_type = Column(String)
    
    # Insurance Specific
    insurance_order_id = Column(String)
    insurance_type = Column(String, index=True)  # ULIP, Traditional, Health, Term, etc.
    sourcing_channel = Column(String)
    user_product_id = Column(String)
    insurer = Column(String, index=True)
    premium_frequency = Column(String)
    policy_issue_date = Column(String)
    policy_number = Column(String)
    application_number = Column(String)
    wpc = Column(String)
    premium = Column(Float)
    
    # Agent Information
    agent_id = Column(String, index=True)
    agent_external_id = Column(String, index=True)  # itf.agent_external_id
    member_id = Column(String, index=True)
    b_agent_external_id = Column(String)  # b.agent_external_id
    
    # Opportunity Metrics
    total_premium = Column(Float)
    baseline_expected_premium = Column(Float)
    premium_gap = Column(Float, index=True)
    opportunity_score = Column(Integer, index=True)
    
    # Metadata
    created_in_db = Column(DateTime(timezone=True), server_default=func.now())
    updated_in_db = Column(DateTime(timezone=True), onupdate=func.now())


class SIPRecord(Base):
    __tablename__ = "sip_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identifiers
    uid = Column(String, index=True)
    sip_meta_id = Column(String, index=True, unique=True)
    user_id = Column(String, index=True)
    goal_id = Column(String)
    
    # Agent/Advisor Information
    agent_id = Column(String, index=True)
    agent_external_id = Column(String, index=True)
    member_id = Column(String, index=True)
    
    # SIP Details
    amount = Column(Float)
    sip_days = Column(String)
    num_days = Column(Integer)
    scheme_name = Column(Text)
    goal_name = Column(String)
    
    # Dates
    created_at = Column(String)
    sip_meta_date = Column(String)
    sip_meta_month = Column(String)
    start_date = Column(String, index=True)
    end_date = Column(String)
    event_date = Column(String)
    inserted_at = Column(String)
    
    # Increment Configuration
    increment_percentage = Column(Float)
    increment_amount = Column(Float)
    increment_period = Column(String, index=True)
    
    # Pause Information
    paused_from = Column(String)
    paused_till = Column(String)
    paused_reason = Column(String)
    
    # Status Fields
    is_active = Column(String)
    sip_sales_status = Column(String, index=True)
    current_sip_status = Column(String, index=True)
    
    # Mandate Information
    had_mandate_at_creation = Column(String)
    has_current_mandate = Column(String)
    mandate_tracking_status = Column(String)
    mandate_confirmed_date = Column(String)
    
    # Order Dates
    first_order_nav_allocated_at = Column(String)
    first_success_order_date = Column(String, index=True)
    latest_success_order_date = Column(String, index=True)
    first_success_order_month = Column(String)
    latest_success_order_month = Column(String)
    
    # Financial Tracking
    success_amount = Column(Float)
    pending_amount = Column(Float)
    failed_amount = Column(Float)
    in_progress_amount = Column(Float)
    paused_amount = Column(Float)
    success_count = Column(Integer)
    
    # Flags
    stepper_enabled = Column(String)
    deleted = Column(String)
    
    # Metadata
    created_in_db = Column(DateTime(timezone=True), server_default=func.now())
    updated_in_db = Column(DateTime(timezone=True), onupdate=func.now())


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User & Basic Info
    user_id = Column(String, index=True)  # Foreign key to users table
    pan_number = Column(String, index=True)
    as_on_date = Column(String, index=True)
    
    # Scheme Identifiers
    wpc = Column(String, index=True)  # Wealthy Product Code
    scheme_name = Column(Text, index=True)
    category = Column(String, index=True)
    amc_name = Column(String, index=True)
    
    # NAV Details
    nav = Column(Float)
    nav_as_on = Column(String)
    
    # Portfolio Position
    current_value = Column(Float, index=True)
    portfolio_weight = Column(Float, index=True)
    
    # Performance Metrics
    benchmark_name = Column(String)
    live_xirr = Column(Float)
    benchmark_xirr = Column(Float)
    xirr_performance = Column(Float, index=True)  # Difference from benchmark
    
    # Returns
    one_year_returns = Column(Float)
    three_year_returns_cagr = Column(Float)
    benchmark_three_year_returns_cagr = Column(Float)
    three_year_returns_alpha = Column(Float, index=True)
    five_year_returns_cagr = Column(Float)
    benchmark_five_year_returns_cagr = Column(Float)
    five_year_returns_alpha = Column(Float, index=True)
    
    # Rolling Returns Comparison (4 quarters)
    rolling_4q_beat_count = Column(Integer)
    rolling_4q_total_count = Column(Integer)
    rolling_4q_beat_percentage = Column(Float)
    
    # Rolling Returns Comparison (12 quarters)
    rolling_12q_beat_count = Column(Integer)
    rolling_12q_total_count = Column(Integer)
    rolling_12q_beat_percentage = Column(Float, index=True)
    
    # Tax Information
    realized_stcg = Column(Float)
    realized_ltcg = Column(Float)
    unrealized_stu = Column(Float)
    unrealized_ltu = Column(Float)
    cost_of_unrealized_stu = Column(Float)
    cost_of_unrealized_ltu = Column(Float)
    unrealized_stcg = Column(Float)
    unrealized_ltcg = Column(Float, index=True)
    
    # Opportunity Analysis
    comment = Column(Text, index=True)  # Contains opportunity insights
    w_rating = Column(String, index=True)  # Wealthy rating
    
    # Metadata
    created_in_db = Column(DateTime(timezone=True), server_default=func.now())
    updated_in_db = Column(DateTime(timezone=True), onupdate=func.now())
