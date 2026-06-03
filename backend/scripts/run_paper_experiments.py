import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Add backend to path to allow script execution
backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from research.dataset_manifest import load_manifest, DatasetManifest
from research.paper_registry import load_paper_registry, PaperExperimentRegistry
from research.experiment_runner import run_lumint_experiment, run_lumint_experiment_with_consensus, save_experiment_outputs
from research.ablation import run_ablation_study
from research.paper_tables import (
    metrics_to_markdown_table,
    metrics_to_csv,
    metrics_to_latex_table,
    latency_to_markdown_table,
    ablation_to_markdown_table,
    ablation_to_csv,
    agreement_to_markdown_table
)

def resolve_path(rel_path: str) -> Path:
    p = Path(rel_path)
    if p.is_absolute():
        return p
    # Try CWD first
    if (Path.cwd() / p).exists() or p.parent.exists():
        return Path.cwd() / p
    # Fallback to backend root
    return backend_root / p

def run_experiments(
    registry_path: Path,
    output_dir: Path,
    synthetic_only: bool,
    real_manifest_dir: Path,
    with_consensus: bool,
    with_ablation: bool,
    dry_run: bool
) -> Dict[str, Any]:
    print(f"Loading paper experiments registry from: {registry_path}")
    registry = load_paper_registry(registry_path)
    
    run_summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "synthetic_only": synthetic_only,
        "with_consensus": with_consensus,
        "with_ablation": with_ablation,
        "dry_run": dry_run,
        "experiments_run": [],
        "experiments_skipped": []
    }
    
    # Ensure output_dir exists if not dry_run
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        
    for exp in registry.experiments:
        exp_id = exp.experiment_id
        module = exp.module.lower()
        status = exp.status
        manifest_rel = exp.manifest_path
        
        # Determine if it's real or synthetic
        is_real = status == "real_data_pending" or "real" in exp_id
        
        if is_real and synthetic_only:
            print(f"[SKIP] Experiment '{exp_id}' is marked as real-data-pending and --synthetic-only is active.")
            run_summary["experiments_skipped"].append({
                "experiment_id": exp_id,
                "reason": "Synthetic-only run mode active"
            })
            continue
            
        # Resolve manifest path
        manifest_path = resolve_path(manifest_rel)
        # Also check under real_manifest_dir if real and file not found at default location
        if is_real and not manifest_path.exists():
            alt_path = real_manifest_dir / Path(manifest_rel).name
            if alt_path.exists():
                manifest_path = alt_path
                
        if not manifest_path.exists():
            print(f"[SKIP] Manifest file for '{exp_id}' not found at {manifest_path}. Skipping.")
            run_summary["experiments_skipped"].append({
                "experiment_id": exp_id,
                "reason": f"Manifest file missing: {manifest_path}"
            })
            continue
            
        if dry_run:
            print(f"[DRY-RUN] Would run experiment '{exp_id}' (Module: {exp.module}) using manifest: {manifest_path}")
            run_summary["experiments_run"].append({
                "experiment_id": exp_id,
                "status": "dry_run"
            })
            continue
            
        print(f"\n[RUNNING] Executing experiment '{exp_id}' ({exp.title})...")
        try:
            manifest = load_manifest(str(manifest_path))
        except Exception as e:
            print(f"[ERROR] Failed to load manifest for '{exp_id}': {e}")
            run_summary["experiments_skipped"].append({
                "experiment_id": exp_id,
                "reason": f"Failed to load manifest: {e}"
            })
            continue
            
        exp_out_dir = output_dir / exp_id
        exp_out_dir.mkdir(parents=True, exist_ok=True)
        
        # Module mapping
        module_map = {
            "phishshield": "url",
            "upishield": "upi",
            "docshield": "document",
            "fusion": "fusion"
        }
        
        # Initialize result metrics to serialize
        exp_metrics = {}
        
        if exp.module == "Ablation":
            # Run ablation study
            print(f"  Running Ablation Study for fusion on {len(manifest.records)} records...")
            # We can associate a consensus fixture if available
            consensus_path = resolve_path("research/fixtures/consensus/fusion_consensus_fixture.json")
            consensus_arg = str(consensus_path) if consensus_path.exists() else None
            
            study_result = run_ablation_study(manifest, "fusion", consensus_fixture_path=consensus_arg)
            
            # Save results
            study_json_path = exp_out_dir / "ablation_study.json"
            with open(study_json_path, "w", encoding="utf-8") as f:
                json.dump(study_result.model_dump(), f, indent=2, ensure_ascii=False)
                
            # Generate markdown table and csv
            md_table = ablation_to_markdown_table(study_result)
            csv_table = ablation_to_csv(study_result)
            
            with open(exp_out_dir / "ablation_table.md", "w", encoding="utf-8") as f:
                f.write(md_table)
            with open(exp_out_dir / "ablation_table.csv", "w", encoding="utf-8") as f:
                f.write(csv_table)
                
            # For summary
            best_variant_data = next((v for v in study_result.variants if v.variant_name == study_result.best_variant), None)
            if best_variant_data:
                exp_metrics = best_variant_data.metrics
                
            print(f"  Ablation study complete. Best variant: {study_result.best_variant}")
            
        elif exp.module == "Agreement":
            # Run agreement / consensus matching
            print(f"  Running Consensus Agreement evaluation...")
            consensus_path = resolve_path("research/fixtures/consensus/fusion_consensus_fixture.json")
            if not consensus_path.exists():
                print("  [WARNING] Consensus fixture fusion_consensus_fixture.json not found. Running baseline agreement.")
                consensus_path = None
                
            result = run_lumint_experiment_with_consensus(manifest, "fusion", str(consensus_path) if consensus_path else None)
            save_experiment_outputs(result, str(exp_out_dir))
            
            # Additional table exports
            if result.agreement:
                with open(exp_out_dir / "agreement_table.md", "w", encoding="utf-8") as f:
                    # Convert model to dict
                    f.write(agreement_to_markdown_table(result.agreement.model_dump()))
                    
            exp_metrics = result.metrics
            print(f"  Consensus agreement complete. Record count: {result.record_count}")
            
        else:
            # Standard single module evaluation
            run_mod = module_map.get(module, module)
            print(f"  Running standard module evaluation '{run_mod}'...")
            
            # Determine if we should apply consensus
            consensus_fixture = None
            if with_consensus:
                # find matching consensus fixture by module name
                fixture_name = f"{run_mod}_consensus_fixture.json"
                possible_path = resolve_path(f"research/fixtures/consensus/{fixture_name}")
                if possible_path.exists():
                    consensus_fixture = str(possible_path)
                    print(f"  Injecting consensus fixture for comparison: {fixture_name}")
                    
            if consensus_fixture:
                result = run_lumint_experiment_with_consensus(manifest, run_mod, consensus_fixture)
            else:
                result = run_lumint_experiment(manifest, run_mod)
                
            save_experiment_outputs(result, str(exp_out_dir))
            
            # Export tables
            with open(exp_out_dir / "metrics.csv", "w", encoding="utf-8") as f:
                f.write(metrics_to_csv(result.metrics))
            with open(exp_out_dir / "metrics.md", "w", encoding="utf-8") as f:
                f.write(metrics_to_markdown_table(result.metrics, result.confidence_intervals))
            with open(exp_out_dir / "metrics.tex", "w", encoding="utf-8") as f:
                f.write(metrics_to_latex_table(result.metrics, result.confidence_intervals, label=f"tab:{exp_id}", caption=exp.title))
            with open(exp_out_dir / "latency.md", "w", encoding="utf-8") as f:
                f.write(latency_to_markdown_table(result.latency))
                
            exp_metrics = result.metrics
            print(f"  Evaluation complete. Accuracy: {exp_metrics.get('accuracy', 0.0):.4f}, F1: {exp_metrics.get('f1', 0.0):.4f}")
            
        run_summary["experiments_run"].append({
            "experiment_id": exp_id,
            "title": exp.title,
            "module": exp.module,
            "status": "success",
            "records_count": len(manifest.records),
            "metrics": exp_metrics
        })
        
    return run_summary

def write_summary_markdown(summary: Dict[str, Any], output_path: Path) -> None:
    lines = []
    lines.append("# Paper Experiment Run Summary\n")
    lines.append(f"- **Timestamp**: {summary['timestamp']}")
    lines.append(f"- **Synthetic Only**: {summary['synthetic_only']}")
    lines.append(f"- **With Consensus**: {summary['with_consensus']}")
    lines.append(f"- **With Ablation**: {summary['with_ablation']}")
    lines.append(f"- **Dry Run**: {summary['dry_run']}\n")
    
    lines.append("## Executed Experiments\n")
    if not summary["experiments_run"]:
        lines.append("*No experiments were executed.*")
    else:
        lines.append("| Experiment ID | Title | Module | Status | Records | F1-Score | Accuracy |")
        lines.append("|---|---|---|---|---|---|---|")
        for exp in summary["experiments_run"]:
            metrics = exp.get("metrics", {})
            f1 = f"{metrics.get('f1', 0.0):.4f}" if "f1" in metrics else "N/A"
            acc = f"{metrics.get('accuracy', 0.0):.4f}" if "accuracy" in metrics else "N/A"
            recs = exp.get("records_count", "N/A")
            lines.append(f"| `{exp['experiment_id']}` | {exp.get('title', 'N/A')} | `{exp.get('module', 'N/A')}` | `{exp.get('status', 'N/A')}` | {recs} | {f1} | {acc} |")
            
    lines.append("\n## Skipped/Pending Experiments\n")
    if not summary["experiments_skipped"]:
        lines.append("*No experiments were skipped.*")
    else:
        lines.append("| Experiment ID | Reason |")
        lines.append("|---|---|")
        for exp in summary["experiments_skipped"]:
            lines.append(f"| `{exp['experiment_id']}` | {exp['reason']} |")
            
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrate full evaluation suite for paper registry.")
    parser.add_argument(
        "--registry",
        type=str,
        default="research/fixtures/paper_experiments.json",
        help="Path to paper experiments registry JSON."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="research_outputs/paper_run",
        help="Directory to write execution reports and data tables."
    )
    parser.add_argument(
        "--synthetic-only",
        action="store_true",
        help="Only run experiments marked as synthetic or completed."
    )
    parser.add_argument(
        "--real-manifest-dir",
        type=str,
        default="real_datasets/manifests",
        help="Directory where local real dataset manifests reside."
    )
    parser.add_argument(
        "--with-consensus",
        action="store_true",
        help="Perform consensus Kappa and agreement statistics where possible."
    )
    parser.add_argument(
        "--with-ablation",
        action="store_true",
        help="Perform modular ablation on the multimodal fusion benchmark."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry-run check without running model inference."
    )
    
    args = parser.parse_args()
    
    registry_file = resolve_path(args.registry)
    output_dir_path = resolve_path(args.output_dir)
    real_dir_path = resolve_path(args.real_manifest_dir)
    
    summary = run_experiments(
        registry_path=registry_file,
        output_dir=output_dir_path,
        synthetic_only=args.synthetic_only,
        real_manifest_dir=real_dir_path,
        with_consensus=args.with_consensus or True, # Default to true for completeness of run
        with_ablation=args.with_ablation or True,    # Default to true for completeness of run
        dry_run=args.dry_run
    )
    
    if not args.dry_run:
        # Write summary JSON
        with open(output_dir_path / "paper_run_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        # Write summary MD
        write_summary_markdown(summary, output_dir_path / "paper_run_summary.md")
        print(f"\n[COMPLETE] Paper run summary saved to {output_dir_path}")
