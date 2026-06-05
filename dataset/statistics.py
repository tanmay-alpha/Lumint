import json
import numpy as np

def calculate_cohen_d(genuine, forged):
    genuine_mean = np.mean(genuine)
    forged_mean = np.mean(forged)
    
    genuine_var = np.var(genuine, ddof=1)
    forged_var = np.var(forged, ddof=1)
    
    pooled_std = np.sqrt(0.5 * (genuine_var + forged_var))
    if pooled_std == 0:
        return 0.0
    return float((forged_mean - genuine_mean) / pooled_std)

def main():
    print("Computing dataset statistics...")
    
    # Load dataset/metadata.jsonl
    records = []
    with open("dataset/metadata.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    total_samples = len(records)
    
    # Calculate distributions
    splits = {"train": 0, "val": 0, "test": 0}
    class_balance = {"genuine": 0, "forged": 0}
    app_dist = {}
    forgery_dist = {}
    difficulty_dist = {}
    
    # Accumulate feature arrays
    features_genuine = {
        "brand_palette_distance": [],
        "text_height_variance": [],
        "ela_hotspot_density": []
    }
    features_forged = {
        "brand_palette_distance": [],
        "text_height_variance": [],
        "ela_hotspot_density": []
    }
    
    for r in records:
        splits[r["split"]] += 1
        
        lbl = "genuine" if r["label"] == 0 else "forged"
        class_balance[lbl] += 1
        
        app_dist[r["app"]] = app_dist.get(r["app"], 0) + 1
        
        f_type = str(r["forgery_type"])
        forgery_dist[f_type] = forgery_dist.get(f_type, 0) + 1
        
        diff = r["difficulty"]
        difficulty_dist[diff] = difficulty_dist.get(diff, 0) + 1
        
        # Features
        feats = r["features"]
        target_dict = features_genuine if r["label"] == 0 else features_forged
        for k in features_genuine.keys():
            target_dict[k].append(feats[k])
            
    # Calculate stats for features
    feature_stats = {}
    for k in features_genuine.keys():
        g_vals = features_genuine[k]
        f_vals = features_forged[k]
        
        g_mean = float(np.mean(g_vals))
        g_std = float(np.std(g_vals, ddof=1))
        f_mean = float(np.mean(f_vals))
        f_std = float(np.std(f_vals, ddof=1))
        
        d = calculate_cohen_d(g_vals, f_vals)
        
        feature_stats[k] = {
            "genuine_mean": g_mean,
            "genuine_std": g_std,
            "forged_mean": f_mean,
            "forged_std": f_std,
            "separation_ratio": d
        }
        
    stats = {
        "total_samples": total_samples,
        "splits": splits,
        "class_balance": class_balance,
        "app_distribution": app_dist,
        "forgery_type_distribution": forgery_dist,
        "difficulty_distribution": difficulty_dist,
        "feature_statistics": feature_stats
    }
    
    # Write to stats.json
    with open("dataset/stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        
    print("Dataset statistics calculated successfully and saved in dataset/stats.json.")
    print("Cohen's d Separation Ratios:")
    for k, v in feature_stats.items():
        print(f"  {k}: {v['separation_ratio']:.4f} (Effect Size)")

if __name__ == "__main__":
    main()
