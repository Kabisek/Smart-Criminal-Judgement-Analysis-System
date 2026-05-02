"""
Enhanced Pydantic models for improved API responses
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class DetailedPredictionRequest(BaseModel):
    case_description: str = Field(..., min_length=50, description="Detailed case description")
    user_type: str = Field(default="general", description="User type: general, lawyer, student")
    analysis_level: str = Field(default="standard", description="Analysis depth: basic, standard, detailed")
    include_precedents: bool = Field(default=True, description="Include similar case precedents")
    language: str = Field(default="en", description="Response language: en, si, ta")

class SimilarCase(BaseModel):
    # Core identification and similarity
    case_id: str
    similarity_score: float
    citation: Optional[str] = None
    
    # Case facts and summary
    case_summary: str
    outcome: str
    
    # Temporal information
    year: Optional[int] = None
    decision_date: Optional[str] = Field(None, description="Date when judgment was delivered (YYYY-MM-DD)")
    
    # Legal details
    key_legal_points: List[str]
    offence: Optional[str] = None
    grounds: Optional[str] = None
    appeal_grounds_list: Optional[List[str]] = Field(None, description="Structured list of appeal grounds")
    
    # Case outcome information
    verdict_reasoning: Optional[str] = Field(None, description="Why the appeal was allowed/dismissed - judge's reasoning")
    judge_commentary: Optional[str] = Field(None, description="Key remarks and observations from the judge")
    
    # Additional metadata
    high_court: Optional[str] = None
    conviction_status: Optional[str] = None
    evidence_types: Optional[List[str]] = Field(None, description="Types of evidence presented in the case")
    
    # Analytics
    appeal_success_rate: Optional[float] = Field(None, description="Success rate for similar cases with same grounds")
    precedent_value: Optional[str] = Field(None, description="Relevance/binding nature of this precedent")
    relevance_badge: Optional[str] = Field("medium", description="Precedent relevance badge: high, medium, low")

class LegalFactor(BaseModel):
    factor_name: str
    importance: float
    explanation: str
    supporting_evidence: List[str]

class StrategyRecommendation(BaseModel):
    recommendation: str
    priority: str  # high, medium, low
    rationale: str
    expected_impact: str

class DetailedPredictionResponse(BaseModel):
    # Basic prediction
    prediction: str
    confidence: float
    confidence_band: str = Field(default="low", description="Reliability band: low, medium, high")
    manual_review_required: bool = Field(default=True, description="Whether manual legal review is mandatory")
    reliability_note: str = Field(default="Manual legal review is recommended.", description="Safety guidance for interpreting prediction")
    abstained: bool = Field(default=False, description="Whether model abstained due to low confidence/ambiguity")
    review_priority: str = Field(default="medium", description="Recommended review priority: low, medium, high")
    top_outcomes: List[Dict[str, Any]] = Field(default_factory=list, description="Top-N ranked outcome probabilities")
    reason_trace: List[str] = Field(default_factory=list, description="Short explanation bullets for prediction reasoning")
    shap_summary: Dict[str, Any] = Field(default_factory=dict, description="SHAP-style explanation payload/status")
    confidence_interval: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Heuristic uncertainty band derived from class-probability separation (not a formal statistical CI)",
    )
    precedent_trend: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Descriptive outcome mix by year among retrieved similar precedents",
    )
    governance_note: Optional[str] = Field(
        default=None,
        description="Limitations: subgroup coverage, advisory-only use",
    )
    probabilities: Dict[str, float]
    detected_features: Dict[str, List[str]]  # Add this missing field
    
    # Enhanced analysis
    legal_reasoning: str
    key_factors: List[LegalFactor]
    risk_assessment: str
    strategy_recommendations: List[StrategyRecommendation]
    
    # Similar cases
    similar_cases: List[SimilarCase]
    
    # Educational content
    legal_concepts: List[str]
    methodology_explanation: str
    
    # Metadata
    processing_time: float
    model_version: str
    feature_importance: Dict[str, float]
    analysis_timestamp: datetime = Field(default_factory=datetime.now)

    # New contextual analytics derived from historical data
    context_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated statistics for offence, location and year relevant to the case"
    )

    # New analytics for grounds and evidence
    grounds_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated success statistics for each detected ground of appeal"
    )
    evidence_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated success statistics for each detected evidence type"
    )

class EducationalResponse(BaseModel):
    # Learning content
    explanation_level: str  # "Basic", "Intermediate", "Advanced"
    legal_concepts: List[str]
    methodology_explanation: str
    
    # Interactive elements
    quiz_questions: List[str]
    further_reading: List[str]
    
    # Case study
    case_study: Dict[str, Any]
    learning_objectives: List[str]
    
    # Progress tracking
    concept_mastery: Dict[str, float]
    next_topics: List[str]

class BatchAnalysisRequest(BaseModel):
    cases: List[str] = Field(..., min_items=1, max_items=10)
    comparison_type: str = Field(default="outcomes", description="Comparison focus: outcomes, factors, trends")
    user_type: str = Field(default="professional", description="User type for analysis depth")

class BatchAnalysisResponse(BaseModel):
    individual_results: List[DetailedPredictionResponse]
    comparative_analysis: Dict[str, Any]
    pattern_identification: List[str]
    success_rate_trends: Dict[str, float]
    recommendations: List[str]

class SimilaritySearchRequest(BaseModel):
    case_description: str = Field(..., min_length=50)
    max_results: int = Field(default=5, ge=1, le=20)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_outcomes: bool = Field(default=True)

class SimilaritySearchResponse(BaseModel):
    query_case_summary: str
    similar_cases: List[SimilarCase]
    search_metadata: Dict[str, Any]
    total_matches: int
    search_time: float

class LearningRequest(BaseModel):
    case_description: str = Field(..., min_length=50)
    learning_mode: str = Field(default="guided", description="guided, independent, assessment")
    difficulty_level: str = Field(default="intermediate", description="beginner, intermediate, advanced")
    include_feedback: bool = Field(default=True)

class AssessmentRequest(BaseModel):
    case_description: str = Field(..., min_length=50)
    assessment_type: str = Field(default="comprehensive", description="evidence, arguments, overall")
    jurisdiction: str = Field(default="srilanka", description="Legal jurisdiction")
    include_precedents: bool = Field(default=True)

class AssessmentResponse(BaseModel):
    evidence_strength: Dict[str, float]
    argument_quality: float
    success_probability: float
    precedent_relevance: List[str]
    strategy_effectiveness: Dict[str, float]
    improvement_suggestions: List[str]
