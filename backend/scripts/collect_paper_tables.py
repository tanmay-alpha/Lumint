import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any

def collect_tables(registry_path: Path, outputs_dir: Path, paper_dir: Path, dry_run: bool = False):
    print(f"Loading experiment registry from: {registry_path}")
    if not registry_path.exists():
        print(f"Error: Registry file not found at {registry_path}")
        sys.exit(1)
        
    with open(registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)
        
    experiments = registry_data.get("experiments", [])
    print(f"Found {len(experiments)} registered experiments.")
    
    tables_dir = paper_dir / "tables"
    if not dry_run:
        tables_dir.mkdir(parents=True, exist_ok=True)
        
    copied_count = 0
    missing_count = 0
    index_entries = []
    
    for exp in experiments:
        exp_id = exp.get("experiment_id")
        title = exp.get("title")
        status = exp.get("status")
        exp_out_dir = outputs_dir / exp_id
        table_target = exp.get("table_target") # e.g. "tables/generated_url_synthetic.csv"
        
        # Determine target file path inside paper folder
        if table_target:
            # table_target might start with 'tables/' so make sure we resolve it relative to paper_dir
            if table_target.startswith("tables/"):
                target_filename = table_target.replace("tables/", "")
            else:
                target_filename = table_target
            dest_file = tables_dir / target_filename
        else:
            dest_file = tables_dir / f"generated_{exp_id}.csv"
            
        print(f"\nProcessing experiment: {exp_id} ({status})")
        
        # Look for output files in exp_out_dir
        source_found = None
        if exp_out_dir.exists() and exp_out_dir.is_dir():
            # Find any csv or md table files in output dir
            csv_files = list(exp_out_dir.glob("*.csv"))
            md_files = list(exp_out_dir.glob("*.md"))
            json_files = list(exp_out_dir.glob("*.json"))
            
            # Prioritize csv, then md, then json
            all_files = csv_files + md_files + json_files
            if all_files:
                source_found = all_files[0]
                
        if source_found:
            print(f"  Found output file to copy: {source_found.name} -> {dest_file.name}")
            if not dry_run:
                shutil.copy2(source_found, dest_file)
            copied_count += 1
            index_entries.append({
                "experiment_id": exp_id,
                "title": title,
                "status": status,
                "file": dest_file.name,
                "source": source_found.name,
                "available": True
            })
        else:
            print(f"  No output tables found in: {exp_out_dir}")
            missing_count += 1
            index_entries.append({
                "experiment_id": exp_id,
                "title": title,
                "status": status,
                "file": dest_file.name,
                "source": None,
                "available": False
            })
            
    # Write tables/index.md
    index_md_path = tables_dir / "index.md"
    print(f"\nWriting index file to: {index_md_path}")
    
    index_content = []
    index_content.append("# Collected Paper Tables Index\n")
    index_content.append(f"This index maps Lumint registered experiments to their collected LaTeX/CSV tables under `paper/tables/`.\n")
    index_content.append("> [!NOTE]")
    index_content.append("> This directory contains generated tables. Some tables may be missing or represented by placeholders if real-world experiments are pending.\n")
    
    index_content.append("## Table Status\n")
    index_content.append("| Experiment ID | Title | Status | Target File | Available |")
    index_content.append("|---|---|---|---|---|")
    
    for entry in index_entries:
        avail_str = "✅ Yes" if entry["available"] else "❌ No (Pending Run)"
        index_content.append(f"| `{entry['experiment_id']}` | {entry['title']} | `{entry['status']}` | `{entry['file']}` | {avail_str} |")
        
    index_content.append("\n## Instructions to Generate Missing Tables\n")
    index_content.append("To populate the missing tables above, execute the corresponding benchmark run command. Example commands:")
    index_content.append("```bash")
    index_content.append("# Run URL detection experiment")
    index_content.append("python -m research.experiment_runner --module PhishShield --output research_outputs/url_detection_synthetic")
    index_content.append("")
    index_content.append("# Run ablation study experiment")
    index_content.append("python -m research.experiment_runner --module Ablation --output research_outputs/ablation_synthetic")
    index_content.append("```\n")
    
    if not dry_run:
        with open(index_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(index_content))
            
    print(f"\nCollection finished: {copied_count} copied, {missing_count} missing/pending.")
    if dry_run:
        print("[DRY RUN] No files were copied or created.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect generated evaluation tables into the paper directory.")
    parser.add_argument(
        "--registry",
        type=str,
        default="research/fixtures/paper_experiments.json",
        help="Path to the paper experiments registry JSON file."
    )
    parser.add_argument(
        "--outputs-dir",
        type=str,
        default="research_outputs",
        help="Path to the research outputs directory."
    )
    parser.add_argument(
        "--paper-dir",
        type=str,
        default="../paper",
        help="Path to the paper root directory."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the collection process without copying or writing any files."
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to python execution directory (which is typically backend/)
    # But let's handle relative paths robustly
    registry_path = Path(args.registry)
    outputs_dir = Path(args.outputs-dir)
    paper_dir = Path(args.paper-dir)
    
    collect_tables(registry_path, outputs_dir, paper_dir, args.dry_run)
