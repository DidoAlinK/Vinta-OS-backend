# Vinta School OS — Comprehensive API Reference

> **Base URL**: `http://localhost:5000/api`
> **Auth**: JWT Bearer tokens via `Authorization: Bearer <access_token>`
> **Tenant Scope**: All protected routes require `X-Academy-Id` header
> **OpenAPI Docs**: `http://localhost:5000/api/docs/` (Swagger UI)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Authentication Flow](#2-authentication-flow)
3. [Complete Route Map](#3-complete-route-map)
4. [Blueprint: Auth (`/api/auth`)](#4-auth)
5. [Blueprint: Students (`/api/students`)](#5-students)
6. [Blueprint: Teachers (`/api/teachers`)](#6-teachers)
7. [Blueprint: Classes (`/api`)](#7-classes)
8. [Blueprint: Calendar (`/api`)](#8-calendar)
9. [Blueprint: Attendance (`/api/attendance`)](#9-attendance)
10. [Blueprint: Billing (`/api/billing`)](#10-billing)
11. [Blueprint: Analytics (`/api/analytics`)](#11-analytics)
12. [Blueprint: Settings (`/api/settings`)](#12-settings)
13. [Blueprint: Notifications (`/api/notifications`)](#13-notifications)
14. [SQLAlchemy Data Models](#14-data-models)
15. [Access Control & Decorators](#15-access-control)
16. [Frontend ↔ Backend Gap Analysis](#16-gap-analysis)

---

## 1. Architecture Overview

| Component | Technology |
|---|---|
| Framework | Flask 3.x (Application Factory pattern) |
| ORM | Flask-SQLAlchemy (mapped_column style) |
| Migrations | Flask-Migrate (Alembic) |
| Auth | Flask-JWT-Extended (access + refresh tokens) |
| API Docs | flask-smorest (OpenAPI 3.1 / Swagger UI) |
| Realtime | Flask-SocketIO (initialized, not wired to routes yet) |
| CORS | Flask-CORS (all `/api/*` origins) |
| Multi-Tenancy | Header-based (`X-Academy-Id`) — every table FK to `academies.id` |
| PIN Auth | bcrypt-hashed 4-digit PINs for profile-level login |
| Currency | Algerian Dinar (DZD) |

**Blueprint Registration** (from `app/__init__.py`):

| Blueprint | URL Prefix | Doc Name |
|---|---|---|
| `auth_bp` | `/api/auth` | Auth |
| `students_bp` | `/api/students` | Students |
| `teachers_bp` | `/api/teachers` | Teachers |
| `classes_bp` | `/api` | Classes |
| `calendar_bp` | `/api` | Calendar |
| `attendance_bp` | `/api/attendance` | Attendance |
| `billing_bp` | `/api/billing` | Billing |
| `analytics_bp` | `/api/analytics` | Analytics |
| `settings_bp` | `/api/settings` | Settings |
| `notifications_bp` | `/api/notifications` | Notifications |

---

## 2. Authentication Flow

The system has a **two-stage auth flow**:

### Stage 1: Academy Signup + Owner Creation (Bootstrap)

```
POST /api/auth/signup          → Creates Academy + Settings + Subscription + Payment Plans
POST /api/auth/create-owner    → Creates the first owner User (JWT NOT required, but X-Academy-Id header required)
```

**Signup flow:**
1. `POST /api/auth/signup` with `{ name, email, password }` — provisions Academy, AcademySettings (DZD, light theme, French), Subscription (starter), and 4 default PaymentPlans
2. Returns `{ academy_id, name }` — frontend stores academy_id
3. `POST /api/auth/create-owner` with `{ academy_id, name, email, password, pin }` + `X-Academy-Id` header — creates the owner User record with both password_hash and pin_hash
4. Returns `{ id, name, role, academy_id }`

### Stage 2: Daily Login (Owner)

```
POST /api/auth/login           → Owner logs in with email + password → gets access_token + refresh_token
```

**Login flow:**
1. `POST /api/auth/login` with `{ email, password }` — validates against `User` with `role='owner'`
2. Returns `{ access_token, refresh_token, user_id, name, role, academy_id }`
3. Frontend stores tokens + academy_id in localStorage

### Stage 3: Profile Picker (PIN-based)

```
GET  /api/auth/profiles        → Lists all active profiles for the academy
POST /api/auth/verify-pin      → Authenticates profile by PIN → returns access_token
```

**Profile picker flow:**
1. `GET /api/auth/profiles` with `X-Academy-Id` header — returns all active Users (owner + staff)
2. User selects a profile → enters PIN
3. `POST /api/auth/verify-pin` with `{ user_id, pin }` + `X-Academy-Id` header
4. Returns `{ access_token, user_id, name, role, academy_id }` (no refresh token for PIN auth)

### Token Refresh

```
POST /api/auth/refresh         → ⚠️ NOT IMPLEMENTED in backend (see gap analysis)
```

The frontend's Axios interceptor calls `POST /auth/refresh` with `{ refresh_token }` on 401, but **this route does not exist in the backend**.

### Other Auth Routes

| Route | Method | Auth | Description |
|---|---|---|---|
| `/api/auth/me` | GET | JWT | Returns current user profile |
| `/api/auth/change-pin` | POST | JWT | Change own PIN (old_pin + new_pin) |
| `/api/auth/create-profile` | POST | JWT + owner role + owner PIN | Create a new staff/owner profile |

---

## 3. Complete Route Map

### Auth (`/api/auth`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 1 | POST | `/api/auth/signup` | None | Create academy (tenant provisioning) |
| 2 | POST | `/api/auth/login` | None | Owner login (email + password) |
| 3 | GET | `/api/auth/profiles` | JWT | List all profiles for academy |
| 4 | POST | `/api/auth/verify-pin` | X-Academy-Id (no JWT) | PIN auth → session token |
| 5 | POST | `/api/auth/create-owner` | X-Academy-Id (no JWT) | Bootstrap first owner |
| 6 | POST | `/api/auth/create-profile` | JWT + owner | Create staff profile |
| 7 | POST | `/api/auth/change-pin` | JWT | Change own PIN |
| 8 | GET | `/api/auth/me` | JWT | Get current user profile |

### Students (`/api/students`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 9 | GET | `/api/students` | JWT + tenant | List students (paginated) |
| 10 | GET | `/api/students/stats` | JWT + tenant | Aggregate student stats |
| 11 | GET | `/api/students/{id}` | JWT + tenant | Single student (profile drawer) |
| 12 | POST | `/api/students` | JWT + tenant | Create student + default guardian + billing |
| 13 | PUT | `/api/students/{id}` | JWT + tenant | Update student fields |
| 14 | DELETE | `/api/students/{id}` | JWT + tenant | Delete student (cascade withdraw) |
| 15 | POST | `/api/students/{id}/enroll` | JWT + tenant | Enroll in a class |
| 16 | GET | `/api/students/{id}/guardians` | JWT + tenant | List guardians |
| 17 | POST | `/api/students/{id}/guardians` | JWT + tenant | Add guardian |

### Teachers (`/api/teachers`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 18 | GET | `/api/teachers` | JWT + tenant | List teachers with classes + week sessions |
| 19 | GET | `/api/teachers/stats` | JWT + tenant | Teacher count by contract type |
| 20 | GET | `/api/teachers/{id}` | JWT + tenant | Teacher detail + schedule + payroll summary |
| 21 | POST | `/api/teachers` | JWT + tenant | Create teacher |
| 22 | PUT | `/api/teachers/{id}` | JWT + tenant | Update teacher |
| 23 | DELETE | `/api/teachers/{id}` | JWT + tenant | Delete teacher |

### Classes (`/api`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 24 | GET | `/api/classrooms` | JWT + tenant | List classrooms |
| 25 | POST | `/api/classrooms` | JWT + tenant | Create classroom |
| 26 | GET | `/api/classes` | JWT + tenant | List classes (with status dots) |
| 27 | GET | `/api/classes/{id}` | JWT + tenant | Class detail + schedules + enrollment |
| 28 | POST | `/api/classes` | JWT + tenant | Create class |
| 29 | PUT | `/api/classes/{id}` | JWT + tenant | Update class |
| 30 | DELETE | `/api/classes/{id}` | JWT + tenant | Delete class (cascade) |
| 31 | POST | `/api/classes/{id}/schedules` | JWT + tenant | Add schedule (auto-generates 12 weeks of sessions) |
| 32 | DELETE | `/api/classes/{id}/schedules/{sid}` | JWT + tenant | Delete schedule block |
| 33 | GET | `/api/subjects` | JWT + tenant | List subjects (calendar palette) |
| 34 | POST | `/api/subjects` | JWT + tenant | Create custom subject |

### Calendar (`/api`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 35 | GET | `/api/calendar/week` | JWT + tenant | Sessions for a week (query: `?date=`) |
| 36 | GET | `/api/calendar/day` | JWT + tenant | Sessions for a day (query: `?date=`) |
| 37 | POST | `/api/sessions` | JWT + tenant | Create session (drag-to-create) |
| 38 | PATCH | `/api/sessions/{id}` | JWT + tenant | Update session times (drag-move/resize) |
| 39 | DELETE | `/api/sessions/{id}` | JWT + tenant | Cancel session |
| 40 | GET | `/api/sessions/{id}/roster` | JWT + tenant | Session student roster |
| 41 | POST | `/api/sessions/{id}/roster` | JWT + tenant | Add student to session roster |

### Attendance (`/api/attendance`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 42 | POST | `/api/attendance/check-in` | JWT + tenant + PIN | Check in student (PIN-verified) |
| 43 | POST | `/api/attendance/check-out` | JWT + tenant | Check out student |
| 44 | POST | `/api/attendance/auto-checkout` | JWT + tenant | Auto-checkout all present students |
| 45 | GET | `/api/attendance/roster/{session_id}` | JWT + tenant | Full roster with attendance status |
| 46 | POST | `/api/attendance/add-to-session` | JWT + tenant | Add student to session (idempotent) |

### Billing (`/api/billing`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 47 | GET | `/api/billing/plans` | JWT + tenant | List payment plans |
| 48 | POST | `/api/billing/plans` | JWT + tenant | Create payment plan |
| 49 | GET | `/api/billing/students` | JWT + tenant | List billing records (filter: `?student_id=&status=`) |
| 50 | POST | `/api/billing/record-payment` | JWT + tenant | Record payment against billing |
| 51 | GET | `/api/billing/stats` | JWT + tenant | Donut ring stats (student + payroll) |
| 52 | GET | `/api/billing/revenue-chart` | JWT + tenant | Monthly revenue chart (query: `?months=6`) |
| 53 | GET | `/api/billing/aging-buckets` | JWT + tenant | Overdue accounts (1-7d, 8-30d, 30d+) |
| 54 | POST | `/api/billing/check-overdue` | JWT + tenant | Trigger overdue status check |
| 55 | POST | `/api/billing/renew-cycles` | JWT + tenant | Trigger billing cycle renewal |
| 56 | GET | `/api/billing/payroll` | JWT + tenant | List teacher payroll records |
| 57 | POST | `/api/billing/payroll/settle/{id}` | JWT + tenant | Mark payroll as settled |

### Analytics (`/api/analytics`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 58 | GET | `/api/analytics/dashboard` | JWT + tenant | Dashboard overview stats |
| 59 | GET | `/api/analytics/revenue-chart` | JWT + tenant | Revenue time-series |
| 60 | GET | `/api/analytics/export/{dataset}` | JWT + tenant | CSV export (students/billing/teacher_hours/chart_data) |

### Settings (`/api/settings`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 61 | GET | `/api/settings/academy` | JWT + tenant | Academy profile |
| 62 | PUT | `/api/settings/academy` | JWT + tenant + owner | Update academy |
| 63 | GET | `/api/settings/appearance` | JWT + tenant | Theme/font/language settings |
| 64 | PUT | `/api/settings/appearance` | JWT + tenant | Update appearance |
| 65 | GET | `/api/settings/billing-config` | JWT + tenant + owner | Billing configuration |
| 66 | PUT | `/api/settings/billing-config` | JWT + tenant + owner | Update billing config |
| 67 | GET | `/api/settings/automations` | JWT + tenant + owner | Automation toggles + tier |
| 68 | PUT | `/api/settings/automations` | JWT + tenant + owner | Update automations (tier-gated) |
| 69 | GET | `/api/settings/staff` | JWT + tenant + owner | List all staff profiles |
| 70 | POST | `/api/settings/staff` | JWT + tenant + owner | Add staff (owner PIN required) |
| 71 | PUT | `/api/settings/staff/{id}` | JWT + tenant + owner | Update staff profile |
| 72 | POST | `/api/settings/staff/{id}/deactivate` | JWT + tenant + owner | Soft-delete staff |
| 73 | GET | `/api/settings/profile` | JWT + tenant | Current user profile |
| 74 | PUT | `/api/settings/profile` | JWT + tenant | Update own profile |
| 75 | GET | `/api/settings/subscription` | JWT + tenant + owner | Subscription details |

### Notifications (`/api/notifications`)

| # | Method | Full Path | Auth | Description |
|---|---|---|---|---|
| 76 | GET | `/api/notifications` | JWT + tenant | List notifications (filter: `?unread_only=true`) |
| 77 | GET | `/api/notifications/unread-count` | JWT + tenant | Unread notification count |
| 78 | POST | `/api/notifications/{id}/read` | JWT + tenant | Mark single as read |
| 79 | POST | `/api/notifications/read-all` | JWT + tenant | Mark all as read |
| 80 | POST | `/api/notifications` | JWT + tenant | Create notification (broadcast or targeted) |

---

## 4. Auth — Detailed Endpoints

### `POST /api/auth/signup`
**No auth required.** Creates a new academy tenant.

**Request:**
```json
{
  "name": "My Academy",
  "email": "admin@myacademy.com",
  "password": "securepassword"
}
```

**Response `201`:**
```json
{
  "academy_id": "uuid-string",
  "name": "My Academy"
}
```

**Side effects:** Creates Academy, AcademySettings (DZD, 30-day plans, light theme, French), Subscription (starter, active), and 4 default PaymentPlans:
- Monthly — 3,500 DA (30 days)
- Monthly — 3,000 DA (30 days)
- Term — 9,000 DA (90 days)
- Term — 8,000 DA (90 days)

---

### `POST /api/auth/login`
**No auth required.** Owner login with email + password.

**Request:**
```json
{
  "email": "admin@myacademy.com",
  "password": "securepassword"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user_id": "uuid",
  "name": "Admin Name",
  "role": "owner",
  "academy_id": "uuid"
}
```

**Claims in JWT:** `{ academy_id, role }`

---

### `POST /api/auth/create-owner`
**No JWT, but `X-Academy-Id` header required.** Bootstrap endpoint — can only be called once per academy.

**Request:**
```json
{
  "academy_id": "uuid",
  "name": "Admin Name",
  "email": "admin@myacademy.com",
  "password": "securepassword",
  "pin": "1234"
}
```

**Response `201`:**
```json
{
  "id": "uuid",
  "name": "Admin Name",
  "role": "owner",
  "academy_id": "uuid"
}
```

**Error `409`:** `{ "error": "Owner already exists for this academy" }`

---

### `POST /api/auth/verify-pin`
**No JWT.** PIN-based authentication for the profile picker.

**Request:**
```json
{
  "user_id": "uuid",
  "pin": "1234"
}
```
**Headers:** `X-Academy-Id: <academy_id>` (validates profile belongs to this academy)

**Response `200`:**
```json
{
  "access_token": "eyJ...",
  "user_id": "uuid",
  "name": "Staff Name",
  "role": "staff",
  "academy_id": "uuid"
}
```

---

### `GET /api/auth/profiles`
**JWT required.** Returns all active profiles for the profile picker.

**Response `200`:**
```json
{
  "profiles": [
    {
      "id": "uuid",
      "name": "Admin",
      "role": "owner",
      "picture": null,
      "avatar_color_1": null,
      "avatar_color_2": null
    }
  ]
}
```

---

### `GET /api/auth/me`
**JWT required.** Returns the current authenticated user's profile.

**Response `200`:**
```json
{
  "id": "uuid",
  "name": "Admin Name",
  "email": "admin@myacademy.com",
  "phone": "+213555123456",
  "role": "owner",
  "academy_id": "uuid",
  "picture": null,
  "is_active": true
}
```

---

### `POST /api/auth/change-pin`
**JWT required.** Change own PIN.

**Request:**
```json
{
  "old_pin": "1234",
  "new_pin": "5678"
}
```

**Response `200`:** `{ "message": "PIN changed successfully" }`

---

### `POST /api/auth/create-profile`
**JWT required + owner role + owner PIN verification.** Create staff profiles.

**Request:**
```json
{
  "name": "New Staff",
  "pin": "1234",
  "phone": "+21355599999",
  "role": "staff",
  "owner_pin": "5678"
}
```

**Response `201`:**
```json
{
  "id": "uuid",
  "name": "New Staff",
  "role": "staff"
}
```

---

## 5. Students — Detailed Endpoints

### `GET /api/students`
List all students with computed billing status.

**Query params:** `page` (default 1), `per_page` (default 50)

**Response `200`:**
```json
{
  "students": [
    {
      "id": "uuid",
      "first_name": "Karim",
      "last_name": "Benali",
      "full_name": "Karim Benali",
      "phone": "+213555123456",
      "parent_phone": "+213555789012",
      "notes": null,
      "status": "paid",
      "classes": "Math CM2, French CM2",
      "plan": "Monthly — 3,500 DA",
      "plan_amount": 3500,
      "renews": "12d",
      "created_at": "2026-01-15T10:00:00"
    }
  ],
  "total": 42,
  "page": 1,
  "pages": 1
}
```

**Status derivation:** `status` comes from the latest `StudentBilling` record:
- `"paid"` — paid and cycle not expired
- `"due"` — cycle expired, not yet overdue
- `"overdue"` — past due_date

---

### `POST /api/students`
**Request:**
```json
{
  "first_name": "Karim",
  "last_name": "Benali",
  "phone": "+213555123456",
  "parent_phone": "+213555789012",
  "notes": "Takes math tutoring"
}
```

**Side effects:**
1. Creates Student record
2. Creates default Guardian named "Parent" with parent_phone
3. Creates default StudentBilling with status=paid, amount=0
4. Creates ActivityLog entry

---

### `GET /api/students/{id}`
**Returns full profile drawer data** including guardians, active enrollments, and billing calendar (last 4 weeks).

---

### `POST /api/students/{id}/enroll`
**Request:** `{ "class_id": "uuid" }`

Creates an Enrollment record (or returns existing if already enrolled).

---

## 6. Teachers — Detailed Endpoints

### `GET /api/teachers`
Lists all teachers with computed fields:
- `classes_assigned` — array of class names
- `sessions_this_week` — count of sessions this week

---

### `GET /api/teachers/{id}`
Returns full teacher detail with:
- `schedule` — all sessions sorted by date/time
- `payroll_summary` — current month payroll, hours this week, active students (for per-student contracts)

---

### `POST /api/teachers`
**Request:**
```json
{
  "first_name": "Amina",
  "last_name": "Hassani",
  "phone": "+213555333333",
  "subject": "Math",
  "contract_type": "hourly",
  "hourly_rate": 1500,
  "per_student_rate": 0
}
```

**Defaults:** `contract_type="hourly"`, `hourly_rate=0`

---

## 7. Classes — Detailed Endpoints

### `GET /api/classes`
Returns classes with enrollment status dots:
- **Red** — class is at/over capacity
- **Green** — has students
- **Grey** — empty

### `GET /api/classes/{id}`
Returns full class detail with schedules and enrollment count.

### `POST /api/classes/{id}/schedules`
Creates a recurring weekly schedule block and **auto-generates 12 weeks of sessions**.

**Request:**
```json
{
  "day_of_week": 1,
  "start_time": "08:00",
  "end_time": "10:00",
  "classroom_id": "uuid-optional"
}
```

**Response `201`:**
```json
{
  "id": "uuid",
  "day_of_week": 1,
  "start_time": "08:00",
  "end_time": "10:00",
  "sessions_created": 12
}
```

---

## 8. Calendar — Detailed Endpoints

### `GET /api/calendar/week`
**Query:** `?date=2026-09-09` (defaults to today)

Returns all sessions Sunday–Saturday of the week containing the given date.

### `GET /api/calendar/day`
**Query:** `?date=2026-09-09` (defaults to today)

Returns all sessions for a specific day.

### `POST /api/sessions`
Create a new session (manual or drag-to-create).

**Request:**
```json
{
  "class_id": "uuid",
  "date": "2026-09-15",
  "start_time": "08:00",
  "end_time": "10:00",
  "teacher_id": "uuid-optional",
  "classroom_id": "uuid-optional",
  "subject": "Math"
}
```

**Behavior:** Times are snapped to 5-minute grid. Teacher and subject are denormalized from Class if not provided.

### `PATCH /api/sessions/{id}`
Update session times (drag-to-move / edge-resize). Only works on `status="scheduled"` sessions.

**Request:** `{ "date": "2026-09-16", "start_time": "09:00", "end_time": "11:00" }`

### `DELETE /api/sessions/{id}`
Cancels a session (sets `status="cancelled"`).

### `GET /api/sessions/{id}/roster`
Returns the student roster with attendance status for a session.

### `POST /api/sessions/{id}/roster`
Add a student to the session roster. Idempotent (returns 200 if already exists).

---

## 9. Attendance — Detailed Endpoints

### `POST /api/attendance/check-in`
**PIN-verified** (uses `@verify_staff_pin` decorator). Marks student as present.

**Request:**
```json
{
  "session_id": "uuid",
  "student_id": "uuid",
  "pin": "1234"
}
```

**Response `200`:**
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "is_present": true,
  "checked_in_at": "2026-09-09T08:05:00",
  "checked_in_by": "staff-uuid"
}
```

### `POST /api/attendance/check-out`
**Request:** `{ "session_id": "uuid", "student_id": "uuid" }`

### `POST /api/attendance/auto-checkout`
**Request:** `{ "session_id": "uuid" }`

Checks out all present students who haven't been checked out yet. Typically called by cron job at class end time.

### `GET /api/attendance/roster/{session_id}`
Full roster with attendance and payment status.

---

## 10. Billing — Detailed Endpoints

### `GET /api/billing/plans`
Lists all payment plans sorted by amount.

### `POST /api/billing/plans`
**Request:**
```json
{
  "name": "Monthly — 4,000 DA",
  "duration_days": 30,
  "amount_da": 4000
}
```

### `GET /api/billing/students`
**Query params:** `?student_id=uuid&status=paid`

### `POST /api/billing/record-payment`
**Request:**
```json
{
  "billing_id": "uuid",
  "amount": 3500,
  "payment_method": "cash",
  "notes": "Full payment"
}
```

**Side effects:** Creates PaymentLog, updates StudentBilling (paid_amount, status), creates ActivityLog.

**Response `200`:**
```json
{
  "billing_id": "uuid",
  "amount_paid": 3500,
  "total_paid": 3500,
  "status": "paid"
}
```

### `GET /api/billing/stats`
Returns donut ring data for both student billing and teacher payroll:

```json
{
  "student_billing": { "paid": 30, "due": 8, "overdue": 4 },
  "teacher_payroll": { "pending": 3, "settled": 2, "overdue": 0 }
}
```

### `GET /api/billing/revenue-chart`
**Query:** `?months=6`

### `GET /api/billing/aging-buckets`
Returns overdue accounts in 3 buckets: `recent` (1-7d), `aging` (8-30d), `critical` (30d+)

### `POST /api/billing/check-overdue`
Marks billings past their due_date as "overdue". Cron job endpoint.

### `POST /api/billing/renew-cycles`
Creates new billing records for students whose cycles have expired. Cron job endpoint.

### `GET /api/billing/payroll`
**Query:** `?teacher_id=uuid`

### `POST /api/billing/payroll/settle/{payroll_id}`
Marks a payroll record as settled (paid).

---

## 11. Analytics — Detailed Endpoints

### `GET /api/analytics/dashboard`
Returns comprehensive dashboard data:

```json
{
  "total_students": 42,
  "total_teachers": 8,
  "total_classes": 6,
  "today_sessions": 3,
  "week_sessions": 18,
  "monthly_income": 145000,
  "billing": {
    "student_billing": { "paid": 30, "due": 8, "overdue": 4 },
    "teacher_payroll": { "pending": 3, "settled": 2, "overdue": 0 }
  }
}
```

### `GET /api/analytics/export/{dataset}`
Supported datasets: `students`, `billing`, `teacher_hours`, `chart_data`

Returns CSV with `Content-Disposition: attachment` header.

---

## 12. Settings — Detailed Endpoints

### Academy Settings
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/settings/academy` | Any authenticated user | Read academy info |
| PUT | `/api/settings/academy` | Owner only | Update name, phone, email, address, weekend_day, current_term |

### Appearance
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/settings/appearance` | Any authenticated user | theme, font_size, language |
| PUT | `/api/settings/appearance` | Any authenticated user | Update theme, font_size, language |

### Billing Config
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/settings/billing-config` | Owner only | currency, plan_duration, reminder settings, whatsapp template |
| PUT | `/api/settings/billing-config` | Owner only | Update billing config |

### Automations
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/settings/automations` | Owner only | auto_checkout, end_class_popup, tier |
| PUT | `/api/settings/automations` | Owner only | Update automations (requires Pro/Scaler tier) |

### Staff Management
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/settings/staff` | Owner only | List all staff profiles |
| POST | `/api/settings/staff` | Owner only + owner PIN | Add staff (body: `{ name, pin, phone?, role?, owner_pin }`) |
| PUT | `/api/settings/staff/{id}` | Owner only | Update staff (name, phone, role) |
| POST | `/api/settings/staff/{id}/deactivate` | Owner only | Soft-delete (sets is_active=false). Cannot deactivate owners. |

### Profile
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/settings/profile` | Any authenticated user | Current user profile |
| PUT | `/api/settings/profile` | Any authenticated user | Update name, phone, email |

### Subscription
| Method | Path | Access | Description |
|---|---|---|---|
| GET | `/api/settings/subscription` | Owner only | tier, status, invoicing_method, dates |

---

## 13. Notifications — Detailed Endpoints

### `GET /api/notifications`
**Query:** `?unread_only=true`

Returns notifications for the current user (user-specific + broadcasts). Limited to 50, ordered by newest first.

### `GET /api/notifications/unread-count`
Returns `{ "unread_count": 5 }`

### `POST /api/notifications/{id}/read`
Marks a single notification as read.

### `POST /api/notifications/read-all`
Marks all user's notifications as read.

### `POST /api/notifications`
**Request:**
```json
{
  "type": "payment_reminder",
  "title": "Payment Due",
  "message": "Karim Benali's payment is due tomorrow",
  "detail": "Monthly plan — 3,500 DA",
  "user_id": "uuid-or-null-for-broadcast",
  "actions": [{ "label": "View", "variant": "primary" }]
}
```

**Types:** `payment_reminder`, `class_ending`, `enrollment_request`, `overdue_alert`, `general`

---

## 14. SQLAlchemy Data Models

### Entity Relationship Diagram (Textual)

```
Academy (1) ──── (N) User
Academy (1) ──── (N) Student
Academy (1) ──── (N) Teacher
Academy (1) ──── (N) Classroom
Academy (1) ──── (N) Class
Academy (1) ──── (N) Session
Academy (1) ──── (N) PaymentPlan
Academy (1) ──── (N) Subject
Academy (1) ──── (N) ActivityLog
Academy (1) ──── (N) Notification
Academy (1) ──── (1) AcademySettings
Academy (1) ──── (1) Subscription

Student (1) ──── (N) Guardian
Student (1) ──── (N) Enrollment ──── (N) Class
Student (1) ──── (N) SessionStudent ──── (N) Session
Student (1) ──── (N) StudentBilling ──── (N) PaymentLog

Teacher (1) ──── (N) Class
Teacher (1) ──── (N) Session
Teacher (1) ──── (N) TeacherPayroll
Teacher (1) ──── (N) TeacherHoursLog ──── (N) Session

Class (1) ──── (N) Schedule ──── (N) Session
Class (1) ──── (N) Enrollment
Class (1) ──── (N) Session
Class (N) ──── (1) Teacher

Schedule (1) ──── (N) Session
Schedule (N) ──── (1) Classroom
```

### Table: `academies`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `name` | String(255) | Academy name |
| `phone` | String(30) | Nullable |
| `email` | String(255) | Nullable |
| `address` | String(500) | Nullable |
| `weekend_day` | Integer | Default 5 (Friday for Algeria) |
| `current_term` | String(100) | e.g., "2026 — Fall term" |
| `created_at` | DateTime | UTC |
| `updated_at` | DateTime | UTC, auto-updates |

### Table: `academy_settings`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | Unique |
| `currency` | String(10) | Default "DZD" |
| `default_plan_duration` | Integer | Default 30 (days) |
| `billing_reminder_days_before` | Integer | Default 3 |
| `due_date_reminder_timing` | Enum("same_day","custom") | |
| `whatsapp_template` | Text | Nullable |
| `auto_checkout_enabled` | Boolean | Default true |
| `end_class_popup_enabled` | Boolean | Default true |
| `default_theme` | Enum("light","dark") | |
| `default_font_size` | Enum("normal","large") | |
| `default_language` | Enum("fr","ar") | |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### Table: `subscriptions`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | Unique |
| `tier` | Enum("starter","pro","scaler") | Default "starter" |
| `status` | Enum("active","inactive","trialing") | Default "active" |
| `invoicing_method` | String(50) | Default "Manual" |
| `started_at` | DateTime | |
| `expires_at` | DateTime | Nullable |
| `created_at` | DateTime | |

### Table: `users`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `name` | String(255) | Display name |
| `email` | String(255) | Required for owners, empty for staff |
| `phone` | String(30) | Nullable |
| `role` | Enum("owner","staff") | |
| `pin_hash` | String(255) | bcrypt hash of 4-digit PIN |
| `password_hash` | String(255) | bcrypt hash, owner only |
| `picture` | JSON | `{ type: 'preset', colors: [...] }` or `{ type: 'upload', dataUrl: '...' }` |
| `avatar_color_1` | String(7) | Legacy gradient start |
| `avatar_color_2` | String(7) | Legacy gradient end |
| `is_active` | Boolean | Default true |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

**Methods:** `hash_pin()`, `verify_pin()`, `set_pin()`, `hash_password()`, `verify_password()`, `set_password()`

### Table: `students`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `first_name` | String(255) | |
| `last_name` | String(255) | |
| `phone` | String(30) | Student's own phone |
| `parent_phone` | String(30) | Primary parent emergency number |
| `notes` | Text | |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

**Property:** `full_name` → `"{first_name} {last_name}"`

### Table: `guardians`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `student_id` | String(36) FK→students | |
| `name` | String(255) | |
| `relationship_type` | String(100) | Free-form: "Mother", "Father", etc. |
| `phone` | String(30) | |
| `is_emergency` | Boolean | Default false |
| `created_at` | DateTime | |

### Table: `enrollments`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `student_id` | String(36) FK→students | |
| `class_id` | String(36) FK→classes | |
| `enrolled_at` | DateTime | |
| `status` | Enum("active","withdrawn") | Default "active" |
| `created_at` | DateTime | |

### Table: `teachers`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `first_name` | String(255) | |
| `last_name` | String(255) | |
| `phone` | String(30) | Nullable |
| `subject` | String(100) | Primary subject |
| `notes` | Text | |
| `contract_type` | Enum("hourly","per_student") | Default "hourly" |
| `hourly_rate` | Integer | DA per hour |
| `per_student_rate` | Integer | DA per student |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### Table: `teacher_payrolls`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `teacher_id` | String(36) FK→teachers | |
| `period_start` | Date | |
| `period_end` | Date | |
| `total_hours` | Numeric(8,2) | Sum of logged hours |
| `total_students` | Integer | Active student count |
| `rate_applied` | Integer | Rate used for calculation |
| `calculated_amount` | Integer | hours×rate OR students×rate |
| `status` | Enum("pending","settled","overdue") | |
| `paid_date` | Date | Nullable |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### Table: `teacher_hours_logs`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `teacher_id` | String(36) FK→teachers | |
| `session_id` | String(36) FK→sessions | |
| `hours` | Numeric(6,2) | Duration in hours |
| `logged_by` | String(36) FK→users | |
| `created_at` | DateTime | |

### Table: `classrooms`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `name` | String(255) | |
| `capacity` | Integer | Default 0 |
| `created_at` | DateTime | |

### Table: `classes`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `name` | String(255) | e.g., "Math CM2" |
| `subject` | String(100) | Extensible (Math, French, English, Science) |
| `color` | String(7) | Hex color for calendar palette |
| `teacher_id` | String(36) FK→teachers | Nullable |
| `capacity` | Integer | Default 30 |
| `notes` | Text | |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### Table: `subjects`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `name` | String(100) | |
| `color` | String(7) | Default "#b3872a" |
| `created_at` | DateTime | |

### Table: `schedules`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `class_id` | String(36) FK→classes | |
| `classroom_id` | String(36) FK→classrooms | Nullable |
| `day_of_week` | Integer | 0=Sun, 1=Mon, ..., 6=Sat |
| `start_time` | Time | |
| `end_time` | Time | |
| `created_at` | DateTime | |

### Table: `sessions`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `class_id` | String(36) FK→classes | |
| `schedule_id` | String(36) FK→schedules | Null for custom sessions |
| `teacher_id` | String(36) FK→teachers | Denormalized from Class |
| `classroom_id` | String(36) FK→classrooms | Denormalized from Schedule |
| `date` | Date | |
| `start_time` | Time | |
| `end_time` | Time | |
| `subject` | String(100) | Denormalized from Class |
| `status` | Enum("scheduled","in_progress","completed","cancelled") | |
| `created_at` | DateTime | |

### Table: `session_students`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `session_id` | String(36) FK→sessions | |
| `student_id` | String(36) FK→students | |
| `is_present` | Boolean | Default false |
| `checked_in_at` | DateTime | Nullable |
| `checked_out_at` | DateTime | Nullable |
| `checked_in_by` | String(36) FK→users | Nullable |
| `payment_status` | Enum("paid","due","overdue") | Denormalized snapshot |
| `created_at` | DateTime | |

### Table: `payment_plans`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `name` | String(255) | e.g., "Monthly — 3,500 DA" |
| `duration_days` | Integer | 30 or 90 |
| `amount_da` | Integer | Price in DA |
| `created_at` | DateTime | |

### Table: `student_billings`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `student_id` | String(36) FK→students | |
| `payment_plan_id` | String(36) FK→payment_plans | |
| `amount_da` | Integer | Amount due |
| `status` | Enum("paid","due","overdue") | |
| `due_date` | Date | |
| `paid_date` | Date | Nullable |
| `paid_amount` | Integer | Nullable, may be partial |
| `cycle_start` | Date | |
| `cycle_end` | Date | |
| `notes` | Text | |
| `created_at` | DateTime | |
| `updated_at` | DateTime | |

### Table: `payment_logs`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `student_billing_id` | String(36) FK→student_billings | |
| `amount_da` | Integer | Amount paid in this transaction |
| `payment_method` | String(50) | "cash", "bank transfer", etc. |
| `recorded_by` | String(36) FK→users | |
| `notes` | Text | |
| `created_at` | DateTime | |

### Table: `activity_logs`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `user_id` | String(36) FK→users | |
| `entity_type` | String(50) | "student", "teacher", "class", "session", "billing", "payment" |
| `entity_id` | String(36) | |
| `action` | String(50) | "created", "updated", "deleted", "checked_in", "checked_out", "payment_received", "payment_overdue", "enrolled", "withdrawn" |
| `description` | Text | Human-readable |
| `metadata` | JSON | Contextual data |
| `created_at` | DateTime | |

### Table: `notifications`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `academy_id` | String(36) FK→academies | |
| `user_id` | String(36) FK→users | Null = broadcast to all |
| `type` | Enum("payment_reminder","class_ending","enrollment_request","overdue_alert","general") | |
| `title` | String(255) | |
| `message` | String(500) | |
| `detail` | Text | |
| `actions` | JSON | Array of `{ label, variant }` |
| `is_read` | Boolean | Default false |
| `created_at` | DateTime | |

---

## 15. Access Control & Decorators

### `@tenant_required`
Verifies:
1. JWT token is valid
2. `X-Academy-Id` header is present
3. Authenticated user belongs to the specified academy
4. User is active

Sets `g.current_user`, `g.current_academy_id`, `g.current_academy`.

### `@owner_only`
Must be used after `@tenant_required`. Checks `g.current_user.role == "owner"`.

### `@verify_staff_pin`
Expects `pin` in JSON request body. Verifies against `g.current_user.verify_pin(pin)`.

---

## 16. Frontend ↔ Backend Gap Analysis

### Backend routes that the frontend DOES NOT use

These endpoints exist in the backend but have **no corresponding `api.*()` call** in the frontend code:

| Route | Method | Notes |
|---|---|---|
| `/api/auth/profiles` | GET | Profile picker — may be used by a component not yet wired |
| `/api/auth/change-pin` | POST | PIN change flow not built |
| `/api/auth/create-profile` | POST | Staff creation via auth flow not built |
| `/api/students/stats` | GET | Stats rail data |
| `/api/students/{id}` | GET | Profile drawer detail |
| `/api/students/{id}/enroll` | POST | Enrollment action |
| `/api/students/{id}/guardians` | GET/POST | Guardian management |
| `/api/teachers/stats` | GET | Stats rail data |
| `/api/teachers/{id}` | GET | Profile drawer detail |
| `/api/classrooms` | GET/POST | Classroom CRUD |
| `/api/classes/{id}` | GET | Class detail |
| `/api/classes/{id}/schedules` | POST | Schedule management |
| `/api/calendar/week` | GET | Week calendar view |
| `/api/calendar/day` | GET | Day calendar view |
| `/api/sessions` | POST | Create session |
| `/api/sessions/{id}` | PATCH | Update session |
| `/api/sessions/{id}` | DELETE | Cancel session |
| `/api/sessions/{id}/roster` | GET/POST | Session roster |
| `/api/attendance/*` | ALL | Entire attendance blueprint unused |
| `/api/billing/plans` | GET/POST | Payment plan management |
| `/api/billing/students` | GET | Billing records |
| `/api/billing/record-payment` | POST | Payment recording |
| `/api/billing/aging-buckets` | GET | Aging analysis |
| `/api/billing/check-overdue` | POST | Overdue check |
| `/api/billing/renew-cycles` | POST | Cycle renewal |
| `/api/billing/payroll` | GET | Payroll records |
| `/api/billing/payroll/settle/{id}` | POST | Payroll settlement |
| `/api/analytics/dashboard` | GET | Dashboard stats |
| `/api/analytics/revenue-chart` | GET | Revenue chart |
| `/api/analytics/export/{dataset}` | GET | CSV export |
| `/api/settings/academy` | GET/PUT | Academy settings (uses `/academy` instead) |
| `/api/settings/appearance` | GET/PUT | Theme settings (uses `/settings` instead) |
| `/api/settings/billing-config` | GET/PUT | Billing config |
| `/api/settings/automations` | GET/PUT | Automation settings |
| `/api/settings/staff` | GET/POST | Staff management (uses `/staff` instead) |
| `/api/settings/staff/{id}` | PUT | Staff update |
| `/api/settings/profile` | GET/PUT | Profile settings |
| `/api/settings/subscription` | GET | Subscription info |
| `/api/notifications` | ALL | Entire notifications blueprint unused |
| `/api/subjects` | GET/POST | Subject palette |

### Frontend calls that the backend DOES NOT have

| Frontend Call | Method | Backend Equivalent | Gap |
|---|---|---|---|
| `POST /auth/refresh` | POST | ❌ **MISSING** | Token refresh endpoint does not exist. Frontend interceptor will fail on expired tokens. |
| `GET /sessions` | GET | ❌ **MISSING** | Frontend calls `GET /sessions` directly. Backend has `GET /api/calendar/week` and `GET /api/calendar/day` instead. |
| `GET /sessions/{id}/students` | GET | ❌ **MISSING** | Frontend expects session students at `/sessions/{id}/students`. Backend has `/api/sessions/{id}/roster` and `/api/attendance/roster/{id}`. |
| `PATCH /sessions/{id}/students/{sid}/presence` | PATCH | ❌ **MISSING** | Frontend toggles presence via PATCH. Backend uses `POST /api/attendance/check-in` and `POST /api/attendance/check-out`. |
| `PATCH /sessions/{id}/students/{sid}/payment` | PATCH | ❌ **MISSING** | Frontend toggles per-session payment status. No backend route for this. |
| `GET /academy` | GET | ⚠️ **WRONG PATH** | Frontend calls `GET /academy`. Backend has `GET /api/settings/academy`. |
| `PATCH /academy` | PATCH | ⚠️ **WRONG PATH/METHOD** | Frontend calls `PATCH /academy`. Backend has `PUT /api/settings/academy` (PUT, not PATCH). |
| `GET /settings` | GET | ⚠️ **WRONG PATH** | Frontend calls `GET /settings`. Backend has `GET /api/settings/appearance`. |
| `PATCH /settings` | PATCH | ⚠️ **WRONG PATH/METHOD** | Frontend calls `PATCH /settings`. Backend has `PUT /api/settings/appearance` (PUT, not PATCH). |
| `GET /staff` | GET | ⚠️ **WRONG PATH** | Frontend calls `GET /staff`. Backend has `GET /api/settings/staff`. |
| `PATCH /staff/{id}/deactivate` | PATCH | ⚠️ **WRONG PATH/METHOD** | Frontend calls `PATCH /staff/{id}/deactivate`. Backend has `POST /api/settings/staff/{id}/deactivate` (POST, not PATCH). |
| `GET /billing/revenue` | GET | ⚠️ **WRONG PATH** | Frontend calls `GET /billing/revenue`. Backend has `GET /api/billing/revenue-chart`. |
| `GET /billing/stats` | GET | ✅ EXISTS | Frontend calls `GET /billing/stats`. Backend has `GET /api/billing/stats`. |

### Summary of Critical Gaps

1. **`POST /auth/refresh`** — Token refresh is broken. The frontend's Axios interceptor will redirect to login on every 401 since the refresh endpoint doesn't exist.

2. **`GET /sessions`** — The entire calendar and dashboard rely on fetching sessions, but the frontend calls a flat `/sessions` endpoint. Backend provides `/calendar/week` and `/calendar/day` instead.

3. **Session student management** — Frontend expects REST-style CRUD on `/sessions/{id}/students`, while backend provides attendance-specific `/attendance/check-in`, `/attendance/check-out`, and `/sessions/{id}/roster`.

4. **Per-session payment toggle** — `PATCH /sessions/{id}/students/{sid}/payment` has no backend implementation.

5. **Settings path mismatch** — Frontend uses top-level paths (`/academy`, `/settings`, `/staff`) while backend nests them under `/settings/`.

6. **HTTP method mismatch** — Frontend uses PATCH for updates, backend uses PUT in many cases.

7. **Revenue endpoint** — Frontend calls `/billing/revenue`, backend exposes `/billing/revenue-chart`.

8. **SocketIO** — Initialized in `extensions.py` but no WebSocket event handlers are registered anywhere.
