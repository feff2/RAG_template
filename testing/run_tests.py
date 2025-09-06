#!/usr/bin/env python3
import argparse
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from tqdm.auto import tqdm

import requests


@dataclass
class TestItem:
    idx: int
    user_id: str
    question: str
    target: str
    url: Optional[str]


def load_data(data_path: Path, user_prefix: str) -> List[TestItem]:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    items: List[TestItem] = []
    for i, row in enumerate(data):
        q = row.get("question", "").strip()
        t = row.get("target", "")
        u = row.get("url")
        items.append(TestItem(idx=i, user_id=f"{user_prefix}-{i+1}", question=q, target=t, url=u))
    return items


def post_query(api_url: str, item: TestItem, timeout: float = 30.0) -> Dict[str, Any]:
    payload = {"user_id": item.user_id, "query": item.question, "target": item.target}
    r = requests.post(api_url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def read_results(results_path: Path) -> List[Dict[str, Any]]:
    if not results_path.exists():
        return []
    try:
        data = json.loads(results_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def find_records_for_users(records: List[Dict[str, Any]], user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    by_uid: Dict[str, Dict[str, Any]] = {}
    wanted = set(user_ids)
    # берём последнюю запись по каждому user_id
    for rec in records:
        uid = rec.get("user_id")
        if uid in wanted:
            by_uid[uid] = rec
    return by_uid


def extract_citation_indices(answer: str) -> List[int]:
    # ищем все [n] (1-базовые индексы)
    return [int(m.group(1)) for m in re.finditer(r"\[(\d+)\]", answer or "")]


def check_citations(answer: str, links: List[str]) -> Dict[str, Any]:
    idxs = extract_citation_indices(answer)
    issues = []
    for n in idxs:
        if n < 1 or n > len(links):
            issues.append({"index": n, "error": "out_of_range"})
    return {
        "cited_indices": idxs,
        "ok": len(issues) == 0,
        "issues": issues,
    }


def normalize_url(u: Optional[str]) -> Optional[str]:
    if u is None:
        return None
    return u.strip().rstrip(",")  # иногда в данных есть запятая на конце


def summarize(
    items: List[TestItem],
    records_by_uid: Dict[str, Dict[str, Any]],
    correctness_threshold: float,
) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    corr_scores: List[float] = []
    faith_scores: List[float] = []
    missing: List[str] = []

    for it in items:
        rec = records_by_uid.get(it.user_id)
        if not rec:
            missing.append(it.user_id)
            continue

        answer = rec.get("answer", "")
        links: List[str] = rec.get("links", []) or []
        correctness_score = rec.get("correctness_score")
        faithfulness = rec.get("faithfulness", {})
        faithfulness_score = None
        if isinstance(faithfulness, dict) and "score" in faithfulness and isinstance(faithfulness["score"], (int, float)):
            faithfulness_score = float(faithfulness["score"])

        citations = check_citations(answer, links)

        # --- URL accuracy checks ---
        expected_url = normalize_url(it.url)
        normalized_links = [normalize_url(x) for x in links]
        # найден ли ожидаемый URL в списке ссылок
        expected_url_present = expected_url in normalized_links if expected_url else None

        # корректно ли процитирован: есть ли индекс [n], который указывает именно на этот URL
        expected_url_cited: Optional[bool]
        if expected_url is None:
            expected_url_cited = None
        else:
            # позиции (1-базовые) ожидаемого URL среди links
            positions = [i + 1 for i, l in enumerate(normalized_links) if l == expected_url]
            if not positions:
                expected_url_cited = False
            else:
                expected_url_cited = any(idx in citations["cited_indices"] for idx in positions)
        # --------------------------------

        row = {
            "user_id": it.user_id,
            "question": it.question,
            "target": it.target,
            "expected_url": expected_url,
            "answer_len": len(answer or ""),
            "links_count": len(links),
            "correctness_score": correctness_score,
            "faithfulness_score": faithfulness_score,
            "citations_ok": citations["ok"],
            "citation_issues": citations["issues"],
            "expected_url_present": expected_url_present,
            "expected_url_cited": expected_url_cited,
        }
        rows.append(row)

        if isinstance(correctness_score, (int, float)):
            corr_scores.append(float(correctness_score))
        if isinstance(faithfulness_score, (int, float)):
            faith_scores.append(float(faithfulness_score))

    passed = sum(
        1 for r in rows
        if isinstance(r["correctness_score"], (int, float)) and r["correctness_score"] >= correctness_threshold
    )
    total_with_score = sum(1 for r in rows if isinstance(r["correctness_score"], (int, float)))

    # агрегаты по URL
    rows_with_expected = [r for r in rows if r["expected_url"] is not None]
    url_found_count = sum(1 for r in rows_with_expected if r["expected_url_present"] is True)
    url_cited_count = sum(
        1 for r in rows_with_expected
        if r["expected_url_present"] is True and r.get("expected_url_cited") is True
    )

    urls_summary = {
        "with_expected": len(rows_with_expected),
        "found_count": url_found_count,
        "found_rate": (url_found_count / len(rows_with_expected)) if rows_with_expected else None,
        "cited_count": url_cited_count,
        "cited_rate": (url_cited_count / len(rows_with_expected)) if rows_with_expected else None,
        "missing_or_mismatch_user_ids": [
            r["user_id"] for r in rows_with_expected if not r["expected_url_present"]
        ],
        "not_cited_user_ids": [
            r["user_id"] for r in rows_with_expected
            if r["expected_url_present"] and not r.get("expected_url_cited")
        ],
    }

    summary = {
        "tests_total": len(items),
        "results_found": len(rows),
        "missing_results_for_user_ids": missing,
        "correctness": {
            "avg": (sum(corr_scores) / len(corr_scores)) if corr_scores else None,
            "threshold": correctness_threshold,
            "pass_count": passed,
            "pass_rate": (passed / total_with_score) if total_with_score else None,
        },
        "faithfulness": {
            "avg": (sum(faith_scores) / len(faith_scores)) if faith_scores else None,
            "count": len(faith_scores),
        },
        "urls": urls_summary,
        "details": rows,
    }
    return summary


def write_outputs(summary: Dict[str, Any], out_json: Path, out_csv: Path) -> None:
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    import csv
    fields = [
        "user_id",
        "question",
        "target",
        "expected_url",
        "answer_len",
        "links_count",
        "correctness_score",
        "faithfulness_score",
        "citations_ok",
        "expected_url_present",
        "expected_url_cited",
    ]
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in summary.get("details", []):
            w.writerow({k: row.get(k) for k in fields})


def main():
    ap = argparse.ArgumentParser(description="Batch test runner for /api/v1/query using data.json and results.json")
    ap.add_argument("--api", default="http://localhost:8080/api/v1/query", help="API endpoint URL")
    ap.add_argument("--data", default="data.json", type=Path, help="Path to input data.json")
    ap.add_argument("--results", default="../results.json", type=Path, help="Path to server-side results.json (mounted/shared)")
    ap.add_argument("--out-json", default="batch_summary.json", type=Path, help="Path to write summary JSON")
    ap.add_argument("--out-csv", default="batch_summary.csv", type=Path, help="Path to write summary CSV")
    ap.add_argument("--user-prefix", default="batch", help="Prefix for user_id (e.g., batch-1, batch-2, ...)")
    ap.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between requests")
    ap.add_argument("--timeout", type=float, default=60.0, help="HTTP timeout per request")
    ap.add_argument("--correctness-threshold", type=float, default=1.0, help="Threshold for pass/fail using correctness_score")
    args = ap.parse_args()

    items = load_data(args.data, args.user_prefix)

    print(f"[run] sending {len(items)} tests to {args.api}")
    for it in tqdm(items):
        try:
            resp = post_query(args.api, it, timeout=args.timeout)
            if "response" in resp:
                ans, links = resp["response"]
                print(f"  - {it.user_id} OK (len={len(ans)}, links={len(links)})")
            else:
                print(f"  - {it.user_id} WARN: unexpected response format: {resp}")
        except Exception as e:
            print(f"  - {it.user_id} ERROR: {e}")
        if args.sleep > 0:
            time.sleep(args.sleep)

    records = read_results(args.results)
    if not records:
        print(f"[warn] results file empty or missing: {args.results}")

    by_uid = find_records_for_users(records, [it.user_id for it in items])
    summary = summarize(items, by_uid, correctness_threshold=args.correctness_threshold)
    write_outputs(summary, args.out_json, args.out_csv)

    print(f"[done] summary -> {args.out_json}, {args.out_csv}")
    if summary["correctness"]["avg"] is not None:
        print(f"  correctness avg: {summary['correctness']['avg']:.3f}, pass_rate: {summary['correctness']['pass_rate']}")
    if summary["faithfulness"]["avg"] is not None:
        print(f"  faithfulness avg: {summary['faithfulness']['avg']:.3f}")
    if summary.get("urls", {}).get("found_rate") is not None:
        print(f"  url found_rate: {summary['urls']['found_rate']:.3f}, cited_rate: {summary['urls']['cited_rate']}")


if __name__ == "__main__":
    main()