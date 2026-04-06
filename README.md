# Tardigrade Backend# Coaching Management System Backend API



## Prerequisites## Project Overview

- Python 3.11+ (recommended)This backend provides REST APIs for a Coaching Management System.

- PostgreSQL (local or remote)

### Tech Stack

## Setup- Flask

1. Create a virtual environment and install dependencies from `backend/requirements.txt`.- Flask-SQLAlchemy

2. Create `backend/.env` with at least:- Flask-Migrate

   - `DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB_NAME`- PostgreSQL

   - `SECRET_KEY=change-me`- JWT Authentication (`Flask-JWT-Extended`)

   - `JWT_SECRET_KEY=change-me`- Role-Based Access Control (RBAC)

   - `GOOGLE_CLIENT_ID` (optional)- Flasgger (Swagger UI)
  - `RAZORPAY_KEY_ID` (optional, for online fee payments)
  - `RAZORPAY_KEY_SECRET` (optional, for online fee payments)

3. Initialize the database (optional but recommended):- API Versioning with `/api/v1`

   - `flask init-db`

4. Seed sample users (optional):### Response Contract

   - `flask seed-data`All API responses follow this format:



## Run```json

- Start the API server:{

  - `python run.py`  "success": true,

  "message": "string",

The API runs on `http://localhost:5000` by default.  "data": {}

}
```

---

## Base URL
- Local Server: `http://localhost:5000`
- API Prefix: `/api/v1`

> Recommended frontend env variable:
> - `VITE_API_BASE_URL=http://localhost:5000`
> or
> - `NEXT_PUBLIC_API_BASE_URL=http://localhost:5000`

---

## Authentication Guide
This API uses JWT Bearer Tokens.

### 1) Register or Login
Use:
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/google`

Google login requires:
- `GOOGLE_CLIENT_ID` in backend `.env`
- `VITE_GOOGLE_CLIENT_ID` in frontend `.env`

### 2) Store `access_token`
Persist securely on frontend (memory/session storage preferred over localStorage for stricter security needs).

### 3) Send token in requests
Header format:

```http
Authorization: Bearer <access_token>
```

### 4) Handle auth errors
- `401 Unauthorized` → Missing/invalid/expired token
- `403 Forbidden` → Authenticated but role not permitted

---

## Swagger API Docs

- Swagger UI: `GET /apidocs/`
- OpenAPI JSON: `GET /apispec_1.json`

### Swagger JWT Usage
1. Open `/apidocs/`
2. Click **Authorize**
3. Enter: `Bearer <access_token>`
4. Run protected APIs directly from Swagger

---

## CLI Commands

- `flask init-db` → Creates database tables for local bootstrap.
- `flask seed-data` → Seeds default users and sample data.

### `flask seed-data` creates/updates
- Admin user: `admin@test.com / Admin@123`
- Director user: `director@test.com / Director@123`
- Student user: `student@test.com / Student@123`
- Coach user: `coach@test.com / Coach@123`
- Student profile for seeded student
- Teacher profile for seeded coach
- Optional sample batch (`Foundation Demo` for current year)

Options:
- `flask seed-data --with-batch` (default)
- `flask seed-data --no-batch`

---

## Endpoints

## Public Routes

### `GET /`
Returns API landing response.

### `GET /api/v1`
Returns API root status.

### `GET /api/v1/health`
Basic health check.

### `POST /api/v1/auth/register`
Create user account.

Request body:

```json
{
  "full_name": "string",
  "email": "string",
  "password": "string",
  "role": "admin | director | manager | coach | student | parent"
}
```

### `POST /api/v1/auth/login`
Authenticate user and get access token.

Request body:

```json
{
  "email": "string",
  "password": "string"
}

### `POST /api/v1/auth/google`
Authenticate user via Google ID token.

Request body:

```json
{
  "credential": "google_id_token"
}
```
```

---

## JWT Protected Routes

### `GET /api/v1/auth/me`
Get current authenticated user details.

### `GET /api/v1/auth/protected`
Protected test route.

### Student CRUD
- `GET /api/v1/students`
- `GET /api/v1/students/<student_id>`
- `PUT /api/v1/students/<student_id>`
- `DELETE /api/v1/students/<student_id>`

### Batch CRUD
- `GET /api/v1/batches`
- `GET /api/v1/batches/<batch_id>`

### Teacher CRUD
- `GET /api/v1/teachers`
- `GET /api/v1/teachers/<teacher_id>`

### Batch-Teacher Assignment
- `GET /api/v1/batches/<batch_id>/teachers`
## Batch Portal Resources

Teachers/coaches can curate resources for each batch.

- `GET /api/v1/batches/<batch_id>/resources` (students see only visible items)
- `POST /api/v1/batches/<batch_id>/resources`
- `PUT /api/v1/batch-resources/<resource_id>`
- `DELETE /api/v1/batch-resources/<resource_id>`

## Quizzes (AI & Manual)

- `POST /api/v1/quizzes/ai-generate`
- `POST /api/v1/quizzes`
- `GET /api/v1/batches/<batch_id>/quizzes`
- `GET /api/v1/quizzes/<quiz_id>`
- `PUT /api/v1/quizzes/<quiz_id>`
- `PUT /api/v1/quizzes/<quiz_id>/questions`
- `POST /api/v1/quizzes/<quiz_id>/publish`
- `POST /api/v1/quizzes/<quiz_id>/close`
- `POST /api/v1/quizzes/<quiz_id>/submit`
- `GET /api/v1/teachers/<teacher_id>/batches`

### Attendance Module
- `GET /api/v1/attendance`
- `GET /api/v1/attendance/<attendance_id>`

### Fee Management Module
- `GET /api/v1/fees`
- `GET /api/v1/fees/<student_fee_id>`
- `GET /api/v1/fee-payments`

### Salary Module
- `GET /api/v1/salaries`
- `GET /api/v1/salaries/summary`

### Test & Results Module
- `GET /api/v1/tests`
- `GET /api/v1/test-results`
- `GET /api/v1/tests/performance-metrics`

### Reporting & Analytics Module
- `GET /api/v1/reports/monthly-attendance`
- `GET /api/v1/reports/revenue-by-month`
- `GET /api/v1/reports/salary-expense-by-month`
- `GET /api/v1/reports/batch-strength`
- `GET /api/v1/reports/active-vs-inactive`

---

## Role Protected Routes

### `GET /api/v1/auth/admin-only`
Required role: `admin`

### `GET /api/v1/auth/users-summary`
Returns total registered users and full admin list.

Required role: `admin`

### `GET /api/v1/auth/registered-users`
Returns all users who have registered so far.

Required role: `admin`

### Admin database console (full CRUD)
Admin-only endpoints that power the database dashboard:

- `GET /api/v1/admin/tables` → list available tables and schema metadata
- `GET /api/v1/admin/tables/<table_name>/rows` → list rows (supports `page`, `per_page`)
- `POST /api/v1/admin/tables/<table_name>/rows` → create a row
- `PUT /api/v1/admin/tables/<table_name>/rows` → update a row
- `DELETE /api/v1/admin/tables/<table_name>/rows` → delete a row

### Attendance management
- `POST /api/v1/attendance` → `coach` or `director`
- `PUT /api/v1/attendance/<attendance_id>` → `coach` or `director`
- `DELETE /api/v1/attendance/<attendance_id>` → `director`

### Fee management
- `POST /api/v1/fees` → `director` or `manager`
- `POST /api/v1/fee-payments` → `director` or `manager`
- `GET /api/v1/fees/revenue-report` → `director` or `manager`

### Salary management
- `POST /api/v1/salaries` → `director` or `manager`
- `PUT /api/v1/salaries/<salary_id>` → `director` or `manager`
- `GET /api/v1/salaries/summary` → `director` or `manager`

### Test & results management
- `POST /api/v1/tests` → `coach` or `director` or `manager`
- `POST /api/v1/test-results` → `coach` or `director` or `manager`

### Reporting & analytics
- `GET /api/v1/reports/monthly-attendance` → `admin` or `director` or `manager` or `coach`
- `GET /api/v1/reports/revenue-by-month` → `admin` or `director` or `manager`
- `GET /api/v1/reports/salary-expense-by-month` → `admin` or `director` or `manager`
- `GET /api/v1/reports/batch-strength` → `admin` or `director` or `manager` or `coach`
- `GET /api/v1/reports/active-vs-inactive` → `admin` or `director` or `manager`

### `POST /api/v1/students`
Required role: `director` or `manager`

### Batch management
- `POST /api/v1/batches` → `director` or `manager`
- `PUT /api/v1/batches/<batch_id>` → `director` or `manager`
- `DELETE /api/v1/batches/<batch_id>` → `director` or `manager`

### Teacher management
- `POST /api/v1/teachers` → `director` or `manager`
- `PUT /api/v1/teachers/<teacher_id>` → `director` or `manager`
- `DELETE /api/v1/teachers/<teacher_id>` → `director` only

### Batch-Teacher assignment management
- `POST /api/v1/batches/<batch_id>/teachers` → `director` or `manager`
- `DELETE /api/v1/batches/<batch_id>/teachers/<teacher_id>` → `director` or `manager`

---

## Example Requests & Responses

### Register
**Request**

```http
POST /api/v1/auth/register
Content-Type: application/json
```

```json
{
  "full_name": "John Director",
  "email": "john@example.com",
  "password": "StrongPass123",
  "role": "director"
}
```

**Success Response (201)**

```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user": {
      "id": 1,
      "email": "john@example.com",
      "full_name": "John Director",
      "role": "director"
    },
    "access_token": "<jwt_token>"
  }
}
```

### Login
**Request**

```http
POST /api/v1/auth/login
Content-Type: application/json
```

```json
{
  "email": "john@example.com",
  "password": "StrongPass123"
}
```

**Success Response (200)**

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "john@example.com",
      "full_name": "John Director",
      "role": "director"
    },
    "access_token": "<jwt_token>"
  }
}
```

### Protected Route Example
**Request**

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

---

## Error Handling Guide

### 400 Bad Request
Validation or payload issues.

Example:

```json
{
  "success": false,
  "message": "email and password are required",
  "data": {}
}
```

### 401 Unauthorized
Invalid token, expired token, or missing token.

### 403 Forbidden
Insufficient role permissions.

### 404 Not Found
Wrong endpoint path.

### 422 Unprocessable Entity
Invalid JWT format/content.

### 500 Internal Server Error
Unexpected server/database error.

---

## Frontend Integration Example (JavaScript `fetch`)

```js
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

export async function login(email, password) {
  const res = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  const json = await res.json();
  if (!res.ok || !json.success) {
    throw new Error(json.message || "Login failed");
  }

  const token = json.data?.access_token;
  localStorage.setItem("access_token", token);
  return json;
}

export async function getStudents() {
  const token = localStorage.getItem("access_token");

  const res = await fetch(`${API_BASE_URL}/api/v1/students`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  });

  const json = await res.json();

  if (res.status === 401) throw new Error("Unauthorized. Please login again.");
  if (res.status === 403) throw new Error("Forbidden. You do not have access.");
  if (!res.ok || !json.success) throw new Error(json.message || "Request failed");

  return json.data;
}
```

---

## Deployment Notes
- Do not use Flask dev server in production.
- Use a production WSGI server (e.g., Gunicorn behind Nginx).
- Set strong secrets in environment variables:
  - `SECRET_KEY`
  - `JWT_SECRET_KEY`
- Set a production-grade PostgreSQL URL in `DATABASE_URL`.
- Restrict CORS origins to trusted frontend domains.
- Run DB migrations during deployment:
  - `flask db migrate -m "..."`
  - `flask db upgrade`
- Enable HTTPS in all environments beyond local development.

---

## Handoff Notes
- Keep API base URL environment-driven in frontend.
- Always parse API responses using `success/message/data`.
- Centralize token handling and error interceptors in one HTTP utility.
- For team consistency, document route/response changes before merging.

> Implementation note: backend role constants include `admin`, `director`, `manager`, `coach`, `student`, and `parent`. If your frontend uses `teacher`, align role values with backend before release.

### Parent Access Scope
- `parent` role has read-only visibility for linked child records (attendance, fees/payments, tests/results).
- Parent write actions (attendance marking, marks entry, batch/salary management) are blocked by RBAC.
- Data scope is enforced server-side: parent can access only their linked child(ren).
