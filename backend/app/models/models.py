import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class UPIShieldEvent(Base):
    """
    Tracks screenshot OCR detections, UTR verifications, and QR code scans.
    """
    __tablename__ = "upi_shield_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    event_type = Column(String(50), nullable=False) # 'screenshot', 'utr_verify', 'qr_scan'
    
    utr_number = Column(String(100), index=True, nullable=True)
    sender_upi_id = Column(String(255), index=True, nullable=True)
    receiver_upi_id = Column(String(255), index=True, nullable=True)
    amount = Column(Float, nullable=True)
    transaction_date = Column(String(100), nullable=True)
    
    is_valid_utr = Column(Integer, default=0) # 0=False, 1=True
    font_anomalies_detected = Column(Integer, default=0) # 0=False, 1=True
    suspicious_handle_flagged = Column(Integer, default=0) # 0=False, 1=True
    
    risk_score = Column(Integer, default=0) # 0 to 100
    risk_level = Column(String(50), default="CLEAN")
    ai_fraud_explanation = Column(Text, nullable=True)
    raw_ocr_text = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), nullable=True)
    case = relationship("Case", back_populates="upi_events")

class Case(Base):
    """
    Manages security analyst investigations, saved evidence, and audit logs.
    """
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="open") # open, under_investigation, resolved, closed
    severity = Column(String(50), default="medium") # low, medium, high, critical
    assigned_analyst = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    saved_evidence = Column(JSON, default=list) # List of dicts representing linked threats
    analyst_notes = Column(Text, default="")
    ai_summary_brief = Column(Text, nullable=True)
    
    upi_events = relationship("UPIShieldEvent", back_populates="case")

class ThreatFeedAlert(Base):
    """
    Real-time Indicators of Compromise (IOC) feed stored for analysis and pushed via websockets.
    """
    __tablename__ = "threat_feed_alerts"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    indicator_type = Column(String(100), nullable=False) # 'domain', 'ip', 'upi_handle', 'hash'
    value = Column(String(500), index=True, nullable=False)
    source = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False) # low, medium, high, critical
    description = Column(Text, nullable=True)
    mitigation_strategy = Column(Text, nullable=True)
