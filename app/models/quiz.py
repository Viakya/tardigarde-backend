from app.extensions import db


class Quiz(db.Model):
    __tablename__ = "quizzes"
    __table_args__ = (
        db.Index("ix_quizzes_batch_id", "batch_id"),
        db.Index("ix_quizzes_status", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), nullable=False, default="medium")
    total_marks = db.Column(db.Integer, nullable=False, default=100)
    question_count = db.Column(db.Integer, nullable=False)
    mode = db.Column(db.String(20), nullable=False, default="practice")
    status = db.Column(db.String(20), nullable=False, default="draft")
    open_at = db.Column(db.DateTime(timezone=True), nullable=True)
    close_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now(), onupdate=db.func.now())
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)
    closed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    batch = db.relationship("Batch", back_populates="quizzes", lazy="joined")
    creator = db.relationship("User", lazy="joined")
    questions = db.relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    submissions = db.relationship("QuizSubmission", back_populates="quiz", cascade="all, delete-orphan")

    def to_dict(self, include_questions=False):
        payload = {
            "id": self.id,
            "batch_id": self.batch_id,
            "title": self.title,
            "description": self.description,
            "difficulty": self.difficulty,
            "total_marks": self.total_marks,
            "question_count": self.question_count,
            "mode": self.mode,
            "status": self.status,
            "open_at": self.open_at.isoformat() if self.open_at else None,
            "close_at": self.close_at.isoformat() if self.close_at else None,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "creator": {
                "id": self.creator.id,
                "full_name": self.creator.full_name,
                "email": self.creator.email,
                "role": self.creator.role,
            }
            if self.creator
            else None,
        }
        if include_questions:
            payload["questions"] = [question.to_dict() for question in self.questions]
        return payload


class QuizQuestion(db.Model):
    __tablename__ = "quiz_questions"
    __table_args__ = (
        db.Index("ix_quiz_questions_quiz_id", "quiz_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    marks = db.Column(db.Numeric(6, 2), nullable=False)

    quiz = db.relationship("Quiz", back_populates="questions")

    def to_dict(self):
        return {
            "id": self.id,
            "quiz_id": self.quiz_id,
            "question_text": self.question_text,
            "options": [self.option_a, self.option_b, self.option_c, self.option_d],
            "correct_option": self.correct_option,
            "explanation": self.explanation,
            "marks": float(self.marks) if self.marks is not None else None,
        }


class QuizSubmission(db.Model):
    __tablename__ = "quiz_submissions"
    __table_args__ = (
        db.UniqueConstraint("quiz_id", "student_id", name="uq_quiz_submission_student"),
        db.Index("ix_quiz_submissions_quiz_id", "quiz_id"),
        db.Index("ix_quiz_submissions_student_id", "student_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    score = db.Column(db.Numeric(6, 2), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="submitted")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())

    quiz = db.relationship("Quiz", back_populates="submissions", lazy="joined")
    student = db.relationship("Student", lazy="joined")
    answers = db.relationship("QuizAnswer", back_populates="submission", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "quiz_id": self.quiz_id,
            "student_id": self.student_id,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "score": float(self.score) if self.score is not None else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class QuizAnswer(db.Model):
    __tablename__ = "quiz_answers"
    __table_args__ = (
        db.Index("ix_quiz_answers_submission_id", "submission_id"),
        db.Index("ix_quiz_answers_question_id", "question_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("quiz_submissions.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    selected_option = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    marks_awarded = db.Column(db.Numeric(6, 2), nullable=False, default=0)

    submission = db.relationship("QuizSubmission", back_populates="answers")
    question = db.relationship("QuizQuestion", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "question_id": self.question_id,
            "selected_option": self.selected_option,
            "is_correct": self.is_correct,
            "marks_awarded": float(self.marks_awarded) if self.marks_awarded is not None else None,
        }
