from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from models import ClientWork, Lead, db
from services import (
    validate_date,
    validate_date_range,
    validate_optional_text,
    validate_progress_status,
    validate_service,
)


work = Blueprint("work", __name__)


def get_user_lead_or_404(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    if lead.user_id != current_user.id:
        abort(403)
    return lead


def get_won_lead_or_400(lead_id):
    lead = get_user_lead_or_404(lead_id)
    if lead.status != "Won":
        abort(400)
    return lead


@work.route("/leads/<int:lead_id>/work", methods=["GET"])
@login_required
def view_work(lead_id):
    lead = get_user_lead_or_404(lead_id)
    return render_template(
        "view_work.html",
        lead=lead,
        work_items=lead.client_work_items,
    )


@work.route("/leads/<int:lead_id>/work/create", methods=["GET", "POST"])
@login_required
def create_work(lead_id):
    lead = get_won_lead_or_400(lead_id)
    error = None
    form_data = {
        "service_type": lead.service or "",
        "progress_status": ClientWork.PROGRESS_OPTIONS[0],
        "result_notes": "",
        "start_date": "",
        "end_date": "",
    }

    if request.method == "POST":
        form_data = {
            "service_type": request.form.get("service_type", ""),
            "progress_status": request.form.get("progress_status", ""),
            "result_notes": request.form.get("result_notes", ""),
            "start_date": request.form.get("start_date", ""),
            "end_date": request.form.get("end_date", ""),
        }
        service_type, error = validate_service(request.form.get("service_type"))
        if not error:
            progress_status, error = validate_progress_status(request.form.get("progress_status"))
        if not error:
            result_notes, _ = validate_optional_text(request.form.get("result_notes"))
            start_date, error = validate_date(request.form.get("start_date"), "Start date")
        if not error:
            end_date, error = validate_date(request.form.get("end_date"), "End date", required=False)
        if not error:
            error = validate_date_range(start_date, end_date)

        if not error:
            work_item = ClientWork(
                lead_id=lead.id,
                service_type=service_type,
                progress_status=progress_status,
                result_notes=result_notes or None,
                start_date=start_date,
                end_date=end_date,
            )
            db.session.add(work_item)
            db.session.commit()
            flash("Client work created successfully.", "success")
            return redirect(url_for("work.view_work", lead_id=lead.id))

    return render_template(
        "create_work.html",
        lead=lead,
        error=error,
        form_data=form_data,
        service_choices=Lead.SERVICE_OPTIONS,
        progress_choices=ClientWork.PROGRESS_OPTIONS,
    )
