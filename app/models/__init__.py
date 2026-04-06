from app.models.associations import batch_teachers, parent_students
from app.models.user import User
from app.models.student import Student
from app.models.batch import Batch
from app.models.teacher import Teacher
from app.models.attendance import Attendance
from app.models.fee_payment import FeePayment
from app.models.batch_resource import BatchResource
from app.models.salary import Salary
from app.models.test import Test
from app.models.test_result import TestResult
from app.models.quiz import Quiz, QuizQuestion, QuizSubmission, QuizAnswer

__all__ = [
	"User",
	"Student",
	"Batch",
	"Teacher",
	"Attendance",
	"FeePayment",
	"BatchResource",
	"Salary",
	"Test",
	"TestResult",
	"Quiz",
	"QuizQuestion",
	"QuizSubmission",
	"QuizAnswer",
	"batch_teachers",
	"parent_students",
]
