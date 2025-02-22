import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base, Contact, LinkPrecedence

# Setup test database
TEST_DATABASE_URL = "sqlite:///./test_database.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency
@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Test cases
def test_identify_new_primary_contact(db_session):
    response = client.post("/identify", json={"email": "test@example.com", "phoneNumber": "1234567890"})
    assert response.status_code == 200
    data = response.json()
    assert data["primaryContactId"] is not None
    assert data["emails"] == ["test@example.com"]
    assert data["phoneNumbers"] == ["1234567890"]
    assert data["secondaryContactIds"] == []

def test_identify_existing_contact(db_session):
    response = client.post("/identify", json={"email": "existing@example.com","phoneNumber": "1111111111"})
    assert response.status_code == 200
    response = client.post("/identify", json={"email": "existing@example.com"})
    assert response.status_code == 200
    data = response.json()
    assert "existing@example.com" in data["emails"], f"Expected {contact.email} in {data['emails']}"

def test_identify_secondary_contact_creation(db_session):
    primary = Contact(email="primary@example.com", phone_number="2222222222", link_precedence=LinkPrecedence.PRIMARY)
    db_session.add(primary)
    db_session.commit()
    
    response = client.post("/identify", json={"email": "new@example.com", "phoneNumber": "2222222222"})
    assert response.status_code == 200
    data = response.json()
    assert data["primaryContactId"] == primary.id
    assert "new@example.com" in data["emails"]
    assert "2222222222" in data["phoneNumbers"]
    assert len(data["secondaryContactIds"]) == 1

def test_invalid_request(db_session):
    response = client.post("/identify", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "At least one of email or phoneNumber must be provided"
