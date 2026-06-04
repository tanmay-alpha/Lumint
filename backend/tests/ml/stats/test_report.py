from ml.stats.report import generate_statistical_report
from ml.stats.tables import generate_paper_table_with_ci


def test_generate_statistical_report_integration():
    # Run integration test on 'doc' module (fastest/smallest)
    report = generate_statistical_report("doc")

    assert report["module"] == "doc"
    assert "LogisticRegression" in report["models"]
    assert "RandomForest" in report["models"]
    assert "GradientBoosting" in report["models"]

    lr_report = report["models"]["LogisticRegression"]
    assert "metrics" in lr_report
    assert "confidence_intervals" in lr_report
    assert "auc_delong_ci" in lr_report

    assert "RF_vs_LR" in report["significance_tests"]
    assert "GB_vs_RF" in report["significance_tests"]
    assert "GB_vs_LR" in report["significance_tests"]

    # Test table formatting
    md = generate_paper_table_with_ci(report)
    assert "Classifier Performance with 95% Confidence Intervals" in md
    assert "Model-to-Model Statistical Significance Comparison" in md
    assert "Best Model Justification" in md
