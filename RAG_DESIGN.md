# Qmate RAG – Design & Implementation Guide

This document describes **how to build the RAG (Retrieval-Augmented Generation)** layer for Qmate: ingestion, retrieval, and generation, with “no relevant info” handling and source citation.

---

## 1. RAG Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           INGESTION (offline / on approval)                       │
│  PDF / FAQ / Resolved query → Chunk → Embed → Store in Vector DB                 │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           QUERY (per student message)                             │
│  User message + optional conversation context                                    │
│       → Embed query → Similarity search (top-k) → Score threshold                │
│       → If no/weak results: "I don't have info" + Talk to Human                   │
│       → Else: Build prompt with chunks → LLM → Response (+ optional sources)     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Principles:**
- **No model retraining.** All updates are via adding/updating vectors.
- **Single vector index** for all content types (PDF, FAQ, resolved); metadata filters by `source_type` and optional `department_id` when needed.
- **Clear “no relevant info” path** so the AI never hallucinates; then offer human handoff.

---

## 2. Data Sources & Metadata

| Source            | How it gets in        | Metadata to store                          |
|-------------------|------------------------|--------------------------------------------|
| **Academic PDFs** | Admin upload → ingest  | `source_type=pdf`, `document_id`, `title`, optional `department_id` |
| **Approved FAQs** | Admin approval → ingest | `source_type=faq`, `faq_id`, optional `department_id` |
| **Resolved queries** | Resolved chat → FAQ approval → ingest | `source_type=resolved_query`, `conversation_id`, `faq_id` |

Every chunk in the vector DB has:
- `id` (UUID)
- `content` (text of the chunk)
- `embedding` (vector)
- `source_type`: `pdf` | `faq` | `resolved_query`
- `source_id`: document_id / faq_id
- `document_title` or `question` (for citation)
- Optional: `department_id`, `chunk_index`, `page_number`

---

## 3. Ingestion Pipeline

### 3.1 Steps

1. **Extract text**  
   - PDF: use `pypdf`, `pdfplumber`, or `PyMuPDF` to extract text (and optionally keep page numbers).  
   - FAQ / Resolved: already plain text (question + answer or Q&A pair).

2. **Chunk**  
   - Strategy: **semantic chunking** preferred (e.g. by paragraph or section), with a max token limit so chunks fit the embedding model’s context.  
   - Typical: **256–512 tokens** per chunk, overlap **~50 tokens** to avoid splitting mid-sentence.  
   - For FAQs: one chunk per Q&A pair is often enough.

3. **Embed**  
   - Call embedding API (e.g. OpenAI `text-embedding-3-small`) for each chunk.  
   - Dimension: 1536 (OpenAI) or match your vector DB.

4. **Upsert**  
   - Insert or update vectors with metadata.  
   - For re-ingestion: delete by `source_id` (and `source_type`) then insert new chunks (idempotent per document/FAQ).

### 3.2 Chunking Strategy (Concrete)

```text
Option A – Fixed size (simplest)
- Max chunk size: 500 characters or ~128 tokens
- Overlap: 50 characters
- Split on sentence boundaries when possible

Option B – Paragraph / section (better for academic PDFs)
- Split on double newline or on headings (e.g. # or bold)
- Max chunk size: 512 tokens; if a section is larger, sub-split with overlap

Option C – For FAQs
- One chunk = "Question: ... Answer: ..." (no splitting)
```

**Recommendation:** Start with **fixed-size + sentence boundary** (Option A); add paragraph/section (Option B) later for better quality on long PDFs.

### 3.3 Idempotency & Updates

- **PDF re-upload:** Delete all chunks where `source_type='pdf'` and `source_id=<document_id>`, then ingest again.
- **FAQ update:** Same: delete by `source_type='faq'` and `source_id=<faq_id>`, then re-ingest.
- **New resolved query:** Only insert; no delete (new FAQ entry).

---

## 4. Vector Store Choice

| Option      | Pros                          | Cons                    |
|------------|--------------------------------|-------------------------|
| **pgvector** | Same DB as app, simple ops     | Scale limits, tuning    |
| **Qdrant**   | Good filters, fast             | Extra service           |
| **Chroma**   | Easy local dev, Python-native  | Production scale        |
| **Pinecone** | Managed, scalable              | Cost, vendor lock-in    |

**Recommendation:**  
- **Development / single institute:** `pgvector` (no extra infra).  
- **Production / multi-tenant or large corpus:** Qdrant or Pinecone.

Schema (conceptual; adapt to your choice):

```text
Collection / Table: knowledge_chunks
- id (primary key)
- content (text)
- embedding (vector, dim=1536)
- source_type (pdf | faq | resolved_query)
- source_id (UUID)
- title (for display: document title or question)
- department_id (nullable)
- created_at
```

---

## 5. Query Flow (Step by Step)

### 5.1 Input

- **Current user message:** string.
- **Conversation context (optional):** last N turns (e.g. last 5 messages) or a short summary (e.g. 200 words) so the model can resolve “it”, “that”, “the same form”.

### 5.2 Query Expansion (Optional but Recommended)

- Turn the last message + context into a **standalone query** so retrieval is less dependent on pronouns.
- Example: User: “What’s the deadline?” Context: “User asked about project submission.” → Expanded: “deadline for project submission”.
- Implement with a small LLM call (“Given conversation context and last message, write a single standalone search query”) or heuristics (e.g. concatenate last 2–3 messages).

### 5.3 Embed & Retrieve

1. Embed the (expanded or raw) query with the **same model** used in ingestion.
2. **Similarity search:** top-k (e.g. k=5–10) by cosine similarity.
3. **Optional filter:** by `department_id` if the conversation is department-scoped.
4. **Score threshold:** if `similarity < threshold` (e.g. 0.65), treat as “no relevant chunk” (see below).

### 5.4 “No Relevant Info” Decision

```text
if no chunks returned:
    → no_relevant_info = True
if chunks returned but max(similarity) < threshold (e.g. 0.65):
    → no_relevant_info = True
else:
    → no_relevant_info = False
```

When `no_relevant_info` is True:
- **Do not** call the LLM with institute content.
- Return a **fixed or templated message** plus “Talk to Human” CTA, e.g.:  
  “I couldn’t find specific information about that in our knowledge base. For accurate help, please use **Talk to Human** so an agent can assist you.”

### 5.5 Prompt Build & LLM Call

When you have at least one chunk above threshold:

1. **Format context:** e.g.  
   `[Source 1] title: ...\ncontent: ...`  
   `[Source 2] ...`
2. **System prompt:** Instruct the model to answer **only** from the provided context, say “I don’t have that information” if the context doesn’t contain the answer, and optionally cite the source (e.g. “Based on [title]”).
3. **User prompt:** Conversation summary (if any) + current message.
4. **LLM:** One call (or stream) to get the final reply.

### 5.6 Output

- **Reply text** to show the student.
- **Optional:** list of `source_id` / `title` for “Based on: …” in the UI.
- **Flag:** `no_relevant_info` (already used above for handoff).

---

## 6. Conversation Context for Multi-Turn

- **Option A:** Last N messages (e.g. 5) appended in the user prompt; retrieval uses only the **last message** (or expanded query). Simple and works well.
- **Option B:** Summarise the conversation every M turns (e.g. every 5) with an LLM, then use “summary + last message” for both retrieval and prompt. Better for long threads, more cost.
- **Recommendation:** Start with Option A (last N messages in prompt, last message for retrieval/query expansion).

---

## 7. Code Structure (Backend)

```text
app/
  services/
    rag/
      __init__.py
      config.py           # embedding model, top_k, threshold, chunk size
      embeddings.py       # get_embedding(text) → list[float]
      chunking.py         # chunk_pdf_text(text) → list[Chunk]; chunk_faq(q, a) → list[Chunk]
      vector_store.py     # abstract interface: upsert(chunks), search(query_embedding, top_k, filter?) → list[ScoredChunk]
      ingestion.py        # ingest_document(doc_id, type, content_or_path), ingest_faq(faq_id, q, a)
      query.py            # retrieve(query, conversation_context?) → (chunks or None, scores)
      generation.py       # build_prompt(chunks, messages) → LLM response
      pipeline.py         # answer(user_message, conversation_id) → { reply, sources, no_relevant_info }
  api/
    conversations.py      # POST /conversations/:id/messages → calls pipeline.answer()
```

### 7.1 Key Interfaces

**Embeddings (e.g. OpenAI):**

```python
# embeddings.py
def get_embedding(text: str) -> list[float]:
    # Call OpenAI text-embedding-3-small; truncate to 8191 tokens if needed
    ...
```

**Vector store:**

```python
# vector_store.py
def search(
    query_embedding: list[float],
    top_k: int = 7,
    threshold: float = 0.65,
    department_id: Optional[UUID] = None,
) -> list[ScoredChunk]:
    # Return chunks with similarity >= threshold, ordered by score
    ...
```

**RAG pipeline (orchestrator):**

```python
# pipeline.py
def answer(
    user_message: str,
    conversation_id: UUID,
    department_id: Optional[UUID] = None,
) -> RAGResponse:
    # 1. Load last N messages for context
    # 2. (Optional) Query expansion
    # 3. query_embedding = get_embedding(user_message or expanded_query)
    # 4. chunks = vector_store.search(query_embedding, top_k=7, threshold=0.65, department_id=department_id)
    # 5. if not chunks: return no_relevant_info=True, fixed message + CTA
    # 6. reply = generation.build_and_call(chunks, conversation_messages, user_message)
    # 7. return reply, sources, no_relevant_info=False
```

---

## 8. Configuration (Suggested)

```python
# config or .env
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
LLM_MODEL = "gpt-4o-mini"  # or gpt-4 for quality

RAG_TOP_K = 7
RAG_SCORE_THRESHOLD = 0.65
RAG_CHUNK_SIZE = 500
RAG_CHUNK_OVERLAP = 50
RAG_CONVERSATION_CONTEXT_MESSAGES = 5
```

Tune `RAG_SCORE_THRESHOLD` and `RAG_TOP_K` on a small set of questions: higher threshold = fewer false positives but more “no relevant info”; lower = more retrieval but more risk of irrelevant context.

---

## 9. Security & Performance

- **Input length:** Cap user message and context size before embedding/LLM (e.g. 4k characters for message, 2k for context).
- **Rate limit:** Per user or per conversation to avoid embedding/LLM abuse.
- **PII:** Avoid putting student PII in chunks that get sent to third-party APIs; keep only institute knowledge in the vector DB.
- **Caching (optional):** Cache embeddings for the same query for a short TTL to reduce cost and latency.

---

## 10. Summary

| Component        | Responsibility |
|-----------------|----------------|
| **Chunking**    | PDF text (and optionally FAQ) → fixed-size or paragraph chunks with overlap. |
| **Embeddings**  | Same model for ingestion and query; OpenAI or self-hosted. |
| **Vector store**| Store chunks with metadata; search by similarity + optional department filter. |
| **Retrieval**   | Top-k + threshold; if below threshold or empty → “no relevant info” + Talk to Human. |
| **Generation**  | Prompt with chunks + conversation; LLM answers only from context; optional citation. |
| **Pipeline**    | Orchestrate: context → retrieve → decide no_info vs generate → return reply + sources. |

This is how the RAG will be built: ingestion (chunk → embed → index), retrieval (embed query → search → threshold), and generation (prompt with context → LLM → response), with a clear “no relevant info” path that triggers human handoff.
