import sys
import argparse
import json
from pathlib import Path

# Setup path so research and app can be imported properly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research.dataset_manifest import load_manifest, validate_manifest
from research.ablation import run_ablation_study

def parse_args():
    parser = argparse.ArgumentParser(description="Lumint Ablation Study Runner CLI")
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to the JSON dataset manifest file"
    )
    parser.add_argument(
        "--module",
        type=str,
        default="fusion",
        choices=["url", "upi", "document", "fusion"],
        help="Module/context to run the ablation study on (default: fusion)"
    )
    parser.add_argument(
        "--consensus-fixture",
        type=str,
        default=None,
        help="Optional path to the consensus fixture JSON file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="backend/research_outputs",
        help="Directory to save the ablation study JSON outputs"
    )
    return parser.parse_args()

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
        
    print(f"Executing ablation study for module '{args.module}' on dataset '{manifest.name}'...")
    
    try:
        study_result = run_ablation_study(
            manifest=manifest,
            module_name=args.module,
            consensus_fixture_path=args.consensus_fixture
        )
    except Exception as e:
        print(f"Ablation study execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    # Print results to stdout
    print("\n" + "="*90)
    print(" L U M I N T   A B L A T I O N   S T U D Y   R E S U L T S")
    print("="*90)
    print(f"{'Variant Name':<22} | {'Records':<8} | {'Accuracy':<8} | {'F1-Score':<8} | {'Mean Latency':<12} | {'Consensus Agrmt':<16}")
    print("-"*90)
    
    for var in study_result.variants:
        acc = f"{var.metrics.get('accuracy', 0.0):.4f}"
        f1 = f"{var.metrics.get('f1', 0.0):.4f}"
        lat = f"{var.latency.get('mean', 0.0):.2f} ms"
        
        agrmt_str = "-"
        if var.agreement is not None:
            pct = var.agreement.get("overall_agreement_rate", 0.0)
            agrmt_str = f"{pct:.2f}%"
            
        is_best = "*" if study_result.best_variant == var.variant_name else " "
        print(f"{is_best}{var.variant_name:<21} | {var.record_count:<8} | {acc:<8} | {f1:<8} | {lat:<12} | {agrmt_str:<16}")
    print("="*90)
    print(f"Best variant selected: {study_result.best_variant}\n")
    
    # Save output JSON
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = out_dir / f"ablation_study_{args.module}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(study_result.model_dump(), f, indent=2, ensure_ascii=False)
        
    print(f"Ablation study results written to: {output_path}")

if __name__ == "__main__":
    main()
