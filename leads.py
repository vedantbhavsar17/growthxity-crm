from sqlalchemy import or_
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import Lead, db
from services import (
    validate_email,
    validate_optional_text,
    validate_phone,
    validate_required_text,
    validate_service,
    validate_status,
)


leads = Blueprint("leads", __name__)


def get_user_lead_or_404(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if lead.user_id != current_user.id:
        abort(403)
    return lead


@leads.route("/api/leads", methods=["POST"])
def create_lead_api():
    data = request.get_json(silent=True) or request.form

    print("RAW DATA:", data)

    form_data = data.get("form_submit_data", {})

    name = ""
    email = ""
    phone = ""
    location = ""

    for field in form_data.values():
        key = field.get("key", "").lower()
        label = field.get("label", "").lower()
        value = field.get("value")

        if "name" in key or "name" in label:
            name = value
        elif "email" in key or "email" in label:
            email = value
        elif "phone" in key or "phone" in label:
            phone = value
        elif "location" in key or "location" in label:
            location = value

    name = name or "Unknown Lead"
    email = email or "noemail@example.com"

    print("MAPPED:", name, email, phone, location)

    new_lead = Lead(
        name=name,
        email=email,
        phone=phone,
        source="Website",
        location=location,
        service="Website Lead",
        status="New",
        user_id=1,
    )

    db.session.add(new_lead)
    db.session.commit()

    return jsonify({"status": "success"})


@leads.route("/dashboard")
@login_required
def dashboard():
    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    leads_query = Lead.query.filter_by(user_id=current_user.id)

    if search_query:
        like_pattern = f"%{search_query}%"
        leads_query = leads_query.filter(
            or_(
                Lead.name.ilike(like_pattern),
                Lead.email.ilike(like_pattern),
                Lead.phone.ilike(like_pattern),
                Lead.service.ilike(like_pattern),
                Lead.location.ilike(like_pattern),
            )
        )

    if status_filter in Lead.STATUS_OPTIONS:
        leads_query = leads_query.filter_by(status=status_filter)
    else:
        status_filter = ""

    user_leads = leads_query.order_by(Lead.id.desc()).all()
    status_counts = {
        status: sum(1 for lead in user_leads if lead.status == status)
        for status in Lead.STATUS_OPTIONS
    }
    source_counts = {}
    for lead in user_leads:
        source = lead.source or "Manual"
        source_counts[source] = source_counts.get(source, 0) + 1
    total_leads = len(user_leads)
    won_count = status_counts["Won"]
    analytics = {
        "total": total_leads,
        "new": sum(1 for lead in user_leads if lead.status == "New"),
        "contacted": sum(1 for lead in user_leads if lead.status == "Contacted"),
        "closed": sum(1 for lead in user_leads if lead.status in ("Won", "Lost", "Closed")),
        "won": won_count,
        "conversion_rate": round((won_count / total_leads) * 100, 1) if total_leads else 0,
        "status_counts": status_counts,
        "show_charts": total_leads >= 5,
        "source_counts": source_counts,
        "show_source_chart": total_leads > 3,
    }

    return render_template(
        "dashboard.html",
        leads=user_leads,
        status_choices=Lead.STATUS_OPTIONS,
        service_choices=Lead.SERVICE_OPTIONS,
        selected_status=status_filter,
        search_query=search_query,
        analytics=analytics,
    )


@leads.route("/add-lead", methods=["GET", "POST"])
@login_required
def add_lead():
    error = None
    form_data = {"name": "", "email": "", "phone": "", "service": "", "location": "", "notes": ""}

    if request.method == "POST":
        form_data = {
            "name": request.form.get("name", ""),
            "email": request.form.get("email", ""),
            "phone": request.form.get("phone", ""),
            "service": request.form.get("service", ""),
            "location": request.form.get("location", ""),
            "notes": request.form.get("notes", ""),
        }
        name, error = validate_required_text(request.form.get("name"), "Name")
        if not error:
            email, error = validate_email(request.form.get("email"))
        if not error:
            phone, error = validate_phone(request.form.get("phone"))
        if not error:
            service, error = validate_service(request.form.get("service"))
        if not error:
            location, error = validate_required_text(request.form.get("location"), "Location")
        if not error:
            notes, _ = validate_optional_text(request.form.get("notes"))

        if not error:
            lead = Lead(
                name=name,
                email=email,
                phone=phone,
                source="Manual",
                service=service,
                location=location,
                notes=notes or None,
                user_id=current_user.id,
            )
            db.session.add(lead)
            db.session.commit()
            flash("Lead added successfully.", "success")
            return redirect(url_for("leads.dashboard"))

    return render_template(
        "add_lead.html",
        error=error,
        form_data=form_data,
        service_choices=Lead.SERVICE_OPTIONS,
    )


@leads.route("/edit-lead/<int:lead_id>", methods=["GET", "POST"])
@login_required
def edit_lead(lead_id):
    lead = get_user_lead_or_404(lead_id)
    error = None

    if request.method == "POST":
        name, error = validate_required_text(request.form.get("name"), "Name")
        if not error:
            email, error = validate_email(request.form.get("email"))
        if not error:
            phone, error = validate_phone(request.form.get("phone"))
        if not error:
            service, error = validate_service(request.form.get("service"))
        if not error:
            location, error = validate_required_text(request.form.get("location"), "Location")
        if not error:
            status, error = validate_status(request.form.get("status"))
        if not error:
            notes, _ = validate_optional_text(request.form.get("notes"))

        if not error:
            lead.name = name
            lead.email = email
            lead.phone = phone
            lead.service = service
            lead.location = location
            lead.notes = notes or None
            lead.status = status
            db.session.commit()
            flash("Lead updated successfully.", "success")
            return redirect(url_for("leads.dashboard"))

    return render_template(
        "edit_lead.html",
        lead=lead,
        status_choices=Lead.STATUS_OPTIONS,
        service_choices=Lead.SERVICE_OPTIONS,
        error=error,
    )


@leads.route("/update-lead-status/<int:lead_id>", methods=["POST"])
@login_required
def update_lead_status(lead_id):
    lead = get_user_lead_or_404(lead_id)
    status, error = validate_status(request.form.get("status"))

    if not error:
        lead.status = status
        db.session.commit()
        flash("Lead status updated successfully.", "success")

    return redirect(url_for("leads.dashboard"))


@leads.route("/delete-lead/<int:lead_id>", methods=["POST"])
@login_required
def delete_lead(lead_id):
    lead = get_user_lead_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    flash("Lead deleted successfully.", "success")
    return redirect(url_for("leads.dashboard"))


@leads.route("/api/leads/<int:lead_id>", methods=["POST"])
@login_required
def update_lead_api(lead_id):
    lead = get_user_lead_or_404(lead_id)
    data = request.get_json(silent=True) or {}

    name, error = validate_required_text(data.get("name"), "Name")
    if not error:
        email, error = validate_email(data.get("email"))
    if not error:
        phone, error = validate_phone(data.get("phone"))
    if not error:
        service, error = validate_service(data.get("service"))
    if not error:
        location, error = validate_required_text(data.get("location"), "Location")
    if not error:
        status, error = validate_status(data.get("status"))
    if not error:
        notes, _ = validate_optional_text(data.get("notes"))

    if error:
        return jsonify({"status": "error", "message": error}), 400

    lead.name = name
    lead.email = email
    lead.phone = phone
    lead.service = service
    lead.location = location
    lead.status = status
    lead.notes = notes or None
    db.session.commit()

    return jsonify(
        {
            "status": "success",
            "message": "Updated successfully",
            "lead": {
                "id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "phone": lead.phone,
                "service": lead.service,
                "location": lead.location,
                "status": lead.status,
                "notes": lead.notes or "",
            },
        }
    )
