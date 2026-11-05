# Architecture
# Groww Mutual Fund FAQ Assistant (RAG Demo)

**Source of truth:** `Doc/PRD.md`  
**Status:** Draft for implementation  
**Last updated:** 4 November 2026

This document describes how the prototype is built. Product rules (answer vs refuse, citations, PII, corpus) stay in the PRD; this file is the technical map.

---

## 1. Design principles

1. **Inspectable RAG.** Every stage writes artifacts to disk. A reviewer can open files and see raw HTML → chunks → embeddings → retrieval → prompt/completion without a debugger.
2. **Config over code.** Embedding model, Chroma path, collection, `k`, chunking strategy, and LLM provider live in config. Secrets live in `.env`.
3. **Same embedder in and out.** Query embeddings use the identical `sentence-transformers` model as ingest. Changing the model requires re-ingest.
4. **Grounded generation.** The LLM may only use retrieved chunk text plus policy instructions. Numbers are never computed from outside the corpus.
5. **Safety before retrieve.** PII and advice/performance intents are classified *before* or independently of generation so traces do not store PAN/email and so advice is not “answered from chunks.”
6. **Local-first.** No user accounts, no Groww private APIs, no production crawler.

---

## 2. System context

```
┌─────────────┐     HTTP GET (5 URLs only)      ┌──────────────────┐
│ Operator    │ ────────────────────────────────►│ groww.in public  │
│ (ingest CLI)│                                  │ scheme / AMC pages│
└──────┬──────┘                                  └──────────────────┘
       │ writes
       ▼
┌─────────────────────────────────────────────────────────────────┐
│ Local app                                                        │
│  config.yaml + .env                                              │
│  data/raw → data/chunks → data/embeddings → chroma persist       │
│  query path: retrieve → generate → data/traces + UI              │
└──────┬──────────────────────────────────────────────────────────┘
       │ HTTPS (chat only)
       ▼
┌─────────────┐     Groq (default) / optional adapters
│ Retail or   │◄──────────────────────────────── Gemini, OpenAI,
│ support user│      Anthropic, Mistral
│ (tiny UI)   │
└─────────────┘
```

**Trust boundary:** Groww HTML is untrusted input (parse carefully, do not execute). User queries are untrusted (PII strip, intent gate). LLM output is untrusted until formatted (length, one URL, last-updated). API keys never leave `.env`.

---

## 3. Runtime split

Two processes, same config and embedding model.

| Runtime | Entry | Writes | Reads | Calls LLM? |
| --- | --- | --- | --- | --- |
| **Ingest** | CLI (`python -m app.ingest` or equivalent) | `data/raw`, `data/chunks`, `data/embeddings`, Chroma persist | `config` sources | No |
| **Serve** | Tiny web UI (Streamlit / FastAPI+static — pick one at implement) | `data/traces/{query_id}_*.json` | Chroma, config, `.env` | Yes |

Ingest is offline and explicit. Chat does **not** re-scrape unless the operator re-runs ingest.

---

## 4. Logical components

```
ingest:
  SourceRegistry → Fetcher → HtmlParser → Chunker → Embedder → ChromaWriter
                                                              ↘ ArtifactWriter

serve:
  UI → PiiGuard → IntentGate → QueryEmbedder → ChromaReader → PromptBuilder → LlmClient → AnswerFormatter
                                        ↘ TraceWriter
```

| Component | Responsibility |
| --- | --- |
| **SourceRegistry** | The five URLs + `page_id`, title, type (`amc` \| `scheme`) from config. Never follows inner links. |
| **Fetcher** | HTTP GET with timeout/UA; saves status; fails loudly per URL. |
| **HtmlParser** | Raw HTML + cleaned visible text; labeled fact rows when present. |
| **Chunker** | Section/fact-aware chunks; metadata: url, title, section, page_id. |
| **Embedder** | `sentence-transformers/all-MiniLM-L6-v2` (config). Used by ingest and serve. |
| **ChromaWriter / Reader** | Persistent collection; metadata filter-capable (url, section). |
| **PiiGuard** | Detect PAN/Aadhaar/account/OTP/email/phone; block; do not write to traces. |
| **IntentGate** | `answer` \| `refuse_advice` \| `refuse_performance` \| `refuse_pii` \| `not_in_corpus` (latter may still retrieve then admit miss). |
| **PromptBuilder** | System policy + top-k chunks + “one citation, ≤3 sentences.” |
| **LlmClient** | Provider adapter; default Groq; model from `LLM_MODEL`. |
| **AnswerFormatter** | Enforce one URL, last-updated from cited page metadata, disclaimer already in UI. |
| **ArtifactWriter / TraceWriter** | JSON/JSONL/HTML on disk for the demo. |

---

## 5. End-to-end data flow

### 5.1 Ingest (Phases 1–4)

```
config.sources[]
    │
    ▼
[Phase 1 Load]
    GET url
    persist  data/raw/{page_id}.html
             data/raw/{page_id}.txt
             data/raw/{page_id}.metadata.json   # url, status, scraped_at, title, page_type
    │
    ▼
[Phase 2 Chunk]
    strategy: section_fact (default; lock after inspecting raw)
    persist  data/chunks/{page_id}.jsonl        # one JSON object per chunk
             data/chunks/_index.json            # counts, strategy name
    │
    ▼
[Phase 3 Embed]
    model.encode(chunk.text)
    persist  data/embeddings/manifest.json      # model id, dim, count
             data/embeddings/ids.json           # chunk_id order
    │
    ▼
[Phase 4 Store]
    chroma.upsert(id, embedding, document, metadata)
    persist  <vector_db.persist_dir>            # Chroma on-disk
```

Chunk record (logical schema):

```json
{
  "chunk_id": "hdfc-large-cap::expense-ratio",
  "page_id": "hdfc-large-cap",
  "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
  "title": "HDFC Large Cap Fund Direct Growth",
  "section": "expense-ratio",
  "page_type": "scheme",
  "text": "Expense ratio: …",
  "char_count": 120,
  "scraped_at": "2026-11-04T09:00:00+05:30"
}
```

Chroma metadata should include `url`, `title`, `section`, `page_id`, `scraped_at` so retrieval traces and citations do not need a second join.

### 5.2 Query (Phases 5–6)

```
UI question
    │
    ▼
PiiGuard ── hit ──► refuse_pii (no retrieve, no LLM, no trace with raw PII)
    │ miss
    ▼
IntentGate
    ├── refuse_advice        → template + educational URL from source list (optional LLM polish)
    ├── refuse_performance   → no compute; link factsheet/page if in corpus else “not computed”
    └── answer | unknown     → retrieve
            │
            ▼
        [Phase 5 Retrieve]
            embed query with same model
            chroma.query(k)
            persist data/traces/{query_id}_retrieval.json
            │
            ▼
        [Phase 6 Generate]
            prompt = policy + chunks
            LLM completion
            persist data/traces/{query_id}_generation.json
            │
            ▼
        AnswerFormatter
            ≤3 sentences, one citation URL (from retrieved metadata),
            “Last updated from sources: {scraped_at of cited page}”
            │
            ▼
        UI
```

If retrieval is empty or chunks do not contain the asked field: generate (or template) **“not in indexed official pages”** — do not invent a number.

---

## 6. Repository layout (target)

```
RAG Chatbot/
  Doc/
    Problem Statemt
    PRD.md
    architecture.md
  config.yaml                 # tunables
  .env.example                # key names, no secrets
  .env                        # gitignored
  README.md
  sources.md                  # 15–25 URLs for submission
  sample_qa.md
  app/
    ingest.py                 # phases 1–4
    serve.py                  # UI entry
    config.py                 # load yaml + env
    pipeline/
      fetch.py
      parse.py
      chunk.py
      embed.py
      store.py
      retrieve.py
      generate.py
      guards.py               # PII + intent
    llm/
      base.py
      groq.py
      gemini.py               # P1 adapter
      openai.py
      anthropic.py
      mistral.py
  data/
    raw/
    chunks/
    embeddings/
    traces/
  chroma/                     # persist dir (gitignored or optional)
```

Stage folders under `data/` are the **demo surface** (FR-13). Do not only keep state inside Chroma.

---

## 7. Chunking strategy

PRD: choose from **actual page shape** after Phase 1. Architecture default until that inspection:

| Page type | Strategy | Why |
| --- | --- | --- |
| Scheme | **One chunk per labeled fact** (expense ratio, exit load, min SIP/investment, lock-in, riskometer, benchmark) + one chunk per remaining heading block (about fund, other narrative) | FAQ queries are field-level; mixing fields causes wrong citations |
| AMC | **One chunk per section** (about AMC, contact/overview). Do not copy scheme-level numbers onto the AMC page | Prevents AMC overview from winning retrieval for “expense ratio of X” |

Rules:

- Never merge two schemes into one chunk.
- Always attach `url` + `section`.
- If a fallback size/overlap splitter is needed for long narrative, it is a config override (`chunking.strategy: recursive`, `size`, `overlap`) — not the default for fact rows.

Lock `chunking.strategy` in `config.yaml` after the first successful load.

---

## 8. Embedding and vector store

| Item | Choice |
| --- | --- |
| Model | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| Device | CPU is enough for this corpus |
| Store | ChromaDB persistent client |
| Distance | Cosine (set in config; keep consistent) |
| `k` | 4 default (range 3–5) |
| Ids | Stable `chunk_id` so re-ingest upserts instead of duplicating |

**Re-ingest required when:** embedding model name changes, chunking strategy changes, or source HTML is refreshed.

**No re-ingest when:** `k`, LLM provider, or system prompt changes.

---

## 9. LLM layer

```
LlmClient.complete(system, user) -> text
        ▲
        │
   provider from config.llm.provider
        │
   ┌────┴────────────────────────────┐
   groq (P0)   gemini  openai  anthropic  mistral
```

- **P0:** Groq adapter. Model id = `LLM_MODEL` in `.env` (PRD placeholder `qwen/qwen3.8-27b`; README records the id that actually works on Groq).
- **P1:** Other providers as thin adapters sharing the same `complete()` interface. Missing API key → clear error, no silent fallback that changes providers.
- Temperature low (e.g. 0–0.2) for factual extraction.
- No tool-calling required for v1.

### System policy (logical, not final wording)

- Answer only from CONTEXT.
- ≤3 sentences.
- Facts only; no buy/sell, no ranking, no computed returns.
- If CONTEXT lacks the fact, say so.
- Citation URL is chosen by the **application** from the chunk that supports the answer (not a URL hallucinated by the model). Preferred: model returns `source_chunk_id` or the formatter picks the top chunk whose `section` matches the question; always emit a URL that exists in retrieval metadata.

---

## 10. Safety architecture

```
                    ┌─────────────┐
   query ──────────►│ PiiGuard    │── yes ──► canned refuse; redact; no disk of secrets
                    └──────┬──────┘
                           │ no
                    ┌──────▼──────┐
                    │ IntentGate  │── advice / performance ──► refuse template
                    └──────┬──────┘      + educational URL from allowlist
                           │ factual
                    ┌──────▼──────┐
                    │ RAG retrieve│
                    └─────────────┘
```

**PII:** regex/pattern list for PAN, Aadhaar, phone, email, OTP-like 4–8 digit codes, account numbers. On hit: do not persist raw query. Optional: persist `query_id` + `pii_blocked: true` only.

**Educational URLs:** only from `sources.md` / config `educational_links[]` (AMFI/SEBI/Groww help). Never blogs.

**Citation integrity:** formatter rejects any URL not in the five ingest URLs (or the single educational URL on refuse paths).

---

## 11. UI architecture

Single page:

- Header: product name + **“Facts-only. No investment advice.”** (always visible)
- Welcome line
- Three example question buttons (PRD §5.1)
- Input + send
- Answer card: body, citation `<a href>`, `Last updated from sources: …`

No chat history store required beyond the current session (optional in-memory list). No auth.

Optional **debug panel** (demo): show retrieved chunk ids and scores from the last trace file. Nice-to-have, not a PRD must, as long as `data/traces/` exists.

---

## 12. Configuration and secrets

`config.yaml` (illustrative keys; names may match loader):

```yaml
sources: [ { id, title, type, url }, ... ]
chunking:
  strategy: section_fact
  size: 512          # unused unless strategy is recursive
  overlap: 64
embedding_model: sentence-transformers/all-MiniLM-L6-v2
vector_db:
  persist_dir: chroma
  collection: groww_hdfc_mf
  distance: cosine
retrieval:
  k: 4
llm:
  provider: groq
educational_links:
  - url: ...
    use_for: [advice, performance]
```

`.env`:

```
GROQ_API_KEY=
LLM_MODEL=
# optional provider keys for P1
```

Never commit `.env`. Never write API keys into traces.

---

## 13. Error handling

| Failure | Behaviour |
| --- | --- |
| Fetch 4xx/5xx or empty body | Log; write `metadata.json` with error; do not chunk that page; ingest exit ≠ 0 if any source fails |
| Parse finds no fact labels | Persist raw text as section chunks; warn in ingest log |
| Chroma empty at serve | UI error: run ingest first |
| LLM timeout / 401 | User-visible error; still write retrieval trace if retrieve succeeded |
| Embedding model download fail | Ingest/serve fail fast with setup hint in README |

---

## 14. Observability for the demo

| Stage | Artifact | Reviewer sees |
| --- | --- | --- |
| Load | `data/raw/*` | Exact HTML and cleaned text |
| Chunk | `data/chunks/*.jsonl` | Field-level pieces + URLs |
| Embed | `data/embeddings/manifest.json` | Model name and dimension |
| Store | Chroma persist + collection count in ingest log | Vectors exist |
| Retrieve | `*_retrieval.json` | Query, k, scores, chunk texts |
| Generate | `*_generation.json` | System/user prompt (redacted), completion, chosen citation |

Traces must **not** contain PII or API keys.

---

## 15. Implementation sequence

Aligns with PRD phases; do not skip artifact writes.

1. Config + SourceRegistry + folder layout  
2. Phase 1 fetch/parse → inspect HTML → lock chunking in config  
3. Phase 2–4 ingest CLI  
4. Phase 5 retrieve + dump traces  
5. Guards + Phase 6 Groq generation + formatter  
6. Tiny UI  
7. P1 LLM adapters if time  
8. README, `sources.md`, `sample_qa.md`, disclaimer text matching UI  

---

## 16. Out of architecture (same as PRD non-goals)

No crawl graph, no holdings APIs, no returns math, no fine-tuning, no multi-tenant auth, no online re-index on each question.

---

*Implementation should follow this map and remain consistent with `Doc/PRD.md`.*
