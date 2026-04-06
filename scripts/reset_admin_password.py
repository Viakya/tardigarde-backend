"""Reset the admin user credentials."""

from app import create_app
from app.extensions import db
from app.models import User


def main() -> None:
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.com").first()
        if not admin:
            admin = User(email="admin@test.com", full_name="Admin User", role="admin", is_active=True)
            admin.set_password("Admin@123")
            db.session.add(admin)
        else:
            admin.full_name = "Admin User"
            admin.role = "admin"
            admin.is_active = True
            admin.set_password("Admin@123")
        db.session.commit()
        print("Admin credentials reset for admin@test.com (password: Admin@123)")


if __name__ == "__main__":
    main()
