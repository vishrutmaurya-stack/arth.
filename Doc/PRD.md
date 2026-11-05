# Product Requirements Document
# Groww Mutual Fund FAQ Assistant (RAG Demo)

**Document owner:** Vishrut  
**Status:** Draft for implementation  
**Source:** `Doc/Problem Statemt`  
**Last updated:** 4 November 2026

---

## 1. Problem statement

Retail users and internal support/content teams need fast, factual answers about a small set of HDFC mutual fund schemes (expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer, benchmark, how to download statements). Today those answers live on public Groww pages and are repeated manually.

Users also ask opinionated questions (“Should I buy/sell?”). Those must not be answered as advice.

This product is a **working RAG prototype**, not a production investment product. Each pipeline stage must persist its output so the demo can show how retrieval-augmented generation works.

## 2. Goals and non-goals

### Goals

- Answer **factual** questions about the in-scope AMC and four HDFC schemes using **only** the five official public pages listed below.
- Return **one source URL** with every answer.
- Refuse advice, portfolio, and performance-comparison questions politely, with a relevant educational link when possible.
- Persist intermediate artifacts for **Data loading → Chunking → Embedding → Vector store → Retrieval → Generation** so each stage can be inspected.
- Keep models, vector DB, and LLM provider **configurable** (config + `.env`).

### Non-goals

- Investment advice, scheme recommendation, or “should I buy/sell” guidance.
- Scraping or following links **inside** the five listed pages.
- Computing or comparing returns, NAV history, or performance rankings.
- Collecting or storing PII (PAN, Aadhaar, account numbers, OTPs, emails, phone numbers).
- Using screenshots of app backends or third-party blogs as sources.
- Multi-AMC coverage, user accounts, or production-scale crawling.

## 3. Users

| Persona | Need |
| --- | --- |
| Retail user comparing schemes | Quick facts (SIP min, exit load, lock-in, riskometer, benchmark) with a link they can verify |
| Support / content team | Same facts for repetitive tickets, without drafting advice |

## 4. In-scope corpus (exactly 5 pages)

Do **not** scrape nested/internal links. Store only these pages.

| # | Entity | URL |
| --- | --- | --- |
| 1 | AMC overview — HDFC Mutual Fund | https://groww.in/mutual-funds/amc/hdfc-mutual-funds |
| 2 | Large Cap — HDFC Large Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| 3 | Flexi Cap — HDFC Flexi Cap Direct Plan Growth | https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth |
| 4 | ELSS (tax saver) — HDFC ELSS Tax Saver Fund Direct Plan Growth | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth |
| 5 | Mid Cap — HDFC Mid Cap Fund Direct Growth | https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth |

**Allowed source class:** official public Groww pages in this list (and, if a refuse/educational path is needed, a single relevant official educational URL such as AMFI/SEBI/Groww help that is already in the submitted source list — never blogs).

## 5. Product experience

### 5.1 UI (tiny)

- Welcome line.
- Three example questions (clickable).
- Persistent note: **“Facts-only. No investment advice.”**
- Chat input + answer area.
- Each answer shows: ≤3 sentences, **one citation link**, and **“Last updated from sources: &lt;timestamp or scrape date&gt;”**.

Suggested example questions:

1. What is the expense ratio of HDFC Large Cap Fund Direct Growth?
2. What is the lock-in for HDFC ELSS Tax Saver Fund Direct Plan Growth?
3. What is the minimum SIP for HDFC Mid Cap Fund Direct Growth?

### 5.2 Answer policy (W1 — think like a model)

| User intent | Behaviour |
| --- | --- |
| Exact fact in corpus (expense ratio, exit load, min SIP, lock-in, riskometer, benchmark, statement download) | Answer from retrieved chunks only; cite the page URL used |
| Fact not on the five pages | Say the fact is not in the indexed official pages; still cite the closest in-scope page if retrieval found one, or state no source |
| Advice / buy-sell / “which is better” / portfolio allocation | Refuse; polite facts-only message; educational link (not a recommendation) |
| Performance / returns / compare CAGR | Do not compute or rank; refuse comparison; point to official factsheet/page if present in corpus, else say not computed |
| PII offered or requested | Do not accept or store; tell the user not to share PII |

### 5.3 Answer format

- Maximum **3 sentences**.
- Exactly **one** citation URL per answer.
- Include **Last updated from sources:** with the ingestion timestamp of the cited page.
- Disclaimer always visible in the UI (not only in the first message).

## 6. Functional requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-1 | Ingest only the five URLs; persist raw HTML/text per URL | P0 |
| FR-2 | Chunk with a strategy suited to Groww scheme/AMC page structure; persist chunks | P0 |
| FR-3 | Embed with `sentence-transformers/all-MiniLM-L6-v2`; persist embeddings metadata | P0 |
| FR-4 | Store vectors in **ChromaDB**; collection name and persist path in config | P0 |
| FR-5 | Retrieve with the **same** embedding model as ingestion | P0 |
| FR-6 | Generate answers with the configured LLM (default Groq); model name from `.env` | P0 |
| FR-7 | Every generated answer includes one source link + last-updated line | P0 |
| FR-8 | Refuse advice and performance claims per §5.2 | P0 |
| FR-9 | Reject/ignore PII in input; do not log PII | P0 |
| FR-10 | Tiny UI with welcome, 3 examples, facts-only note | P0 |
| FR-11 | Config file for chunking, embedding model, Chroma path, retrieval `k`, LLM provider | P0 |
| FR-12 | Swap LLM provider via config/`.env` (Groq default; Gemini, OpenAI, Anthropic, Mistral stubs or adapters) | P1 |
| FR-13 | Demo view or folder of **stage artifacts** (raw → chunks → embeddings → retrieval traces → final answer) | P0 |

## 7. Non-functional requirements

| ID | Requirement |
| --- | --- |
| NFR-1 | Local-first prototype; no requirement for production hosting |
| NFR-2 | Answers grounded in retrieved text; no silent hallucination of numbers |
| NFR-3 | Setup documented so a reviewer can run ingest + chat locally |
| NFR-4 | API keys only in `.env`; never committed |
| NFR-5 | Latency is secondary to correctness and citations for this demo |

## 8. RAG architecture and phased delivery

Each phase **writes explicit artifacts** (files and/or a `data/` tree) so the demo can show the pipeline.

```
URLs (config)
    → Phase 1: Load     → data/raw/{page_id}.html + .txt + metadata.json
    → Phase 2: Chunk    → data/chunks/{page_id}.jsonl
    → Phase 3: Embed    → data/embeddings/ (ids, model name, dim)
    → Phase 4: Store    → chroma persist dir
    → Phase 5: Retrieve → data/traces/{query_id}_retrieval.json
    → Phase 6: Generate → data/traces/{query_id}_generation.json + UI answer
```

### Phase 1 — Data loading

- Fetch the five URLs.
- Extract visible text (scheme facts tables, headings, key labels).
- Save raw HTML, cleaned text, URL, HTTP status, scrape timestamp.
- Fail the page loudly if fetch/parse fails; do not silently skip without a log.

### Phase 2 — Data chunking

The coding agent chooses the strategy from the **actual page shape** after Phase 1 (do not guess before inspecting raw text). Expected pattern for Groww scheme pages: labeled fact rows (Expense ratio, Exit load, Min SIP, etc.) plus narrative sections.

**Default strategy (to confirm after load):**

- **Metadata-aware / section chunks:** one chunk per labeled fact or heading block (expense ratio, exit load, min investment/SIP, lock-in, riskometer, benchmark, about fund, how to download statements if present).
- Keep **source URL + field name** on every chunk.
- Avoid oversized mixed chunks that blend two schemes or AMC + scheme.
- AMC page: chunk by section (about AMC, fund list context) without inventing scheme-level numbers that belong on scheme pages.

Persist: `chunk_id`, `url`, `title`, `section`, `text`, `char_count`.

### Phase 3 — Data embedding

- Model: **`sentence-transformers/all-MiniLM-L6-v2`** (name in config; changeable).
- Persist model id, embedding dimension, and chunk-id mapping.

### Phase 4 — Vector DB

- **ChromaDB**, persistent on disk.
- Collection name, persist directory, and distance metric in config.

### Phase 5 — Data retrieval

- Embed the query with the **same** model as ingestion.
- Query the **same** Chroma collection.
- Persist: query text, top-k ids, scores, chunk texts, URLs.
- `k` in config (suggested 3–5 for this tiny corpus).

### Phase 6 — LLM generation

- Default provider: **Groq**.
- Default model: from `.env` (problem statement: `qwen/qwen3.8-27b` — use the env value as source of truth; correct the id if Groq’s catalog differs).
- Also support wiring for **Gemini, OpenAI, Anthropic, Mistral** via provider switch in config (implement Groq first; other providers as thin adapters if time allows).
- System prompt: facts-only, ≤3 sentences, one citation, refuse advice/performance math, never use PII.

## 9. Configuration

All tunables live in a config file (e.g. `config.yaml` or `config.py`). Secrets live in `.env`.

| Key | Purpose | Default |
| --- | --- | --- |
| `sources` | The five URLs | See §4 |
| `chunking` | Strategy name + size/overlap if used | Section/fact-aware |
| `embedding_model` | Sentence-transformers id | `sentence-transformers/all-MiniLM-L6-v2` |
| `vector_db` | Chroma persist path + collection | local `chroma/` |
| `retrieval.k` | Top-k | `4` |
| `llm.provider` | groq / gemini / openai / anthropic / mistral | `groq` |
| `GROQ_API_KEY` | Secret | `.env` |
| `LLM_MODEL` | Model id | `.env` (Qwen on Groq) |

Changing embedding model or chunking **requires re-ingest**. Retrieval and LLM can change without re-chunking if the embedding model is unchanged.

## 10. Out of scope (explicit)

- Crawling beyond the five URLs  
- User login, holdings, or Groww account APIs  
- Charts of NAV/returns  
- Multi-turn “portfolio construction”  
- Fine-tuning the LLM  

## 11. Success metrics (demo)

- **Grounding:** Sample Q&A (5–10) has correct facts vs the live page at scrape time, each with a working citation.
- **Safety:** Advice and “which fund is better” queries are refused; no PII stored.
- **Format:** Answers ≤3 sentences; last-updated line present.
- **Inspectability:** Reviewer can open files for raw, chunks, embeddings meta, retrieval trace, and final prompt/completion.
- **Reproducibility:** README lets a reviewer ingest + ask a question locally.

## 12. Deliverables (submission)

| Deliverable | Description |
| --- | --- |
| Working prototype | App or notebook; if hosting is unavailable, ≤3-minute demo video |
| Source list | CSV or MD of 15–25 URLs used (the 5 ingest URLs plus any educational/refuse links) |
| README | Setup, scope (AMC + four schemes), known limits |
| Sample Q&A | 5–10 queries with assistant answers + links |
| Disclaimer snippet | Facts-only, no advice — same text as UI |
| Stage artifacts | Explicit data for each RAG stage (demo requirement) |

## 13. Skills this demo must exhibit

- **W1 — Thinking like a model:** Identify the exact fact; answer vs refuse.
- **W2 — LLMs & prompting:** Concise instruction style, polite refusals, citation wording.
- **W3 — RAG only:** Small-corpus retrieval with accurate citations from the official pages.

## 14. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Groww page layout changes / JS-rendered content | Persist raw HTML; document parse failures; prefer static extract of labeled fields |
| Numbers stale vs live site | Show scrape timestamp; do not live-scrape on every chat unless a refresh command is run |
| Model hallucinates a ratio not in chunks | Prompt: answer only from context; if missing, say so |
| Wrong Groq model id | Read `LLM_MODEL` from `.env`; document the working Groq model name in README |
| User pastes PAN/email | Pattern-block and discard; never write to traces |

## 15. Open items

- Confirm Groq model string (`qwen/qwen3.8-27b` vs current Groq catalog).
- After Phase 1, lock chunking strategy in config based on real page structure.
- Whether “how to download capital-gains statement” exists on these five pages; if not, refuse with “not in indexed pages” rather than inventing steps.

---

*This PRD is the implementation contract for the phase-wise RAG FAQ assistant. Implementation should follow phases 1–6 in order and keep artifacts inspectable.*
