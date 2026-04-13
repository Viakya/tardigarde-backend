from app.extensions import db


class BatchResource(db.Model):
    __tablename__ = "batch_resources"
    __table_args__ = (
        db.Index("ix_batch_resources_batch_id", "batch_id"),
        db.Index("ix_batch_resources_created_by", "created_by"),
        db.Index("ix_batch_resources_type", "resource_type"),
    )

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("batches.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(500), nullable=False)
    resource_type = db.Column(db.String(40), nullable=False, default="link")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    visible_to_students = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=db.func.now(),
        onupdate=db.func.now(),
    )

    batch = db.relationship("Batch", back_populates="resources", lazy="joined")
    creator = db.relationship("User", lazy="joined")

    def to_dict(self):
        return {
            "id": self.id,
            "batch_id": self.batch_id,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "resource_type": self.resource_type,
            "created_by": self.created_by,
            "visible_to_students": self.visible_to_students,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "creator": {
                "id": self.creator.id,
                "full_name": self.creator.full_name,
                "email": self.creator.email,
                "role": self.creator.role,
            }
            if self.creator
            else None,
        }
