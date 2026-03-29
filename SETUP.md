# Quick Setup Guide

This is a quick reference guide to get ET PharmAI up and running. For detailed documentation, see [README.md](./README.md).

## 🚀 5-Minute Setup

### Step 1: Backend Setup

```bash
# Navigate to backend
cd Agentichost-main

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (from Agentichost-main directory: cp .env.example .env)

# Edit Agentichost-main/.env and set at least one LLM key (no dummy mode):
# - GEMINI_API_KEY=your_gemini_key   (primary; get from https://makersuite.google.com/app/apikey)
# - GROQ_API_KEY=your_groq_key       (fallback or primary; get from https://console.groq.com)
# If both are set, Gemini is used first and Groq is used when Gemini fails (e.g. 429).

# Start backend
python main.py
```

### Step 2: Frontend Setup (New Terminal)

```bash
# Navigate to frontend
cd PharmAI-main

# Install dependencies
npm install

# Create .env file (copy from PharmAI-main/.env.example)
# Minimum: VITE_API_URL=http://localhost:8000
# Optional: VITE_GOOGLE_MAPS_API_KEY=... for plant location map (see "Google Maps" below).

# Start frontend
npm run dev
```

### Step 3: Access Application

Open your browser: `http://localhost:5173`

## ✅ Verification Checklist

- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 5173
- [ ] `.env` in `Agentichost-main/` with at least one of `GEMINI_API_KEY` or `GROQ_API_KEY` (real API; no dummy responses)
- [ ] `.env` file created in `PharmAI-main/` with `VITE_API_URL` (and optionally `VITE_GOOGLE_MAPS_API_KEY` for plant map)
- [ ] No errors in terminal output
- [ ] Can access `http://localhost:5173` in browser
- [ ] Can access `http://localhost:8000/docs` (API docs)

## 🔑 Getting Your Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key
5. Paste it in `Agentichost-main/.env` as `GEMINI_API_KEY=your_key_here`

## 🐛 Quick Troubleshooting

**Backend won't start:**
- Check Python version: `python3 --version` (needs 3.8+)
- Verify `.env` file exists and has `GEMINI_API_KEY`
- Check if port 8000 is available

**Frontend won't start:**
- Check Node version: `node --version` (needs 18+)
- Run `npm install` again
- Verify `.env` file has `VITE_API_URL`

**Can't connect to API:**
- Ensure backend is running
- Check `VITE_API_URL` matches backend URL
- Verify CORS settings in backend `.env`

**429 / "Quota exceeded" (Gemini):**
- The app **automatically retries** when Gemini returns 429 (e.g. free tier: 20 requests/day per model). It waits the time suggested by the API (e.g. ~27s) then retries.
- If you still see failures, you may have hit the **daily free-tier limit**. Check usage: [Google AI rate limits](https://ai.dev/rate-limit). Consider a paid plan for higher limits: [Gemini API pricing](https://ai.google.dev/pricing).
- You can add a **Groq API key** (optional) so that when Gemini returns 429 after retries, the app uses Groq as fallback for more free requests per day. See "Groq API key (optional fallback)" below.

## Groq API key (optional fallback)

When Gemini hits rate limits (429), the app can use **Groq** as a fallback if `GROQ_API_KEY` is set. This gives you more effective free requests per day without changing Gemini’s limit.

1. Go to [console.groq.com](https://console.groq.com).
2. Sign in (or create an account).
3. Open **API Keys** (or **Keys** in the dashboard).
4. Click **Create API Key**, name it (e.g. "PharmAI"), and copy the key.
5. Add to `Agentichost-main/.env`:  
   `GROQ_API_KEY=your_groq_api_key_here`

If `GROQ_API_KEY` is not set, only Gemini is used (no Groq fallback). When Groq is used, the backend logs `[LLM] Using Groq fallback for: <operation>` and the frontend shows a notice listing which operations used Groq.

## Google Maps (optional – plant location map)

The **Demographic** agent recommends plant locations based on energy ease, land availability, and proximity to markets. To show these on a map:

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project → **APIs & Services** → **Library** → enable **Maps JavaScript API**.
3. **APIs & Services** → **Credentials** → **Create credentials** → **API key**.
4. Restrict the key: **Application restrictions** → **HTTP referrers** → add e.g. `http://localhost:5173/*`, `https://yourdomain.com/*`.
5. In `PharmAI-main/.env` add:  
   `VITE_GOOGLE_MAPS_API_KEY=your_api_key_here`  
   (Use the same key as in your previous project if you already have one.)

Without this key, the recommended plant locations still appear as a list with scores; only the map view is skipped.

## 📚 Next Steps

- Read the full [README.md](./README.md) for detailed documentation
- Check [Agentichost README](./Agentichost-main/README.md) for backend details
- Check [PharmAI README](./PharmAI-main/README.md) for frontend details
