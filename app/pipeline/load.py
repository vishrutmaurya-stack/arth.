"""Phase 3: load scraped files into inspectable document JSON."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from app.config import Config, Source
from app.pipeline.artifacts import write_json
from app.pipeline.parse import extract_next_data

RISK_RE = re.compile(r"\b(Very High|Moderately High|High|Moderate|Low|Very Low)\s+Risk\b", re.I)
AGE_RE = re.compile(r"\bAMC Age\s*\n\s*(\d+\s+years?)\b", re.I)
DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_html(fragment: str) -> str:
    if not fragment:
        return ""
    soup = BeautifulSoup(fragment, "lxml")
    return _clean(soup.get_text("\n"))


def _indian_group(value: float, decimals: int = 2) -> str:
    sign = "-" if value < 0 else ""
    raw = f"{abs(value):.{decimals}f}"
    integer, _, fraction = raw.partition(".")
    if len(integer) > 3:
        last_three = integer[-3:]
        rest = integer[:-3]
        groups: list[str] = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        integer = ",".join(groups + [last_three])
    if decimals:
        return f"{sign}{integer}.{fraction}"
    return f"{sign}{integer}"


def _inr(value: Any, decimals: int = 2) -> str | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return _clean(value) or None
    return f"₹{_indian_group(number, decimals)}"


def _inr_cr(value: Any) -> str | None:
    formatted = _inr(value, 2)
    return f"{formatted} Cr" if formatted else None


def _percent(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    number = text[:-1].strip() if text.endswith("%") else text
    try:
        # Groww renders expense ratios with two decimals (1.20%, 0.60%).
        return f"{float(number):.2f}%"
    except (TypeError, ValueError):
        return f"{text}%" if not text.endswith("%") else text


def _date(value: Any) -> str | None:
    text = _clean(value)
    if not text:
        return None
    match = DATE_PREFIX_RE.match(text)
    return match.group(1) if match else text


def _lock_in(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    parts: list[str] = []
    for key, singular in (("years", "year"), ("months", "month"), ("days", "day")):
        number = value.get(key)
        if number:
            parts.append(f"{number} {singular}{'' if number == 1 else 's'}")
    return " ".join(parts) or None


def _riskometer(data: dict[str, Any], text: str) -> str | None:
    description = _clean(data.get("meta_desc"))
    match = re.search(r"Risk is ([^.]+)", description, re.I)
    value = _clean(match.group(1)) if match else ""
    if not value:
        match = RISK_RE.search(text)
        value = _clean(match.group(0)) if match else ""
    if value and not value.lower().endswith("risk"):
        value = f"{value} Risk"
    return value or None


def _add_fact(
    facts: dict[str, dict[str, str]],
    field: str,
    label: str,
    value: Any,
    source: str,
) -> None:
    text = _clean(value)
    if not text or field in facts:
        return
    facts[field] = {
        "field": field,
        "label": label,
        "value": text,
        "text": f"{label}: {text}",
        "source": source,
    }


def _manager_names(data: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for manager in data.get("fund_manager_details") or []:
        name = _clean(manager.get("person_name"))
        if name and name not in names:
            names.append(name)
    if not names:
        fallback = _clean(data.get("fund_manager"))
        if fallback:
            names.append(fallback)
    return names


def _scheme_facts(data: dict[str, Any], text: str) -> list[dict[str, str]]:
    facts: dict[str, dict[str, str]] = {}
    lines = [line.strip() for line in text.splitlines()]
    amc_info = data.get("amc_info") or {}
    category_info = data.get("category_info") or {}
    rta = data.get("rta_details") or {}

    _add_fact(facts, "scheme-name", "Scheme name", data.get("scheme_name"), "next_data")
    _add_fact(facts, "fund-house", "Fund house", data.get("fund_house"), "next_data")
    _add_fact(facts, "category", "Category", data.get("category"), "next_data")
    _add_fact(facts, "sub-category", "Sub-category", data.get("sub_category"), "next_data")
    _add_fact(facts, "plan", "Plan", data.get("plan_type"), "next_data")
    _add_fact(facts, "scheme-type", "Scheme type", data.get("scheme_type"), "next_data")
    _add_fact(facts, "expense-ratio", "Expense ratio", _percent(data.get("expense_ratio")), "next_data")
    _add_fact(
        facts,
        "base-expense-ratio",
        "Base expense ratio",
        _percent(data.get("base_expense_ratio")),
        "next_data",
    )
    _add_fact(facts, "exit-load", "Exit load", data.get("exit_load"), "next_data")
    _add_fact(
        facts,
        "min-sip",
        "Minimum SIP investment",
        _inr(data.get("min_sip_investment"), 0),
        "next_data",
    )
    _add_fact(
        facts,
        "min-lumpsum",
        "Minimum lumpsum investment",
        _inr(data.get("min_investment_amount"), 0),
        "next_data",
    )
    _add_fact(
        facts,
        "min-additional-investment",
        "Minimum additional investment",
        _inr(data.get("mini_additional_investment"), 0),
        "next_data",
    )
    _add_fact(facts, "fund-size-aum", "Fund size (AUM)", _inr_cr(data.get("aum")), "next_data")
    _add_fact(facts, "nav", "NAV", _inr(data.get("nav"), 2), "next_data")
    _add_fact(facts, "nav-date", "NAV date", data.get("nav_date"), "next_data")
    _add_fact(facts, "rating", "Groww rating", data.get("groww_rating"), "next_data")
    _add_fact(facts, "riskometer", "Riskometer", _riskometer(data, text), "visible_text")
    _add_fact(
        facts,
        "benchmark",
        "Fund benchmark",
        data.get("benchmark_name") or data.get("benchmark"),
        "next_data",
    )
    visible_launch = _value_after_label(lines, "Launch Date")
    _add_fact(
        facts,
        "launch-date",
        "Launch date",
        visible_launch or data.get("launch_date"),
        "visible_text" if visible_launch else "next_data",
    )
    _add_fact(facts, "lock-in", "Lock-in", _lock_in(data.get("lock_in")), "next_data")
    _add_fact(
        facts,
        "fund-managers",
        "Fund managers",
        ", ".join(_manager_names(data)),
        "next_data",
    )
    _add_fact(facts, "investment-objective", "Investment objective", data.get("description"), "next_data")
    _add_fact(facts, "stamp-duty", "Stamp duty", data.get("stamp_duty"), "next_data")
    _add_fact(facts, "tax-implication", "Tax implication", category_info.get("tax_impact"), "next_data")
    _add_fact(facts, "registrar", "Registrar & Transfer Agent", rta.get("rta_name"), "next_data")
    _add_fact(facts, "custodian", "Custodian", rta.get("custodian_name"), "next_data")
    _add_fact(facts, "amc-website", "AMC website", amc_info.get("vro_website"), "next_data")
    rank = _clean(amc_info.get("rank"))
    _add_fact(
        facts,
        "amc-rank",
        "AMC rank (total assets)",
        f"#{rank} in India" if rank else None,
        "next_data",
    )
    _add_fact(facts, "amc-total-aum", "AMC total AUM", _inr_cr(amc_info.get("aum")), "next_data")
    _add_fact(facts, "amc-phone", "AMC phone", amc_info.get("phone"), "next_data")
    _add_fact(facts, "amc-email", "AMC e-mail", amc_info.get("email"), "next_data")
    _add_fact(facts, "amc-address", "AMC address", amc_info.get("address"), "next_data")

    return list(facts.values())


def _amc_facts(item: dict[str, Any], funds: dict[str, Any], text: str) -> list[dict[str, str]]:
    facts: dict[str, dict[str, str]] = {}
    info = item.get("key_information") or {}
    total_aum = info.get("total_aum")
    total_schemes = funds.get("total_results") or funds.get("total_result")
    age_match = AGE_RE.search(text)

    _add_fact(facts, "fund-house", "Fund house", info.get("fund_house"), "next_data")
    _add_fact(
        facts,
        "asset-management-company",
        "Asset management company name",
        info.get("asset_management_company"),
        "next_data",
    )
    _add_fact(
        facts,
        "amc-incorporation-date",
        "AMC incorporation date",
        _date(info.get("amc_incorporation_date")),
        "next_data",
    )
    _add_fact(
        facts,
        "sponsor-name",
        "Sponsor name",
        ", ".join(_clean(name) for name in info.get("sponsor_name") or [] if _clean(name)),
        "next_data",
    )
    _add_fact(
        facts,
        "trustee-organisation",
        "Trustee organisation",
        info.get("trustee_organisation"),
        "next_data",
    )
    _add_fact(
        facts,
        "name-of-trustees",
        "Name of trustees",
        ", ".join(_clean(name) for name in info.get("name_of_trustee") or [] if _clean(name)),
        "next_data",
    )
    _add_fact(facts, "md", "MD", info.get("md"), "next_data")
    _add_fact(facts, "ceo", "CEO", info.get("ceo"), "next_data")
    _add_fact(facts, "cio", "CIO", info.get("cio"), "next_data")
    _add_fact(facts, "compliance-officer", "Compliance officer", info.get("compliance_officer"), "next_data")
    _add_fact(
        facts,
        "investor-service-officer",
        "Investor service officer",
        info.get("investor_service_officer"),
        "next_data",
    )
    _add_fact(facts, "total-aum", "Total AUM", _inr_cr(total_aum), "next_data")
    _add_fact(facts, "no-of-schemes", "No of schemes", total_schemes, "next_data")
    _add_fact(facts, "amc-age", "AMC age", age_match.group(1) if age_match else None, "visible_text")
    _add_fact(facts, "address", "Address", info.get("address"), "next_data")
    _add_fact(facts, "website", "Website", info.get("website"), "next_data")

    return list(facts.values())


def _value_after_label(lines: list[str], label: str) -> str:
    try:
        start = lines.index(label)
    except ValueError:
        return ""
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _block_after_heading(
    lines: list[str],
    heading: str,
    stop_headings: set[str],
    skip_lines: set[str] | None = None,
) -> str:
    try:
        start = lines.index(heading)
    except ValueError:
        return ""
    skipped = skip_lines or set()
    collected: list[str] = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if stripped in stop_headings:
            break
        if not stripped or stripped in skipped or stripped == ";":
            continue
        collected.append(stripped)
    return _clean("\n".join(collected))


def _fund_management_section(data: dict[str, Any]) -> dict[str, str] | None:
    details = data.get("fund_manager_details") or []
    if not details:
        names = _manager_names(data)
        if not names:
            return None
        return {
            "heading": "Fund management",
            "text": "Fund managers: " + ", ".join(names),
            "source": "next_data",
        }

    people: list[str] = []
    seen: set[str] = set()
    for manager in details:
        name = _clean(manager.get("person_name"))
        if not name or name in seen:
            continue
        seen.add(name)
        parts = [name]
        education = _clean(manager.get("education"))
        experience = _clean(manager.get("experience"))
        if education:
            parts.append(f"Education: {education}")
        if experience:
            parts.append(f"Experience: {experience}")
        people.append("\n".join(parts))
    if not people:
        return None
    return {
        "heading": "Fund management",
        "text": _clean("\n\n".join(people)),
        "source": "next_data",
    }


def _scheme_sections(data: dict[str, Any], text: str, scheme_name: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in text.splitlines()]
    sections: list[dict[str, str]] = []

    about_heading = f"About {scheme_name}"
    about = _block_after_heading(
        lines,
        "About",
        {"Investment Objective", "Fund benchmark", "Scheme Information Document(SID)"},
        skip_lines={scheme_name},
    )
    if about:
        sections.append({"heading": about_heading, "text": about, "source": "visible_text"})
    elif data.get("description"):
        sections.append(
            {
                "heading": about_heading,
                "text": _clean(data.get("description")),
                "source": "next_data",
            }
        )

    objective = _block_after_heading(
        lines,
        "Investment Objective",
        {"Fund benchmark", "Scheme Information Document(SID)", "Fund house"},
    )
    objective_source = "visible_text"
    if not objective:
        objective = _clean(data.get("description"))
        objective_source = "next_data"
    if objective:
        sections.append(
            {"heading": "Investment Objective", "text": objective, "source": objective_source}
        )

    benchmark = _block_after_heading(
        lines,
        "Fund benchmark",
        {"Scheme Information Document(SID)", "Fund house", "Rank (total assets)"},
    )
    benchmark_source = "visible_text"
    if not benchmark:
        benchmark = _clean(data.get("benchmark_name") or data.get("benchmark"))
        benchmark_source = "next_data"
    if benchmark:
        sections.append(
            {"heading": "Fund benchmark", "text": benchmark, "source": benchmark_source}
        )

    exit_block = _block_after_heading(
        lines,
        "Exit load, stamp duty and tax",
        {"Check past data", "Compare similar funds", "Fund management", "About"},
    )
    exit_source = "visible_text"
    if not exit_block:
        exit_parts = []
        if data.get("exit_load"):
            exit_parts.append(f"Exit load: {_clean(data.get('exit_load'))}")
        if data.get("stamp_duty"):
            exit_parts.append(f"Stamp duty on investment: {_clean(data.get('stamp_duty'))}")
        tax_impact = _clean((data.get("category_info") or {}).get("tax_impact"))
        if tax_impact:
            exit_parts.append(f"Tax implication: {tax_impact}")
        exit_block = _clean("\n".join(exit_parts))
        exit_source = "next_data"
    if exit_block:
        sections.append(
            {
                "heading": "Exit load, stamp duty and tax",
                "text": exit_block,
                "source": exit_source,
            }
        )

    management = _fund_management_section(data)
    if management:
        sections.append(management)

    return sections


def _amc_sections(item: dict[str, Any], funds: dict[str, Any]) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    for content in item.get("contentList") or []:
        heading = _clean(content.get("title"))
        body = _strip_html(content.get("content") or "")
        if heading and body:
            sections.append({"heading": heading, "text": body, "source": "next_data"})

    names = [
        _clean(entry.get("fund_name") or entry.get("scheme_name"))
        for entry in funds.get("content") or []
    ]
    names = [name for name in names if name]
    if names:
        total = funds.get("total_results") or funds.get("total_result") or len(names)
        sections.append(
            {
                "heading": "List of HDFC Mutual Fund in India",
                "text": _clean(
                    f"The page lists {total} HDFC Mutual Fund schemes. "
                    "Scheme names include: " + ", ".join(names) + "."
                ),
                "source": "next_data",
            }
        )
    return sections


def _amc_payload(data: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not isinstance(data, list):
        return None, None
    item = next(
        (
            entry
            for entry in data
            if isinstance(entry, dict) and "key_information" in entry and "contentList" in entry
        ),
        None,
    )
    funds = next(
        (
            entry
            for entry in data
            if isinstance(entry, dict) and isinstance(entry.get("content"), list)
        ),
        None,
    )
    return item, funds


def load_source(config: Config, source: Source) -> tuple[dict[str, Any] | None, str | None]:
    metadata_path = config.raw_dir / f"{source.id}.metadata.json"
    html_path = config.raw_dir / f"{source.id}.html"
    text_path = config.raw_dir / f"{source.id}.txt"

    if not metadata_path.exists():
        return None, "missing metadata file"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"unreadable metadata: {exc}"
    if metadata.get("error"):
        return None, f"scrape error: {metadata['error']}"
    if not html_path.exists() or not text_path.exists():
        return None, "missing raw html/txt file"

    try:
        html = html_path.read_text(encoding="utf-8")
        text = _clean(text_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, f"unreadable raw file: {exc}"
    if not text:
        return None, "empty visible text"

    next_data = extract_next_data(html)
    page_props = (
        ((next_data.get("props") or {}).get("pageProps") or {})
        if isinstance(next_data, dict)
        else {}
    )
    if source.type == "amc":
        item, funds = _amc_payload(page_props.get("amcMainPageData"))
        if item is None:
            return None, "could not find AMC data in __NEXT_DATA__"
        facts = _amc_facts(item, funds or {}, text)
        sections = _amc_sections(item, funds or {})
    else:
        data = page_props.get("mfServerSideData")
        if not isinstance(data, dict):
            return None, "missing mfServerSideData in __NEXT_DATA__"
        facts = _scheme_facts(data, text)
        sections = _scheme_sections(data, text, _clean(data.get("scheme_name") or source.title))

    document = {
        "page_id": source.id,
        "url": metadata.get("url") or source.url,
        "title": metadata.get("title") or source.title,
        "page_type": metadata.get("page_type") or source.type,
        "scraped_at": metadata.get("scraped_at"),
        "text": text,
        "facts": facts,
        "sections": sections,
    }
    write_json(config.loaded_dir / f"{source.id}.json", document)
    return document, None


def load_all(config: Config) -> tuple[list[dict[str, Any]], bool]:
    results: list[dict[str, Any]] = []
    failed = False
    for source in config.sources:
        print(f"Loading {source.id} [{source.type}]")
        document, error = load_source(config, source)
        if error or document is None:
            failed = True
            print(f"  FAILED {error}")
            results.append({"page_id": source.id, "ok": False, "error": error})
            continue
        print(
            f"  ok facts={len(document['facts'])} "
            f"sections={len(document['sections'])} chars={len(document['text'])}"
        )
        results.append(
            {
                "page_id": source.id,
                "ok": True,
                "facts": len(document["facts"]),
                "sections": len(document["sections"]),
                "char_count": len(document["text"]),
            }
        )

    write_json(
        config.loaded_dir / "_index.json",
        {"pages": results, "source_count": len(config.sources), "failed": failed},
    )
    return results, failed
