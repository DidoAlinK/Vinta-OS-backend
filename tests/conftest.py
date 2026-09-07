"""
Vinta School OS — Pytest Fixtures
Academy fixtures, tenant context mocks, database setup/teardown.
"""
import uuid
import pytest
from datetime import date, timedelta
from app import create_app
from app.extensions import db as _db
from app.models.academy import Academy, AcademySettings, Subscription
from app.models.user import User
from app.models.student import Student, Guardian, Enrollment
from app.models.teacher import Teacher
from app.models.class_room import Class, Classroom, Subject
from app.models.scheduling import Schedule, Session
from app.models.billing import PaymentPlan, StudentBilling, PaymentLog
from app.models.attendance import SessionStudent
from app.models.audit import ActivityLog


@pytest.fixture(scope="session")
def app():
    """Create the Flask application for the entire test session."""
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    """Fresh database session for each test. Rolls back after each test."""
    with app.app_context():
        _db.session.begin_nested()
        yield _db
        _db.session.rollback()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def academy(db):
    """Create a test academy with all default settings."""
    academy = Academy(
        id=str(uuid.uuid4()),
        name="Test Academy",
        email="test@academy.com",
        phone="+213555123456",
        weekend_day=5,
        current_term="2026 — Fall term",
    )
    db.session.add(academy)

    settings = AcademySettings(
        academy_id=academy.id,
        currency="DZD",
        default_plan_duration=30,
        auto_checkout_enabled=True,
        end_class_popup_enabled=True,
        default_theme="light",
        default_language="fr",
    )
    db.session.add(settings)

    subscription = Subscription(
        academy_id=academy.id,
        tier="starter",
        status="active",
    )
    db.session.add(subscription)

    db.session.flush()
    return academy


@pytest.fixture
def owner(db, academy):
    """Create the owner profile for the test academy."""
    owner = User(
        id=str(uuid.uuid4()),
        academy_id=academy.id,
        name="Test Owner",
        email="owner@test.com",
        role="owner",
        pin_hash=User.hash_pin("1234"),
        password_hash=User.hash_password("password123"),
        is_active=True,
    )
    db.session.add(owner)
    db.session.flush()
    return owner


@pytest.fixture
def staff(db, academy):
    """Create a staff profile for the test academy."""
    staff = User(
        id=str(uuid.uuid4()),
        academy_id=academy.id,
        name="Test Staff",
        email="staff@test.com",
        role="staff",
        pin_hash=User.hash_pin("5678"),
        is_active=True,
    )
    db.session.add(staff)
    db.session.flush()
    return staff


@pytest.fixture
def payment_plans(db, academy):
    """Create default payment plans for the test academy."""
    plans = [
        PaymentPlan(
            id=str(uuid.uuid4()),
            academy_id=academy.id,
            name="Monthly — 3,500 DA",
            duration_days=30,
            amount_da=3500,
        ),
        PaymentPlan(
            id=str(uuid.uuid4()),
            academy_id=academy.id,
            name="Term — 9,000 DA",
            duration_days=90,
            amount_da=9000,
        ),
    ]
    for plan in plans:
        db.session.add(plan)
    db.session.flush()
    return plans


@pytest.fixture
def teacher(db, academy):
    """Create a test teacher."""
    teacher = Teacher(
        id=str(uuid.uuid4()),
        academy_id=academy.id,
        first_name="Ali",
        last_name="Bensalem",
        phone="+213555987654",
        subject="Math",
        contract_type="hourly",
        hourly_rate=1500,
    )
    db.session.add(teacher)
    db.session.flush()
    return teacher


@pytest.fixture
def classroom(db, academy):
    """Create a test classroom."""
    room = Classroom(
        id=str(uuid.uuid4()),
        academy_id=academy.id,
        name="Room 1",
        capacity=30,
    )
    db.session.add(room)
    db.session.flush()
    return room


@pytest.fixture
def class_obj(db, academy, teacher, classroom):
    """Create a test class with teacher and schedule."""
    cls = Class(
        id=str(uuid.uuid4()),
        academy_id=academy.id,
        name="Math — CM2",
        subject="Math",
        color="#b3872a",
        teacher_id=teacher.id,
        capacity=25,
    )
    db.session.add(cls)
    db.session.flush()

    schedule = Schedule(
        id=str(uuid.uuid4()),
        class_id=cls.id,
        classroom_id=classroom.id,
        day_of_week=1,  # Monday
        start_time="08:00",
        end_time="09:00",
    )
    db.session.add(schedule)

    return cls


@pytest.fixture
def student(db, academy, class_obj, payment_plans):
    """Create a test student with guardian, enrollment, and billing."""
    student = Student(
        id=str(uuid.uuid4()),
        academy_id=academy.id,
        first_name="Yasmine",
        last_name="Benali",
        phone="+213555111222",
        parent_phone="+213555333444",
    )
    db.session.add(student)
    db.session.flush()

    guardian = Guardian(
        id=str(uuid.uuid4()),
        student_id=student.id,
        name="Father",
        relationship="Father",
        phone="+213555333444",
        is_emergency=True,
    )
    db.session.add(guardian)

    enrollment = Enrollment(
        id=str(uuid.uuid4()),
        student_id=student.id,
        class_id=class_obj.id,
        status="active",
    )
    db.session.add(enrollment)

    today = date.today()
    billing = StudentBilling(
        id=str(uuid.uuid4()),
        student_id=student.id,
        payment_plan_id=payment_plans[0].id,
        amount_da=3500,
        status="paid",
        due_date=today + timedelta(days=15),
        paid_date=today,
        paid_amount=3500,
        cycle_start=today,
        cycle_end=today + timedelta(days=30),
    )
    db.session.add(billing)
    db.session.flush()

    return student


@pytest.fixture
def session_obj(db, academy, class_obj, teacher):
    """Create a test session."""
    from datetime import time
    session = Session(
        id=str(uuid.uuid4()),
        academy_id=academy.id,
        class_id=class_obj.id,
        teacher_id=teacher.id,
        date=date.today(),
        start_time=time(8, 0),
        end_time=time(9, 0),
        subject="Math",
        status="scheduled",
    )
    db.session.add(session)
    db.session.flush()
    return session


@pytest.fixture
def auth_headers_owner(client, owner):
    """Get JWT auth headers for the owner."""
    resp = client.post("/api/auth/login", json={
        "email": "owner@test.com",
        "password": "password123",
    })
    token = resp.get_json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Academy-Id": owner.academy_id,
        "Content-Type": "application/json",
    }


@pytest.fixture
def auth_headers_staff(client, staff, owner):
    """Get JWT auth headers for the staff member via PIN verification."""
    # First login as owner to get token for profile listing
    resp = client.post("/api/auth/login", json={
        "email": "owner@test.com",
        "password": "password123",
    })
    token = resp.get_json()["access_token"]

    # Verify staff PIN
    resp = client.post(
        "/api/auth/verify-pin",
        json={"user_id": staff.id, "pin": "5678"},
        headers={
            "Authorization": f"Bearer {token}",
            "X-Academy-Id": staff.academy_id,
        },
    )
    staff_token = resp.get_json()["access_token"]
    return {
        "Authorization": f"Bearer {staff_token}",
        "X-Academy-Id": staff.academy_id,
        "Content-Type": "application/json",
    }
