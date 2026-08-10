# 🧠 ERKEK AI

> AI-powered digital mentor for men.

![Python](https://img.shields.io/badge/Python-3.14-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)
![Tests](https://img.shields.io/badge/tests-24%20passed-brightgreen)
![Status](https://img.shields.io/badge/status-alpha-orange)

**ERKEK AI** — ер адамдарға өмірлік жағдайларды салқын ақылмен
талдауға, жауапкершілікті қабылдауға және нақты әрекет жасауға
көмектесетін AI-негізіндегі цифрлық ментор.

ERKEK AI адамның орнына шешім қабылдамайды.  
Жүйенің мақсаты — жағдайды түсінуге, бақылауға болатын нәрселерді
анықтауға және келесі дұрыс қадамды жасауға көмектесу.

---

## 🚧 Project Status

**Active Development — Alpha**

Қазіргі уақытта негізгі backend архитектурасы жұмыс істейді,
ал Next.js негізіндегі web-интерфейс әзірленуде.

---

## ✨ Features

- 🧠 Context-aware AI responses
- 💾 Long-term User Memory
- 🔄 Memory Conflict Resolution
- 💬 Conversation History
- 📝 Incremental Conversation Summary
- 📦 Conversation Archive
- 🧩 Multi-category Message Analysis
- 🎭 Emotion Detection
- ⚠️ Risk Detection & Safety Layer
- 🎯 Dynamic Response Style
- 🧱 Dynamic Prompt Builder
- 🌐 Kazakh & Russian language support
- 🔐 User Registration & Login
- 🔑 JWT Authentication
- 🛡️ Protected Chat API
- 📋 Application Logging
- 🔁 OpenAI API Error Handling & Fallback
- 🧪 Automated Tests

---

## 🧠 ERKEK AI Brain Pipeline

```text
User Message
     │
     ▼
Language Detection
     │
     ▼
Memory Extraction
     │
     ▼
Memory Conflict Resolution
     │
     ▼
Category Analysis
     │
     ├── Primary Category
     └── Secondary Categories
     │
     ▼
Emotion Detection
     │
     ▼
Risk Analysis
     │
     ├── Safety Response
     │
     └── Normal AI Pipeline
     │
     ▼
Response Style Detection
     │
     ▼
Prompt Builder
     │
     ├── System Prompt
     ├── Long-term Memory
     ├── Conversation Summary
     ├── Recent History
     └── Current Message
     │
     ▼
OpenAI
     │
     ▼
ERKEK AI Response
     │
     ▼
Conversation Storage
     │
     ▼
Incremental Summary Update
```

---

## 🧩 Multi-category Analysis

ERKEK AI бір хабарламадағы бірнеше мәселені қатар анықтай алады.

Мысалы:

```text
Пайдаланушы:

"Ажырастым, екі балам бар,
қарызым бар және жұмысым тұрақсыз."

Primary Category:
Finance

Secondary Categories:
Fatherhood
Relationship
Career
```

Қазіргі негізгі категориялар:

- Relationship
- Fatherhood
- Finance
- Business
- Career
- Discipline
- Loneliness
- Health
- Self Development
- General

---

## 💾 Memory System

ERKEK AI пайдаланушымен әр әңгімені нөлден бастамау үшін
ұзақ мерзімді контекст сақтай алады.

Memory жүйесінде сақталуы мүмкін:

- Language
- Age
- Marital status
- Children
- Career
- Financial status
- Main goal
- Additional goals
- Habits
- Important events

Жаңа ақпарат бұрынғы ақпаратпен қайшы келсе,
**Memory Conflict Resolution** механизмі оны өңдейді.

---

## 💬 Conversation Intelligence

ERKEK AI контексті бірнеше деңгей арқылы басқарады:

```text
Long-term Memory
        +
Conversation Summary
        +
Recent Messages
        +
Current Message
```

Incremental Summary жүйесі бүкіл әңгімені әр сұраныста қайта
өңдемей, тек жаңа хабарламалар негізінде summary-ді жаңартады.

---

## ⚠️ Safety Layer

Risk Analyzer пайдаланушы хабарламасының қауіп деңгейін анықтайды:

```text
Low
Medium
High
Critical
```

Жоғары қауіп анықталған жағдайда стандартты AI pipeline орнына
арнайы safety response механизмі іске қосылады.

---

## 🔐 Authentication

Authentication жүйесі:

- User Registration
- User Login
- Secure Password Hashing
- JWT Access Tokens
- Protected API Routes
- Unauthorized Request Handling

Chat API authenticated user арқылы қорғалады.

---

## 🛠 Tech Stack

### Backend

- Python
- FastAPI
- Pydantic
- SQLite
- OpenAI API
- JWT Authentication
- Pytest

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

---

## 📁 Project Structure

```text
ERKEK-AI/
│
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── brain/
│   │   ├── core/
│   │   ├── database/
│   │   ├── prompts/
│   │   ├── routes/
│   │   └── services/
│   │
│   └── tests/
│
└── frontend/
    ├── app/
    ├── components/
    └── lib/
```

---

## 🧪 Automated Tests

ERKEK AI backend негізгі компоненттері automated tests арқылы
тексеріледі.

**Current status: 24 tests passed ✅**

Тесттер қамтиды:

- Category Analysis
- Multi-category Analysis
- Memory Extraction
- Memory Conflict Resolution
- Risk Detection
- Prompt Builder
- Chat API
- Authentication
- JWT Protected Chat

Тесттерді іске қосу:

```bash
python -m pytest -v
```

---

## 🗺️ Roadmap

### Backend Core

- [x] Brain Architecture
- [x] Long-term Memory
- [x] Memory Conflict Resolution
- [x] Conversation History
- [x] Incremental Summary
- [x] Conversation Archive
- [x] Multi-category Analyzer
- [x] Emotion Detection
- [x] Risk / Safety Layer
- [x] Response Style Engine
- [x] Dynamic Prompt Builder
- [x] Logging
- [x] Authentication
- [x] JWT Protected Chat
- [x] Automated Tests

### Frontend

- [x] Next.js initialization
- [x] Register UI
- [x] Login UI
- [ ] Frontend ↔ Backend integration
- [ ] JWT Session Handling
- [ ] Chat Interface
- [ ] Conversation Sidebar
- [ ] Protected Routes
- [ ] Logout
- [ ] Responsive Mobile UI

### Production

- [ ] Production Database
- [ ] Rate Limiting
- [ ] Security Hardening
- [ ] Docker
- [ ] CI/CD
- [ ] VPS Deployment
- [ ] Domain Integration
- [ ] HTTPS
- [ ] Monitoring & Backups

---

## 🔒 Security

Sensitive information must never be committed to the repository.

This includes:

```text
.env
OPENAI_API_KEY
JWT_SECRET_KEY
Production credentials
User database files
```

---

## ⚠️ Disclaimer

ERKEK AI кәсіби медициналық, психологиялық, заңдық немесе
қаржылық қызметті алмастырмайды.

Жоғары тәуекелді жағдайларда тиісті кәсіби мамандарға жүгіну қажет.

---

## 📌 Version

**ERKEK AI v0.1.0-alpha**

Currently under active development.

---

## 📄 License

Copyright © 2026 ERKEK AI.

All rights reserved.
