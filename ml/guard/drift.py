import pandas as pd
import numpy as np
from typing import Dict, Optional, Union, List, Any
from scipy.stats import ks_2samp

class DriftMonitor:
    """
    Monitors data drift by comparing current production data against 
    a reference dataset (training data) using statistical tests:
    - KS-Test for continuous variables
    - PSI (Population Stability Index) for distribution shift
    """
    
    def __init__(self, reference_data: pd.DataFrame):
        """
        Initialize with the training data (reference).
        """
        self.reference_data = reference_data
        
    def _calculate_psi(self, expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
        """
        Calculate Population Stability Index (PSI) for a single feature.
        """
        def scale_range(input_num, min_val, max_val):
            input_num += (0.0001)  # Avoid zero division
            return (input_num - min_val) / (max_val - min_val)

        breakpoints = np.arange(0, buckets + 1) / (buckets) * 100
        breakpoints = np.percentile(expected, breakpoints)
        
        # Determine counts for bins
        params_expected = np.histogram(expected, breakpoints)[0]
        params_actual = np.histogram(actual, breakpoints)[0]
        
        # Calculate percentages
        expected_percents = params_expected / len(expected)
        actual_percents = params_actual / len(actual)
        
        # Avoid zero division
        expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
        actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
        
        psi_value = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
        return float(psi_value)

    def detect_drift(self, current_data: Union[pd.DataFrame, List[Dict]]) -> Dict:
        """
        Run drift detection on a batch of new data.
        Returns a dictionary report with KS and PSI scores.
        """
        # Convert list of dicts to DataFrame if needed
        if isinstance(current_data, list):
            current_data = pd.DataFrame(current_data)
            
        common_cols = list(set(self.reference_data.columns) & set(current_data.columns))
        numeric_cols = self.reference_data[common_cols].select_dtypes(include=np.number).columns.tolist()
        
        if not numeric_cols:
            return {"error": "No numeric columns to test for drift"}
            
        drift_report = {
            "drift_detected": False,
            "drifted_columns": {},
            "summary": {"total_columns": len(numeric_cols), "drifted_count": 0}
        }
        
        drift_count = 0
        
        for col in numeric_cols:
            ref_series = self.reference_data[col].dropna().values
            curr_series = current_data[col].dropna().values
            
            if len(ref_series) < 2 or len(curr_series) < 2:
                continue
                
            # 1. Run KS-Test (P-value < 0.05 indicates drift)
            ks_stat, p_value = ks_2samp(ref_series, curr_series)
            
            # 2. Run PSI (> 0.2 indicates significant drift)
            try:
                psi_score = self._calculate_psi(ref_series, curr_series)
            except Exception:
                psi_score = 0.0
            
            is_drifted = p_value < 0.05 or psi_score > 0.2
            
            result = {
                "ks_stat": round(ks_stat, 4),
                "p_value": round(p_value, 4),
                "psi": round(psi_score, 4),
                "drift_detected": is_drifted
            }
            
            if is_drifted:
                drift_report["drifted_columns"][col] = result
                drift_count += 1
                
        drift_report["drift_detected"] = drift_count > 0
        drift_report["summary"]["drifted_count"] = drift_count
        drift_report["summary"]["share_of_drifted_columns"] = drift_count / len(numeric_cols)
        
        return drift_report

    def detect_prediction_drift(self, current_data: pd.DataFrame, target_column: str) -> Dict:
        """
        Check if the model's predictions (target) have drifted.
        """
        return self.detect_drift(current_data[[target_column]])
