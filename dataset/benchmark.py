import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, matthews_corrcoef

def get_metrics(y_true, y_pred, y_prob):
    # Safe metrics calculation if split has only one class
    if len(np.unique(y_true)) < 2:
        auc = 0.5
    else:
        auc = float(roc_auc_score(y_true, y_prob))
        
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "auc": auc,
        "mcc": float(matthews_corrcoef(y_true, y_pred))
    }

def main():
    print("Running baseline benchmark suite...")
    
    # 1. Load dataset metadata
    records = []
    with open("dataset/metadata.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    df = pd.DataFrame(records)
    
    # Flatten features
    for col in ["brand_palette_distance", "text_height_variance", "ela_hotspot_density", "utr_valid", "ocr_confidence", "font_consistent"]:
        df[col] = df["features"].apply(lambda x: x[col])
        
    # Convert booleans to float
    df["utr_valid"] = df["utr_valid"].astype(float)
    df["font_consistent"] = df["font_consistent"].astype(float)
    
    # Split into train and test sets
    train_df = df[df["split"] == "train"].copy()
    test_df = df[df["split"] == "test"].copy()
    
    # Define feature groups
    all_features = ["brand_palette_distance", "text_height_variance", "ela_hotspot_density", "utr_valid", "ocr_confidence", "font_consistent"]
    color_features = ["brand_palette_distance"]
    ela_features = ["ela_hotspot_density"]
    fakepay_features = ["ocr_confidence", "utr_valid"]
    
    # 2. Train baseline models
    # A. Color-only
    color_model = LogisticRegression(random_state=42)
    color_model.fit(train_df[color_features], train_df["label"])
    
    # B. ELA-only
    ela_model = LogisticRegression(random_state=42)
    ela_model.fit(train_df[ela_features], train_df["label"])
    
    # C. FakePay-style
    fakepay_model = LogisticRegression(random_state=42)
    fakepay_model.fit(train_df[fakepay_features], train_df["label"])
    
    # D. CMFA-LR
    cmfa_lr = LogisticRegression(random_state=42)
    cmfa_lr.fit(train_df[all_features], train_df["label"])
    
    # E. CMFA-RF
    cmfa_rf = RandomForestClassifier(random_state=42, n_estimators=100)
    cmfa_rf.fit(train_df[all_features], train_df["label"])
    
    # F. CMFA-GB
    cmfa_gb = GradientBoostingClassifier(random_state=42)
    cmfa_gb.fit(train_df[all_features], train_df["label"])
    
    # Helper to evaluate a classifier function on a subset
    def evaluate_model(predict_fn):
        y_true = test_df["label"].values
        y_pred, y_prob = predict_fn(test_df)
        
        # Overall
        overall = get_metrics(y_true, y_pred, y_prob)
        
        # Stratified by difficulty
        difficulties = {}
        for diff in ["easy", "medium", "hard"]:
            mask = test_df["difficulty"] == diff
            if mask.sum() > 0:
                difficulties[diff] = get_metrics(y_true[mask], y_pred[mask], y_prob[mask])
            else:
                difficulties[diff] = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "auc": 0.5, "mcc": 0.0}
                
        # Stratified by app
        apps = {}
        for app in ["phonepay", "googlepay", "paytm", "bhim"]:
            mask = test_df["app"] == app
            if mask.sum() > 0:
                apps[app] = get_metrics(y_true[mask], y_pred[mask], y_prob[mask])
            else:
                apps[app] = {"precision": 0.0, "recall": 0.0, "f1": 0.0, "auc": 0.5, "mcc": 0.0}
                
        return {
            "overall": overall,
            "by_difficulty": difficulties,
            "by_app": apps
        }
        
    results = {}
    
    # 1. Random Classifier
    np.random.seed(42)
    def pred_random(data):
        probs = np.random.uniform(0, 1, len(data))
        preds = (probs >= 0.5).astype(int)
        return preds, probs
    results["Random Classifier"] = evaluate_model(pred_random)
    
    # 2. UTR-only
    def pred_utr(data):
        # 1 if invalid, else 0
        preds = (data["utr_valid"] == 0.0).astype(int).values
        probs = preds.astype(float) # deterministic probability
        return preds, probs
    results["UTR-only"] = evaluate_model(pred_utr)
    
    # 3. Color-only
    def pred_color(data):
        preds = color_model.predict(data[color_features])
        probs = color_model.predict_proba(data[color_features])[:, 1]
        return preds, probs
    results["Color-only"] = evaluate_model(pred_color)
    
    # 4. ELA-only
    def pred_ela(data):
        preds = ela_model.predict(data[ela_features])
        probs = ela_model.predict_proba(data[ela_features])[:, 1]
        return preds, probs
    results["ELA-only"] = evaluate_model(pred_ela)
    
    # 5. FakePay-style
    def pred_fakepay(data):
        preds = fakepay_model.predict(data[fakepay_features])
        probs = fakepay_model.predict_proba(data[fakepay_features])[:, 1]
        return preds, probs
    results["FakePay-style"] = evaluate_model(pred_fakepay)
    
    # 6. CMFA-LR
    def pred_cmfa_lr(data):
        preds = cmfa_lr.predict(data[all_features])
        probs = cmfa_lr.predict_proba(data[all_features])[:, 1]
        return preds, probs
    results["CMFA-LR"] = evaluate_model(pred_cmfa_lr)
    
    # 7. CMFA-RF
    def pred_cmfa_rf(data):
        preds = cmfa_rf.predict(data[all_features])
        probs = cmfa_rf.predict_proba(data[all_features])[:, 1]
        return preds, probs
    results["CMFA-RF"] = evaluate_model(pred_cmfa_rf)
    
    # 8. CMFA-GB
    def pred_cmfa_gb(data):
        preds = cmfa_gb.predict(data[all_features])
        probs = cmfa_gb.predict_proba(data[all_features])[:, 1]
        return preds, probs
    results["CMFA-GB"] = evaluate_model(pred_cmfa_gb)
    
    # Save results to benchmark_results.json
    with open("dataset/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print("Benchmark results saved in dataset/benchmark_results.json.")
    
    # Display table of overall performance
    print("\n--- OVERALL BENCHMARK RESULTS ---")
    print(f"{'Baseline':<25} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'AUC':<10} | {'MCC':<10}")
    print("-" * 85)
    for model_name, metrics in results.items():
        o = metrics["overall"]
        print(f"{model_name:<25} | {o['precision']:<10.4f} | {o['recall']:<10.4f} | {o['f1']:<10.4f} | {o['auc']:<10.4f} | {o['mcc']:<10.4f}")

if __name__ == "__main__":
    main()
