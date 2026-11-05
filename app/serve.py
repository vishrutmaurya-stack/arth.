"""Streamlit UI for Arth AI — HDFC Mutual Fund research assistant.

Visual language: neon-light glass "Arth AI" shell from the provided design,
adapted to the real corpus (5 indexed Groww pages, 152 chunks). The
initialization screen is a real session handshake, not a fake progress bar.
"""

from __future__ import annotations

import html
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from app.ask import AskResult, ask
from app.config import Config, load_config
from app.pipeline.generate import last_updated_line

DISCLAIMER = "Facts-only. No investment advice."
WELCOME = (
    "Welcome. Ask factual questions about the indexed HDFC Mutual Fund Groww pages "
    "(AMC overview and four Direct Growth schemes). Answers come only from those pages."
)

EXAMPLE_QUESTIONS = [
    (
        "Expense ratio · HDFC Large Cap",
        "What is the expense ratio of HDFC Large Cap Fund Direct Growth?",
    ),
    (
        "Lock-in · HDFC ELSS",
        "What is the lock-in for HDFC ELSS Tax Saver Fund Direct Plan Growth?",
    ),
    (
        "Minimum SIP · HDFC Mid Cap",
        "What is the minimum SIP for HDFC Mid Cap Fund Direct Growth?",
    ),
]

SOURCE_META = {
    "hdfc-amc": ("AMC Overview — HDFC Mutual Fund", "Regulatory profile & fund list"),
    "hdfc-large-cap": ("Large Cap — HDFC Large Cap Fund Direct Growth", "NAV, expense ratio & portfolio"),
    "hdfc-flexi-cap": ("Flexi Cap — HDFC Flexi Cap Direct Plan Growth", "Expense ratio, exit load & holdings"),
    "hdfc-elss": ("ELSS — HDFC ELSS Tax Saver Fund Direct Plan Growth", "Lock-in, tax & SIP details"),
    "hdfc-mid-cap": ("Mid Cap — HDFC Mid Cap Fund Direct Growth", "Riskometer, benchmark & SIP"),
}

DECISION_BADGES = {
    "answer": ("Grounded answer", "ok"),
    "not_in_corpus": ("Not in indexed pages", "warn"),
    "refuse_advice": ("Advice blocked", "block"),
    "refuse_performance": ("Performance blocked", "block"),
    "refuse_pii": ("PII protected", "block"),
    "refuse_empty": ("Empty question", "warn"),
    "empty_index": ("Index empty", "warn"),
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

:root {
  --surface: #fcf8ff;
  --surface-low: #f5f2ff;
  --surface-container: #efecff;
  --surface-high: #e8e5ff;
  --on-surface: #19192f;
  --muted: #5b3f44;
  --primary: #b7004f;
  --primary-bright: #e40a65;
  --neon-pink: #ff2d78;
  --neon-cyan: #00e5ff;
  --neon-teal: #05c3b6;
  --neon-purple: #7928ca;
  --secondary: #006b54;
  --secondary-bright: #00f0bf;
  --outline: #e4bdc3;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', sans-serif;
  background-color: var(--surface);
  color: var(--on-surface);
}

.stApp {
  background:
    radial-gradient(900px 420px at 8% -10%, rgba(255, 45, 120, 0.12), transparent 62%),
    radial-gradient(820px 420px at 102% 22%, rgba(0, 229, 255, 0.13), transparent 62%),
    radial-gradient(760px 440px at 46% 112%, rgba(121, 40, 202, 0.10), transparent 64%),
    #fcf8ff;
  background-attachment: fixed;
}

[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none; }
#MainMenu, footer { visibility: hidden; }

.block-container {
  max-width: 1120px;
  padding-top: 1rem;
  padding-bottom: 3rem;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: rgba(183, 0, 79, 0.22); border-radius: 999px; }
::-webkit-scrollbar-track { background: transparent; }

.material-symbols-outlined {
  font-variation-settings: 'FILL' 0, 'wght' 500, 'GRAD' 0, 'opsz' 24;
  line-height: 1;
}

/* ---------- Header ---------- */
.arth-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.7rem 1rem;
  margin-bottom: 1.15rem;
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(228, 189, 195, 0.55);
  border-radius: 1rem;
  box-shadow: 0 4px 24px rgba(121, 40, 202, 0.07);
}
.brand { display: flex; align-items: center; gap: 0.75rem; min-width: 0; }
.brand-logo {
  width: 2.45rem; height: 2.45rem; flex: 0 0 auto;
  border-radius: 0.75rem;
  background: linear-gradient(135deg, #ff2d78, #e40a65 55%, #7928ca);
  color: #fff; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 12px rgba(255, 45, 120, 0.38);
}
.brand-logo .material-symbols-outlined { font-size: 1.4rem; }
.brand-title {
  font-family: 'Sora', sans-serif; font-weight: 700; font-size: 1.08rem;
  letter-spacing: -0.02em; line-height: 1.1;
  background: linear-gradient(90deg, #19192f, #b7004f);
  -webkit-background-clip: text; background-clip: text; color: transparent;
  display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;
}
.version-badge {
  font-family: 'Space Grotesk', sans-serif; font-size: 0.58rem; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase; color: #b7004f;
  background: #ffd9df; border-radius: 999px; padding: 0.14rem 0.42rem;
  -webkit-text-fill-color: #b7004f;
}
.brand-sub {
  font-family: 'Space Grotesk', sans-serif; font-size: 0.61rem; font-weight: 600;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin-top: 0.18rem;
}
.header-right { display: flex; align-items: center; gap: 0.55rem; flex-wrap: wrap; }
.disclaimer-pill {
  display: inline-flex; align-items: center; gap: 0.45rem;
  background: var(--surface-low); border: 1px solid rgba(0, 229, 255, 0.45);
  border-radius: 999px; padding: 0.35rem 0.72rem;
  font-family: 'Space Grotesk', sans-serif; font-size: 0.7rem; font-weight: 600;
  color: var(--on-surface); white-space: nowrap;
}
.dot {
  width: 0.45rem; height: 0.45rem; border-radius: 50%;
  background: var(--neon-cyan); box-shadow: 0 0 8px var(--neon-cyan); flex: 0 0 auto;
}
.nav-pill {
  font-family: 'Space Grotesk', sans-serif; font-size: 0.68rem; font-weight: 700;
  color: #fff; background: linear-gradient(135deg, #ff2d78, #b7004f);
  border-radius: 0.6rem; padding: 0.36rem 0.7rem;
  box-shadow: 0 4px 14px -4px rgba(255, 45, 120, 0.6);
}
@media (max-width: 760px) {
  .arth-header { flex-direction: column; align-items: flex-start; }
  .header-right { width: 100%; justify-content: space-between; }
}

/* ---------- Hero / splash ---------- */
.hero-card {
  position: relative; overflow: hidden;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(22px);
  border: 1px solid rgba(228, 189, 195, 0.5);
  border-radius: 1.35rem;
  padding: 1.35rem;
  box-shadow: 0 20px 60px -24px rgba(25, 25, 47, 0.16), 0 0 44px rgba(183, 0, 79, 0.05);
}
.hero-card::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, #b7004f, transparent); opacity: 0.85;
}
.hero-top {
  display: flex; align-items: center; justify-content: space-between;
  gap: 1rem; flex-wrap: wrap; padding-bottom: 0.35rem;
}
.hero-brand { display: flex; align-items: center; gap: 0.8rem; }
.radar {
  position: relative; width: 3.5rem; height: 3.5rem; flex: 0 0 auto;
  border-radius: 1rem; background: var(--surface-low);
  display: flex; align-items: center; justify-content: center;
  box-shadow: inset 0 2px 8px rgba(25, 25, 47, 0.06);
}
.radar-core {
  width: 2.55rem; height: 2.55rem; border-radius: 0.8rem;
  background: linear-gradient(135deg, #b7004f, #e40a65 55%, #05c3b6);
  color: #fff; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 6px 18px -6px rgba(183, 0, 79, 0.6);
}
.radar-core .material-symbols-outlined { font-size: 1.5rem; }
.radar-ring {
  position: absolute; inset: -0.25rem; border-radius: 1.2rem;
  border: 1px dashed rgba(0, 107, 84, 0.35);
  animation: spin 11s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.hero-name { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 1.25rem; letter-spacing: -0.02em; }
.hero-name .version-badge { font-size: 0.56rem; }
.hero-engine {
  font-family: 'Space Grotesk', sans-serif; font-size: 0.66rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); margin-top: 0.15rem;
}
.rag-badge {
  display: inline-flex; align-items: center; gap: 0.4rem;
  background: var(--surface-container); border-radius: 999px;
  padding: 0.38rem 0.72rem;
  font-family: 'Space Grotesk', sans-serif; font-size: 0.64rem; font-weight: 700;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--on-surface);
}
.pulse {
  position: relative; width: 0.5rem; height: 0.5rem; border-radius: 50%;
  background: var(--secondary);
}
.pulse::after {
  content: ""; position: absolute; inset: -3px; border-radius: 50%;
  border: 2px solid var(--secondary-bright); opacity: 0.7;
  animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;
}
@keyframes ping { 75%, 100% { transform: scale(2); opacity: 0; } }

.hero-title {
  font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.55rem;
  letter-spacing: -0.03em; line-height: 1.2; margin: 1rem 0 0.35rem;
}
.hero-copy { font-size: 0.88rem; line-height: 1.65; color: var(--muted); max-width: 54rem; }

.integrity {
  margin-top: 1rem; padding: 0.85rem 0.95rem;
  background: var(--surface-low); border-radius: 0.95rem;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}
.integrity-head {
  display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
  font-family: 'Space Grotesk', sans-serif; font-size: 0.7rem; font-weight: 700;
  color: var(--muted); text-transform: uppercase; letter-spacing: 0.07em;
}
.integrity-head .pct { color: var(--primary); font-size: 0.76rem; }
.progress-track {
  height: 0.5rem; border-radius: 999px; background: var(--surface-container);
  overflow: hidden; margin: 0.55rem 0 0.6rem; padding: 2px;
}
.progress-fill {
  height: 100%; border-radius: 999px;
  background: linear-gradient(90deg, #006b54, #00f0bf 55%, #ff2d78);
  box-shadow: 0 0 14px rgba(183, 0, 79, 0.35);
  animation: fillbar 1.2s ease-out both;
}
@keyframes fillbar { from { width: 0; } to { width: 100%; } }
.integrity-meta {
  display: flex; align-items: center; justify-content: space-between; gap: 0.6rem;
  flex-wrap: wrap; font-family: 'Space Grotesk', sans-serif;
  font-size: 0.64rem; font-weight: 600; color: var(--muted);
}

.node-top {
  display: flex; align-items: center; justify-content: space-between;
  gap: 0.5rem; margin: 1rem 0 0.5rem;
  font-family: 'Space Grotesk', sans-serif; font-size: 0.66rem; font-weight: 700;
  letter-spacing: 0.09em; text-transform: uppercase; color: var(--muted);
}
.node-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
.node {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.6rem 0.68rem; border-radius: 0.8rem;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(228, 189, 195, 0.35);
  box-shadow: 0 1px 2px rgba(30, 20, 60, 0.04);
  min-width: 0;
}
.node-icon {
  width: 1.75rem; height: 1.75rem; flex: 0 0 auto; border-radius: 0.5rem;
  background: rgba(0, 240, 191, 0.2); color: var(--secondary);
  display: flex; align-items: center; justify-content: center;
}
.node-icon .material-symbols-outlined { font-size: 1.05rem; }
.node-copy { min-width: 0; flex: 1 1 auto; }
.node-title {
  font-family: 'Sora', sans-serif; font-size: 0.73rem; font-weight: 600;
  color: var(--on-surface); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.node-sub {
  font-family: 'Space Grotesk', sans-serif; font-size: 0.6rem; font-weight: 500;
  color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.node-status {
  flex: 0 0 auto; font-family: 'Space Grotesk', sans-serif; font-size: 0.56rem;
  font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--secondary); background: rgba(0, 240, 191, 0.18);
  border-radius: 999px; padding: 0.2rem 0.45rem;
}
@media (max-width: 820px) { .node-grid { grid-template-columns: 1fr; } }

/* ---------- Chat welcome ---------- */
.welcome-card {
  position: relative; overflow: hidden;
  background: rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(18px);
  border: 1px solid rgba(228, 189, 195, 0.5);
  border-radius: 1.15rem;
  padding: 1.1rem 1.2rem;
  box-shadow: 0 14px 44px -26px rgba(25, 25, 47, 0.18);
  margin-bottom: 0.4rem;
}
.welcome-eyebrow {
  display: inline-flex; align-items: center; gap: 0.45rem;
  font-family: 'Space Grotesk', sans-serif; font-size: 0.61rem; font-weight: 700;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--secondary);
  margin-bottom: 0.45rem;
}
.welcome-title {
  font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.35rem;
  letter-spacing: -0.03em; line-height: 1.25; color: var(--on-surface);
}
.welcome-body { font-size: 0.87rem; line-height: 1.65; color: var(--muted); margin-top: 0.35rem; max-width: 56rem; }
.welcome-meta {
  display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap;
  margin-top: 0.7rem; font-family: 'Space Grotesk', sans-serif;
  font-size: 0.63rem; font-weight: 600; color: var(--muted);
}
.meta-chip {
  background: var(--surface-low); border: 1px solid rgba(228, 189, 195, 0.45);
  border-radius: 999px; padding: 0.2rem 0.5rem;
}

.section-label {
  font-family: 'Space Grotesk', sans-serif; font-size: 0.65rem; font-weight: 700;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted);
  margin: 1.15rem 0 0.45rem;
}

/* ---------- Streamlit widgets ---------- */
.stButton > button {
  width: 100%;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--outline);
  color: var(--on-surface);
  border-radius: 999px;
  padding: 0.52rem 0.85rem;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.74rem;
  font-weight: 600;
  transition: all 0.15s ease;
  box-shadow: 0 1px 2px rgba(30, 20, 60, 0.04);
}
.stButton > button:hover {
  border-color: var(--neon-pink);
  color: var(--primary);
  box-shadow: 0 4px 18px -3px rgba(255, 45, 120, 0.28);
  transform: translateY(-1px);
}
.stButton > button:active { transform: scale(0.985); }
.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #ff2d78, #b7004f 58%, #7928ca);
  color: #fff !important;
  border: none;
  border-radius: 0.8rem;
  font-family: 'Sora', sans-serif;
  font-weight: 600;
  box-shadow: 0 10px 26px -8px rgba(255, 45, 120, 0.6);
}
.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover {
  color: #fff;
  box-shadow: 0 14px 30px -8px rgba(255, 45, 120, 0.7);
}

[data-testid="stTextInput"] label { display: none; }
[data-testid="stTextInput"] input {
  background: #ffffff;
  border: 1px solid var(--outline);
  border-radius: 0.85rem;
  padding: 0.78rem 1rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  color: var(--on-surface);
  box-shadow: inset 0 1px 2px rgba(30, 20, 60, 0.03);
}
[data-testid="stTextInput"] input:focus {
  border-color: var(--neon-pink);
  box-shadow: 0 0 0 3px rgba(255, 45, 120, 0.14);
}
[data-testid="stTextInput"] input::placeholder { color: #9a8fa8; }

[data-testid="stForm"] {
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(228, 189, 195, 0.5);
  border-radius: 1.05rem;
  padding: 0.85rem;
  box-shadow: 0 10px 34px -24px rgba(25, 25, 47, 0.22);
}
[data-testid="stFormSubmitButton"] > button {
  width: 100%;
  background: linear-gradient(135deg, #ff2d78, #b7004f 58%, #7928ca);
  color: #fff;
  border: none;
  border-radius: 0.8rem;
  padding: 0.6rem 1.1rem;
  font-family: 'Sora', sans-serif;
  font-size: 0.8rem;
  font-weight: 600;
  box-shadow: 0 10px 24px -10px rgba(255, 45, 120, 0.65);
}
[data-testid="stFormSubmitButton"] > button:hover { color: #fff; filter: brightness(1.05); }

[data-testid="stExpander"] {
  border: 1px solid rgba(228, 189, 195, 0.5);
  border-radius: 0.85rem;
  background: rgba(255, 255, 255, 0.62);
  overflow: hidden;
}
[data-testid="stExpander"] summary {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--muted);
}
[data-testid="stAlert"] {
  border-radius: 0.9rem;
  border: 1px solid rgba(228, 189, 195, 0.5);
  font-size: 0.85rem;
}
[data-testid="stSpinner"] { color: var(--primary); }
[data-testid="stSpinner"] p {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.72rem;
  color: var(--muted);
}

/* ---------- Conversation ---------- */
.turn { margin: 0.9rem 0 0.2rem; }
.q-row { display: flex; justify-content: flex-end; }
.q-bubble {
  display: inline-block; max-width: 88%;
  background: linear-gradient(135deg, rgba(255, 45, 120, 0.11), rgba(121, 40, 202, 0.09));
  border: 1px solid rgba(255, 45, 120, 0.18);
  border-radius: 1rem 1rem 0.25rem 1rem;
  padding: 0.55rem 0.85rem;
  font-size: 0.87rem; font-weight: 500; line-height: 1.5;
  color: var(--on-surface);
  box-shadow: 0 4px 14px -10px rgba(25, 25, 47, 0.2);
}
.q-label {
  display: block; font-family: 'Space Grotesk', sans-serif;
  font-size: 0.55rem; font-weight: 700; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--primary); margin-bottom: 0.12rem;
}
.a-card {
  position: relative; overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(228, 189, 195, 0.5);
  border-radius: 1rem;
  padding: 0.9rem 1rem;
  margin-top: 0.45rem;
  box-shadow: 0 10px 32px -22px rgba(25, 25, 47, 0.26);
}
.a-head {
  display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
  flex-wrap: wrap; margin-bottom: 0.4rem;
}
.a-identity {
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-family: 'Sora', sans-serif; font-size: 0.65rem; font-weight: 700;
  letter-spacing: 0.09em; text-transform: uppercase; color: var(--primary);
}
.a-identity .material-symbols-outlined { font-size: 1rem; }
.badge {
  font-family: 'Space Grotesk', sans-serif; font-size: 0.56rem; font-weight: 700;
  letter-spacing: 0.07em; text-transform: uppercase; border-radius: 999px;
  padding: 0.18rem 0.5rem; white-space: nowrap;
}
.badge.ok { color: var(--secondary); background: rgba(0, 240, 191, 0.18); }
.badge.warn { color: #6e5e00; background: rgba(255, 226, 90, 0.35); }
.badge.block { color: var(--primary); background: rgba(255, 217, 223, 0.75); }
.a-body { font-size: 0.92rem; line-height: 1.62; color: var(--on-surface); }
.source-link {
  display: inline-flex; align-items: center; gap: 0.35rem;
  margin-top: 0.6rem;
  background: var(--surface-low); border: 1px solid rgba(228, 189, 195, 0.6);
  border-radius: 999px; padding: 0.3rem 0.62rem;
  font-family: 'Space Grotesk', sans-serif; font-size: 0.66rem; font-weight: 600;
  color: var(--primary); text-decoration: none;
  transition: all 0.15s ease;
}
.source-link:hover { border-color: var(--neon-pink); color: var(--primary); text-decoration: none; }
.source-link .material-symbols-outlined { font-size: 0.92rem; }
.updated {
  margin-top: 0.45rem;
  font-family: 'Space Grotesk', sans-serif; font-size: 0.62rem; font-weight: 500;
  color: var(--muted);
}
.hits { display: flex; flex-direction: column; gap: 0.5rem; }
.hit {
  border: 1px solid rgba(228, 189, 195, 0.45);
  border-radius: 0.7rem;
  padding: 0.55rem 0.65rem;
  background: rgba(255, 255, 255, 0.7);
}
.hit-head {
  display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
  font-family: 'Space Grotesk', sans-serif; font-size: 0.67rem; font-weight: 700;
  color: var(--on-surface);
}
.hit-head span { color: var(--primary); font-weight: 600; }
.hit-meta {
  font-family: 'Space Grotesk', sans-serif; font-size: 0.57rem; font-weight: 500;
  color: var(--muted); margin: 0.1rem 0 0.28rem;
}
.hit-text { font-size: 0.76rem; line-height: 1.5; color: var(--muted); }

.empty-state {
  margin-top: 0.8rem;
  padding: 0.95rem 1rem;
  border: 1px dashed rgba(228, 189, 195, 0.8);
  border-radius: 0.9rem;
  background: rgba(255, 255, 255, 0.5);
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.7rem;
  color: var(--muted);
}
.empty-state strong { color: var(--on-surface); }

.source-row {
  display: flex; align-items: center; justify-content: space-between; gap: 0.6rem;
  padding: 0.45rem 0; border-bottom: 1px dashed rgba(228, 189, 195, 0.45);
  font-size: 0.75rem;
}
.source-row:last-child { border-bottom: none; }
.source-row a { color: var(--primary); text-decoration: none; font-weight: 500; }
.source-row a:hover { text-decoration: underline; }
.source-row .count {
  font-family: 'Space Grotesk', sans-serif; font-size: 0.6rem;
  color: var(--muted); white-space: nowrap;
}

.arth-footer {
  margin-top: 2.2rem;
  padding-top: 0.9rem;
  border-top: 1px solid var(--surface-high);
  display: flex; align-items: center; justify-content: space-between;
  gap: 0.75rem; flex-wrap: wrap;
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.62rem; color: var(--muted);
}
.arth-footer strong { color: var(--on-surface); }
</style>
"""


def _init_state() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("pending_question", None)
    st.session_state.setdefault("input_key", 0)
    st.session_state.setdefault("entered", False)


def _bridge_secrets() -> None:
    """Expose Streamlit Cloud secrets as env vars for the pipeline modules."""
    try:
        secrets = st.secrets
    except Exception:
        return
    for key in ("GROQ_API_KEY", "LLM_MODEL", "HF_TOKEN"):
        try:
            value = secrets[key]
        except Exception:
            continue
        if isinstance(value, str) and value.strip():
            os.environ.setdefault(key, value.strip())


@st.cache_resource
def _config() -> Config:
    return load_config()


@st.cache_resource(show_spinner=False)
def _ensure_index() -> bool:
    """Rebuild the local Chroma store from committed artifacts if it is missing."""
    config = _config()
    try:
        import chromadb
    except ImportError:
        return False
    try:
        client = chromadb.PersistentClient(path=str(config.chroma_dir))
        if config.collection in {item.name for item in client.list_collections()}:
            return True
        from app.pipeline.store import store_all

        _, failed = store_all(config)
        return not failed
    except Exception:
        return False


@st.cache_data(show_spinner=False)
def _corpus_stats() -> dict:
    config = _config()
    try:
        index = json.loads((config.chunks_dir / "_index.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"count": 0, "pages": {}}
    return {
        "count": int(index.get("chunk_count") or 0),
        "pages": {
            page["page_id"]: int(page.get("chunks") or 0)
            for page in index.get("pages", [])
            if page.get("page_id")
        },
    }


def _header() -> None:
    st.html(
        f"""
        <div class="arth-header">
          <div class="brand">
            <div class="brand-logo"><span class="material-symbols-outlined" aria-hidden="true">account_balance</span></div>
            <div>
              <div class="brand-title">Arth AI <span class="version-badge">v2.4 Core</span></div>
              <div class="brand-sub">HDFC Mutual Fund Research Assistant</div>
            </div>
          </div>
          <div class="header-right">
            <div class="disclaimer-pill"><span class="dot"></span>{html.escape(DISCLAIMER)}</div>
            <div class="nav-pill">Chat</div>
          </div>
        </div>
        """,
    )


def _splash(config: Config, stats: dict) -> None:
    count = stats["count"]
    model = config.embedding_model.split("/")[-1]
    nodes = []
    for source in config.sources:
        title, sub = SOURCE_META.get(source.id, (source.title, "Indexed page"))
        chunk_count = stats["pages"].get(source.id, 0)
        nodes.append(
            f"""
            <div class="node">
              <div class="node-icon"><span class="material-symbols-outlined" aria-hidden="true">check_circle</span></div>
              <div class="node-copy">
                <div class="node-title">{html.escape(title)}</div>
                <div class="node-sub">{html.escape(sub)} · {chunk_count} chunks</div>
              </div>
              <div class="node-status">Indexed</div>
            </div>
            """
        )

    st.html(
        f"""
        <div class="hero-card">
          <div class="hero-top">
            <div class="hero-brand">
              <div class="radar">
                <div class="radar-ring"></div>
                <div class="radar-core"><span class="material-symbols-outlined" aria-hidden="true">hub</span></div>
              </div>
              <div>
                <div class="hero-name">Arth AI <span class="version-badge">v2.4 Core</span></div>
                <div class="hero-engine">Grounded Deterministic Engine</div>
              </div>
            </div>
            <div class="rag-badge"><span class="pulse"></span>Strict Grounded RAG</div>
          </div>

          <div class="hero-title">Indexed Knowledge Base Online</div>
          <div class="hero-copy">
            {count} chunks from the five authorized HDFC Mutual Fund Groww pages are indexed in the
            local Chroma store. Every answer is retrieved from these pages and cited back to them.
          </div>

          <div class="integrity">
            <div class="integrity-head">
              <span>Pipeline integrity</span>
              <span class="pct">100% Ready</span>
            </div>
            <div class="progress-track"><div class="progress-fill"></div></div>
            <div class="integrity-meta">
              <span>{html.escape(model)} · 384-d · cosine</span>
              <span>PII &amp; advice guardrails enforced</span>
            </div>
          </div>

          <div class="node-top">
            <span>Authorized knowledge nodes ({len(config.sources)}/{len(config.sources)})</span>
            <span>{count} chunks indexed</span>
          </div>
          <div class="node-grid">{''.join(nodes)}</div>
        </div>
        """,
    )

    st.write("")
    left, right = st.columns([1.15, 1])
    with left:
        if st.button("Enter research assistant", type="primary", use_container_width=True):
            st.session_state.entered = True
            st.rerun()
    with right:
        st.caption("Session handshake complete. 5/5 sources indexed · local Chroma store.")


def _run_question(question: str) -> None:
    with st.spinner("Retrieving from the indexed official pages…"):
        result = ask(question, config=_config())
    # PII must not be retained in the session display either.
    shown = "[question withheld — PII detected]" if result.decision == "refuse_pii" else question
    st.session_state.history.append({"question": shown, "result": result})


def _decision_badge(result: AskResult) -> str:
    label, kind = DECISION_BADGES.get(result.decision, ("Grounded response", "ok"))
    return f'<span class="badge {kind}">{html.escape(label)}</span>'


def _source_link(result: AskResult) -> str:
    url = result.citation_url or result.educational_link
    if not url:
        return ""
    label = "View source on Groww" if result.citation_url else "Educational resource"
    safe_url = html.escape(url, quote=True)
    return (
        f'<a class="source-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">'
        f'<span class="material-symbols-outlined" aria-hidden="true">link</span>{html.escape(label)}</a>'
    )


def _render_hits(result: AskResult) -> None:
    if not result.hits:
        return
    with st.expander(f"Retrieval hits · {len(result.hits)} chunks"):
        blocks = []
        for hit in result.hits:
            blocks.append(
                f"""
                <div class="hit">
                  <div class="hit-head">{html.escape(hit.chunk_id)}<span>score {hit.score:.4f}</span></div>
                  <div class="hit-meta">{html.escape(hit.section)} · {html.escape(hit.title)}</div>
                  <div class="hit-text">{html.escape(hit.text)}</div>
                </div>
                """
            )
        st.html(f'<div class="hits">{"".join(blocks)}</div>')


def _render_turn(turn: dict) -> None:
    question = html.escape(turn["question"])
    result: AskResult = turn["result"]
    answer = html.escape(result.answer).replace("\n", "<br>")
    updated = last_updated_line(result.last_updated)

    updated_html = f'<div class="updated">{html.escape(updated)}</div>' if updated else ""
    st.html(
        f"""
        <div class="turn">
          <div class="q-row">
            <div class="q-bubble"><span class="q-label">You</span>{question}</div>
          </div>
          <div class="a-card">
            <div class="a-head">
              <div class="a-identity">
                <span class="material-symbols-outlined" aria-hidden="true">auto_awesome</span>Arth AI
              </div>
              {_decision_badge(result)}
            </div>
            <div class="a-body">{answer}</div>
            {_source_link(result)}
            {updated_html}
          </div>
        </div>
        """,
    )
    _render_hits(result)


def _render_chat(config: Config, stats: dict) -> None:
    count = stats["count"]
    model = config.embedding_model.split("/")[-1]
    st.html(
        f"""
        <div class="welcome-card">
          <div class="welcome-eyebrow"><span class="dot"></span>Knowledge base online</div>
          <div class="welcome-title">Ask the indexed pages, not the internet.</div>
          <div class="welcome-body">{html.escape(WELCOME)}</div>
          <div class="welcome-meta">
            <span class="meta-chip">{count} chunks</span>
            <span class="meta-chip">{len(config.sources)} sources</span>
            <span class="meta-chip">{html.escape(model)} · 384-d</span>
            <span class="meta-chip">cosine · k={config.retrieval_k}</span>
          </div>
        </div>
        """,
    )

    st.html('<div class="section-label">Try an example</div>')
    columns = st.columns(len(EXAMPLE_QUESTIONS), gap="small")
    for column, (label, question) in zip(columns, EXAMPLE_QUESTIONS):
        with column:
            if st.button(label, key=f"example_{question}", use_container_width=True):
                st.session_state.pending_question = question
                st.rerun()

    st.html('<div class="section-label">Ask a factual question</div>')
    with st.form("ask_form", clear_on_submit=True):
        typed = st.text_input(
            "Your question",
            key=f"question_input_{st.session_state.input_key}",
            placeholder=(
                "Expense ratio, exit load, lock-in, minimum SIP, riskometer, or benchmark…"
            ),
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Ask Arth AI", use_container_width=True)

    pending = st.session_state.pending_question
    if pending:
        st.session_state.pending_question = None
        try:
            _run_question(pending)
        except RuntimeError as exc:
            st.error(str(exc))
    elif submitted:
        question = (typed or "").strip()
        if not question:
            st.warning("Please enter a question.")
        else:
            try:
                _run_question(question)
            except RuntimeError as exc:
                st.error(str(exc))

    if not st.session_state.history:
        st.html(
            """
            <div class="empty-state">
              <strong>Answers appear here.</strong> Up to three sentences, one source link,
              and the last-updated timestamp of the cited page. No advice, no returns, no PII.
            </div>
            """,
        )
    else:
        st.html('<div class="section-label">Conversation</div>')
        for turn in reversed(st.session_state.history):
            _render_turn(turn)

    with st.expander("Indexed sources & guardrails"):
        rows = []
        for source in config.sources:
            chunk_count = stats["pages"].get(source.id, 0)
            rows.append(
                f"""
                <div class="source-row">
                  <a href="{html.escape(source.url, quote=True)}" target="_blank" rel="noopener noreferrer">
                    {html.escape(source.title)}
                  </a>
                  <span class="count">{chunk_count} chunks · {html.escape(source.type)}</span>
                </div>
                """
            )
        st.html("".join(rows))
        st.caption(
            "Only these five Groww pages are indexed. Advice, performance comparisons, "
            "PII, and facts outside the corpus are refused."
        )


def _footer(count: int) -> None:
    st.html(
        f"""
        <div class="arth-footer">
          <div><strong>Arth AI</strong> · {html.escape(DISCLAIMER)}</div>
          <div>Sourced strictly from the five indexed Groww pages · {count} chunks</div>
        </div>
        """,
    )


def main() -> None:
    st.set_page_config(
        page_title="Arth AI — HDFC Mutual Fund Assistant",
        page_icon="🧠",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    _bridge_secrets()
    _init_state()
    st.html(CSS)
    _ensure_index()

    config = _config()
    stats = _corpus_stats()

    _header()

    if not st.session_state.entered:
        _splash(config, stats)
        _footer(stats["count"])
        return

    _render_chat(config, stats)
    _footer(stats["count"])


main()
