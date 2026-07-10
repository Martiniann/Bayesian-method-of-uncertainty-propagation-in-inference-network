"""
Report generator for Bayesian Uncertainty Propagation in Inference Network.
Runs all available data files and outputs a structured Markdown report.
Usage: python generate_report.py [--output report.md]
"""

import sys
import os
import io
import argparse
from contextlib import redirect_stdout
from datetime import datetime, timezone
from typing import Optional

# ── import project classes ────────────────────────────────────────────────────
from main import Bayes, getData

DATA_FILES = ["data1.txt", "data2.txt", "data3.txt"]


def run_dataset(path: str) -> Optional[dict]:
    """Run the Bayesian analysis on *path* and return a result dict."""
    if not os.path.exists(path):
        return None

    bias, interval, data = getData(path)
    bayes = Bayes(data, interval, bias)

    # Capture all printed output
    capture = io.StringIO()
    with redirect_stdout(capture):
        result = bayes.combined_calculation()

    P_EEap, P_HEap, O_HEap, Ls, glob, final = result
    log = capture.getvalue()

    # Build tree image path (unique per dataset)
    dot_path = path.replace(".txt", "_tree.dot")
    png_path = path.replace(".txt", "_tree.png")
    _export_tree(bayes, result, dot_path, png_path)

    return {
        "file": path,
        "bias": bias,
        "interval": interval,
        "n_evidences": len(data),
        "P_E": bayes.P_E,
        "P_HE": bayes.P_HE,
        "P_HnE": bayes.P_HnE,
        "Guess": bayes.Guess,
        "P_EEap": P_EEap,
        "P_HEap": P_HEap,
        "O_HEap": O_HEap,
        "Ls": Ls,
        "glob": glob,
        "final_probability": final,
        "tree_png": png_path,
        "log": log,
    }


def _export_tree(bayes, result, dot_path, png_path):
    """Generate dot/png tree for a dataset."""
    try:
        from anytree import Node
        from anytree.exporter import DotExporter
        import pydot

        P_EEap, P_HEap, O_HEap, Ls, glob, final = result
        root = Node("Data")
        for i in range(len(P_EEap)):
            bayes_node   = Node(f"Bayes {P_EEap[i]}",       parent=root)
            ctr_node     = Node(f"CTR {P_HEap[i]}",          parent=bayes_node)
            chance_node  = Node(f"Chance {O_HEap[i]}",       parent=ctr_node)
            suff_node    = Node(f"Sufficiency {Ls[i]}",      parent=chance_node)
            glob_node    = Node(f"Glob {glob}",              parent=suff_node)
            _            = Node(f"Probability {final}",      parent=glob_node)

        DotExporter(root).to_dotfile(dot_path)
        (graph,) = pydot.graph_from_dot_file(dot_path)
        graph.write_png(png_path)
    except Exception as exc:
        print(f"  [warn] Could not export tree for {dot_path}: {exc}", file=sys.stderr)


# ── Markdown builders ─────────────────────────────────────────────────────────

def evidence_table(r: dict) -> str:
    """Markdown table for the evidence inputs of one dataset."""
    rows = [
        "| # | P(E) | P(H\|E) | P(H\|¬E) | Guess | P(E') | P(H\|E') | Odds | λ (LS) |",
        "|---|------|---------|----------|-------|-------|----------|------|--------|",
    ]
    for i in range(r["n_evidences"]):
        rows.append(
            f"| {i+1} "
            f"| {r['P_E'][i]} "
            f"| {r['P_HE'][i]} "
            f"| {r['P_HnE'][i]} "
            f"| {r['Guess'][i]} "
            f"| {r['P_EEap'][i]} "
            f"| {r['P_HEap'][i]} "
            f"| {r['O_HEap'][i]} "
            f"| {r['Ls'][i]} |"
        )
    return "\n".join(rows)


def dataset_section(r: dict, idx: int) -> str:
    name = os.path.basename(r["file"])
    lines = [
        f"## Dataset {idx}: `{name}`",
        "",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Prior probability P(H) | **{r['bias']}** |",
        f"| Evidence interval | [{r['interval'][0]}, {r['interval'][-1]}] |",
        f"| Number of evidences | {r['n_evidences']} |",
        f"| Combined GLOB | {r['glob']} |",
        f"| **Final posterior P(H\|E₁…Eₙ)** | **{r['final_probability']}** |",
        "",
        "### Evidence breakdown",
        "",
        evidence_table(r),
        "",
    ]
    if os.path.exists(r["tree_png"]):
        lines += [
            "### Inference tree",
            "",
            f"![Inference tree for {name}]({r['tree_png']})",
            "",
        ]
    return "\n".join(lines)


def build_report(results: list) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    sections = [
        "# Bayesian Uncertainty Propagation — Report",
        "",
        f"> Generated on **{now}**",
        "",
        "This report summarises the Bayesian inference calculations performed on all",
        "available datasets using the **Subjective Bayes / CTR / GLOB** pipeline.",
        "",
        "---",
        "",
    ]

    # Summary table
    sections += [
        "## Summary",
        "",
        "| Dataset | Prior P(H) | # Evidences | GLOB | **Posterior P(H)** |",
        "|---------|-----------|-------------|------|-------------------|",
    ]
    for i, r in enumerate(results, start=1):
        sections.append(
            f"| `{os.path.basename(r['file'])}` "
            f"| {r['bias']} "
            f"| {r['n_evidences']} "
            f"| {r['glob']} "
            f"| **{r['final_probability']}** |"
        )
    sections += ["", "---", ""]

    # Per-dataset detail
    for i, r in enumerate(results, start=1):
        sections.append(dataset_section(r, i))
        sections.append("---")
        sections.append("")

    return "\n".join(sections)


# ── CLI entry-point ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Bayesian analysis report")
    parser.add_argument(
        "--output", default="report.md",
        help="Output markdown file (default: report.md)"
    )
    parser.add_argument(
        "--github-summary", action="store_true",
        help="Also write to $GITHUB_STEP_SUMMARY if set"
    )
    args = parser.parse_args()

    print("Running Bayesian analysis on all datasets …")
    results = []
    for path in DATA_FILES:
        print(f"  Processing {path} …", end=" ")
        r = run_dataset(path)
        if r is None:
            print("not found, skipped.")
        else:
            print(f"done  →  posterior P(H) = {r['final_probability']}")
            results.append(r)

    if not results:
        print("ERROR: No datasets found.", file=sys.stderr)
        sys.exit(1)

    report_md = build_report(results)

    # Write local file
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(report_md)
    print(f"\nReport written to: {args.output}")

    # Write to GitHub Actions step summary if requested
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if args.github_summary and summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(report_md)
        print(f"Report appended to GitHub Step Summary: {summary_path}")


if __name__ == "__main__":
    main()




