from fastapi import HTTPException
from pydantic import validate_email
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.job_application import Contacts, JobApplication, NoteLog
from app.schemas.contacts import ContactsCreate, ContactsUpdate, ContactsLinkJobApplication, ContactsFilterParams
from app.schemas.job_application import ApiResponse


def create_contacts(data: ContactsCreate, user_id: str):
    try:
        contacts_instance = Contacts(
            name=data.name,
            email=data.email,
            company=data.company,
            relationship_type=data.relationship_type,
            role=data.role,
            linkedIn_url=data.linkedIn_url,
            user_id=user_id
        )
        contacts_instance.save_to_db()
        if data.notes:
            note = NoteLog(notes=data.notes, contacts_id=contacts_instance.id)
            note.save_to_db()
        return {
            "success": True,
            "message": "Contact created successfully",
            "data": {
                "id": contacts_instance.id,
                "name": contacts_instance.name
            }
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error creating contact")


def update_contacts(data: ContactsUpdate, db: Session, contact_id: str):
    try:
        db_contact = db.query(Contacts).filter(Contacts.id == contact_id).first()
        if db_contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")

        db_contact.name = data.name if data.name else db_contact.name
        if data.email:
            try:
                email_info, email = validate_email(data.email)
            except Exception as error:
                raise HTTPException(status_code=400, detail=f"Invalid email: {error}")
            if email:
                db_contact.email = data.email
        db_contact.role = data.role if data.role else db_contact.role
        db_contact.linkedIn_url = data.linkedIn_url if data.linkedIn_url else db_contact.linkedIn_url
        if data.company:
            db_contact.company = data.company
        if data.relationship_type:
            db_contact.relationship_type = data.relationship_type
        if data.notes:
            note = NoteLog(notes=data.notes, contacts_id=db_contact.id)
            note.save_to_db()
        db.commit()
        db.refresh(db_contact)
        return {
            "success": True,
            "message": "Contact updated successfully",
            "data": {
                "id": db_contact.id,
                "name": db_contact.name
            }
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error updating contact")


def get_contacts_by_id(contact_id: str, user_id: str, db: Session):
    try:
        db_contact = db.query(Contacts).filter(Contacts.id == contact_id,
                                               Contacts.user_id == user_id).first()
        if not db_contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        return ApiResponse(success=True, payload=db_contact)
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error getting contact")


def get_contacts(user_id: str, db: Session, limit: int, filters: ContactsFilterParams):
    try:
        latest_note_sub = (
            select(NoteLog.contacts_id, func.max(NoteLog.created_at).label("latest_note"))
            .group_by(NoteLog.contacts_id)
            .subquery()
        )

        stmt = (
            select(Contacts)
            .outerjoin(latest_note_sub, Contacts.id == latest_note_sub.c.contacts_id)
            .where(Contacts.user_id == user_id)
            .order_by(latest_note_sub.c.latest_note.desc().nulls_last(), Contacts.name.asc())
            .limit(limit + 1)
        )

        if filters.q:
            stmt = stmt.where(Contacts.company.ilike(f"%{filters.q}%"))

        db_contacts = db.execute(stmt).scalars().all()
        results = db_contacts if db_contacts else []
        return ApiResponse(success=True, payload={"data": results})
    except Exception as error:
        logger.error(error)
        raise HTTPException(status_code=404, detail="Error getting contact")


def delete_contacts(user_id: str, contact_id: str, db: Session):
    try:
        db_contact = db.query(Contacts).filter(Contacts.id == contact_id,
                                               Contacts.user_id == user_id).first()
        if db_contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        db.delete(db_contact)
        db.commit()
        return {
            "success": True,
            "message": "Contact deleted successfully"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error deleting contact")


def link_contact_to_job_application(data: ContactsLinkJobApplication, db: Session, contact_id: str):
    try:
        job_application_id = data.job_application_id
        db_job = db.query(JobApplication).filter(JobApplication.id == job_application_id).first()
        if db_job is None:
            raise HTTPException(status_code=404, detail="Job application not found")
        db_contact = db.query(Contacts).filter(Contacts.id == contact_id).first()
        if db_contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        db_contact.job_applications.append(db_job)
        db.commit()
        db.refresh(db_job)
        return {
            "success": True,
            "message": "Contact Linked to Job Application successfully"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error updating contact")
