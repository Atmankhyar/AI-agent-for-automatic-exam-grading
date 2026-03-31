# 🤖 AI Agent for Automatic Exam Grading (ExamESICorrector)

An end-to-end automated pipeline for grading various types of exam questions (Multiple Choice, Open-Ended, and Code) using cutting-edge AI technologies. Built with an asynchronous microservices architecture utilizing FastAPI and Next.js.

![Project Status](https://img.shields.io/badge/Status-In%20Development-yellow?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Next.js](https://img.shields.io/badge/Next.js-black?style=for-the-badge&logo=next.js)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis)

## 📌 Features

- **Multi-format Grading:** Supports Multiple Choice Questions (MCQ), Open-Ended responses, and Programming code tasks.
- **AI-Powered Evaluation:** Leverages LLMs and OCR for processing handwritten text and evaluating nuanced answers.
- **Asynchronous Processing:** Built-in task queue management with Celery and Redis to handle heavy workloads at scale.

## 📁 Repository Structure

- `backend/` : Core API built with FastAPI, Celery background tasks, OCR/LLM analysis logic, and database schemas.
- `frontend/` : User portal built with Next.js (Work in progress).
- `infra/` : Docker configuration and infrastructure files.

## 🚀 Quickstart (Local Development)

### 1. Backend Setup
```bash
# Set up the environment file
cp backend/.env.example backend/.env

# Install Python dependencies
pip install -r backend/requirements.txt
```

### 2. Infrastructure Services
Start the PostgreSQL database and Redis cache:
```bash
docker compose up db redis -d
```

### 3. Run the Application
Apply the database migrations and start the FastAPI server:
```bash
# Run the FastAPI server natively (From the backend directory)
uvicorn app.main:app --reload --port 8000
```


