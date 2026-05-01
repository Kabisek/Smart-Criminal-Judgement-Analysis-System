"""
Enhanced prediction routes for improved user experience
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
import logging
import time
from datetime import datetime

from comp3.api.models.enhanced_schemas import (
    DetailedPredictionRequest, DetailedPredictionResponse,
    EducationalResponse, BatchAnalysisRequest, BatchAnalysisResponse,
    SimilaritySearchRequest, SimilaritySearchResponse,
    LearningRequest, AssessmentRequest, AssessmentResponse,
    SimilarCase, LegalFactor, StrategyRecommendation
)
from comp3.api.services.prediction_service import get_prediction_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/predict/detailed", response_model=DetailedPredictionResponse)
async def predict_detailed_outcome(request: DetailedPredictionRequest):
    """
    Enhanced prediction with legal reasoning and analysis
    
    This endpoint provides:
    - Basic prediction with confidence
    - Detailed legal reasoning
    - Key influencing factors
    - Risk assessment
    - Strategy recommendations
    - Similar case precedents
    - Educational content for students
    
    Args:
        request: Detailed prediction request with user preferences
        
    Returns:
        DetailedPredictionResponse with comprehensive analysis
    """
    try:
        start_time = time.time()
        
        # Validate input
        if len(request.case_description.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="Case description must be at least 50 characters long"
            )
        
        logger.info(f"Received detailed prediction request for {request.user_type} user")
        
        # Get prediction service
        prediction_service = get_prediction_service()
        
        # Make basic prediction
        basic_result = await prediction_service.predict_appeal_outcome(request.case_description)
        
        # Generate enhanced analysis based on user type
        enhanced_analysis = await _generate_enhanced_analysis(
            request.case_description, 
            basic_result, 
            request.user_type,
            request.analysis_level
        )
        
        # Find similar cases if requested
        similar_cases = []
        if request.include_precedents:
            # Use the same similar cases from basic result to avoid duplicate async calls
            similar_cases_data = basic_result.get('similar_cases', [])
            
            # Convert to SimilarCase objects
            for case in similar_cases_data:
                # Convert similarity from percentage to score
                similarity_score = case['similarity'] / 100.0
                
                # Lower threshold to 0.5 (50%) instead of 0.7 (70%)
                if similarity_score >= 0.5:
                    similar_cases.append(SimilarCase(
                        case_id=case['case_id'],
                        similarity_score=similarity_score,
                        case_summary=case.get('facts', ''),
                        outcome=case['outcome'],
                        key_legal_points=[case.get('grounds', '')],
                        citation=None,  # Not available in current data
                        year=None     # Not available in current data
                    ))
        
        # Create response
        processing_time = time.time() - start_time
        
        response = DetailedPredictionResponse(
            # Basic prediction
            prediction=basic_result['prediction'],
            confidence=basic_result['confidence'],
            probabilities=basic_result['probabilities'],
            detected_features=basic_result['detected_features'],  # Add this line
            
            # Enhanced analysis
            legal_reasoning=enhanced_analysis['legal_reasoning'],
            key_factors=enhanced_analysis['key_factors'],
            risk_assessment=enhanced_analysis['risk_assessment'],
            strategy_recommendations=enhanced_analysis['strategy_recommendations'],
            
            # Similar cases
            similar_cases=similar_cases,
            
            # Educational content
            legal_concepts=enhanced_analysis['legal_concepts'],
            methodology_explanation=enhanced_analysis['methodology_explanation'],
            
            # Metadata
            processing_time=processing_time,
            model_version="Improved Ensemble v2.0",
            feature_importance=enhanced_analysis['feature_importance']
        )
        
        logger.info(f"Detailed prediction completed: {response.prediction} with {response.confidence:.1f}% confidence")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in detailed prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Detailed prediction failed: {str(e)}"
        )

@router.post("/learn/analyze", response_model=EducationalResponse)
async def analyze_case_for_learning(request: LearningRequest):
    """
    Educational case analysis for law students
    
    This endpoint provides:
    - Step-by-step legal analysis
    - Concept explanations
    - Interactive learning elements
    - Progress tracking
    - Personalized recommendations
    
    Args:
        request: Learning-focused analysis request
        
    Returns:
        EducationalResponse with learning content
    """
    try:
        logger.info(f"Received learning analysis request for {request.difficulty_level} level")
        
        # Get prediction service
        prediction_service = get_prediction_service()
        
        # Make prediction
        basic_result = await prediction_service.predict_appeal_outcome(request.case_description)
        
        # Generate educational content
        educational_content = await _generate_educational_content(
            request.case_description,
            basic_result,
            request.learning_mode,
            request.difficulty_level
        )
        
        # Create response
        response = EducationalResponse(
            explanation_level=request.difficulty_level,
            legal_concepts=educational_content['legal_concepts'],
            methodology_explanation=educational_content['methodology_explanation'],
            quiz_questions=educational_content['quiz_questions'],
            further_reading=educational_content['further_reading'],
            case_study=educational_content['case_study'],
            learning_objectives=educational_content['learning_objectives'],
            concept_mastery=educational_content['concept_mastery'],
            next_topics=educational_content['next_topics']
        )
        
        logger.info(f"Educational analysis completed for {request.learning_mode} mode")
        return response
        
    except Exception as e:
        logger.error(f"Error in educational analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Educational analysis failed: {str(e)}"
        )

@router.post("/find/similar", response_model=SimilaritySearchResponse)
async def find_similar_cases_endpoint(request: SimilaritySearchRequest):
    """
    Find legally similar cases with detailed comparison
    
    This endpoint provides:
    - Similar cases with similarity scores
    - Key legal differences
    - Precedent analysis
    - Outcome predictions for similar cases
    
    Args:
        request: Similarity search parameters
        
    Returns:
        SimilaritySearchResponse with matching cases
    """
    try:
        logger.info(f"Received similarity search request with threshold {request.similarity_threshold}")
        
        # Find similar cases
        similar_cases = await _find_similar_cases(
            request.case_description, 
            request.max_results,
            request.similarity_threshold
        )
        
        # Generate search metadata
        search_metadata = {
            "similarity_threshold": request.similarity_threshold,
            "max_results": request.max_results,
            "include_outcomes": request.include_outcomes,
            "search_method": "hybrid_bert_tfidf"
        }
        
        # Create response
        response = SimilaritySearchResponse(
            query_case_summary=_summarize_case(request.case_description),
            similar_cases=similar_cases,
            search_metadata=search_metadata,
            total_matches=len(similar_cases),
            search_time=0.5  # Placeholder for actual search time
        )
        
        logger.info(f"Similarity search completed: {len(similar_cases)} matches found")
        return response
        
    except Exception as e:
        logger.error(f"Error in similarity search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Similarity search failed: {str(e)}"
        )

@router.post("/analyze/batch", response_model=BatchAnalysisResponse)
async def analyze_batch_cases(request: BatchAnalysisRequest):
    """
    Analyze multiple cases for comparison and patterns
    
    This endpoint provides:
    - Individual predictions for each case
    - Comparative analysis across cases
    - Pattern identification
    - Success probability trends
    
    Args:
        request: Batch analysis parameters
        
    Returns:
        BatchAnalysisResponse with comprehensive analysis
    """
    try:
        if len(request.cases) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 cases allowed per batch analysis"
            )
        
        logger.info(f"Received batch analysis request for {len(request.cases)} cases")
        
        # Get prediction service
        prediction_service = get_prediction_service()
        
        # Analyze each case
        individual_results = []
        for i, case_description in enumerate(request.cases):
            basic_result = await prediction_service.predict_appeal_outcome(case_description)
            enhanced_analysis = await _generate_enhanced_analysis(
                case_description, 
                basic_result, 
                request.user_type,
                "standard"
            )
            
            detailed_response = DetailedPredictionResponse(
                prediction=basic_result['prediction'],
                confidence=basic_result['confidence'],
                probabilities=basic_result['probabilities'],
                legal_reasoning=enhanced_analysis['legal_reasoning'],
                key_factors=enhanced_analysis['key_factors'],
                risk_assessment=enhanced_analysis['risk_assessment'],
                strategy_recommendations=enhanced_analysis['strategy_recommendations'],
                similar_cases=[],
                legal_concepts=enhanced_analysis['legal_concepts'],
                methodology_explanation=enhanced_analysis['methodology_explanation'],
                processing_time=0.5,
                model_version="Improved Ensemble v2.0",
                feature_importance=enhanced_analysis['feature_importance']
            )
            individual_results.append(detailed_response)
        
        # Generate comparative analysis
        comparative_analysis = await _generate_comparative_analysis(individual_results, request.comparison_type)
        
        # Create response
        response = BatchAnalysisResponse(
            individual_results=individual_results,
            comparative_analysis=comparative_analysis,
            pattern_identification=comparative_analysis['patterns'],
            success_rate_trends=comparative_analysis['trends'],
            recommendations=comparative_analysis['recommendations']
        )
        
        logger.info(f"Batch analysis completed for {len(request.cases)} cases")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch analysis failed: {str(e)}"
        )

# Helper functions
async def _generate_enhanced_analysis(case_description: str, basic_result: Dict, user_type: str, analysis_level: str) -> Dict[str, Any]:
    """Generate enhanced analysis based on user type and preferences"""
    
    # Extract key factors from detected features
    detected_features = basic_result.get('detected_features', {})
    
    # Generate legal reasoning based on prediction
    legal_reasoning = _generate_legal_reasoning(basic_result['prediction'], detected_features)
    
    # Generate key factors with importance
    key_factors = _generate_key_factors(detected_features, basic_result['probabilities'])
    
    # Generate risk assessment
    risk_assessment = _generate_risk_assessment(basic_result['confidence'], detected_features)
    
    # Generate strategy recommendations based on user type
    strategy_recommendations = _generate_strategy_recommendations(
        basic_result['prediction'], 
        detected_features, 
        user_type
    )
    
    # Generate educational content
    legal_concepts = _extract_legal_concepts(detected_features)
    methodology_explanation = _generate_methodology_explanation(analysis_level)
    
    # Generate feature importance
    feature_importance = _calculate_feature_importance(detected_features, basic_result['probabilities'])
    
    return {
        'legal_reasoning': legal_reasoning,
        'key_factors': key_factors,
        'risk_assessment': risk_assessment,
        'strategy_recommendations': strategy_recommendations,
        'legal_concepts': legal_concepts,
        'methodology_explanation': methodology_explanation,
        'feature_importance': feature_importance
    }

def _generate_legal_reasoning(prediction: str, detected_features: Dict) -> str:
    """Generate legal reasoning explanation"""
    
    reasoning_templates = {
        'Appeal_Allowed': "The appeal is likely to be allowed based on several key factors. The presence of procedural errors or evidentiary issues in the original trial strengthens the grounds for appeal. The model identifies significant legal or factual errors that warrant appellate intervention.",
        'Appeal_Dismissed': "The appeal is likely to be dismissed as the original trial appears sound. The evidence and legal procedures followed appear to meet judicial standards. No significant reversible error has been identified that would justify overturning the original judgment.",
        'Partly_Allowed': "The appeal may be partially allowed, indicating mixed success. Some grounds may succeed while others fail, suggesting partial merit in the appellant's arguments. The court may modify certain aspects while upholding others."
    }
    
    base_reasoning = reasoning_templates.get(prediction, reasoning_templates['Appeal_Dismissed'])
    
    # Add specific detected factors
    if detected_features.get('grounds'):
        grounds_list = ', '.join(detected_features['grounds'][:3])  # Limit to first 3
        base_reasoning += f" Key grounds identified include: {grounds_list}."
    
    if detected_features.get('evidence'):
        evidence_count = len(detected_features['evidence'])
        base_reasoning += f" Evidence analysis shows {evidence_count} types of evidence presented."
    
    return base_reasoning

def _generate_key_factors(detected_features: Dict, probabilities: Dict) -> List[LegalFactor]:
    """Generate key legal factors with importance scores"""
    
    factors = []
    
    # Grounds of appeal factors
    if detected_features.get('grounds'):
        for ground in detected_features['grounds'][:3]:  # Top 3 grounds
            importance = 0.8 if ground in ['contradictions', 'procedural_error'] else 0.6
            factors.append(LegalFactor(
                factor_name=f"Ground: {ground}",
                importance=importance,
                explanation=f"This ground of appeal is significant for determining success probability",
                supporting_evidence=[f"Detected in case description: {ground}"]
            ))
    
    # Evidence factors
    if detected_features.get('evidence'):
        for evidence in detected_features['evidence'][:2]:  # Top 2 evidence types
            importance = 0.7 if evidence in ['eyewitness', 'medical_evidence'] else 0.5
            factors.append(LegalFactor(
                factor_name=f"Evidence: {evidence}",
                importance=importance,
                explanation=f"Type and quality of evidence significantly impacts appeal outcomes",
                supporting_evidence=[f"Evidence type identified: {evidence}"]
            ))
    
    # Probabilistic factors
    if probabilities.get('Appeal_Allowed', 0) > 60:
        factors.append(LegalFactor(
            factor_name="High Success Probability",
            importance=0.9,
            explanation="Model predicts high probability of appeal success",
            supporting_evidence=[f"Success probability: {probabilities['Appeal_Allowed']:.1f}%"]
        ))
    
    return factors

def _generate_risk_assessment(confidence: float, detected_features: Dict) -> str:
    """Generate risk assessment based on confidence and features"""
    
    if confidence > 70:
        risk_level = "Low Risk"
        explanation = "High confidence prediction with strong supporting factors"
    elif confidence > 50:
        risk_level = "Medium Risk"
        explanation = "Moderate confidence with mixed supporting factors"
    else:
        risk_level = "High Risk"
        explanation = "Low confidence prediction with significant uncertainties"
    
    return f"{risk_level}: {explanation}. Consider additional evidence preparation and legal research to strengthen the appeal."

def _generate_strategy_recommendations(prediction: str, detected_features: Dict, user_type: str) -> List[StrategyRecommendation]:
    """Generate strategy recommendations based on user type"""
    
    recommendations = []
    
    if user_type == "lawyer":
        if prediction == "Appeal_Allowed":
            recommendations.append(StrategyRecommendation(
                recommendation="Focus on procedural errors and evidentiary issues",
                priority="high",
                rationale="These are strongest grounds identified by the analysis",
                expected_impact="Higher probability of success"
            ))
        else:
            recommendations.append(StrategyRecommendation(
                recommendation="Consider gathering additional evidence or identifying new legal grounds",
                priority="high",
                rationale="Current grounds appear insufficient for success",
                expected_impact="Improved appeal prospects"
            ))
    
    elif user_type == "student":
        recommendations.append(StrategyRecommendation(
            recommendation="Study the identified grounds of appeal in detail",
            priority="medium",
            rationale="Understanding legal principles behind these grounds is crucial",
            expected_impact="Better legal analysis skills"
        ))
    
    else:  # general public
        recommendations.append(StrategyRecommendation(
            recommendation="Consult with legal professional for detailed advice",
            priority="high",
            rationale="Professional guidance essential for appeal preparation",
            expected_impact="Better case preparation and presentation"
        ))
    
    return recommendations

def _extract_legal_concepts(detected_features: Dict) -> List[str]:
    """Extract relevant legal concepts from detected features"""
    
    concepts = []
    
    if detected_features.get('grounds'):
        concepts.extend([
            "Grounds of Appeal",
            "Procedural Errors",
            "Evidentiary Issues"
        ])
    
    if detected_features.get('evidence'):
        concepts.extend([
            "Evidence Law",
            "Witness Testimony",
            "Forensic Evidence"
        ])
    
    if detected_features.get('offence'):
        concepts.append("Criminal Law Classification")
    
    return list(set(concepts))  # Remove duplicates

def _generate_methodology_explanation(analysis_level: str) -> str:
    """Generate explanation of the analysis methodology"""
    
    explanations = {
        "basic": "This analysis uses machine learning to identify key legal factors and predict appeal outcomes based on historical case patterns.",
        "standard": "The analysis combines traditional legal feature extraction with advanced NLP techniques including BERT embeddings and TF-IDF text analysis to provide comprehensive appeal outcome predictions.",
        "detailed": "This sophisticated analysis employs an ensemble model trained on thousands of Sri Lankan appeal cases, using hybrid feature engineering that combines domain-specific legal features with contextual text embeddings to generate highly accurate predictions."
    }
    
    return explanations.get(analysis_level, explanations["standard"])

def _calculate_feature_importance(detected_features: Dict, probabilities: Dict) -> Dict[str, float]:
    """Calculate importance scores for detected features"""
    
    importance = {}
    
    # Grounds importance
    if detected_features.get('grounds'):
        for i, ground in enumerate(detected_features['grounds']):
            importance[f"ground_{ground}"] = 0.8 - (i * 0.1)  # Decreasing importance
    
    # Evidence importance
    if detected_features.get('evidence'):
        for i, evidence in enumerate(detected_features['evidence']):
            importance[f"evidence_{evidence}"] = 0.7 - (i * 0.1)
    
    # Add prediction confidence as overall importance
    importance["prediction_confidence"] = max(probabilities.values()) / 100.0
    
    return importance

async def _find_similar_cases(case_description: str, max_results: int = 5, threshold: float = 0.5) -> List[SimilarCase]:
    """Find similar cases using prediction service"""
    
    try:
        # Get prediction service
        prediction_service = get_prediction_service()
        
        # Make basic prediction to get BERT embedding
        basic_result = await prediction_service.predict_appeal_outcome(case_description)
        
        # Find similar cases using service
        similar_cases_data = prediction_service.predictor.find_similar_cases(
            basic_result['bert_embedding'], 
            top_k=max_results
        )
        
        logger.info(f"Found {len(similar_cases_data)} similar cases from service")
        
        # Convert to SimilarCase objects
        similar_cases = []
        for case in similar_cases_data:
            # Convert similarity from percentage to score
            similarity_score = case['similarity'] / 100.0
            
            logger.info(f"Processing case {case['case_id']} with similarity {similarity_score:.3f} (threshold: {threshold})")
            
            # Lower threshold to 0.5 (50%) instead of 0.7 (70%)
            if similarity_score >= threshold:
                similar_cases.append(SimilarCase(
                    case_id=case['case_id'],
                    similarity_score=similarity_score,
                    case_summary=case['facts'][:200] + "..." if len(case['facts']) > 200 else case['facts'],
                    outcome=case['outcome'],
                    key_legal_points=[case['grounds'][:100] + "..." if len(case['grounds']) > 100 else case['grounds']],
                    citation=None,  # Not available in current data
                    year=None     # Not available in current data
                ))
        
        logger.info(f"Returning {len(similar_cases)} similar cases after filtering")
        return similar_cases
        
    except Exception as e:
        logger.error(f"Error finding similar cases: {e}")
        # Fallback to empty list
        return []

async def _generate_educational_content(case_description: str, basic_result: Dict, learning_mode: str, difficulty_level: str) -> Dict[str, Any]:
    """Generate educational content for students"""
    
    return {
        'legal_concepts': _extract_legal_concepts(basic_result.get('detected_features', {})),
        'methodology_explanation': _generate_methodology_explanation(difficulty_level),
        'quiz_questions': [
            "What are the key grounds of appeal identified in this case?",
            "How does the evidence type affect appeal outcomes?",
            "What procedural factors are most important for appeal success?"
        ],
        'further_reading': [
            "Sri Lankan Penal Code - Appeals Procedure",
            "Evidence Law in Sri Lanka",
            "Landmark Appeal Cases in Sri Lanka"
        ],
        'case_study': {
            'title': "Analysis of Appeal Success Factors",
            'case_type': basic_result['prediction'],
            'key_learning': "Understanding the relationship between grounds and evidence",
            'discussion_points': ["Procedural compliance", "Evidence sufficiency", "Legal precedent"]
        },
        'learning_objectives': [
            "Identify grounds of appeal",
            "Analyze evidence strength",
            "Understand appeal success factors"
        ],
        'concept_mastery': {
            "Grounds of Appeal": 0.7,
            "Evidence Analysis": 0.6,
            "Legal Reasoning": 0.8
        },
        'next_topics': [
            "Advanced Evidence Law",
            "Appellate Court Procedures",
            "Legal Research Methods"
        ]
    }

async def _generate_comparative_analysis(results: List[DetailedPredictionResponse], comparison_type: str) -> Dict[str, Any]:
    """Generate comparative analysis across multiple cases"""
    
    # Calculate success rates
    outcomes = [r.prediction for r in results]
    success_rates = {
        'Appeal_Allowed': outcomes.count('Appeal_Allowed') / len(outcomes) * 100,
        'Appeal_Dismissed': outcomes.count('Appeal_Dismissed') / len(outcomes) * 100,
        'Partly_Allowed': outcomes.count('Partly_Allowed') / len(outcomes) * 100
    }
    
    # Identify patterns
    patterns = []
    if success_rates['Appeal_Allowed'] > 50:
        patterns.append("High success rate for appeal allowance in this batch")
    if len(set(outcomes)) == 1:
        patterns.append("Consistent outcomes across all cases")
    
    # Generate recommendations
    recommendations = []
    if success_rates['Appeal_Dismissed'] > 60:
        recommendations.append("Consider strengthening grounds of appeal for better success rates")
    
    return {
        'success_rates': success_rates,
        'patterns': patterns,
        'trends': success_rates,
        'recommendations': recommendations
    }

def _summarize_case(case_description: str) -> str:
    """Generate a brief summary of the case"""
    # Simple summarization - in production, use proper NLP
    sentences = case_description.split('.')[:3]  # First 3 sentences
    return '. '.join(sentences) + '...'
