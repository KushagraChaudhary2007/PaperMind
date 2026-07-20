# 🧠 PaperMind

### AI-Powered Research Paper Simplifier & Research Assistant

PaperMind is a full-stack AI web application that helps students, researchers, and developers understand research papers faster.

Users can securely upload academic PDFs, extract their content, generate structured AI summaries, ask questions grounded in the uploaded paper, compare multiple papers, and generate research roadmaps — all from one platform.

🌐 **Live App:** https://paper-mind-three.vercel.app  
⚙️ **Backend API:** https://papermind-production-023d.up.railway.app

---

## ✨ Features

### 🔐 Authentication
- Secure user registration and login
- Protected routes and user-specific paper access
- Token-based authentication

### 📄 Research Paper Upload
- Upload academic papers in PDF format
- Extract text automatically from uploaded PDFs
- Store and manage papers from a personal dashboard

### 🤖 AI Summary
Generate structured AI-powered summaries of uploaded research papers to quickly understand:
- Main ideas
- Methodology
- Important findings
- Limitations
- Key takeaways

### 💬 Ask PaperMind
Ask natural-language questions about an uploaded research paper.

PaperMind:
1. Splits the paper into manageable text chunks
2. Uses lightweight **TF-IDF retrieval** to find the most relevant sections
3. Sends only relevant context to Gemini
4. Generates a grounded answer based on the uploaded paper

This approach avoids loading heavy transformer models on the production server while keeping responses contextual and efficient.

### 🗺️ Research Roadmap
Generate a structured learning/research roadmap based on a paper to help users understand:
- Prerequisite topics
- Important concepts
- Suggested learning sequence
- Possible next research directions

### ⚖️ Paper Comparison
Select two uploaded papers and generate a structured comparison across their:
- Core ideas
- Approaches
- Methodologies
- Findings
- Strengths
- Limitations

---

## 🖥️ Tech Stack

### Frontend
- React
- Vite
- JavaScript
- HTML
- CSS
- React Router

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- PyMuPDF

### AI & Retrieval
- Google Gemini API
- Gemini generation model configurable through environment variables
- TF-IDF retrieval using Scikit-learn
- Cosine similarity for relevant-context retrieval

### Deployment
- **Frontend:** Vercel
- **Backend:** Railway
- **Source Control:** GitHub

---

## 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │       User           │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React + Vite UI    │
                    │      (Vercel)        │
                    └──────────┬───────────┘
                               │ HTTPS API
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend    │
                    │      (Railway)       │
                    └───────┬──────┬───────┘
                            │      │
              ┌─────────────┘      └──────────────┐
              ▼                                   ▼
    ┌────────────────────┐             ┌────────────────────┐
    │ SQLAlchemy / Data  │             │    Gemini API      │
    │ Users, Papers,     │             │ Summary, Chat,     │
    │ Chats, Roadmaps    │             │ Comparison, etc.   │
    └────────────────────┘             └────────────────────┘
              │
              ▼
    ┌────────────────────┐
    │  PDF Text + Chunks │
    │ TF-IDF Retrieval   │
    └────────────────────┘
```

---

## 🔄 How Ask PaperMind Works

```text
Uploaded PDF
    ↓
Text Extraction
    ↓
Paper Chunking
    ↓
TF-IDF Vectorization
    ↓
Cosine Similarity Search
    ↓
Most Relevant Paper Chunks
    ↓
Gemini + Retrieved Context
    ↓
Grounded Answer
```

This retrieval pipeline was designed to reduce production memory usage by avoiding local SentenceTransformer/PyTorch model loading.

---

## 📁 Project Structure

```text
PaperMind/
│
├── Backend/
│   ├── main.py
│   ├── model.py
│   ├── rag_service.py
│   ├── requirements.txt
│   └── ...
│
├── Frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── components/
│   │   └── ...
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
│
└── README.md
```

---

## 🚀 Running PaperMind Locally

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd PaperMind
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with your actual repository URL.

---

## ⚙️ Backend Setup

### 2. Open the Backend Folder

```bash
cd Backend
```

### 3. Create a Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file inside `Backend/`.

Example:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite
FRONTEND_URL=http://localhost:5173
```

Also include any authentication/database environment variables required by your current backend configuration.

> Never commit real API keys or secrets to GitHub.

### 6. Start the FastAPI Backend

Use the command that matches your backend entry point, for example:

```bash
uvicorn main:app --reload
```

The backend will normally be available at:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

---

## 🎨 Frontend Setup

Open another terminal:

```bash
cd Frontend
```

Install dependencies:

```bash
npm install
```

Create a `.env` file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the development server:

```bash
npm run dev
```

The frontend will normally run at:

```text
http://localhost:5173
```

---

## 🌍 Production Configuration

### Vercel

Set:

```env
VITE_API_BASE_URL=https://papermind-production-023d.up.railway.app
```

### Railway

Set the production frontend origin:

```env
FRONTEND_URL=https://paper-mind-three.vercel.app
```

Also configure:

```env
GEMINI_API_KEY=your_secret_key
GEMINI_MODEL=gemini-3.1-flash-lite
```

Keep all secrets inside the deployment platform's environment-variable settings.

---

## 📸 Screenshots

Add screenshots of the deployed application here.

Suggested screenshots:

### Login / Register
```text
docs/screenshots/login.png
```

### Dashboard
```text
docs/screenshots/dashboard.png
```

### Paper Analysis & AI Summary
```text
docs/screenshots/ai-summary.png
```

### Ask PaperMind
```text
docs/screenshots/ask-papermind.png
```

### Paper Comparison
```text
docs/screenshots/comparison.png
```

### Research Roadmap
```text
docs/screenshots/roadmap.png
```

Example Markdown:

```md
![PaperMind Dashboard](docs/screenshots/dashboard.png)
```

---

## 🔒 Security Notes

- Authentication is required for protected PaperMind functionality.
- Papers are accessed through authenticated user ownership checks.
- API keys and secrets are stored as environment variables.
- Production frontend access is controlled through backend CORS configuration.
- Secrets should never be committed to the repository.

---

## 🧠 Engineering Challenges Solved

During development, PaperMind addressed several real-world production challenges:

### Production CORS
Configured communication between the Vercel frontend and Railway backend.

### Environment-Based API Configuration
Used Vite environment variables so the same frontend can work with:
- Local FastAPI during development
- Railway in production

### Railway Memory Optimization
The original semantic retrieval system used a local SentenceTransformer model, which caused high production memory usage.

The retrieval architecture was redesigned to use:

```text
TF-IDF + Cosine Similarity + Gemini Generation
```

This removed the need to load PyTorch and transformer weights on Railway.

### AI API Rate Limits
The application includes handling for AI API failures/rate limits and uses a lightweight generation model suitable for interactive workflows.

---

## 🔮 Future Improvements

Possible future upgrades:

- Citation generator and bibliography export
- Multi-paper conversational research assistant
- Semantic/vector database retrieval for larger document collections
- Highlight exact PDF passages used in AI answers
- Export summaries and roadmaps as PDF
- Research workspace and folders
- Collaborative paper collections
- Streaming AI responses
- Usage analytics and history
- Improved mobile experience

---

## 🎯 Project Purpose

PaperMind was built as a practical AI/ML full-stack project demonstrating:

- Full-stack web development
- REST API development
- Authentication
- PDF processing
- Retrieval-Augmented Generation concepts
- AI API integration
- Database-backed application design
- Production deployment
- Debugging real deployment issues such as CORS, memory limits, and API quotas

---

## 📝 API Documentation

When running locally:

```text
http://127.0.0.1:8000/docs
```

Production backend:

```text
https://papermind-production-023d.up.railway.app/docs
```

FastAPI automatically provides interactive Swagger documentation for available API endpoints.

---

## 👨‍💻 Author

Built as an AI/ML-focused full-stack project by a B.Tech Computer Science student specializing in Artificial Intelligence & Machine Learning.

---

## ⭐ Support

If you find PaperMind useful or interesting, consider starring the repository.

---

### PaperMind

**Upload. Understand. Compare. Explore research faster with AI.**
