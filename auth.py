from sqlalchemy.exc import IntegrityError
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db
from services import (
    normalize_email,
    validate_email,
    validate_login_password,
    validate_password,
    validate_required_text,
)

auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():
    error = None
    form_data = {"name": "", "email": ""}

    if request.method == "POST":
        form_data = {
            "name": request.form.get("name", ""),
            "email": request.form.get("email", ""),
        }
        name, error = validate_required_text(request.form.get("name"), "Name")
        if not error:
            email, error = validate_email(request.form.get("email"))
        if not error:
            password, error = validate_password(request.form.get("password"))
        if not error and User.query.filter_by(email=email).first():
            error = "An account with this email already exists."

        if not error:
            user = User(
                name=name,
                email=email,
                password=generate_password_hash(password),
            )
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                error = "An account with this email already exists."
            else:
                login_user(user)
                flash("Registration successful. Welcome to Growthxity CRM.", "success")
                return redirect(url_for("leads.dashboard"))

    return render_template("register.html", error=error, form_data=form_data)


@auth.route("/login", methods=["GET", "POST"])
def login():
    error = None
    form_data = {"email": ""}

    if request.method == "POST":
        form_data["email"] = request.form.get("email", "")
        email, error = validate_email(request.form.get("email"))
        if not error:
            password, error = validate_login_password(request.form.get("password"))

        if not error:
            user = User.query.filter_by(email=normalize_email(email)).first()

            if user and check_password_hash(user.password, password):
                login_user(user)
                flash("Login successful. Welcome back.", "success")
                return redirect(url_for("leads.dashboard"))

            error = "Invalid email or password."

    return render_template("login.html", error=error, form_data=form_data)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
