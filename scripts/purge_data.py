"""Purge all application data except select users.

Keeps:
- manager@test.com
- any user with role == 'director'
"""

from app import create_app
from app.extensions import db
from app.models import (
    Attendance,
    Batch,
    FeePayment,
    Salary,
    Student,
    Teacher,
    Test,
    TestResult,
    User,
)
from app.models.associations import batch_teachers, parent_students

KEEP_EMAILS = {"manager@test.com"}
KEEP_ROLES = {"director"}


def purge_data() -> dict:
    """Delete all rows except selected users and return counts."""
    counts = {}

    # Delete dependent tables first
    counts["test_results"] = db.session.execute(TestResult.__table__.delete()).rowcount
    counts["tests"] = db.session.execute(Test.__table__.delete()).rowcount
    counts["attendance"] = db.session.execute(Attendance.__table__.delete()).rowcount
    counts["fee_payments"] = db.session.execute(FeePayment.__table__.delete()).rowcount
    counts["salaries"] = db.session.execute(Salary.__table__.delete()).rowcount

    # Association tables
    counts["batch_teachers"] = db.session.execute(batch_teachers.delete()).rowcount
    counts["parent_students"] = db.session.execute(parent_students.delete()).rowcount

    # Core entities
    counts["students"] = db.session.execute(Student.__table__.delete()).rowcount
    counts["teachers"] = db.session.execute(Teacher.__table__.delete()).rowcount
    counts["batches"] = db.session.execute(Batch.__table__.delete()).rowcount

    # Users: keep manager@test.com and any directors
    keep_filter = (User.email.in_(KEEP_EMAILS)) | (User.role.in_(KEEP_ROLES))
    counts["users_deleted"] = (
        db.session.query(User).filter(~keep_filter).delete(synchronize_session=False)
    )

    db.session.commit()
    return counts


def main() -> None:
    app = create_app()
    with app.app_context():
        counts = purge_data()
        print("Purge complete. Rows deleted:")
        for key, value in counts.items():
            print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
