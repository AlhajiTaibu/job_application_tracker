from sqlalchemy import Column, ForeignKey, Table

from sqlalchemy.dialects.postgresql.base import UUID
from app.database import Base

documents_association_table = Table('documents_association_table', Base.metadata,
    Column('job_application_id', UUID(as_uuid=True), ForeignKey('job_application.id')),
    Column('documents_id', UUID(as_uuid=True), ForeignKey('documents.id'))
)

association_table = Table('association', Base.metadata,
    Column('job_application_id', UUID(as_uuid=True), ForeignKey('job_application.id')),
    Column('contacts_id', UUID(as_uuid=True), ForeignKey('contacts.id'))
)