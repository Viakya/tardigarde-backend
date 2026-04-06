import click
from flask.cli import with_appcontext
from datetime import date

from app.extensions import db
from app.models import Batch, Student, Teacher, User


def _seed_full_sample_dataset() -> dict:
    """Seed a small, realistic dataset across all core tables.

    Mirrors scripts/seed_sample_data.py but as a Flask CLI-friendly helper.
    Returns stats about created rows.
    """

    from datetime import timedelta

    from app.models import Attendance, FeePayment, Salary, Test, TestResult

    stats = {
        "users": 0,
        "batches": 0,
        "students": 0,
        "teachers": 0,
        "fees": 0,
        "salaries": 0,
        "attendance": 0,
        "tests": 0,
        "results": 0,
    }

    def get_or_create_user(email: str, full_name: str, role: str, password: str = "Test@123") -> User:
        user = User.query.filter_by(email=email).first()
        if user is None:
            user = User(email=email, full_name=full_name, role=role, is_active=True)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()
            stats["users"] += 1
        return user

    def get_or_create_batch(name: str, year: int) -> Batch:
        batch = Batch.query.filter_by(batch_name=name, year=year).first()
        if batch is None:
            batch = Batch(batch_name=name, year=year, is_active=True)
            db.session.add(batch)
            db.session.flush()
            stats["batches"] += 1
        return batch

    def get_or_create_teacher(user: User, specialization: str) -> Teacher:
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if teacher is None:
            teacher = Teacher(user_id=user.id, specialization=specialization, is_active=True)
            db.session.add(teacher)
            db.session.flush()
            stats["teachers"] += 1
        return teacher

    def get_or_create_student(user: User, batch: Batch, phone: str) -> Student:
        student = Student.query.filter_by(user_id=user.id).first()
        if student is None:
            student = Student(user_id=user.id, batch_id=batch.id, phone_number=phone, is_active=True)
            db.session.add(student)
            db.session.flush()
            stats["students"] += 1
        else:
            student.batch_id = batch.id
        return student

    manager = get_or_create_user("manager@test.com", "Manager User", "manager", "Manager@123")

    admin = User.query.filter_by(email="admin@test.com").first()
    if admin is None:
        admin = get_or_create_user("admin@test.com", "Admin User", "admin", "Admin@123")
    else:
        admin.full_name = "Admin User"
        admin.role = "admin"
        admin.is_active = True
        admin.set_password("Admin@123")

    director = User.query.filter_by(role="director").first()
    if director is None:
        director = get_or_create_user("director@test.com", "Director User", "director", "Director@123")

    current_year = date.today().year
    batches = [
        get_or_create_batch("Foundation", current_year),
        get_or_create_batch("Momentum", current_year),
        get_or_create_batch("Sprint", current_year),
    ]

    teacher_users = [
        get_or_create_user("coach1@test.com", "Coach One", "coach"),
        get_or_create_user("coach2@test.com", "Coach Two", "coach"),
        get_or_create_user("coach3@test.com", "Coach Three", "coach"),
    ]

    teachers = [
        get_or_create_teacher(teacher_users[0], "Mathematics"),
        get_or_create_teacher(teacher_users[1], "Science"),
        get_or_create_teacher(teacher_users[2], "Reasoning"),
    ]

    batches[0].teachers = [teachers[0], teachers[1]]
    batches[1].teachers = [teachers[1], teachers[2]]
    batches[2].teachers = [teachers[0], teachers[2]]

    parent1 = get_or_create_user("parent1@test.com", "Parent One", "parent")
    parent2 = get_or_create_user("parent2@test.com", "Parent Two", "parent")

    student_users = [
        get_or_create_user("student1@test.com", "Student One", "student"),
        get_or_create_user("student2@test.com", "Student Two", "student"),
        get_or_create_user("student3@test.com", "Student Three", "student"),
        get_or_create_user("student4@test.com", "Student Four", "student"),
        get_or_create_user("student5@test.com", "Student Five", "student"),
    ]

    students = [
        get_or_create_student(student_users[0], batches[0], "9000000001"),
        get_or_create_student(student_users[1], batches[0], "9000000002"),
        get_or_create_student(student_users[2], batches[1], "9000000003"),
        get_or_create_student(student_users[3], batches[1], "9000000004"),
        get_or_create_student(student_users[4], batches[2], "9000000005"),
    ]

    for student in students[:3]:
        if parent1 not in student.parents:
            student.parents.append(parent1)
    for student in students[2:]:
        if parent2 not in student.parents:
            student.parents.append(parent2)

    today = date.today()

    for student in students:
        db.session.add(
            FeePayment(
                student_id=student.id,
                amount=5000,
                payment_date=today - timedelta(days=3),
                payment_method="cash",
                received_by=manager.id,
                remarks="Seed payment",
            )
        )
        stats["fees"] += 1

    for teacher in teachers:
        db.session.add(
            Salary(
                teacher_id=teacher.id,
                amount=12000,
                payment_date=today - timedelta(days=5),
                payment_method="bank",
                paid_by=manager.id,
                remarks="Seed salary",
            )
        )
        stats["salaries"] += 1

    for student in students:
        for offset in range(2):
            attendance_date = today - timedelta(days=offset)
            existing = Attendance.query.filter_by(
                student_id=student.id, attendance_date=attendance_date
            ).first()
            if existing is None:
                db.session.add(
                    Attendance(
                        student_id=student.id,
                        batch_id=student.batch_id,
                        attendance_date=attendance_date,
                        status="present",
                        marked_by=manager.id,
                    )
                )
                stats["attendance"] += 1

    for batch in batches:
        test = Test.query.filter_by(batch_id=batch.id, title="Weekly Quiz").first()
        if test is None:
            test = Test(
                batch_id=batch.id,
                title="Weekly Quiz",
                subject="General",
                max_marks=100,
                test_date=today - timedelta(days=1),
                created_by=director.id,
                is_active=True,
            )
            db.session.add(test)
            db.session.flush()
            stats["tests"] += 1

        batch_students = [s for s in students if s.batch_id == batch.id]
        for student in batch_students:
            existing_result = TestResult.query.filter_by(
                test_id=test.id, student_id=student.id
            ).first()
            if existing_result is None:
                db.session.add(
                    TestResult(
                        test_id=test.id,
                        student_id=student.id,
                        marks_obtained=78,
                        remarks="Seed result",
                        is_active=True,
                    )
                )
                stats["results"] += 1

    db.session.commit()
    return stats


def register_commands(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_data_command)
    app.cli.add_command(seed_sample_data_command)


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Initialize database tables directly (useful for local bootstrap)."""
    db.create_all()
    click.echo("Database initialized.")


def _upsert_user(email, full_name, role, password):
    user = User.query.filter_by(email=email).first()
    was_created = user is None

    if was_created:
        user = User(email=email)
        db.session.add(user)

    user.full_name = full_name
    user.role = role
    user.is_active = True
    user.set_password(password)

    return user, was_created


@click.command("seed-data")
@click.option(
    "--with-batch/--no-batch",
    default=True,
    show_default=True,
    help="Create sample batch and attach seeded student to it.",
)
@with_appcontext
def seed_data_command(with_batch):
    """Seed default users (admin/director/student) and optional sample batch."""
    stats = {
        "users_created": 0,
        "users_updated": 0,
        "students_created": 0,
        "students_updated": 0,
        "teachers_created": 0,
        "teachers_updated": 0,
        "batches_created": 0,
    }

    try:
        db.create_all()

        sample_batch = None
        if with_batch:
            current_year = date.today().year
            sample_batch = Batch.query.filter_by(batch_name="Foundation Demo", year=current_year).first()
            if sample_batch is None:
                sample_batch = Batch(batch_name="Foundation Demo", year=current_year, is_active=True)
                db.session.add(sample_batch)
                stats["batches_created"] += 1

        users_to_seed = [
            {
                "email": "admin@test.com",
                "full_name": "Admin User",
                "role": "admin",
                "password": "Admin@123",
            },
            {
                "email": "director@test.com",
                "full_name": "Director User",
                "role": "director",
                "password": "Director@123",
            },
            {
                "email": "student@test.com",
                "full_name": "Student User",
                "role": "student",
                "password": "Student@123",
            },
            {
                "email": "coach@test.com",
                "full_name": "Coach User",
                "role": "coach",
                "password": "Coach@123",
            },
            {
                "email": "manager@test.com",
                "full_name": "Manager User",
                "role": "manager",
                "password": "Manager@123",
            },
            {
                "email": "parent@test.com",
                "full_name": "Parent User",
                "role": "parent",
                "password": "Parent@123",
            },
        ]

        seeded_users = {}
        for user_data in users_to_seed:
            user, created = _upsert_user(
                email=user_data["email"],
                full_name=user_data["full_name"],
                role=user_data["role"],
                password=user_data["password"],
            )
            seeded_users[user_data["email"]] = user
            if created:
                stats["users_created"] += 1
            else:
                stats["users_updated"] += 1

        db.session.flush()

        student_user = seeded_users["student@test.com"]
        student_profile = Student.query.filter_by(user_id=student_user.id).first()

        if student_profile is None:
            student_profile = Student(
                user_id=student_user.id,
                batch_id=sample_batch.id if sample_batch else None,
                phone_number="9999999999",
                address="Sample Address",
                is_active=True,
            )
            db.session.add(student_profile)
            stats["students_created"] += 1
        else:
            student_profile.is_active = True
            if sample_batch:
                student_profile.batch_id = sample_batch.id
            stats["students_updated"] += 1

        coach_user = seeded_users["coach@test.com"]
        teacher_profile = Teacher.query.filter_by(user_id=coach_user.id).first()

        if teacher_profile is None:
            teacher_profile = Teacher(
                user_id=coach_user.id,
                specialization="General",
                phone_number="8888888888",
                is_active=True,
            )
            db.session.add(teacher_profile)
            stats["teachers_created"] += 1
        else:
            teacher_profile.is_active = True
            stats["teachers_updated"] += 1

        db.session.commit()

        click.echo("Seed completed successfully.")
        click.echo(f"Users created: {stats['users_created']}, updated: {stats['users_updated']}")
        click.echo(f"Student profiles created: {stats['students_created']}, updated: {stats['students_updated']}")
        click.echo(f"Teacher profiles created: {stats['teachers_created']}, updated: {stats['teachers_updated']}")
        if with_batch:
            click.echo(f"Sample batches created: {stats['batches_created']}")

        click.echo("\nSeed login credentials:")
        click.echo("- admin@test.com / Admin@123")
        click.echo("- director@test.com / Director@123")
        click.echo("- manager@test.com / Manager@123")
        click.echo("- student@test.com / Student@123")
        click.echo("- coach@test.com / Coach@123")
        click.echo("- parent@test.com / Parent@123")

    except Exception as exc:
        db.session.rollback()
        raise click.ClickException(f"Seed failed: {exc}") from exc


@click.command("seed-sample-data")
@with_appcontext
def seed_sample_data_command():
    """Seed a fuller dataset across all modules (students, batches, fees, attendance, tests, etc.)."""
    try:
        stats = _seed_full_sample_dataset()
        click.echo("Seed complete.")
        for key, value in stats.items():
            click.echo(f"- {key}: {value}")
    except Exception as exc:
        db.session.rollback()
        raise click.ClickException(f"Seed failed: {exc}") from exc
