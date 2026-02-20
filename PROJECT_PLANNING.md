# Qmate – Hybrid AI–Human Student Support System  
## Full Project Planning Document

---

## 1. Executive Summary

**Qmate** is a hybrid support platform where students get instant AI answers from verified institute knowledge (RAG over PDFs, FAQs, resolved queries). When the AI cannot help or the student prefers a human, the system hands off to human agents with full context, department-wise queuing, and real-time chat. Resolved human conversations feed back into the knowledge base as approved FAQs, enabling continuous improvement while keeping humans in control of accuracy.

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                        │
│  Web App (Student)  │  Web App (Agent)  │  Optional: Mobile / PWA            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY / BACKEND                               │
│  Auth  │  Chat API  │  Queue API  │  Admin API  │  WebSocket (real-time)     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────┐           ┌─────────────────┐           ┌─────────────────┐
│  Auth & User  │           │  AI / RAG       │           │  Human Support  │
│  (JWT, roles) │           │  Vector DB      │           │  Queue, Chat    │
└───────────────┘           └─────────────────┘           └─────────────────┘
        │                             │                             │
        ▼                             ▼                             ▼
┌───────────────┐           ┌─────────────────┐           ┌─────────────────┐
│  PostgreSQL   │           │  Vector DB      │           │  Redis (queue,  │
│  (users,     │           │  (embeddings)   │           │   presence)     │
│   depts,     │           │  + Embedding    │           │  + WebSocket    │
│   config)    │           │  + LLM API      │           │  server         │
└───────────────┘           └─────────────────┘           └─────────────────┘
```

---

## 3. Core Features Breakdown

### 3.1 Authentication & Access Control

| Feature | Description | Priority |
|--------|-------------|----------|
| **Student signup** | Email/password (or OTP), institute domain validation if needed | P0 |
| **Student login** | JWT-based; optional “remember me” | P0 |
| **Agent login** | Separate role; department assignment | P0 |
| **Admin login** | Super-admin for config, FAQ approval, analytics | P0 |
| **Password reset** | Email link or OTP | P1 |
| **Profile** | Name, department, contact; editable by user | P1 |
| **Session management** | Refresh tokens, logout, concurrent session handling | P1 |

**Roles:** `student`, `agent`, `admin`.

---

### 3.2 AI Support (RAG)

| Feature | Description | Priority |
|--------|-------------|----------|
| **Vector DB** | Store embeddings for: academic PDFs, approved FAQs, past resolved queries | P0 |
| **Ingestion pipeline** | PDF upload → chunking → embedding → index (no model retraining) | P0 |
| **Query flow** | Student message → embed → similarity search → top-k chunks → LLM with context → response | P0 |
| **“No relevant info”** | If similarity score below threshold or no chunks: clear message + “Talk to Human” CTA | P0 |
| **Conversation context** | Multi-turn: last N messages or summarised context in prompt | P0 |
| **Source citation** | Optional: “Based on [PDF name / FAQ]” in response | P1 |
| **Feedback on AI** | Thumbs up/down or “Was this helpful?” to improve future tuning | P1 |

**Tech choices (suggested):**  
- Vector DB: Pinecone, Weaviate, Qdrant, or pgvector (PostgreSQL extension).  
- Embeddings: OpenAI `text-embedding-3-small` or open-source (e.g. sentence-transformers).  
- LLM: OpenAI GPT-4/3.5 or Azure OpenAI; optional local model for privacy.

---

### 3.3 Handoff: AI → Human

| Feature | Description | Priority |
|--------|-------------|----------|
| **“Talk to Human”** | Single action; no re-entering history | P0 |
| **Context collection** | Auto: department, last N AI messages, current issue summary (and optional form) | P0 |
| **Context payload** | Same context sent to queue and to agent when chat starts | P0 |
| **Conversation continuity** | Full thread (AI + human) visible to agent; student sees one continuous thread | P0 |

---

### 3.4 Human Support: Queue & Availability

| Feature | Description | Priority |
|--------|-------------|----------|
| **Department-wise queue** | One queue per department (e.g. CS, Admin, Fees); configurable | P0 |
| **Fair queue** | FIFO per department; optional priority (e.g. urgent tag) | P0 |
| **Queue position** | Student sees: “You are #3 in queue” | P0 |
| **Estimated wait time** | Based on avg resolution time and active agents (can be simple formula initially) | P1 |
| **Working hours** | 9 AM–5 PM (configurable per institute/timezone); outside = human disabled or scheduled | P0 |
| **Outside-hours UX** | Message: “Human support is available 9 AM–5 PM. You can stay in queue or schedule a callback.” | P0 |
| **Schedule callback** | Form: preferred time slot in working hours; stored and shown to agents | P1 |

---

### 3.5 Human Agent Experience

| Feature | Description | Priority |
|--------|-------------|----------|
| **Agent dashboard** | List of assigned chat; “Next in queue” preview | P0 |
| **Assign next student** | When agent clicks “Take next” or becomes free, system assigns next from department queue | P0 |
| **Full context** | Department, previous AI conversation, current issue summary + full chat history | P0 |
| **Real-time chat** | One-to-one; WebSocket or long-polling; typing indicators, read receipts optional | P0 |
| **Resolve & close** | Agent marks “Resolved” and closes; student can be prompted for feedback | P0 |
| **Agent status** | Available / Busy / Away; only “Available” agents get new assignments | P0 |
| **After close** | Agent goes back to “Available”; next request from queue | P0 |

---

### 3.6 When No Agent Is Available

| Scenario | Behaviour | Priority |
|----------|-----------|----------|
| Queue empty, no agents | Student can continue with AI only | P0 |
| In queue, no agents | Message: “No agent available. Continue with AI, stay in queue, or schedule callback.” | P0 |
| Stay in queue | Request stays; when an agent comes online, queue is processed in order | P0 |
| Schedule callback | Stored; agent or cron can trigger “callback list” for outreach (email/in-app) | P1 |

---

### 3.7 Knowledge Base Self-Improvement

| Feature | Description | Priority |
|--------|-------------|----------|
| **Resolved chat → FAQ candidate** | When agent closes as “Resolved”, chat (or summary) becomes a FAQ candidate | P0 |
| **Approval workflow** | Admin (or senior agent) reviews and approves before adding to vector DB | P0 |
| **Add to vector DB** | Approved FAQ → chunked → embedded → added to index (no retraining) | P0 |
| **Audit** | Log what was added, when, from which chat (for rollback/quality) | P1 |

---

## 4. Data Models (High Level)

### 4.1 Users & Auth

- **User**: id, email, password_hash, role (student | agent | admin), department_id (nullable for students, required for agents), name, created_at, updated_at.
- **Department**: id, name, slug, queue_config (e.g. working_hours, timezone).
- **Session/RefreshToken**: id, user_id, token, expires_at.

### 4.2 Knowledge Base

- **Document**: id, title, type (pdf | faq | resolved_query), file_path or content_ref, department_id (optional), uploaded_at, status (pending | approved).
- **Chunk**: id, document_id, content, embedding (vector), chunk_index.
- **FAQ**: id, question, answer, source_chat_id (if from resolved chat), approved_by, approved_at.

### 4.3 Conversations & Chat

- **Conversation**: id, student_id, department_id, status (ai_only | waiting_for_agent | with_agent | resolved | closed), created_at, closed_at.
- **Message**: id, conversation_id, sender_type (student | ai | agent), sender_id (user_id for agent), content, created_at.
- **HumanSupportRequest**: id, conversation_id, student_id, department_id, context_summary, queue_position_at_request, status (queued | assigned | in_progress | resolved), assigned_agent_id, created_at, assigned_at, resolved_at.

### 4.4 Queue & Agents

- **QueueEntry**: id, human_support_request_id, department_id, position, created_at (or priority_score).
- **AgentStatus**: agent_id, status (available | busy | away), current_conversation_id, updated_at.
- **CallbackRequest**: id, student_id, conversation_id, preferred_slot_start, preferred_slot_end, status (pending | contacted | completed).

### 4.5 Feedback & Analytics

- **Feedback**: id, conversation_id, rating (1–5 or thumbs), comment (optional), created_at.
- **WorkingHoursConfig**: department_id, timezone, start_time, end_time, days_of_week.

---

## 5. API Design (REST + WebSocket)

### 5.1 Auth

- `POST /auth/signup` – Student/Agent signup (body: email, password, name, role, department_id if agent).
- `POST /auth/login` – Returns access_token, refresh_token, user.
- `POST /auth/refresh` – Refresh token.
- `POST /auth/logout` – Invalidate refresh token.
- `GET /auth/me` – Current user + department.

### 5.2 Student – AI Chat

- `POST /conversations` – Create conversation (optional department).
- `GET /conversations` – List my conversations (paginated).
- `GET /conversations/:id` – Get conversation + messages.
- `POST /conversations/:id/messages` – Send message; backend runs RAG and returns AI reply (or stream).
- Optional: `GET /conversations/:id/messages/stream` – SSE/streaming AI response.

### 5.3 Student – Human Support

- `POST /conversations/:id/request-human` – “Talk to Human”; creates HumanSupportRequest, enqueues, returns queue position and ETA if applicable.
- `GET /conversations/:id/queue-status` – Queue position, estimated wait, working-hours message.
- `POST /conversations/:id/schedule-callback` – Preferred slot (when no agent).
- `GET /human-support/working-hours` – Current department working hours and “is_available_now”.

### 5.4 Real-Time Chat (Human)

- **WebSocket** `/ws/chat/:conversationId` – Connect with JWT.  
  - Client sends: `{ type: "message", content: "..." }`.  
  - Server sends: `{ type: "message", sender, content, timestamp }`, `typing`, `agent_joined`, `chat_closed`, etc.
- Fallback: `POST /conversations/:id/messages` (agent message) + polling `GET /conversations/:id/messages?since=...` for students.

### 5.5 Agent

- `GET /agent/queue` – List queue entries for agent’s department(s).
- `POST /agent/status` – Set status (available | busy | away).
- `POST /agent/assign-next` – Take next from queue; returns conversation_id and full context.
- `POST /conversations/:id/close` – Resolve and close; optional feedback prompt to student.
- `GET /agent/callback-requests` – List scheduled callbacks for department.

### 5.6 Admin

- `GET /admin/stats` – Conversations, resolution time, queue metrics.
- `GET /admin/documents` – List documents; upload PDF.
- `POST /admin/documents/:id/approve` – Approve for ingestion.
- `GET /admin/faq-candidates` – From resolved chats.
- `POST /admin/faq-candidates/:id/approve` – Approve and add to vector DB.
- `GET /admin/departments` – CRUD departments and working hours.
- `GET /admin/agents` – List agents, status, load.

### 5.7 Feedback

- `POST /conversations/:id/feedback` – Rating and optional comment (after chat closed).

---

## 6. Technology Stack Recommendations

| Layer | Option A (Fast to ship) | Option B (Scale / cost control) |
|-------|-------------------------|----------------------------------|
| **Backend** | Python: FastAPI | Same or Node (NestJS) |
| **DB** | PostgreSQL + pgvector | PostgreSQL + dedicated vector DB |
| **Vector DB** | pgvector | Qdrant / Pinecone / Weaviate |
| **Embeddings** | OpenAI API | sentence-transformers (self-hosted) |
| **LLM** | OpenAI GPT-4/3.5 | Azure OpenAI / open-source (Ollama, vLLM) |
| **Real-time** | WebSocket (FastAPI/Starlette or Socket.IO) | Same |
| **Queue state** | Redis (sorted set per department) | Redis or in-DB with locks |
| **Cache** | Redis (sessions, rate limit) | Redis |
| **Frontend** | React/Next.js or Vue | Same |
| **Deploy** | Docker + single server to start | K8s/ECS later |

---

## 7. Implementation Phases

### Phase 1 – Foundation (Weeks 1–2)

- Project setup: repo, linting, env config.
- PostgreSQL: users, departments, roles.
- Auth: signup, login, JWT, refresh, `/me`.
- Basic conversation and message tables; REST: create conversation, send message (no AI yet).

### Phase 2 – AI / RAG (Weeks 3–4)

- Vector DB setup (e.g. pgvector or cloud).
- Document model and PDF ingestion: chunking, embedding, indexing.
- RAG query: embed query → search → LLM with context.
- “No relevant info” detection and “Talk to Human” in response.
- Optional: streaming response.

### Phase 3 – Human Request & Queue (Weeks 5–6)

- HumanSupportRequest and QueueEntry models.
- Working hours config and “is_available_now” logic.
- `POST /request-human`: context collection, enqueue, return position.
- Queue position API; simple ETA (e.g. based on avg resolution time).
- Outside-hours message and “schedule callback” stub.

### Phase 4 – Agent Flow & Real-Time Chat (Weeks 7–8)

- Agent auth and dashboard.
- Agent status (available/busy/away).
- Assign-next: dequeue and assign to agent; send full context.
- WebSocket: real-time messages, typing, agent_joined, chat_closed.
- Close conversation and trigger feedback.

### Phase 5 – Self-Improvement & Admin (Weeks 9–10)

- On “resolve”: create FAQ candidate from chat (summary or Q&A extraction).
- Admin: list FAQ candidates, approve, add to vector DB (embed and index).
- Admin: upload PDF, approve documents, department CRUD, working hours.
- Basic analytics: conversations per day, resolution time, queue depth.

### Phase 6 – Polish & Scale (Ongoing)

- Callback scheduling and agent “callback list”.
- Refined ETA and queue fairness (priority, SLA).
- Rate limiting, security review, monitoring.
- Optional: mobile app or PWA.

---

## 8. Security & Compliance

- **Auth:** Bcrypt/Argon2 for passwords; short-lived access token, secure refresh token.
- **API:** Rate limiting per user/IP; CORS; input validation and sanitization.
- **Data:** PII (emails, names) in DB with access control; encrypt sensitive config.
- **Vector DB:** Prefer same VPC; no sensitive data in embeddings if possible.
- **Audit:** Log admin actions and FAQ approvals.
- **Compliance:** Align with institute policy (e.g. FERPA-like if applicable).

---

## 9. Success Metrics

- **AI:** % of queries answered without human; user satisfaction (thumbs/rating).
- **Human:** Avg wait time, avg resolution time, feedback score.
- **System:** Uptime, queue depth over time, FAQ growth rate.
- **Business:** Deflection rate (AI-only resolution), agent utilization.

---

## 10. File Structure (Backend – Example)

```
Backend/
├── .env.example
├── README.md
├── requirements.txt
├── pyproject.toml
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── conversations.py
│   │   ├── agent.py
│   │   ├── admin.py
│   │   └── human_support.py
│   ├── core/
│   │   ├── security.py
│   │   ├── queue.py            # Redis queue logic
│   │   └── working_hours.py
│   ├── models/                 # SQLAlchemy/Pydantic
│   ├── services/
│   │   ├── rag.py              # Embed, search, LLM
│   │   ├── ingestion.py        # PDF → chunks → vector
│   │   ├── faq_approval.py     # Resolved chat → FAQ → vector
│   │   └── context_builder.py  # Handoff context
│   ├── websocket/
│   │   └── chat.py
│   └── db/
│       ├── session.py
│       └── migrations/
├── tests/
└── scripts/
    └── ingest_pdf.py
```

---

## 11. Next Steps

1. **Confirm stack:** Python/FastAPI vs Node; pgvector vs dedicated vector DB; OpenAI vs self-hosted LLM.  
2. **Clone this plan** into tickets (e.g. GitHub issues) per phase.  
3. **Set up repo:** Backend + Frontend; Docker Compose for Postgres, Redis, and optionally vector DB.  
4. **Start Phase 1:** Auth and conversation CRUD.  
5. **Define “department”** and working hours per institute (single or multi-tenant).

This document is the single source of truth for scope; adjust timelines and priorities per team size and institute constraints.
