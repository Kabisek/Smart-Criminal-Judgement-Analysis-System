"""
Prediction service for Appeal Outcome Decision Support
"""
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from datetime import datetime
import time
import pandas as pd

# Add backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from comp3.src.core.models import AppealPredictor
from comp3.dashboard_normalization import (
    canonicalize_high_court,
    infer_region_bucket,
    offence_group_column,
    REGION_LOCATION_NOT_STATED,
)
from comp3.api.config import (
    MODEL_PATH,
    SELECTOR_PATH,
    LABEL_ENCODER_PATH,
    X_TRAIN_PATH,
    BERT_EMBEDDINGS_PATH,
    DATASET_PATH,
    Y_TRAIN_PATH,
    TFIDF_VECTORIZER_PATH,
    SCALER_PATH,
    SIMILAR_CASES_TOP_K,
    DEFAULT_METADATA
)

logger = logging.getLogger(__name__)

GOVERNANCE_NOTE = (
    "This estimate is derived from historical appeal records and machine-learned patterns. "
    "Accuracy can vary by offence type, court, and time period—especially where few examples exist. "
    "It supports analysis only and does not replace professional legal advice."
)

# Short-lived cache for dashboard analytics (same filters → same payload within TTL).
_DASHBOARD_CACHE: Dict[Tuple, Tuple[float, Dict[str, Any]]] = {}
_DASHBOARD_CACHE_TTL_SEC = 120.0
_DASHBOARD_CACHE_MAX_KEYS = 48


def _dashboard_cache_get(key: Tuple) -> Dict[str, Any] | None:
    ent = _DASHBOARD_CACHE.get(key)
    if not ent:
        return None
    ts, payload = ent
    if time.monotonic() - ts > _DASHBOARD_CACHE_TTL_SEC:
        del _DASHBOARD_CACHE[key]
        return None
    return payload


def _dashboard_cache_set(key: Tuple, payload: Dict[str, Any]) -> None:
    if len(_DASHBOARD_CACHE) >= _DASHBOARD_CACHE_MAX_KEYS and key not in _DASHBOARD_CACHE:
        oldest_k = min(_DASHBOARD_CACHE, key=lambda k: _DASHBOARD_CACHE[k][0])
        del _DASHBOARD_CACHE[oldest_k]
    _DASHBOARD_CACHE[key] = (time.monotonic(), payload)


class PredictionService:
    """Service for handling appeal outcome predictions"""
    
    def __init__(self):
        """Initialize the prediction service"""
        self.predictor = None
        self._initialize_predictor()
    
    def _initialize_predictor(self):
        """Initialize the appeal predictor"""
        try:
            logger.info("Initializing AppealPredictor...")
            
            # Check if all required files exist
            required_files = [
                MODEL_PATH,
                SELECTOR_PATH,
                LABEL_ENCODER_PATH,
                X_TRAIN_PATH,
                BERT_EMBEDDINGS_PATH,
                DATASET_PATH,
                Y_TRAIN_PATH,
                TFIDF_VECTORIZER_PATH,
                SCALER_PATH
            ]
            
            missing_files = []
            for file_path in required_files:
                if not file_path.exists():
                    missing_files.append(str(file_path))
            
            if missing_files:
                raise FileNotFoundError(f"Missing required model files: {missing_files}")
            
            # Initialize predictor
            self.predictor = AppealPredictor(
                model_path=MODEL_PATH,
                selector_path=SELECTOR_PATH,
                label_encoder_path=LABEL_ENCODER_PATH,
                x_train_path=X_TRAIN_PATH,
                bert_embeddings_path=BERT_EMBEDDINGS_PATH,
                dataset_path=DATASET_PATH,
                y_train_path=Y_TRAIN_PATH
            )
            
            logger.info("AppealPredictor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize AppealPredictor: {e}")
            raise
    
    async def predict_appeal_outcome(self, case_description: str) -> Dict[str, Any]:
        """
        Predict appeal outcome for a given case description
        
        Args:
            case_description: Detailed case description
            
        Returns:
            Dictionary with prediction results
        """
        try:
            if not self.predictor:
                raise RuntimeError("Predictor not initialized")
            
            logger.info(f"Starting prediction for case description length: {len(case_description)}")
            
            # Get prediction
            prediction_result = self.predictor.predict_appeal(case_description)
            
            # Find similar cases only for valid in-domain predictions.
            is_domain_mismatch = (
                prediction_result.get('abstained', False)
                and prediction_result.get('prediction') == 'Insufficient_Legal_Context'
            )
            if is_domain_mismatch:
                similar_cases = []
            else:
                similar_cases = self.predictor.find_similar_cases(
                    case_description,
                    prediction_result['bert_embedding'],
                    top_k=SIMILAR_CASES_TOP_K
                )
            
            # Get model metadata
            metadata = self.predictor.get_model_metadata()
            
            # Pull out analytics if available
            context_analysis = prediction_result.get('context_analysis', {})
            grounds_analysis = prediction_result.get('grounds_analysis', {})
            evidence_analysis = prediction_result.get('evidence_analysis', {})
            # Create final response, including extended analytics
            response = {
                'status': 'success',
                'prediction': prediction_result['prediction'],
                'confidence': prediction_result['confidence'],
                'probabilities': prediction_result['probabilities'],
                'detected_features': prediction_result['detected_features'],
                'confidence_band': prediction_result.get('confidence_band', 'low'),
                'manual_review_required': prediction_result.get('manual_review_required', True),
                'reliability_note': prediction_result.get('reliability_note', 'Manual legal review is recommended.'),
                'abstained': prediction_result.get('abstained', False),
                'review_priority': prediction_result.get('review_priority', 'medium'),
                'top_outcomes': prediction_result.get('top_outcomes', []),
                'reason_trace': prediction_result.get('reason_trace', []),
                'shap_summary': prediction_result.get('shap_summary', {}),
                'context_analysis': context_analysis,
                'grounds_analysis': grounds_analysis,
                'evidence_analysis': evidence_analysis,
                'similar_cases': similar_cases,
                'metadata': metadata,
                'confidence_interval': prediction_result.get('confidence_interval'),
                'precedent_trend': prediction_result.get('precedent_trend'),
                'governance_note': GOVERNANCE_NOTE,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Prediction completed: {prediction_result['prediction']} with {prediction_result['confidence']:.1f}% confidence")
            
            return response
            
        except Exception as e:
            logger.error(f"Error in predict_appeal_outcome: {e}")
            raise
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information and status
        
        Returns:
            Dictionary with model information
        """
        try:
            if not self.predictor:
                return {
                    'status': 'not_initialized',
                    'message': 'Model not loaded',
                    'timestamp': datetime.now().isoformat()
                }
            
            metadata = self.predictor.get_model_metadata()
            
            return {
                'status': 'ready',
                'metadata': metadata,
                'model_files': {
                    'model': str(MODEL_PATH),
                    'selector': str(SELECTOR_PATH),
                    'label_encoder': str(LABEL_ENCODER_PATH),
                    'training_data': str(DATASET_PATH)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_dashboard_analytics(
        self,
        year: int | None = None,
        offence: str | None = None,
        high_court: str | None = None,
        region: str | None = None,
    ) -> Dict[str, Any]:
        """
        Build analytics dashboard payload from the full historical dataset.
        Uses grouped offence labels, canonical high court names, and coarse region buckets.
        """
        empty_filters = {"years": [], "offences": [], "courts": [], "regions": []}

        try:
            if not self.predictor:
                raise RuntimeError("Predictor not initialized")

            cache_key = (year, offence, high_court, region)
            cached = _dashboard_cache_get(cache_key)
            if cached is not None:
                return cached

            df_base = self.predictor.df_cases.copy()
            if df_base.empty:
                return {
                    "filters": empty_filters,
                    "kpis": {},
                    "outcome_distribution": [],
                    "yearly_trend": [],
                    "offence_distribution": [],
                    "court_distribution": [],
                    "region_distribution": [],
                    "appeal_type_distribution": [],
                    "table_rows": [],
                }

            def simplify_outcome(val: str) -> str:
                if isinstance(val, str):
                    lower = val.lower()
                    if lower.startswith('dismissed'):
                        return 'Appeal_Dismissed'
                    if lower.startswith('allowed'):
                        return 'Appeal_Allowed'
                    if lower.startswith('partly'):
                        return 'Partly_Allowed'
                return 'Other'

            if 'result_category' not in df_base.columns:
                if 'combined_outcome' in df_base.columns:
                    df_base['result_category'] = df_base['combined_outcome'].apply(simplify_outcome)
                else:
                    df_base['result_category'] = 'Other'

            og_col = offence_group_column(df_base)
            df_base['_offence_group'] = (
                df_base[og_col].fillna('Unknown').astype(str).replace('', 'Unknown')
            )
            if 'high_court_location' in df_base.columns:
                df_base['_court_canon'] = df_base['high_court_location'].apply(canonicalize_high_court)
            else:
                df_base['_court_canon'] = 'Unknown'
            if 'location_of_offence' in df_base.columns:
                df_base['_region'] = df_base['location_of_offence'].apply(infer_region_bucket)
            else:
                df_base['_region'] = REGION_LOCATION_NOT_STATED

            filters = {
                "years": sorted([int(y) for y in df_base['coa_year'].dropna().unique().tolist()])
                if 'coa_year' in df_base.columns else [],
                "offences": sorted([str(v) for v in df_base['_offence_group'].dropna().unique().tolist()]),
                "courts": sorted([str(v) for v in df_base['_court_canon'].dropna().unique().tolist()]),
                "regions": sorted([str(v) for v in df_base['_region'].dropna().unique().tolist()]),
            }

            df = df_base.copy()
            if year is not None and 'coa_year' in df.columns:
                df = df[df['coa_year'] == year]
            if offence:
                df = df[df['_offence_group'] == offence]
            if high_court:
                df = df[df['_court_canon'] == high_court]
            if region:
                df = df[df['_region'] == region]

            total = int(len(df))
            outcome_counts = df['result_category'].value_counts().to_dict() if total > 0 else {}
            allowed = int(outcome_counts.get('Appeal_Allowed', 0))
            dismissed = int(outcome_counts.get('Appeal_Dismissed', 0))
            partly = int(outcome_counts.get('Partly_Allowed', 0))

            kpis = {
                "total_cases": total,
                "allowed_rate": round((allowed / total) * 100, 1) if total else 0.0,
                "dismissed_rate": round((dismissed / total) * 100, 1) if total else 0.0,
                "partly_rate": round((partly / total) * 100, 1) if total else 0.0,
            }

            outcome_distribution = [
                {"outcome": "Appeal_Allowed", "count": allowed},
                {"outcome": "Partly_Allowed", "count": partly},
                {"outcome": "Appeal_Dismissed", "count": dismissed},
            ]

            yearly_trend = []
            if 'coa_year' in df.columns and total:
                for y, grp in df.groupby('coa_year'):
                    counts = grp['result_category'].value_counts().to_dict()
                    yearly_trend.append({
                        "year": int(y),
                        "total": int(len(grp)),
                        "allowed": int(counts.get('Appeal_Allowed', 0)),
                        "partly": int(counts.get('Partly_Allowed', 0)),
                        "dismissed": int(counts.get('Appeal_Dismissed', 0)),
                    })
                yearly_trend.sort(key=lambda x: x["year"])

            offence_distribution = []
            if total:
                top_offences = df['_offence_group'].value_counts().head(12).index.tolist()
                for off in top_offences:
                    grp = df[df['_offence_group'] == off]
                    counts = grp['result_category'].value_counts().to_dict()
                    offence_distribution.append({
                        "offence": str(off),
                        "total": int(len(grp)),
                        "allowed": int(counts.get('Appeal_Allowed', 0)),
                        "partly": int(counts.get('Partly_Allowed', 0)),
                        "dismissed": int(counts.get('Appeal_Dismissed', 0)),
                    })

            court_distribution = []
            if total:
                top_courts = df['_court_canon'].value_counts().head(12).index.tolist()
                for ct in top_courts:
                    grp = df[df['_court_canon'] == ct]
                    counts = grp['result_category'].value_counts().to_dict()
                    court_distribution.append({
                        "court": str(ct),
                        "total": int(len(grp)),
                        "allowed": int(counts.get('Appeal_Allowed', 0)),
                        "partly": int(counts.get('Partly_Allowed', 0)),
                        "dismissed": int(counts.get('Appeal_Dismissed', 0)),
                    })

            region_distribution = []
            if total:
                top_regions = df['_region'].value_counts().head(12).index.tolist()
                for reg in top_regions:
                    grp = df[df['_region'] == reg]
                    counts = grp['result_category'].value_counts().to_dict()
                    region_distribution.append({
                        "region": str(reg),
                        "total": int(len(grp)),
                        "allowed": int(counts.get('Appeal_Allowed', 0)),
                        "partly": int(counts.get('Partly_Allowed', 0)),
                        "dismissed": int(counts.get('Appeal_Dismissed', 0)),
                    })

            appeal_type_distribution = []
            if 'appeal_type_simplified' in df.columns and total:
                ape = df['appeal_type_simplified'].fillna('Unknown').astype(str).replace('', 'Unknown')
                top_at = ape.value_counts().head(10).index.tolist()
                for at in top_at:
                    grp = df.loc[ape == at]
                    counts = grp['result_category'].value_counts().to_dict()
                    appeal_type_distribution.append({
                        "appeal_type": str(at),
                        "total": int(len(grp)),
                        "allowed": int(counts.get('Appeal_Allowed', 0)),
                        "partly": int(counts.get('Partly_Allowed', 0)),
                        "dismissed": int(counts.get('Appeal_Dismissed', 0)),
                    })

            table_rows = []
            cols = [
                'court_of_appeal_case_no', 'coa_year', 'offence_category',
                'high_court_location', 'result_category', 'brief_facts_summary',
                'brief_judgment_file_summary', 'court_of_appeal_analysis_summary',
                '_offence_group', '_court_canon', '_region',
            ]
            available_cols = [c for c in cols if c in df.columns]
            if available_cols:

                def _row_text(val) -> str:
                    if val is None or (isinstance(val, float) and pd.isna(val)):
                        return ''
                    s = str(val).strip()
                    return '' if s.lower() == 'nan' else s

                for _, row in df[available_cols].head(200).iterrows():
                    facts = _row_text(row.get('brief_facts_summary'))
                    bj = _row_text(row.get('brief_judgment_file_summary')) if 'brief_judgment_file_summary' in available_cols else ''
                    coa_txt = _row_text(row.get('court_of_appeal_analysis_summary')) if 'court_of_appeal_analysis_summary' in available_cols else ''
                    raw_off = str(row.get('offence_category', '') or '').strip()
                    grp_off = str(row.get('_offence_group', 'N/A'))
                    row_out = {
                        "case_id": str(row.get('court_of_appeal_case_no', 'N/A')),
                        "year": int(row.get('coa_year')) if pd.notna(row.get('coa_year')) else None,
                        "offence": grp_off,
                        "offence_raw": raw_off if raw_off else None,
                        "court": str(row.get('_court_canon', 'N/A')),
                        "court_raw": str(row.get('high_court_location', '') or '').strip() or None,
                        "region": str(row.get('_region', REGION_LOCATION_NOT_STATED)),
                        "outcome": str(row.get('result_category', 'Other')),
                        "summary": facts[:280],
                        "summary_detail": facts[:2000],
                    }
                    if bj.strip():
                        row_out["judgment_file_summary"] = bj[:320]
                        row_out["judgment_file_summary_detail"] = bj[:4500]
                    if coa_txt.strip():
                        row_out["appeal_analysis_summary"] = coa_txt[:320]
                        row_out["appeal_analysis_summary_detail"] = coa_txt[:4500]
                    table_rows.append(row_out)

            out = {
                "filters": filters,
                "applied_filters": {
                    "year": year,
                    "offence": offence,
                    "high_court": high_court,
                    "region": region,
                },
                "kpis": kpis,
                "outcome_distribution": outcome_distribution,
                "yearly_trend": yearly_trend,
                "offence_distribution": offence_distribution,
                "court_distribution": court_distribution,
                "region_distribution": region_distribution,
                "appeal_type_distribution": appeal_type_distribution,
                "table_rows": table_rows,
            }
            _dashboard_cache_set(cache_key, out)
            return out
        except Exception as e:
            logger.error(f"Error building dashboard analytics: {e}")
            return {
                "error": str(e),
                "filters": empty_filters,
                "kpis": {},
                "outcome_distribution": [],
                "yearly_trend": [],
                "offence_distribution": [],
                "court_distribution": [],
                "region_distribution": [],
                "appeal_type_distribution": [],
                "table_rows": [],
            }

    async def get_fairness_slice_report(self, min_slice_n: int = 25) -> Dict[str, Any]:
        """
        Label distribution and outcome rates by offence group, court, and year (dataset-level).
        For model-error fairness, run the offline script with batch predictions.
        """
        try:
            if not self.predictor:
                raise RuntimeError("Predictor not initialized")

            df_base = self.predictor.df_cases.copy()
            if df_base.empty:
                return {
                    "generated_at": datetime.now().isoformat(),
                    "dataset_rows": 0,
                    "min_slice_n": min_slice_n,
                    "overall": {},
                    "by_offence": [],
                    "by_court": [],
                    "by_year": [],
                    "notes": ["Dataset is empty."],
                }

            def simplify_outcome(val: str) -> str:
                if isinstance(val, str):
                    lower = val.lower()
                    if lower.startswith('dismissed'):
                        return 'Appeal_Dismissed'
                    if lower.startswith('allowed'):
                        return 'Appeal_Allowed'
                    if lower.startswith('partly'):
                        return 'Partly_Allowed'
                return 'Other'

            if 'result_category' not in df_base.columns:
                if 'combined_outcome' in df_base.columns:
                    df_base['result_category'] = df_base['combined_outcome'].apply(simplify_outcome)
                else:
                    df_base['result_category'] = 'Other'

            og_col = offence_group_column(df_base)
            df_base['_offence_group'] = (
                df_base[og_col].fillna('Unknown').astype(str).replace('', 'Unknown')
            )
            if 'high_court_location' in df_base.columns:
                df_base['_court_canon'] = df_base['high_court_location'].apply(canonicalize_high_court)
            else:
                df_base['_court_canon'] = 'Unknown'

            total = int(len(df_base))
            oc = df_base['result_category'].value_counts().to_dict()
            allowed = int(oc.get('Appeal_Allowed', 0))
            dismissed = int(oc.get('Appeal_Dismissed', 0))
            partly = int(oc.get('Partly_Allowed', 0))
            other = total - allowed - dismissed - partly

            overall = {
                "n": total,
                "appeal_allowed_pct": round(100 * allowed / total, 2) if total else 0.0,
                "partly_allowed_pct": round(100 * partly / total, 2) if total else 0.0,
                "appeal_dismissed_pct": round(100 * dismissed / total, 2) if total else 0.0,
                "other_pct": round(100 * other / total, 2) if total else 0.0,
            }

            def slice_stats(group_col: str, top: int = 40) -> List[Dict[str, Any]]:
                rows_out: List[Dict[str, Any]] = []
                for key in df_base[group_col].value_counts().head(top).index.tolist():
                    grp = df_base[df_base[group_col] == key]
                    n = int(len(grp))
                    counts = grp['result_category'].value_counts().to_dict()
                    a = int(counts.get('Appeal_Allowed', 0))
                    p = int(counts.get('Partly_Allowed', 0))
                    d = int(counts.get('Appeal_Dismissed', 0))
                    rows_out.append({
                        "slice_value": str(key),
                        "n": n,
                        "appeal_allowed_pct": round(100 * a / n, 2) if n else 0.0,
                        "partly_allowed_pct": round(100 * p / n, 2) if n else 0.0,
                        "appeal_dismissed_pct": round(100 * d / n, 2) if n else 0.0,
                        "low_sample": n < min_slice_n,
                    })
                return rows_out

            by_offence = slice_stats('_offence_group')
            by_court = slice_stats('_court_canon')

            by_year: List[Dict[str, Any]] = []
            if 'coa_year' in df_base.columns:
                for y in sorted(df_base['coa_year'].dropna().unique().tolist()):
                    try:
                        yi = int(y)
                    except (TypeError, ValueError):
                        continue
                    grp = df_base[df_base['coa_year'] == y]
                    n = int(len(grp))
                    counts = grp['result_category'].value_counts().to_dict()
                    a = int(counts.get('Appeal_Allowed', 0))
                    p = int(counts.get('Partly_Allowed', 0))
                    d = int(counts.get('Appeal_Dismissed', 0))
                    by_year.append({
                        "year": yi,
                        "n": n,
                        "appeal_allowed_pct": round(100 * a / n, 2) if n else 0.0,
                        "partly_allowed_pct": round(100 * p / n, 2) if n else 0.0,
                        "appeal_dismissed_pct": round(100 * d / n, 2) if n else 0.0,
                        "low_sample": n < min_slice_n,
                    })

            notes = [
                f"Slices with n < {min_slice_n} are flagged as low_sample (descriptive only).",
                "This report reflects label distribution in the corpus, not model calibration or error rates.",
            ]

            return {
                "generated_at": datetime.now().isoformat(),
                "dataset_rows": total,
                "min_slice_n": min_slice_n,
                "overall": overall,
                "by_offence": by_offence,
                "by_court": by_court,
                "by_year": by_year,
                "notes": notes,
            }
        except Exception as e:
            logger.error(f"Error building fairness slice report: {e}")
            return {
                "generated_at": datetime.now().isoformat(),
                "error": str(e),
                "dataset_rows": 0,
                "min_slice_n": min_slice_n,
                "overall": {},
                "by_offence": [],
                "by_court": [],
                "by_year": [],
                "notes": [],
            }

# Singleton instance
_prediction_service = None

def get_prediction_service() -> PredictionService:
    """Get or create the prediction service singleton"""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = PredictionService()
    return _prediction_service
