from sqlalchemy import CheckConstraint
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    leads = db.relationship(
        "Lead",
        backref="user",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class Lead(db.Model):
    __tablename__ = "leads"
    STATUS_OPTIONS = (
        "New",
        "Contacted",
        "Qualified",
        "Proposal Sent",
        "Negotiation",
        "Won",
        "Lost",
    )
    VALID_STATUS_OPTIONS = STATUS_OPTIONS + ("Closed",)
    SERVICE_OPTIONS = (
        "Website Lead",
        "Web Development",
        "App Development",
        "SEO",
        "Performance Marketing",
        "CRM Setup",
        "Branding",
    )
    __table_args__ = (
        CheckConstraint(
            "status IN ('New', 'Contacted', 'Qualified', 'Proposal Sent', 'Negotiation', 'Won', 'Lost', 'Closed')",
            name="ck_leads_status_valid",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    source = db.Column(db.String(100), nullable=True)
    service = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="New", index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    client_work_items = db.relationship(
        "ClientWork",
        backref="lead",
        lazy="selectin",
        cascade="all, delete-orphan",
    )


class ClientWork(db.Model):
    __tablename__ = "client_work"
    PROGRESS_OPTIONS = ("Not Started", "In Progress", "Completed", "On Hold")

    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("leads.id"), nullable=False, index=True)
    service_type = db.Column(db.String(100), nullable=False)
    progress_status = db.Column(db.String(50), nullable=False, default="Not Started")
    result_notes = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
