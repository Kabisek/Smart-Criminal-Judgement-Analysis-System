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
    case_id: str
    similarity_score: float
    case_summary: str
    outcome: str
    key_legal_points: List[str]
    citation: Optional[str] = None
    year: Optional[int] = None

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
