# Student Result Calculator Portal

A modern Flask-based Student Result Management System where users can:

- Create account
- Login securely
- Add subject-wise marks
- Calculate percentage automatically
- View previous results
- Store data permanently using Supabase
- Send messages through contact form

This project is built using Flask, HTML, CSS, and Supabase database.

---

## Features

- User Authentication
- Student Dashboard
- Subject-wise Result Management
- Percentage & Grade Calculation
- Previous Results History
- Contact Us Form
- Supabase Database Integration
- Modern Responsive UI

---

## Technologies Used

- Flask
- HTML5
- CSS3
- Supabase
- PostgreSQL
- Gunicorn
- Render

---

## Percentage Formula

Percentage is calculated using:

Percentage = (Obtained Marks / Total Marks) × 100

---

## Grade System

| Percentage | Grade |
|---|---|
| 90+ | A+ |
| 75+ | A |
| 60+ | B |
| 40+ | C |
| Below 40 | Fail |

---

## Project Structure

student-portal/
│
├── app.py
├── requirements.txt
├── Procfile
├── README.md
│
├── templates/
│   ├── login.html
│   ├── signup.html
│   └── dashboard.html
│
└── static/
    └── style.css

---

## Installation

```bash
pip install -r requirements.txt
