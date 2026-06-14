#!/usr/bin/env python3
"""Parallel batch processor for app.py standardization.

Usage:
  python app_parallel2.py --file <input.json> --out <output.json> [--workers N] [--chunk-size M]

This script splits the input rows into chunks and processes them in parallel
worker processes. Each worker imports `app` and calls `_call_llm` so the LLM
is loaded per worker (avoids pickling model objects).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List


def _read_input(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    # reuse app's normalization if available, but keep a simple fallback
    try:
        # ensure local directory is on sys.path so `import app` works
        sys.path.insert(0, os.path.dirname(__file__))
        import app as _app

        return _app._normalize_input(payload)
    except Exception:
        # fallback: if top-level list
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
            return payload["rows"]
        return []


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            json.dump(r, f, ensure_ascii=False)
            f.write("\n")


def _process_chunk(chunk: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Import inside worker to avoid pickling large objects and to let each
    # worker initialize its own LLM instance if needed.
    sys.path.insert(0, os.path.dirname(__file__))
    import app as _app  # type: ignore

    out: List[Dict[str, Any]] = []
    for row in chunk:
        # try several keys for program text to be robust
        program_text = (
            (row or {}).get("program")
            or (row or {}).get("Program Name")
            or ""
        )
        try:
            result = _app._call_llm(program_text)
            row["llm-generated-program"] = result.get("standardized_program", "")
            row["llm-generated-university"] = result.get(
                "standardized_university", "Unknown"
            )
        except Exception:
            # If LLM fails in worker, fall back to app's rules-first parser
            try:
                prog, uni = _app._split_fallback(program_text)
                prog = _app._post_normalize_program(prog)
                uni = _app._post_normalize_university(uni)
                row["llm-generated-program"] = prog
                row["llm-generated-university"] = uni
            except Exception:
                row["llm-generated-program"] = ""
                row["llm-generated-university"] = "Unknown"
        out.append(row)
    return out


def chunked(rows: List[Dict[str, Any]], chunk_size: int):
    for i in range(0, len(rows), chunk_size):
        yield rows[i : i + chunk_size]


def main() -> None:
    parser = argparse.ArgumentParser(description="Parallel LLM standardizer")
    parser.add_argument("--file", required=True, help="Input JSON file")
    parser.add_argument("--out", required=True, help="Output JSONL file")
    parser.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=25,
        help="Number of rows per worker task (larger => less overhead)",
    )
    args = parser.parse_args()

    rows = _read_input(args.file)
    total = len(rows)
    if total == 0:
        print("No rows found in input; exiting.")
        return

    # decide sensible chunk size if user didn't set (allow override)
    chunk_size = args.chunk_size or max(1, math.ceil(total / (args.workers * 8)))

    tasks = list(chunked(rows, chunk_size))
    print(f"Processing {total} rows in {len(tasks)} tasks using {args.workers} workers...")

    results: List[Dict[str, Any]] = []

    # Open output and log files; write chunks as they complete so progress
    # is visible immediately. Use append mode to allow restarting safely.
    out_path = args.out
    log_path = os.path.join(os.path.dirname(__file__), "app_parallel2.log")
    completed_rows = 0
    total_tasks = len(tasks)

    with open(log_path, "a", encoding="utf-8") as logf, open(out_path, "w", encoding="utf-8") as outf:
        def _log(msg: str) -> None:
            line = f"[{__file__}] {msg}\n"
            logf.write(line)
            logf.flush()
            print(line, end="", flush=True)

        _log(f"Starting processing {total} rows in {total_tasks} tasks using {args.workers} workers")

        with ProcessPoolExecutor(max_workers=args.workers) as ex:
            future_to_idx = {ex.submit(_process_chunk, t): i for i, t in enumerate(tasks)}
            try:
                for fut in as_completed(future_to_idx):
                    idx = future_to_idx[fut]
                    try:
                        chunk_out = fut.result()
                    except Exception as e:
                        _log(f"Task {idx} raised: {e}")
                        continue

                    # write chunk results immediately
                    for r in chunk_out:
                        json.dump(r, outf, ensure_ascii=False)
                        outf.write("\n")
                    outf.flush()

                    completed_rows += len(chunk_out)
                    _log(f"Completed task {idx+1}/{total_tasks}: wrote {len(chunk_out)} rows; total completed {completed_rows}/{total}")

            except KeyboardInterrupt:
                _log("Interrupted; cancelling workers...")
                for f in future_to_idx:
                    f.cancel()
                raise

    with open(log_path, "a", encoding="utf-8") as logf:
        line = f"[{__file__}] Wrote {completed_rows} lines to {out_path}\n"
        logf.write(line)
        logf.flush()
        print(line, end="", flush=True)


if __name__ == "__main__":
    main()
