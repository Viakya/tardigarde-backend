"""Seed a small, realistic dataset across all core tables."""

from datetime import date, timedelta

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


def get_or_create_user(email: str, full_name: str, role: str, password: str = "Test@123") -> User:
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(email=email, full_name=full_name, role=role, is_active=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
    return user


def get_or_create_batch(name: str, year: int) -> Batch:
    batch = Batch.query.filter_by(batch_name=name, year=year).first()
    if batch is None:
        batch = Batch(batch_name=name, year=year, is_active=True)
        db.session.add(batch)
        db.session.flush()
    return batch


def get_or_create_teacher(user: User, specialization: str) -> Teacher:
    teacher = Teacher.query.filter_by(user_id=user.id).first()
    if teacher is None:
        teacher = Teacher(user_id=user.id, specialization=specialization, is_active=True)
        db.session.add(teacher)
        db.session.flush()
    return teacher


def get_or_create_student(user: User, batch: Batch, phone: str) -> Student:
    student = Student.query.filter_by(user_id=user.id).first()
    if student is None:
        student = Student(user_id=user.id, batch_id=batch.id, phone_number=phone, is_active=True)
        db.session.add(student)
        db.session.flush()
    else:
        student.batch_id = batch.id
    return student


def seed_data() -> dict:
    stats = {"users": 0, "batches": 0, "students": 0, "teachers": 0, "fees": 0, "salaries": 0, "attendance": 0, "tests": 0, "results": 0}

    manager = User.query.filter_by(email="manager@test.com").first()
    if manager is None:
        manager = get_or_create_user("manager@test.com", "Manager User", "manager", "Manager@123")
        stats["users"] += 1

    admin = User.query.filter_by(email="admin@test.com").first()
    if admin is None:
        admin = get_or_create_user("admin@test.com", "Admin User", "admin", "Admin@123")
        stats["users"] += 1
    else:
        admin.full_name = "Admin User"
        admin.role = "admin"
        admin.is_active = True
        admin.set_password("Admin@123")

    director = User.query.filter_by(role="director").first()
    if director is None:
        director = get_or_create_user("director@test.com", "Director User", "director", "Director@123")
        stats["users"] += 1

    current_year = date.today().year
    batches = [
        get_or_create_batch("Foundation", current_year),
        get_or_create_batch("Momentum", current_year),
        get_or_create_batch("Sprint", current_year),
    ]
    stats["batches"] += len(batches)

    teacher_users = [
        get_or_create_user("coach1@test.com", "Coach One", "coach"),
        get_or_create_user("coach2@test.com", "Coach Two", "coach"),
        get_or_create_user("coach3@test.com", "Coach Three", "coach"),
    ]
    stats["users"] += len(teacher_users)

    teachers = [
        get_or_create_teacher(teacher_users[0], "Mathematics"),
        get_or_create_teacher(teacher_users[1], "Science"),
        get_or_create_teacher(teacher_users[2], "Reasoning"),
    ]
    stats["teachers"] += len(teachers)

    # Assign teachers to batches
    batches[0].teachers = [teachers[0], teachers[1]]
    batches[1].teachers = [teachers[1], teachers[2]]
    batches[2].teachers = [teachers[0], teachers[2]]

    parent1 = get_or_create_user("parent1@test.com", "Parent One", "parent")
    parent2 = get_or_create_user("parent2@test.com", "Parent Two", "parent")
    stats["users"] += 2

    student_users = [
        get_or_create_user("student1@test.com", "Student One", "student"),
        get_or_create_user("student2@test.com", "Student Two", "student"),
        get_or_create_user("student3@test.com", "Student Three", "student"),
        get_or_create_user("student4@test.com", "Student Four", "student"),
        get_or_create_user("student5@test.com", "Student Five", "student"),
    ]
    stats["users"] += len(student_users)

    students = [
        get_or_create_student(student_users[0], batches[0], "9000000001"),
        get_or_create_student(student_users[1], batches[0], "9000000002"),
        get_or_create_student(student_users[2], batches[1], "9000000003"),
        get_or_create_student(student_users[3], batches[1], "9000000004"),
        get_or_create_student(student_users[4], batches[2], "9000000005"),
    ]
    stats["students"] += len(students)

    # Link parents
    for student in students[:3]:
        if parent1 not in student.parents:
            student.parents.append(parent1)
    for student in students[2:]:
        if parent2 not in student.parents:
            student.parents.append(parent2)

    today = date.today()

    # Fee payments
    for student in students:
        fee_payment = FeePayment(
            student_id=student.id,
            amount=5000,
            payment_date=today - timedelta(days=3),
            payment_method="cash",
            received_by=manager.id,
            remarks="Seed payment",
        )
        db.session.add(fee_payment)
        stats["fees"] += 1

    # Salaries
    for teacher in teachers:
        salary = Salary(
            teacher_id=teacher.id,
            amount=12000,
            payment_date=today - timedelta(days=5),
            payment_method="bank",
            paid_by=manager.id,
            remarks="Seed salary",
        )
        db.session.add(salary)
        stats["salaries"] += 1

    # Attendance
    for student in students:
        for offset in range(2):
            attendance_date = today - timedelta(days=offset)
            existing_attendance = Attendance.query.filter_by(
                student_id=student.id,
                attendance_date=attendance_date,
            ).first()
            if existing_attendance is None:
                attendance = Attendance(
                    student_id=student.id,
                    batch_id=student.batch_id,
                    attendance_date=attendance_date,
                    status="present",
                    marked_by=manager.id,
                )
                db.session.add(attendance)
                stats["attendance"] += 1

    # Tests and results
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

        batch_students = [student for student in students if student.batch_id == batch.id]
        for student in batch_students:
            existing_result = TestResult.query.filter_by(test_id=test.id, student_id=student.id).first()
            if existing_result is None:
                result = TestResult(
                    test_id=test.id,
                    student_id=student.id,
                    marks_obtained=78,
                    remarks="Seed result",
                    is_active=True,
                )
                db.session.add(result)
                stats["results"] += 1

    db.session.commit()
    return stats


def main() -> None:
    app = create_app()
    with app.app_context():
        stats = seed_data()
        print("Seed complete.")
        for key, value in stats.items():
            print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
