import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add backend to path to allow script execution
backend_root = Path(__file__).resolve().parents[1]
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from research.paper_registry import load_paper_registry

def resolve_path(rel_path: str) -> Path:
    p = Path(rel_path)
    if p.is_absolute():
        return p
    if (Path.cwd() / p).exists() or p.parent.exists():
        return Path.cwd() / p
    return backend_root / p

def build_bundle(source_dir: Path, paper_dir: Path, registry_path: Path, dry_run: bool = False):
    print(f"Building paper bundle...")
    print(f"  Source outputs directory: {source_dir}")
    print(f"  Paper root directory: {paper_dir}")
    print(f"  Registry path: {registry_path}")
    
    tables_dir = paper_dir / "tables"
    figures_dir = paper_dir / "figures"
    
    if not dry_run:
        tables_dir.mkdir(parents=True, exist_ok=True)
        figures_dir.mkdir(parents=True, exist_ok=True)
        # Create gitkeep files
        (tables_dir / ".gitkeep").touch(exist_ok=True)
        (figures_dir / ".gitkeep").touch(exist_ok=True)
        
    registry = None
    if registry_path.exists():
        try:
            registry = load_paper_registry(registry_path)
        except Exception as e:
            print(f"  [WARNING] Could not load experiment registry: {e}")
            
    # Load summary of the run if it exists
    summary_path = source_dir / "paper_run_summary.json"
    summary_data = {}
    if summary_path.exists():
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                summary_data = json.load(f)
        except Exception as e:
            print(f"  [WARNING] Could not load run summary json: {e}")
            
    # ----------------------------------------------------
    # Table 1: Dataset Summary (Always generate from registry)
    # ----------------------------------------------------
    table_1_path = tables_dir / "table_1_dataset_summary.md"
    print(f"  Generating {table_1_path.name}...")
    
    t1_content = []
    t1_content.append("# Table 1: Lumint Evaluation Datasets Summary\n")
    t1_content.append("This table provides an overview of the registered benchmark evaluation datasets used for testing the Lumint framework.\n")
    t1_content.append("| Dataset / Experiment ID | Title | Target Module | Split | Status | Notes |")
    t1_content.append("|---|---|---|---|---|---|")
    
    if registry:
        for exp in registry.experiments:
            t1_content.append(
                f"| `{exp.experiment_id}` | {exp.title} | `{exp.module}` | BENCHMARK | `{exp.status}` | {exp.notes or ''} |"
            )
    else:
        t1_content.append("| - | - | - | - | - | - |")
        
    if not dry_run:
        with open(table_1_path, "w", encoding="utf-8") as f:
            f.write("\n".join(t1_content))
            
    # Helper to load metrics from a standard experiment JSON
    def load_exp_metrics(exp_id: str) -> Optional[Dict[str, Any]]:
        # Look inside source_dir / exp_id for any json file (standard experiment runner names them by UUID)
        exp_dir = source_dir / exp_id
        if exp_dir.exists() and exp_dir.is_dir():
            json_files = list(exp_dir.glob("exp-*.json"))
            if json_files:
                try:
                    with open(json_files[0], "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return None
        
    # Helper to load ablation study
    def load_ablation_study(exp_id: str) -> Optional[Dict[str, Any]]:
        study_file = source_dir / exp_id / "ablation_study.json"
        if study_file.exists():
            try:
                with open(study_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    # ----------------------------------------------------
    # Table 2: Detection Performance
    # ----------------------------------------------------
    table_2_path = tables_dir / "table_2_detection_performance.md"
    print(f"  Generating {table_2_path.name}...")
    
    t2_content = []
    t2_content.append("# Table 2: Fraud Detection Performance Metrics\n")
    t2_content.append("Comparative performance of individual modules and the unified multimodal fusion scoring layer.\n")
    t2_content.append("| Module / Experiment | Type | Records | Accuracy | Precision | Recall | F1-Score | FPR | FNR |")
    t2_content.append("|---|---|---|---|---|---|---|---|---|")
    
    target_exps = [
        ("url_detection_synthetic", "Synthetic"),
        ("upi_forensics_synthetic", "Synthetic"),
        ("document_forensics_synthetic", "Synthetic"),
        ("fusion_synthetic", "Synthetic"),
        ("url_real_dataset_pending", "Real-World"),
        ("upi_real_dataset_pending", "Real-World")
    ]
    
    found_any_t2 = False
    for exp_id, exp_type in target_exps:
        data = load_exp_metrics(exp_id)
        if data:
            found_any_t2 = True
            m = data.get("metrics", {})
            t2_content.append(
                f"| `{exp_id}` | {exp_type} | {data.get('record_count', 0)} | "
                f"{m.get('accuracy', 0.0):.4f} | {m.get('precision', 0.0):.4f} | {m.get('recall', 0.0):.4f} | "
                f"**{m.get('f1', 0.0):.4f}** | {m.get('fpr', 0.0):.4f} | {m.get('fnr', 0.0):.4f} |"
            )
        else:
            t2_content.append(f"| `{exp_id}` | {exp_type} | *Pending* | - | - | - | - | - | - |")
            
    if not found_any_t2:
        t2_content.append("\n> [!WARNING]\n> No experiment runs found in source directory. Please execute: `python scripts/run_paper_experiments.py --synthetic-only` to populate synthetic results.")
        
    if not dry_run:
        with open(table_2_path, "w", encoding="utf-8") as f:
            f.write("\n".join(t2_content))

    # ----------------------------------------------------
    # Table 3: Latency Profile
    # ----------------------------------------------------
    table_3_path = tables_dir / "table_3_latency_profile.md"
    print(f"  Generating {table_3_path.name}...")
    
    t3_content = []
    t3_content.append("# Table 3: System Latency Profile (Milliseconds)\n")
    t3_content.append("Latency profile benchmark for individual detection modules and the fusion layer.\n")
    t3_content.append("| Module / Experiment | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) | Min (ms) | Max (ms) |")
    t3_content.append("|---|---|---|---|---|---|---|")
    
    latency_exps = [
        "url_detection_synthetic",
        "upi_forensics_synthetic",
        "document_forensics_synthetic",
        "fusion_synthetic"
    ]
    
    found_any_t3 = False
    for exp_id in latency_exps:
        data = load_exp_metrics(exp_id)
        if data:
            found_any_t3 = True
            lat = data.get("latency", {})
            t3_content.append(
                f"| `{exp_id}` | {lat.get('mean', 0.0):.2f} | {lat.get('median', 0.0):.2f} | "
                f"{lat.get('p95', 0.0):.2f} | {lat.get('p99', 0.0):.2f} | {lat.get('min', 0.0):.2f} | {lat.get('max', 0.0):.2f} |"
            )
        else:
            t3_content.append(f"| `{exp_id}` | - | - | - | - | - | - |")
            
    if not found_any_t3:
        t3_content.append("\n> [!WARNING]\n> No experiment runs found. Run full orchestrator to populate.")
        
    if not dry_run:
        with open(table_3_path, "w", encoding="utf-8") as f:
            f.write("\n".join(t3_content))

    # ----------------------------------------------------
    # Table 4: Ablation
    # ----------------------------------------------------
    table_4_path = tables_dir / "table_4_ablation.md"
    print(f"  Generating {table_4_path.name}...")
    
    t4_content = []
    t4_content.append("# Table 4: Multimodal Ablation Study\n")
    t4_content.append("Evaluating the degradation of F1-Score when individual modal signals are ablated from the Fusion layer.\n")
    
    ablation_data = load_ablation_study("ablation_synthetic")
    if ablation_data:
        t4_content.append("| Variant Name | Description | Record Count | Accuracy | F1 Score | Mean Latency (ms) |")
        t4_content.append("|---|---|---|---|---|---|")
        for var in ablation_data.get("variants", []):
            m = var.get("metrics", {})
            lat = var.get("latency", {})
            acc = m.get("accuracy", 0.0)
            f1 = m.get("f1", 0.0)
            mean_lat = lat.get("mean", 0.0)
            
            is_best = " (Best)" if ablation_data.get("best_variant") == var.get("variant_name") else ""
            t4_content.append(
                f"| **{var.get('variant_name')}**{is_best} | {var.get('notes') or ''} | {var.get('record_count')} | "
                f"{acc:.4f} | **{f1:.4f}** | {mean_lat:.2f} |"
            )
    else:
        t4_content.append("| Variant Name | Description | Record Count | Accuracy | F1 Score | Mean Latency (ms) |")
        t4_content.append("|---|---|---|---|---|---|")
        t4_content.append("| *Pending* | Run ablation_synthetic to populate | - | - | - | - |")
        t4_content.append("\n> [!WARNING]\n> Ablation study outputs not found. Run command: `python scripts/run_paper_experiments.py --synthetic-only` to run ablation benchmarks.")
        
    if not dry_run:
        with open(table_4_path, "w", encoding="utf-8") as f:
            f.write("\n".join(t4_content))

    # ----------------------------------------------------
    # Table 5: Consensus Agreement
    # ----------------------------------------------------
    table_5_path = tables_dir / "table_5_consensus_agreement.md"
    print(f"  Generating {table_5_path.name}...")
    
    t5_content = []
    t5_content.append("# Table 5: External Consensus Agreement Strength\n")
    t5_content.append("Kappa metrics and agreement rates of Lumint risk labels against ground truth consensus layers.\n")
    
    consensus_data = load_exp_metrics("consensus_agreement_synthetic")
    if consensus_data and consensus_data.get("agreement"):
        t5_content.append("| Agreement Indicator | Value / Rate | Interpretation |")
        t5_content.append("|---|---|---|")
        agr = consensus_data["agreement"]
        
        rate = agr.get("agreement_rate", 0.0) * 100.0
        kappa = agr.get("cohen_kappa")
        kappa_str = f"{kappa:.4f}" if kappa is not None else "N/A"
        
        t5_content.append(f"| Cohen's Kappa | {kappa_str} | Inter-annotator agreement strength against consensus |")
        t5_content.append(f"| Overall Agreement Rate | {rate:.2f}% | Raw percentage of matching classifications |")
        t5_content.append(f"| Total Records Checked | {agr.get('total_records', 0)} | Total overlap support |")
    else:
        t5_content.append("| Agreement Indicator | Value / Rate | Interpretation |")
        t5_content.append("|---|---|---|")
        t5_content.append("| *Pending* | Run consensus_agreement_synthetic to populate | - |")
        t5_content.append("\n> [!WARNING]\n> Consensus agreement metrics not found. Run command: `python scripts/run_paper_experiments.py --synthetic-only` to run consensus benchmarks.")
        
    if not dry_run:
        with open(table_5_path, "w", encoding="utf-8") as f:
            f.write("\n".join(t5_content))

    # ----------------------------------------------------
    # Generate Tables Index Page: tables/index.md
    # ----------------------------------------------------
    index_path = tables_dir / "index.md"
    print(f"  Generating {index_path.name}...")
    
    idx_content = []
    idx_content.append("# Paper Evaluation Results Tables Index\n")
    idx_content.append("This directory houses the LaTeX/Markdown/CSV tables that compile the final results of the Lumint framework evaluation.\n")
    
    idx_content.append("## Table Catalog\n")
    idx_content.append("| Filename | Content Summary | Status |")
    idx_content.append("|---|---|---|")
    
    # Check physical availability of each file
    def get_status_badge(p: Path) -> str:
        if p.exists() and p.stat().st_size > 300:
            return "✅ Ready"
        return "❌ Pending"
        
    idx_content.append(f"| [table_1_dataset_summary.md]({table_1_path.name}) | Comprehensive catalog of registered benchmarks. | {get_status_badge(table_1_path)} |")
    idx_content.append(f"| [table_2_detection_performance.md]({table_2_path.name}) | Point estimates of Accuracy, Recall, F1, FPR, FNR. | {get_status_badge(table_2_path)} |")
    idx_content.append(f"| [table_3_latency_profile.md]({table_3_path.name}) | Hardware/latency profile and percentile stats (Mean/Median/P95). | {get_status_badge(table_3_path)} |")
    idx_content.append(f"| [table_4_ablation.md]({table_4_path.name}) | Modular degradation values under ablation testing. | {get_status_badge(table_4_path)} |")
    idx_content.append(f"| [table_5_consensus_agreement.md]({table_5_path.name}) | Agreement rates and Kappa statistics against consensus. | {get_status_badge(table_5_path)} |")
    
    idx_content.append("\n## Reproduction Protocol\n")
    idx_content.append("To execute the full synthetic paper experiment pipeline and refresh all bundle tables, execute:")
    idx_content.append("```bash")
    idx_content.append("cd backend")
    idx_content.append("python scripts/run_paper_experiments.py --synthetic-only")
    idx_content.append("python scripts/build_paper_bundle.py --source-dir research_outputs/paper_run --paper-dir ../paper")
    idx_content.append("```\n")
    idx_content.append("This processes synthetic fixtures deterministically, updates metrics, compiles ablated permutations, and updates all paper artifacts.")
    
    if not dry_run:
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("\n".join(idx_content))
            
    print(f"Paper Result Bundle build finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect and build paper evaluation tables bundle.")
    parser.add_argument(
        "--source-dir",
        type=str,
        default="research_outputs/paper_run",
        help="Source directory where experiment run outputs are stored."
    )
    parser.add_argument(
        "--paper-dir",
        type=str,
        default="../paper",
        help="Target paper root directory."
    )
    parser.add_argument(
        "--registry",
        type=str,
        default="research/fixtures/paper_experiments.json",
        help="Path to paper experiments registry JSON."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the build process without writing or modifying files."
    )
    
    args = parser.parse_args()
    
    src = resolve_path(args.source_dir)
    pap = resolve_path(args.paper_dir)
    reg = resolve_path(args.registry)
    
    build_bundle(src, pap, reg, args.dry_run)
