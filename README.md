# LangGraph Contract Analysis Workflow

A Flask web app that uses LangGraph to analyze legal contracts with AI. Upload a PDF contract and get a risk analysis, plain-language summary, and email notification — with optional Google Calendar integration for creator brand deals.

## Features

- PDF contract parsing and clause extraction
- AI-powered risk analysis (content ownership, exclusivity, usage rights, payment terms)
- Web research for unclear legal terms
- Email summary delivery
- **Creator mode**: deliverables extraction + Google Calendar invites for deadlines
- Password-protected access

## Tech Stack

- **Backend**: Flask, Gunicorn
- **AI Orchestration**: LangGraph, LangChain, OpenAI
- **PDF Processing**: pdfplumber
- **Notifications**: SMTP email, Google Calendar API
- **Search**: DuckDuckGo (via LangChain)

## Setup

### Environment Variables

Create a `.env` file with:

```
MODEL=gpt-5-mini
OPENAI_API_KEY=
SENDER_EMAIL=
EMAIL_PASSWORD=
SECRET_KEY=
APP_PASSWORD_HASH=
GOOGLE_CALENDAR_TOKEN_JSON=
```

### Local Development

```bash
pip install -r requirements.txt
python src/app.py
```

### Deployment (Railway)

1. Connect your GitHub repo on [railway.app](https://railway.app)
2. Add the environment variables above in the Railway dashboard
3. Railway auto-detects the `Procfile` and `requirements.txt` — deploy triggers automatically
4. Generate a domain under Settings → Networking

## Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        START: Contract Upload                   │
│                    (PDF → Text Extraction)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  1. Extract Company  │
                  │                      │
                  │  • LLM extraction    │
                  │  • Regex fallback    │
                  │  • For email subject │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  2. Parse Contract   │
                  │                      │
                  │  • Extract clauses   │
                  │  • Deliverables      │
                  │  • Payment terms     │
                  │  • Legal flags       │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  3. Analyze Risks    │
                  │                      │
                  │  • Content ownership │
                  │  • Exclusivity       │
                  │  • Usage rights      │
                  │  • Risk scoring      │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  4. Research Terms   │
                  │                      │
                  │  • Detect unclear    │
                  │    legal terms       │
                  │  • Web search        │
                  │  • Summarize results │
                  │  • Add context       │
                  └──────────┬───────────┘
                             │
                             ▼
              ┌──────────────┴──────────────┐
              │                             │
              ▼ (creator mode)              ▼ (legal mode)
   ┌──────────────────────┐                 │
   │ 5a. Extract          │                 │
   │     Deliverables     │                 │
   │                      │                 │
   │ • Due dates          │                 │
   │ • Times & timezones  │                 │
   │ • Calendar format    │                 │
   └──────────┬───────────┘                 │
              │                             │
              └──────────────┬──────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  6. Write Summary    │
                  │                      │
                  │  • Friendly language │
                  │  • Include research  │
                  │  • Markdown format   │
                  │  • Risk highlights   │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │  7. Send             │
                  │     Notifications    │
                  │                      │
                  │  • Email summary     │
                  │  • Calendar invites  │
                  │    (creator mode)    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │         END          │
                  │                      │
                  │     Analysis         │
                  │     Complete         │
                  └──────────────────────┘
```

## Mode Differences

### Legal Mode
```
extract_company → parse_contract → analyze_risks
→ research_terms → write_summary → send_notifications
```
- Basic contract analysis
- No deliverables extraction
- No calendar integration
- Research included (if unclear terms found)

### Creator Mode
```
extract_company → parse_contract → analyze_risks
→ research_terms → extract_deliverables
→ write_summary → send_notifications
```
- Brand deal focused
- Deliverables extraction
- Calendar invites sent
- Research included (if unclear terms found)
