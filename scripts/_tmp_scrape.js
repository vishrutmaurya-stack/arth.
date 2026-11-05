const fs = require("fs");
const path = require("path");

const sources = [
  {
    id: "hdfc-amc",
    type: "amc",
    title: "HDFC Mutual Fund",
    url: "https://groww.in/mutual-funds/amc/hdfc-mutual-funds",
  },
  {
    id: "hdfc-large-cap",
    type: "scheme",
    title: "HDFC Large Cap Fund Direct Growth",
    url: "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
  },
  {
    id: "hdfc-flexi-cap",
    type: "scheme",
    title: "HDFC Flexi Cap Direct Plan Growth",
    url: "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
  },
  {
    id: "hdfc-elss",
    type: "scheme",
    title: "HDFC ELSS Tax Saver Fund Direct Plan Growth",
    url: "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
  },
  {
    id: "hdfc-mid-cap",
    type: "scheme",
    title: "HDFC Mid Cap Fund Direct Growth",
    url: "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
  },
];

const allowed = new Set(sources.map((s) => s.url));
const outDir = path.join(process.cwd(), "data", "raw");
fs.mkdirSync(outDir, { recursive: true });
const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36";

function visibleAndExtras(html) {
  const nextMatch = html.match(
    /<script id="__NEXT_DATA__" type="application\/json">([\s\S]*?)<\/script>/
  );
  const ldMatches = [
    ...html.matchAll(
      /<script type="application\/ld\+json">([\s\S]*?)<\/script>/gi
    ),
  ];
  const visible = html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, "\n")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .split("\n")
    .map((l) => l.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .join("\n");
  const parts = [visible];
  let hasNext = false;
  if (nextMatch) {
    hasNext = true;
    parts.push("=== next_data ===");
    try {
      parts.push(JSON.stringify(JSON.parse(nextMatch[1]), null, 2));
    } catch {
      parts.push(nextMatch[1]);
    }
  }
  if (ldMatches.length) {
    parts.push("=== json_ld ===");
    const blocks = [];
    for (const m of ldMatches) {
      try {
        blocks.push(JSON.parse(m[1]));
      } catch {
        /* skip invalid json-ld */
      }
    }
    parts.push(JSON.stringify(blocks, null, 2));
  }
  const text = parts.filter(Boolean).join("\n\n");
  return {
    text,
    extras: {
      has_next_data: hasNext,
      json_ld_count: ldMatches.length,
      sparse: visible.length < 500,
      char_count_visible: visible.length,
      char_count_text: text.length,
    },
  };
}

(async () => {
  const records = [];
  let failed = false;
  for (const s of sources) {
    if (!allowed.has(s.url)) {
      throw new Error("blocked: URL is not in the configured source list");
    }
    console.log("Scraping", s.id, s.url);
    const fetched_at = new Date().toISOString();
    const metadata = {
      page_id: s.id,
      url: s.url,
      title: s.title,
      page_type: s.type,
      http_status: null,
      scraped_at: fetched_at,
      final_url: null,
      error: null,
      char_count_text: 0,
      sparse: false,
      has_next_data: false,
      json_ld_count: 0,
    };
    try {
      const res = await fetch(s.url, {
        headers: {
          "User-Agent": UA,
          Accept: "text/html",
          "Accept-Language": "en-IN,en;q=0.9",
        },
        redirect: "follow",
      });
      metadata.http_status = res.status;
      metadata.final_url = res.url;
      const html = await res.text();
      if (!res.ok) {
        metadata.error = "http_" + res.status;
        failed = true;
      } else if (!html.trim()) {
        metadata.error = "empty_body";
        failed = true;
      } else {
        const { text, extras } = visibleAndExtras(html);
        Object.assign(metadata, extras);
        fs.writeFileSync(path.join(outDir, s.id + ".html"), html);
        fs.writeFileSync(path.join(outDir, s.id + ".txt"), text);
      }
    } catch (e) {
      metadata.error = "request_failed: " + e.message;
      failed = true;
      console.error("  FAILED", e.message);
    }
    fs.writeFileSync(
      path.join(outDir, s.id + ".metadata.json"),
      JSON.stringify(metadata, null, 2) + "\n"
    );
    records.push(metadata);
    console.log(
      " ",
      metadata.error ||
        "ok status=" +
          metadata.http_status +
          " chars=" +
          metadata.char_count_text +
          " sparse=" +
          metadata.sparse
    );
  }
  fs.writeFileSync(
    path.join(outDir, "_index.json"),
    JSON.stringify({ pages: records, source_count: sources.length }, null, 2) +
      "\n"
  );
  if (failed) process.exit(1);
})();
