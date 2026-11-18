# 🎓 EduPath - AI-Powered Learning Platform

EduPath is a comprehensive, full-stack Learning Management System (LMS) built for students from Classes 5 to 12. It bridges the gap between students, teachers, and parents with AI-driven analytics, live interactive classes, and automated reporting.

Built with **Django**, **PostgreSQL**, and **Vanilla CSS/JS**, the platform is designed to be fast, responsive, and highly scalable.

---

## ✨ Key Features

### 🎓 For Students
*   **Interactive Learning:** Video lectures, chapter-wise quizzes, and file-based assignments.
*   **Live Classes:** Join Jitsi-powered live classes directly from the dashboard.
*   **Gamification:** Earn XP points, level up, and climb the global Leaderboard.
*   **AI Risk Predictor:** See personal performance status (Safe, Medium, High Risk) based on real-time attendance and quiz averages.
*   **Certificates:** Automatically generate and download verifiable PDF certificates upon 100% course completion.
*   **Report Cards:** Download a comprehensive PDF progress report.

### 👨‍🏫 For Teachers
*   **Command Center:** Full analytics on student performance, pending grading, and class averages.
*   **Live-Class Attendance:** Advanced heartbeat tracking to monitor exactly how long students stay in live classes.
*   **Revenue Dashboard:** Track earnings per course, view monthly charts, and download PDF payout statements.
*   **Class Reports:** Download a single PDF containing an overview of all students and their detailed individual progress.
*   **Course Management:** Add chapters, lectures, quizzes, and upload course thumbnails.

### 👨‍👩‍👧 For Parents
*   **Multi-Child Tracking:** Link multiple children to a single parent account.
*   **Deep Insights:** View attendance, recent quiz history, and AI risk statuses for each child.
*   **Automated Reports:** Download individual child report cards or a combined PDF for all linked children.

### 👨‍💼 For Admins
*   **Custom Dashboard:** Track platform-wide revenue, top-selling courses, and recent enrollments.
*   **Audit Logs:** Keep track of critical system actions.
*   **Full Control:** Manage users, courses, payments, and discussions via the Django Admin panel.

---

## 🛠️ Tech Stack

*   **Backend:** Python, Django 4.x
*   **Database:** SQLite (Local) / PostgreSQL (Production)
*   **PDF Generation:** ReportLab
*   **Live Video:** Jitsi Meet External API
*   **Frontend:** HTML5, Vanilla CSS, JavaScript (Chart.js for analytics)
*   **Deployment Ready:** WhiteNoise (static files), `dj-database-url` (Render compatible)

---

## 🚀 Local Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/edupath.git
cd edupath
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```
*(Ensure `reportlab`, `python-dotenv`, `dj-database-url`, and `whitenoise` are in your `requirements.txt`)*

### 4. Environment Variables
Create a `.env` file in the root directory:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
# Optional: Add Razorpay keys if testing payments
RAZORPAY_KEY_ID=your_key
RAZORPAY_KEY_SECRET=your_secret
```

### 5. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a Superuser (Admin)
```bash
python manage.py createsuperuser
```

---

## 🌱 Seeding Demo Data (Highly Recommended)

To instantly populate the platform with a fully functional environment (Teachers, Students, Parents, Courses, Payments, Live Classes, and Certificates), run the custom seeder:

```bash
python manage.py seed_demo
```

**Demo Credentials** (Password for all: `demo1234`):

*   **Teacher:** `t_priya` (Priya Sharma - Math)
*   **Student:** `s_aarav` (Aarav Patel - Class 8)
*   **Parent:** `p_nilesh` (Nilesh Patel - Linked to 2 children)

> **Note:** To wipe demo data and start fresh, run `python manage.py seed_demo --reset`

---

## 🖼️ Adding Course Images

To instantly download and attach professional images to all demo courses, run this in your terminal:

```bash
python manage.py shell
```

Then paste the image download script provided in the docs.

---

## 🏃‍♂️ Running the Application

```bash
python manage.py runserver
```

*   **Main Website:** http://127.0.0.1:8000/
*   **Django Admin:** http://127.0.0.1:8000/admin/
*   **Custom Admin Dashboard:** http://127.0.0.1:8000/dashboard/admin-dashboard/

---

## ☁️ Deployment Notes (Render)

This project is configured for deployment on Render.

*   The `settings.py` uses `dj_database_url` to automatically parse the `DATABASE_URL` provided by Render.
*   WhiteNoise is configured to serve static files seamlessly.
*   **Important:** Because Render's disk is ephemeral, media files (course images, submitted assignments) will be deleted upon server restart. For production, configure **AWS S3** or **Cloudinary** for media storage.

---

## 🔒 Security & Best Practices

*   All PDF generation (Certificates, Report Cards) is securely scoped. A parent can only download a report for a child explicitly linked to their account.
*   Live class attendance is tracked using a secure JavaScript heartbeat, preventing users from spoofing attendance.
*   Role-Based Access Control (RBAC) ensures students cannot access teacher revenue pages, and parents cannot join live classes.
