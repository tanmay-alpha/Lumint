"""
Test suite for real dataset download script.
Mocks live network requests and verifies file generation.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd
from data.download_phishing import main

MOCK_ARFF = """@relation phishing
@attribute check1 { -1, 0, 1 }
@attribute Result { -1, 1 }
@data
-1,1
1,-1
"""

def test_download_phishing_mocked(tmp_path):
    mock_csv = tmp_path / "phishing_uci.csv"
    mock_json = tmp_path / "phishing_uci_metadata.json"

    # Patch urllib.request.urlopen and output paths
    with patch("urllib.request.urlopen") as mock_urlopen, \
         patch("data.download_phishing.OUTPUT_CSV", mock_csv), \
         patch("data.download_phishing.METADATA_JSON", mock_json):
        
        mock_response = MagicMock()
        mock_response.read.return_value = MOCK_ARFF.encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Execute download main
        main()

        # Assertions
        assert mock_urlopen.called
        assert mock_csv.exists()
        assert mock_json.exists()

        # Verify CSV contents
        df = pd.read_csv(mock_csv)
        assert len(df) == 2
        assert "url" in df.columns
        assert "label" in df.columns
        assert df.iloc[0]["label"] == 0
        assert df.iloc[1]["label"] == 1
