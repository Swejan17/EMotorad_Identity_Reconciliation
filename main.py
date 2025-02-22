from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime, timezone
from enum import Enum as PyEnum

DATABASE_URL =  "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Enum for link precedence
class LinkPrecedence(PyEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"

# Database Model
class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    linked_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    link_precedence = Column(Enum(LinkPrecedence), default=LinkPrecedence.PRIMARY)
    created_at = Column(DateTime, default= datetime.now(timezone.utc))
    updated_at = Column(DateTime, default= datetime.now(timezone.utc), onupdate= datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True)

    linked_contact = relationship("Contact", remote_side=[id], backref="linked_contacts")

# Request Model
class IdentifyRequest(BaseModel):
    email: EmailStr | None = None
    phoneNumber: constr(min_length=10, max_length=15,pattern="^\\d+$") | None = None

# Response Model
class IdentifyResponse(BaseModel):
    primaryContactId: int
    emails: list[str]
    phoneNumbers: list[str]
    secondaryContactIds: list[int]

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Identify Endpoint
@app.post("/identify", response_model=IdentifyResponse)
def identify(request: IdentifyRequest, db: Session = Depends(get_db)):
    if not request.email and not request.phoneNumber:
        raise HTTPException(status_code=400, detail="At least one of email or phoneNumber must be provided")
    
    query = db.query(Contact)

    if request.email and request.phoneNumber:
        # Filter by both email and phoneNumber if both are provided
        query = query.filter(
            (Contact.email == request.email) | (Contact.phone_number == request.phoneNumber)
        )
    elif request.email:
        # Filter only by email if phoneNumber is None
        query = query.filter(Contact.email == request.email)
    elif request.phoneNumber:
        # Filter only by phoneNumber if email is None
        query = query.filter(Contact.phone_number == request.phoneNumber)

    matching_contacts = query.all()
        
    if not matching_contacts:
        # No match, create a new primary contact
        new_contact = Contact(email=request.email, phone_number=request.phoneNumber, link_precedence=LinkPrecedence.PRIMARY)
        db.add(new_contact)
        db.commit()
        db.refresh(new_contact)
        new_contact.linked_id = new_contact.id
        db.commit()
        db.refresh(new_contact)
        return IdentifyResponse(
            primaryContactId=new_contact.id,
            emails=[new_contact.email] if new_contact.email else [],
            phoneNumbers=[new_contact.phone_number] if new_contact.phone_number else [],
            secondaryContactIds=[],
        )
    
    # Find the primary contact
    primary_contact = min(matching_contacts, key=lambda c: c.created_at)
    if primary_contact.link_precedence == LinkPrecedence.SECONDARY:
        primary_contact = db.query(Contact).filter(Contact.id == primary_contact.linked_id).first()
    
    secondary_contacts = db.query(Contact).filter(Contact.linked_id == primary_contact.id).all()
    
    # Check if the incoming request data is new
    existing_emails = {c.email for c in matching_contacts if c.email} | {c.email for c in secondary_contacts if c.email}
    existing_phones = {c.phone_number for c in matching_contacts if c.phone_number} | {c.phone_number for c in secondary_contacts if c.phone_number}
    
    if ((request.email not in existing_emails and request.email is not None) or (request.phoneNumber not in existing_phones and request.phoneNumber is not None)):
        # Create a new secondary contact
        new_secondary = Contact(email=request.email, phone_number=request.phoneNumber, linked_id=primary_contact.id, link_precedence=LinkPrecedence.SECONDARY)
        db.add(new_secondary)
        db.commit()
        db.refresh(new_secondary)
        secondary_contacts.append(new_secondary)
    
    return IdentifyResponse(
        primaryContactId=primary_contact.id,
        emails=set([c.email for c in secondary_contacts if c.email]),
        phoneNumbers=set([c.phone_number for c in secondary_contacts if c.phone_number ]),
        secondaryContactIds=[c.id for c in secondary_contacts],
    )

# Create the database tables
Base.metadata.create_all(bind=engine)