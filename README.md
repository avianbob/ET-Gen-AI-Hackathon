# ET PharmAI - Pharmaceutical Analysis Platform

A comprehensive pharmaceutical analysis platform consisting of a FastAPI backend and a React frontend (PharmAI) that provides intelligent pharmaceutical market research and analysis capabilities.

## VIDEO LINK: https://drive.google.com/file/d/1Xm_jLXXHV3IJCCvUA35PVe857PgI0Nxw/view?usp=sharing

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Project Structure](#project-structure)
- [Backend features map](#where-major-backend-features-live) 
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

## 🎯 Project Overview

ET PharmAI is an AI-powered pharmaceutical analysis platform that enables users to:
- Conduct comprehensive pharmaceutical market research
- Analyze drug molecules and compounds
- Generate detailed reports with insights
- Access demographic, market, patent, and clinical trial data
- Export analysis reports as PDFs

## 🏗️ Architecture

The project consists of two main components:

1. **backend (Backend)**: One FastAPI process hosts every capability—classic ET analysis (`/api/run-agent`, PDF export, clinical-trials helpers) and extended APIs (search, chat, knowledge base, files, auth, WebSocket progress). There is no separate backend service or second Uvicorn app in this repository.
2. **PharmAI (Frontend)**: React + Vite single-page application

```
┌─────────────────┐
│   PharmAI       │  React Frontend (Port 5173)
│   (Frontend)    │
└────────┬────────┘
         │ HTTP/REST + WebSocket
         │
┌────────▼────────┐
│     Backend     │  Single FastAPI app (Port 8000)
│   (Backend)     │
└─────────────────┘
         │
         ├── /api/run-agent, reports, tests (app/routes/agent_routes.py)
         ├── Extended REST under /api, /api/auth, /api/knowledge (app/routes/repurpose/)
         ├── WebSocket /ws/{session_id} (app/routes/repurpose/websocket.py)
         ├── LLM: Gemini, Groq, Ollama (app/services/repurpose/llm/, app/services/gemini_service.py)
         ├── Vector RAG: ChromaDB (app/services/repurpose/vector_store/)
         ├── Optional MongoDB + JWT auth (app/services/repurpose/database/, auth/)
         └── Optional Supabase (app/services/repurpose/database/supabase_client.py)
```

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (for backend)
- **Node.js 18+** and **npm** (for frontend)
- **Google Gemini API Key** ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Quick Start

### 1. Clone the Repository

```bash
cd "~/Downloads/ET-Gen-AI-Hackathon"
```

### 2. Backend Setup (backend)

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Environment Configuration section)
cp .env.example .env
# Edit .env with your configuration

# Run the backend server
python main.py
```

The backend will start on `http://localhost:8000` (or the port specified in your `.env` file).

### 3. Frontend Setup (PharmAI)

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file (see Environment Configuration section)
cp .env.example .env
# Edit .env with your configuration

# Start the development server
npm run dev
```

The frontend will start on `http://localhost:5173` (default Vite port).

### 4. Access the Application

Open your browser and navigate to:
```
http://localhost:5173
```

## ⚙️ Environment Configuration

### Backend (.env) - backend

**Step 1:** Navigate to the `backend` directory:

```bash
cd backend
```

**Step 2:** Create a `.env` file manually:

```bash
# On macOS/Linux:
touch .env

# On Windows:
# type nul > .env
```

**Step 3:** Open the `.env` file in a text editor and add the following content:

```env
# Server Configuration
PORT=8000
FRONTEND_URL=http://localhost:5173

# Google Gemini API Configuration
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here
```

**Required Variables:**
- `GEMINI_API_KEY`: Your Google Gemini API key (required) - Replace `your_gemini_api_key_here` with your actual API key
- `PORT`: Backend server port (default: 8000)
- `FRONTEND_URL`: Frontend URL for CORS configuration (default: http://localhost:5173)

### Frontend (.env) - PharmAI

**Step 1:** Navigate to the `frontend` directory:

```bash
cd frontend
```

**Step 2:** Create a `.env` file manually:

```bash
# On macOS/Linux:
touch .env

# On Windows:
# type nul > .env
```

**Step 3:** Open the `.env` file in a text editor and add the following content:

```env
# API Configuration
# Backend API URL - should match the PORT in backend .env
VITE_API_URL=http://localhost:8000
```

**Required Variables:**
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

> **Note**: In Vite, environment variables must be prefixed with `VITE_` to be accessible in the frontend code. After creating or modifying `.env` files, restart the respective servers.

## 📁 Project Structure

```
ET PharmAI/
├── backend/          # Backend (single FastAPI app)
│   ├── main.py                # Entry: builds app, registers all routes
│   ├── app/
│   │   ├── platform_bootstrap.py   # Extended routes, /health, /platform, WS, startup hooks
│   │   ├── paths.py                # BACKEND_ROOT, PDF template paths
│   │   ├── repurpose_settings.py   # Pydantic settings (.env) for extended features
│   │   ├── graph/                  # LangGraph workflow (state, nodes, workflow)
│   │   ├── agents/
│   │   │   ├── …                   # Classic ET agents (demographics, market, patent_trials, …)
│   │   │   └── repurposing/        # Data-source agents for extended search/scoring pipeline
│   │   ├── routes/
│   │   │   ├── agent_routes.py     # /api/run-agent, PDF/PPTX, clinical-trials test, LLM test
│   │   │   └── repurpose/          # search, chat, export, files, auth, knowledge, market, …
│   │   ├── controllers/            # Classic pipeline controller
│   │   ├── models/                 # Request/response models (classic)
│   │   ├── schemas/                # Pydantic (incl. repurpose_api.py, repurpose_scoring.py)
│   │   └── services/
│   │       ├── gemini_service.py   # Classic Gemini + clinical tooling
│   │       ├── export_report_pdf.py
│   │       └── repurpose/          # LLM factory, cache, Chroma, Mongo, scoring, chat, …
│   ├── database/supabase/          # SQL migrations (optional Supabase)
│   ├── data/cache/                 # On-disk JSON cache (not Redis)
│   ├── data/vector_db/             # Chroma persistence (default path from settings)
│   ├── templates/pdf/              # Jinja HTML templates for PDF export
│   ├── requirements.txt
│   └── .env
│
└── frontend/              # Frontend (React + Vite)
    ├── src/
    │   ├── api/
    │   ├── components/
    │   ├── pages/
    │   └── main.jsx
    ├── package.json
    └── .env
```

### Where major backend features live

| Capability | Implemented? | Location (under `backend/`) |
|------------|--------------|--------------------------------------|
| **Redis** | **No** — not used anywhere in this repo. Caching is file-based JSON. | — |
| **Disk cache** | Yes | `app/services/repurpose/cache/cache_manager.py`, `data/cache/` |
| **Vector / RAG (ChromaDB)** | Yes | `app/services/repurpose/vector_store/` |
| **MongoDB (optional)** | Yes, off by default (`USE_MONGODB`) | `app/services/repurpose/database/mongodb.py`, `repositories.py` |
| **Supabase (optional)** | Yes, if `SUPABASE_URL` / key set | `app/services/repurpose/database/supabase_client.py`, `database/supabase/*.sql` |
| **WebSocket (live updates)** | Yes | `app/routes/repurpose/websocket.py`, mounted in `app/platform_bootstrap.py` |
| **JWT auth** | Yes | `app/services/repurpose/auth/`, routes in `app/routes/repurpose/auth.py` |
| **LangGraph orchestration** | Yes | `app/graph/` |
| **Extended REST (search, chat, export, …)** | Yes | `app/routes/repurpose/*.py` |
| **Classic `/api/run-agent` pipeline** | Yes | `app/routes/agent_routes.py`, `app/controllers/agent_controller.py`, `app/agents/` |
| **PDF / Excel export** | Yes | `app/services/export_report_pdf.py`, `app/services/repurpose/utils/html_pdf_generator.py`, `excel_generator.py` |
| **Groq / Ollama** | Yes (optional) | `app/services/repurpose/llm/` |

## 🔌 API Documentation

Once the backend is running, you can access the interactive API documentation at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Main Endpoints

#### POST `/api/run-agent`
Run a pharmaceutical analysis agent with a query.

**Request Body:**
```json
{
  "query": "Analyze the market potential for drug X",
  "complexity": 5
}
```

**Response:**
```json
{
  "agent_id": "unique-agent-id",
  "analysis": "Detailed analysis...",
  "recommendation": "Strategic recommendations..."
}
```

#### POST `/api/generate-pdf`
Generate a PDF report from analysis text.

**Request Body:**
```json
{
  "text": "Report content here..."
}
```

**Response:** PDF file download

## 🛠️ Development

### Backend Development

```bash
cd backend
source venv/bin/activate  # Activate virtual environment
python main.py            # Run development server
```

### Frontend Development

```bash
cd frontend
npm run dev              # Start Vite dev server with HMR
npm run build            # Build for production
npm run preview          # Preview production build
```

## 🐛 Troubleshooting

### Backend Issues

**Issue: `GEMINI_API_KEY not found`**
- Solution: Ensure your `.env` file exists in `backend/` and contains a valid `GEMINI_API_KEY`

**Issue: `Port already in use`**
- Solution: Change the `PORT` value in your `.env` file or stop the process using that port

**Issue: CORS errors**
- Solution: Verify `FRONTEND_URL` in backend `.env` matches your frontend URL

### Frontend Issues

**Issue: `Cannot connect to API`**
- Solution: Check that `VITE_API_URL` in frontend `.env` matches your backend URL and port
- Ensure the backend server is running

**Issue: Environment variables not loading**
- Solution: Restart the Vite dev server after creating/modifying `.env` file
- Ensure variables are prefixed with `VITE_`

**Issue: `Module not found` errors**
- Solution: Run `npm install` to ensure all dependencies are installed

### General Issues

**Issue: Dependencies installation fails**
- Solution: 
  - Backend: Ensure you're using Python 3.8+ and try `pip install --upgrade pip` first
  - Frontend: Try deleting `node_modules` and `package-lock.json`, then run `npm install` again

## 📝 Additional Notes

- The backend uses Google's Gemini AI for query enhancement and report customization
- The system supports multiple specialized agents for different analysis types
- Reports can be exported as PDFs
- The frontend uses React 19 with Vite for fast development and building

## 🔐 Security Notes

- Never commit `.env` files to version control
- Keep your `GEMINI_API_KEY` secure and never share it publicly
- Use environment-specific configurations for different deployment environments

## 📄 License

[Add your license information here]

## 👥 Contributors

## 👨‍💻 My Contribution

- Contributed to project documentation and improved README structure for better usability
- Assisted in building and understanding responsive Agentic AI workflows using FastAPI and LLM integrations
- Contributed to concepts and implementation of Generative AI features for pharmaceutical analysis
- Supported testing, debugging, and validation of backend APIs and frontend integration
- Collaborated with team members on overall system design and feature development

---

For more detailed information about each component, refer to:
- [backend README](./backend/README.md)
- [PharmAI README](./frontend/README.md)
