from pydantic import validate_email
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.models.job_application import Contacts, JobApplication
from app.schemas import job_application
from app.schemas.job_application import ApiResponse


def create_contacts(data: job_application.ContactsCreate, user_id: str):
    try:
        contacts_instance = Contacts(
            name=data.name,
            email=data.email,
            role=data.role,
            notes=data.notes,
            linkedIn_url=data.linkedIn_url,
            user_id=user_id
        )
        contacts_instance.save_to_db()
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


def update_contacts(data: job_application.ContactsUpdate, db: Session, contact_id: str):
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
        db_contact.notes = data.notes if data.notes else db_contact.notes
        db_contact.linkedIn_url = data.linkedIn_url if data.linkedIn_url else db_contact.linkedIn_url
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


def get_contacts(user_id: str, db: Session, limit: int):
    try:
        db_contacts = db.query(Contacts).filter(Contacts.user_id == user_id).limit(limit).all()
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


def link_contact_to_job_application(data: job_application.ContactsLinkJobApplication, db: Session, contact_id: str):
    try:
        job_application_id = data.job_application_id
        db_job = db.query(JobApplication).filter(JobApplication.id == job_application_id).first()
        if db_job is None:
            raise HTTPException(status_code=404, detail="Job application not found")
        db_contact = db.query(Contacts).filter(Contacts.id == contact_id).first()
        if db_contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")
        db_job.contacts_id = contact_id
        db.commit()
        db.refresh(db_job)
        return {
            "success": True,
            "message": "Contact Linked to Job Application successfully"
        }
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=404, detail="Error updating contact")
