from sqlalchemy.orm import Session
from db.models.email import Email

def create_email(db: Session, data: dict):
    email = Email(**data)
    db.add(email)
    db.commit()
    db.refresh(email)
    return email

def get_email(db: Session, email_id):
    return db.query(Email).filter(Email.id == email_id).first()

def update_status(db: Session, email_id, status: str):
    email = get_email(db, email_id)
    if email:
        email.status = status
        db.commit()
    return email