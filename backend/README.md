# Agentichost - Backend API Server

FastAPI-based backend service for the ET PharmAI platform, providing pharmaceutical analysis capabilities through specialized AI agents.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Google Gemini API Key

### Installation

1. **Create a virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

4. **Run the server:**

```bash
python main.py
```

The server will start on `http://localhost:8000` (or the port specified in your `.env` file).

## 📋 Environment Variables

Create a `.env` file in the root directory with the following variables:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PORT` | Server port number | No | `8000` |
| `FRONTEND_URL` | Frontend URL for CORS | No | `http://localhost:5173` |
| `GEMINI_API_KEY` | Google Gemini API key | **Yes** | - |

### Example `.env` file:

```env
PORT=8000
FRONTEND_URL=http://localhost:5173
GEMINI_API_KEY=your_actual_api_key_here
```

## 🏗️ Architecture

The backend follows a modular architecture with specialized agents:

- **Master Agent**: Orchestrates multiple worker agents
- **Demographics Agent**: Analyzes demographic data
- **Market Agents**: IQVIA insights and EXIM trends
- **Patent & Trials Agents**: Clinical trials and patent landscape analysis
- **Production Agents**: Process design and techno-economic analysis
- **Knowledge Agents**: Internal knowledge and web intelligence
- **Report Generator**: Creates PDF reports from analysis results

## 📡 API Endpoints

### POST `/api/run-agent`

Execute a pharmaceutical analysis agent.

**Request:**
```json
{
  "query": "Analyze market potential for drug X",
  "complexity": 5
}
```

**Response:**
```json
{
  "agent_id": "uuid-here",
  "analysis": "Detailed analysis results...",
  "recommendation": "Strategic recommendations..."
}
```

### POST `/api/generate-pdf`

Generate a PDF report from text content.

**Request:**
```json
{
  "text": "Report content here..."
}
```

**Response:** PDF file (application/pdf)

## 📚 API Documentation

When the server is running, access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 Development

### Running in Development Mode

```bash
python main.py
```

### Project Structure

```
Agentichost-main/
├── app/
│   ├── agents/              # Specialized analysis agents
│   │   ├── base.py         # Base agent class
│   │   ├── demographics/   # Demographic analysis
│   │   ├── grading.py      # Analysis grading
│   │   ├── knowledge/      # Knowledge base agents
│   │   ├── market/         # Market analysis agents
│   │   ├── master.py       # Master orchestrator
│   │   ├── patent_trials/  # Patent and trial agents
│   │   ├── production/     # Production analysis
│   │   ├── report_generator.py  # PDF generation
│   │   └── worker_agents.py     # Worker agent definitions
│   ├── controllers/        # Request controllers
│   ├── models/            # Data models
│   ├── routes/            # API route definitions
│   ├── schemas/           # Pydantic schemas
│   └── services/          # External services
│       └── gemini_service.py  # Gemini AI integration
├── main.py                # Application entry point
└── requirements.txt       # Python dependencies
```

## 🧪 Testing

[Add testing instructions here]

## 🐛 Troubleshooting

### Common Issues

**Error: `GEMINI_API_KEY not found`**
- Ensure `.env` file exists in the project root
- Verify `GEMINI_API_KEY` is set correctly
- Restart the server after modifying `.env`

**Error: `Port already in use`**
- Change `PORT` in `.env` to an available port
- Or stop the process using port 8000

**Error: CORS issues**
- Verify `FRONTEND_URL` in `.env` matches your frontend URL
- Ensure frontend is running on the specified URL

**Error: Gemini model initialization fails**
- Check your API key is valid and has proper permissions
- Verify internet connection for API access
- Check Gemini API service status

## 📦 Dependencies

Key dependencies:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `google-generativeai`: Gemini AI integration
- `python-dotenv`: Environment variable management
- `pydantic`: Data validation
- `fpdf2`: PDF generation
- `requests`: HTTP client

See `requirements.txt` for complete list.

## 🔐 Security

- Never commit `.env` files
- Keep API keys secure
- Use environment variables for sensitive data
- Implement proper authentication for production

## 📄 License

[Add license information]
