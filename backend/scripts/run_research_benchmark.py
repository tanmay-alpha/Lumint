import sys
import argparse
from pathlib import Path
from typing import List

# Setup path so research and app can be imported properly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.dataset_manifest import load_manifest, validate_manifest, DatasetType, DatasetManifest
from research.experiment_runner import run_lumint_experiment, save_experiment_outputs, ExperimentResult, ExperimentRunConfig

def parse_args():
    parser = argparse.ArgumentParser(description="Lumint Benchmark Experiment Runner CLI")
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to the JSON dataset manifest file"
    )
    parser.add_argument(
        "--module",
        type=str,
        required=True,
        choices=["url", "upi", "document", "fusion", "all"],
        help="Lumint module to evaluate ('all' runs each applicable module sequentially)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="backend/research_outputs",
        help="Directory to save raw json results and markdown reports (default: backend/research_outputs)"
    )
    parser.add_argument(
        "--notes",
        type=str,
        default=None,
        help="Optional notes to append to the run config"
    )
    parser.add_argument(
        "--consensus-fixture",
        type=str,
        default=None,
        help="Path to the consensus fixture JSON file (optional)"
    )
    parser.add_argument(
        "--with-consensus",
        action="store_true",
        help="Enable external consensus analysis mapping if fixture is provided"
    )
    parser.add_argument(
        "--bootstrap-resamples",
        type=int,
        default=100,
        help="Number of resamples for statistical confidence bootstrapping (default: 100)"
    )
    return parser.parse_args()

def filter_records_for_module(manifest: DatasetManifest, module: str) -> DatasetManifest:
    filtered_records = []
    for r in manifest.records:
        if module == "url" and r.dataset_type == DatasetType.URL:
            filtered_records.append(r)
        elif module == "upi" and r.dataset_type == DatasetType.UPI_SCREENSHOT:
            filtered_records.append(r)
        elif module == "document" and r.dataset_type == DatasetType.DOCUMENT:
            filtered_records.append(r)
        elif module == "fusion":
            meta = r.metadata or {}
            if "document_result" in meta or "phishing_result" in meta or "upi_result" in meta:
                filtered_records.append(r)
                
    return DatasetManifest(
        name=f"{manifest.name}_{module}",
        version=manifest.version,
        records=filtered_records,
        notes=manifest.notes
    )

def print_result_table(results: List[ExperimentResult]):
    print("\n" + "="*98)
    print(" L U M I N T   B E N C H M A R K   S U M M A R Y")
    print("="*98)
    print(f"{'Module / Model':<20} | {'Records':<8} | {'Accuracy':<8} | {'F1-Score':<8} | {'Mean Latency':<12} | {'Errors':<6} | {'Consensus Agrmt':<18}")
    print("-"*98)
    for res in results:
        metrics = res.metrics
        latency = res.latency
        acc = f"{metrics.get('accuracy', 0.0):.4f}"
        f1 = f"{metrics.get('f1', 0.0):.4f}"
        lat = f"{latency.get('mean', 0.0):.2f} ms"
        errs = str(res.errors_count)
        
        agrmt_str = "-"
        if res.agreement is not None:
            pct = res.agreement.agreement_rate * 100.0
            dis = res.agreement.disagreement_count
            agrmt_str = f"{pct:.1f}% ({dis} dis)"
            
        print(f"{res.model_name:<20} | {res.record_count:<8} | {acc:<8} | {f1:<8} | {lat:<12} | {errs:<6} | {agrmt_str:<18}")
    print("="*98 + "\n")

def run_single_module(
    manifest: DatasetManifest, 
    module: str, 
    output_dir: str, 
    notes: str = None,
    consensus_fixture: str = None,
    bootstrap_resamples: int = 100
) -> ExperimentResult:
    config = ExperimentRunConfig(
        experiment_name=f"lumint_bench_{module}",
        module_name=module,
        manifest_path=None,
        output_dir=output_dir,
        notes=notes,
        consensus_fixture_path=consensus_fixture,
        consensus_provider="fixture" if consensus_fixture else None
    )
    
    filtered_manifest = filter_records_for_module(manifest, module)
    
    if not filtered_manifest.records:
        print(f"Warning: No matching records found in manifest for module '{module}'. Running on all records as fallback.")
        filtered_manifest = manifest
        
    print(f"Running benchmark for module: {module} ({len(filtered_manifest.records)} records)...")
    result = run_lumint_experiment(filtered_manifest, module, config)
    
    # 1. Run Bootstrapping for confidence intervals
    try:
        from research.statistics import bootstrap_metric_ci, bootstrap_confidence_interval
        y_true = [r.true_label for r in result.results]
        y_pred = [r.predicted_label for r in result.results]
        
        ci_dict = {}
        for metric_name in ["accuracy", "precision", "recall", "f1"]:
            lower, mean_val, upper = bootstrap_metric_ci(y_true, y_pred, metric_name, n_resamples=bootstrap_resamples)
            ci_dict[metric_name] = (lower, mean_val, upper)
            
        latencies = [r.latency_ms for r in result.results]
        lower_l, mean_l, upper_l = bootstrap_confidence_interval(latencies, n_resamples=bootstrap_resamples)
        ci_dict["mean"] = (lower_l, mean_l, upper_l)
        
        result.confidence_intervals = ci_dict
    except Exception as e:
        print(f"Warning: Could not compute statistical confidence intervals: {e}")
        
    # 2. Run Error Taxonomy
    try:
        from research.error_analysis import analyze_errors, summarize_top_errors
        error_cases = analyze_errors(result.results, filtered_manifest)
        result.error_summary = summarize_top_errors(error_cases)
    except Exception as e:
        print(f"Warning: Could not compute error taxonomy analysis: {e}")
        
    # 3. Run Ablation Study for fusion module
    if module == "fusion":
        try:
            from research.ablation import run_ablation_study
            study = run_ablation_study(filtered_manifest, module, consensus_fixture_path=consensus_fixture)
            result.ablation_study = study
        except Exception as e:
            print(f"Warning: Could not compute ablation study: {e}")
            
    # Save the updated result outputs
    save_experiment_outputs(result, output_dir)
    print(f"Results saved to: {output_dir}")
    print(f"Experiment ID: {result.experiment_id}")
    
    # Inline consensus agreement printing
    if result.agreement is not None:
        pct = result.agreement.agreement_rate * 100.0
        print(f"External Consensus Agreement Rate: {pct:.2f}% ({result.agreement.disagreement_count} disagreements)")
        
    return result

def main():
    args = parse_args()
    
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Error: Manifest file not found at: {args.manifest}")
        sys.exit(1)
        
    try:
        manifest = load_manifest(str(manifest_path))
    except Exception as e:
        print(f"Error loading manifest: {e}")
        sys.exit(1)
        
    if not validate_manifest(manifest):
        print("Error: Manifest validation failed. Please check record IDs and paths.")
        sys.exit(1)
        
    # Set up consensus fixture path if either arg or flag is set
    consensus_path = args.consensus_fixture
    if args.with_consensus and not consensus_path:
        if args.module != "all":
            default_p = Path("research/fixtures/consensus") / f"{args.module}_consensus_fixture.json"
            if default_p.exists():
                consensus_path = str(default_p)
            
    output_results = []
    
    if args.module == "all":
        # Run sequentially on each known module type
        for mod in ["url", "upi", "document", "fusion"]:
            mod_consensus = None
            if consensus_path:
                c_dir = Path(consensus_path).parent
                specific_fixture = c_dir / f"{mod}_consensus_fixture.json"
                if specific_fixture.exists():
                    mod_consensus = str(specific_fixture)
                else:
                    mod_consensus = consensus_path
            elif args.with_consensus:
                default_p = Path("research/fixtures/consensus") / f"{mod}_consensus_fixture.json"
                if default_p.exists():
                    mod_consensus = str(default_p)
                    
            res = run_single_module(
                manifest=manifest,
                module=mod,
                output_dir=args.output_dir,
                notes=args.notes,
                consensus_fixture=mod_consensus,
                bootstrap_resamples=args.bootstrap_resamples
            )
            output_results.append(res)
    else:
        res = run_single_module(
            manifest=manifest,
            module=args.module,
            output_dir=args.output_dir,
            notes=args.notes,
            consensus_fixture=consensus_path,
            bootstrap_resamples=args.bootstrap_resamples
        )
        output_results.append(res)
        
    print_result_table(output_results)

if __name__ == "__main__":
    main()
