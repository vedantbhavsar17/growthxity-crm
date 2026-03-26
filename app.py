from flask import Flask, redirect, render_template, url_for
from flask_login import LoginManager, current_user
from sqlalchemy import inspect, text

from auth import auth
from leads import leads
from models import User, db
from work import work

login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)
    app.register_blueprint(auth)
    app.register_blueprint(leads)
    app.register_blueprint(work)

    @app.route("/")
    def home():
        if current_user.is_authenticated:
            return redirect(url_for("leads.dashboard"))
        return render_template("index.html")

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(400)
    def bad_request(_error):
        return render_template("400.html"), 400

    def ensure_lead_columns():
        inspector = inspect(db.engine)
        if "leads" not in inspector.get_table_names():
            return

        create_statement = db.session.execute(
            text("SELECT sql FROM sqlite_master WHERE type='table' AND name='leads'")
        ).scalar() or ""

        if "Proposal Sent" not in create_statement:
            db.session.execute(text("ALTER TABLE leads RENAME TO leads_legacy"))
            db.session.execute(
                text(
                    """
                    CREATE TABLE leads (
                        id INTEGER NOT NULL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(255) NOT NULL,
                        phone VARCHAR(20) NOT NULL,
                        source VARCHAR(100),
                        service VARCHAR(100),
                        location VARCHAR(120),
                        notes TEXT,
                        status VARCHAR(50) NOT NULL,
                        user_id INTEGER NOT NULL,
                        CONSTRAINT ck_leads_status_valid
                            CHECK (status IN ('New', 'Contacted', 'Qualified', 'Proposal Sent', 'Negotiation', 'Won', 'Lost', 'Closed')),
                        FOREIGN KEY(user_id) REFERENCES users (id)
                    )
                    """
                )
            )
            db.session.execute(
                text(
                    """
                    INSERT INTO leads (id, name, email, phone, source, service, location, notes, status, user_id)
                    SELECT id, name, email, phone, NULL, service, location, notes, status, user_id
                    FROM leads_legacy
                    """
                )
            )
            db.session.execute(text("DROP TABLE leads_legacy"))
            db.session.execute(text("CREATE INDEX ix_leads_status ON leads (status)"))
            db.session.execute(text("CREATE INDEX ix_leads_user_id ON leads (user_id)"))
            db.session.commit()
            inspector = inspect(db.engine)

        existing_columns = {column["name"] for column in inspector.get_columns("leads")}
        column_updates = {
            "source": "ALTER TABLE leads ADD COLUMN source VARCHAR(100)",
            "service": "ALTER TABLE leads ADD COLUMN service VARCHAR(100)",
            "location": "ALTER TABLE leads ADD COLUMN location VARCHAR(120)",
            "notes": "ALTER TABLE leads ADD COLUMN notes TEXT",
        }

        for column_name, statement in column_updates.items():
            if column_name not in existing_columns:
                db.session.execute(text(statement))

        db.session.commit()

    with app.app_context():
        db.create_all()
        ensure_lead_columns()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
