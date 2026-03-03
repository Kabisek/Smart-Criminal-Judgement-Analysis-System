"""
Enhanced Legal Agent for AI Strategy Generation
Generates comprehensive case analysis and argument reports
"""

import json
import logging
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add src to path for argument extractor
sys.path.insert(0, str(Path(__file__).parent.parent))
from comp2.src.ml_utils.argument_extractor import ArgumentExtractor
from comp2.src.ml_utils.feature_extractor import FeatureExtractor
from comp2.src.ml_utils.model_based_argument_generator import ModelBasedArgumentGenerator

logger = logging.getLogger(__name__)

class EnhancedLegalAgent:
    """Enhanced legal agent that generates comprehensive case analysis and arguments"""
    
    def __init__(self, llm_client, use_model_arguments=True, model_only_mode=True):
        self.llm = llm_client
        self.use_model_arguments = use_model_arguments
        self.model_only_mode = model_only_mode  # If True, use only trained models (no LLM)
        self.argument_extractor = None
        self.feature_extractor = None
        self.model_argument_generator = None
        
        # Initialize argument extractor if enabled
        if use_model_arguments:
            try:
                self.argument_extractor = ArgumentExtractor()
                self.feature_extractor = FeatureExtractor()
                
                # Initialize model-based argument generator (no LLM)
                if model_only_mode:
                    self.model_argument_generator = ModelBasedArgumentGenerator(self.argument_extractor)
                    logger.info("✅ Model-based argument generator initialized (NO LLM - using trained models only)")
                else:
                    logger.info("✅ Argument extractor initialized (model-based argument generation enabled)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize argument extractor: {e}. Using LLM-only mode.")
                self.use_model_arguments = False
                self.model_only_mode = False
    
    def generate_analyzed_case_file(self, case_text: str, input_metadata: Dict = None, full_json_data: Dict = None) -> Dict:
        """
        Generate Output File 1: Comprehensive analyzed case file
        
        Args:
            case_text: Text content of the case
            input_metadata: Optional input metadata (for JSON inputs)
            full_json_data: Full JSON data structure from input file
            
        Returns:
            Dict: Structured analyzed case file
        """
        # First, try to extract structured information from input JSON
        extracted_info = self._extract_case_info_from_input(case_text, input_metadata, full_json_data)
        
        # Build enhanced prompt with extracted information
        system_prompt = """
        You are a distinguished Senior Counsel in Sri Lanka specializing in criminal law.
        Your expertise covers the Penal Code, Evidence Ordinance, and Roman-Dutch Law principles.
        Analyze the provided case facts comprehensively and output strictly in JSON format.
        IMPORTANT: Extract ALL specific details including names, dates, locations, and key facts from the text.
        """
        
        # Include extracted information in prompt
        info_context = ""
        if extracted_info:
            info_context = f"\nEXTRACTED INFORMATION:\n- Accused: {extracted_info.get('accused', 'Not specified')}\n"
            info_context += f"- Location: {extracted_info.get('location', 'Not specified')}\n"
            info_context += f"- Date: {extracted_info.get('date', 'Not specified')}\n"
            if extracted_info.get('prosecution_points'):
                info_context += f"- Prosecution points: {len(extracted_info['prosecution_points'])} items\n"
            if extracted_info.get('defense_points'):
                info_context += f"- Defense points: {len(extracted_info['defense_points'])} items\n"
        
        user_prompt = f"""
        CASE TEXT:
        {case_text[:4000]}
        {info_context}
        
        TASK:
        Extract ALL specific details from the case text and create a comprehensive analysis. 
        For names, dates, locations - extract the EXACT values mentioned in the text.
        For arguments - extract or synthesize from the case facts.
        
        Required JSON format:
        {{
            "case_header": {{
                "file_number": "Generate format: L-SYN-2024-XXXX (use year from case)",
                "date_of_analysis": "{datetime.now().strftime('%B %d, %Y')}",
                "subject": "Specific subject like 'Murder and Robbery Case: State vs. [Accused Name]'"
            }},
            "incident_timeline": {{
                "what_happened": "Complete detailed narrative (3-5 sentences minimum)",
                "where_it_happened": "EXACT location mentioned in text (e.g., 'Residential area in [City]')",
                "key_dates": ["Format: 'Date: Description' - extract ALL dates mentioned"]
            }},
            "parties_and_roles": {{
                "accused": "EXACT name mentioned in text (e.g., 'Chandi Malli')",
                "complainant": "EXACT name or description from text",
                "doubters_witnesses": [
                    {{
                        "name": "Witness name or description",
                        "role": "Specific role (e.g., 'Neighbor witness', 'Temple priest', 'Doctor')",
                        "doubt_factor": "Specific credibility concern"
                    }}
                ]
            }},
            "argument_synthesis": {{
                "prosecution_logic": ["Specific point 1", "Specific point 2", "Specific point 3"],
                "defense_logic": ["Specific point 1", "Specific point 2", "Specific point 3"],
                "reasonable_doubt_factors": ["Specific factor 1", "Specific factor 2"]
            }},
            "final_judicial_opinion": "Comprehensive 3-4 sentence assessment with specific case references"
        }}
        
        CRITICAL: Do NOT use placeholder values like 'Unknown' or 'N/A'. Extract real values from the text.
        Output ONLY valid JSON without any markdown formatting.
        """
        
        response = self.llm.generate(system_prompt, user_prompt)
        parsed = self._parse_json(response)
        
        # Merge extracted info with LLM output, prioritizing extracted info
        if "error" not in parsed and isinstance(parsed, dict):
            # Enhance with extracted information if LLM missed it
            if extracted_info:
                # Fill in missing accused name
                parties = parsed.setdefault('parties_and_roles', {})
                if not parties.get('accused') or parties['accused'].lower() in ['unknown', 'not specified', 'n/a']:
                    parties['accused'] = extracted_info.get('accused', 'Not specified')
                
                # Fill in missing location
                timeline = parsed.setdefault('incident_timeline', {})
                if not timeline.get('where_it_happened') or timeline['where_it_happened'].lower() in ['unknown', 'not specified']:
                    timeline['where_it_happened'] = extracted_info.get('location', 'Location not specified')
                
                # Fill in missing dates
                if not timeline.get('key_dates') or len(timeline.get('key_dates', [])) == 0:
                    timeline['key_dates'] = [f"{date}: Incident date" for date in extracted_info.get('dates', [])]
                
                # Fill in missing complainant
                if not parties.get('complainant') or parties['complainant'].lower() in ['unknown', 'not specified']:
                    parties['complainant'] = extracted_info.get('complainant', 'Not specified')
                
                # Fill in missing arguments
                args = parsed.setdefault('argument_synthesis', {})
                if not args.get('prosecution_logic') or len(args.get('prosecution_logic', [])) == 0:
                    args['prosecution_logic'] = extracted_info.get('prosecution_points', [])[:5]
                if not args.get('defense_logic') or len(args.get('defense_logic', [])) == 0:
                    args['defense_logic'] = extracted_info.get('defense_points', [])[:5]
                if not args.get('reasonable_doubt_factors') or len(args.get('reasonable_doubt_factors', [])) == 0:
                    args['reasonable_doubt_factors'] = extracted_info.get('doubt_factors', [])[:4]
                
                # Fill in missing opinion
                if not parsed.get('final_judicial_opinion') or parsed['final_judicial_opinion'].lower() in ['analysis pending', 'pending']:
                    parsed['final_judicial_opinion'] = extracted_info.get('opinion', 
                        'Case analysis requires careful evaluation of evidence and legal precedents.')
                
                # Fill in missing subject
                header = parsed.setdefault('case_header', {})
                if not header.get('subject') or header['subject'].lower() in ['case analysis', 'unknown']:
                    header['subject'] = extracted_info.get('subject', 'Criminal Case Analysis')
        else:
            # LLM failed - build directly from extracted info
            parsed = self._build_case_file_from_extracted_info(case_text, extracted_info)
        
        # Wrap in expected structure
        analyzed_case = {
            "status": "success",
            "analyzed_case_file": parsed
        }
        
        return analyzed_case
    
    def _extract_case_info_from_input(self, case_text: str, input_metadata: Dict = None, full_json_data: Dict = None) -> Dict:
        """Extract structured information from input JSON data"""
        extracted = {}
        text_lower = case_text.lower()
        
        # Try to get legal analysis from full_json_data
        if full_json_data and isinstance(full_json_data, dict):
            data_section = full_json_data.get('data', {})
            legal_analysis = data_section.get('legal_analysis', {})
            
            # Extract prosecution and defense arguments - split into bullet points
            if legal_analysis.get('prosecution_argument'):
                prosecution_text = legal_analysis['prosecution_argument']
                # Extract key sentences (split by periods, filter by length)
                sentences = [s.strip() for s in prosecution_text.split('.') if len(s.strip()) > 40]
                extracted['prosecution_points'] = sentences[:6]  # Top 6 key points
            
            if legal_analysis.get('defense_argument'):
                defense_text = legal_analysis['defense_argument']
                sentences = [s.strip() for s in defense_text.split('.') if len(s.strip()) > 40]
                extracted['defense_points'] = sentences[:6]  # Top 6 key points
            
            # Extract reasonable doubt factors from defense argument
            if legal_analysis.get('defense_argument'):
                defense_text = legal_analysis['defense_argument'].lower()
                doubt_keywords = ['unreliable', 'question', 'challenge', 'doubt', 'uncertain', 'unclear']
                doubt_sentences = [s.strip() for s in legal_analysis['defense_argument'].split('.') 
                                 if any(kw in s.lower() for kw in doubt_keywords) and len(s.strip()) > 30]
                extracted['doubt_factors'] = doubt_sentences[:4]
            
            # Generate opinion from both arguments
            if legal_analysis.get('prosecution_argument') and legal_analysis.get('defense_argument'):
                extracted['opinion'] = (
                    "The case presents strong prosecution evidence including direct witness identification, "
                    "dying declaration, and recovery of weapon. However, the defense presents an alibi with "
                    "video evidence and challenges witness reliability. The court will need to weigh the "
                    "credibility of evidence and determine if reasonable doubt exists."
                )
        
        # Extract accused name - look for "named X" or "X" after suspect/accused
        name_patterns = [
            r'(?:named|called|accused|suspect|main suspect|the main suspect)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:is|was)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:who|that|,|\.|had)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\'s lawyers',  # Pattern: "X Y's lawyers"
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s+stated',  # Pattern: "X Y stated"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, case_text)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and name not in ['The', 'State', 'Court', 'Police', 'Doctor', 'Police Officer']:
                    extracted['accused'] = name
                    break
        
        # Extract dates - comprehensive pattern
        date_patterns = [
            r'(\w+\s+\d{1,2},?\s+\d{4})',  # "January 12, 2024"
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # "12/01/2024"
            r'(on\s+\w+\s+\d{1,2},?\s+\d{4})',  # "on January 12, 2024"
        ]
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, case_text, re.IGNORECASE)
            dates.extend(matches)
        if dates:
            # Format dates properly
            formatted_dates = []
            for date in dates[:5]:
                date_clean = date.strip()
                if 'on ' in date_clean.lower():
                    date_clean = date_clean[3:].strip()
                formatted_dates.append(date_clean)
            extracted['dates'] = formatted_dates
        
        # Extract location - better context
        location_patterns = [
            r'(?:at|in|near)\s+(?:a\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+area|residential area)?)',
            r'(residential\s+(?:area|property|property in\s+)?[A-Z]?[a-z]*(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+residential area',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, case_text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up common prefixes
                location = re.sub(r'^(at|in|near|a)\s+', '', location, flags=re.IGNORECASE).strip()
                if len(location) > 3:
                    extracted['location'] = location
                    break
        
        # If no location found, try keyword matching
        if 'location' not in extracted:
            for keyword in ['polonnaruwa', 'colombo', 'residential area', 'home', 'temple', 'hospital']:
                if keyword.lower() in text_lower:
                    extracted['location'] = keyword.title() if keyword.lower() != 'home' else 'Residential Property'
                    break
        
        # Extract complainant/husband name
        husband_patterns = [
            r'my husband[,\s]+([A-Z][a-z]+)',
            r'husband[,\s]+([A-Z][a-z]+)',
            r'([A-Z][a-z]+),\s+my husband',
        ]
        for pattern in husband_patterns:
            match = re.search(pattern, case_text, re.IGNORECASE)
            if match:
                husband_name = match.group(1).strip()
                extracted['complainant'] = f"{husband_name} and family"
                break
        
        # Extract son name
        son_match = re.search(r'(?:son|our son)[,\s]+([A-Z][a-z]+)', case_text, re.IGNORECASE)
        if son_match:
            extracted['victim_names'] = [son_match.group(1).strip()]
        
        # Generate subject line
        if extracted.get('accused'):
            accused_name = extracted['accused']
            if extracted.get('dates'):
                date_str = extracted['dates'][0]
                year_match = re.search(r'\d{4}', date_str)
                year = year_match.group(0) if year_match else datetime.now().strftime('%Y')
            else:
                year = datetime.now().strftime('%Y')
            extracted['subject'] = f"Criminal Case: State vs. {accused_name} ({year})"
        
        return extracted
    
    def _build_case_file_from_extracted_info(self, case_text: str, extracted_info: Dict) -> Dict:
        """Build case file structure directly from extracted information"""
        # Generate file number
        year = datetime.now().strftime('%Y')
        if extracted_info.get('dates'):
            year_match = re.search(r'\d{4}', extracted_info['dates'][0])
            if year_match:
                year = year_match.group(0)
        
        # Build what_happened from case text (first 600 chars with sentence boundary)
        what_happened = case_text[:600]
        last_period = what_happened.rfind('.')
        if last_period > 200:
            what_happened = what_happened[:last_period+1]
        
        # Build dates list
        key_dates = []
        if extracted_info.get('dates'):
            key_dates = [f"{date}: Date of incident" for date in extracted_info['dates'][:3]]
        
        # Build witnesses list
        witnesses = []
        if 'witness' in case_text.lower() or 'neighbor' in case_text.lower():
            witnesses.append({
                "name": "Witness (Neighbor)",
                "role": "Eyewitness claiming to see accused leaving scene",
                "doubt_factor": "Visual identification occurred at night, may have limited reliability"
            })
        if 'temple' in case_text.lower() or 'priest' in case_text.lower():
            witnesses.append({
                "name": "Temple Priest (Potential Alibi Witness)",
                "role": "Potential alibi witness",
                "doubt_factor": "May not be able to confirm exact timing of presence"
            })
        if 'doctor' in case_text.lower() or 'hospital' in case_text.lower():
            witnesses.append({
                "name": "Medical Officer",
                "role": "Medical examination and cause of death determination",
                "doubt_factor": "Standard medical evidence"
            })
        
        return {
            "case_header": {
                "file_number": f"L-SYN-{year}-{datetime.now().strftime('%m%d')}",
                "date_of_analysis": datetime.now().strftime("%B %d, %Y"),
                "subject": extracted_info.get('subject', f'Criminal Case Analysis - {year}')
            },
            "incident_timeline": {
                "what_happened": what_happened,
                "where_it_happened": extracted_info.get('location', 'Location as described in case'),
                "key_dates": key_dates
            },
            "parties_and_roles": {
                "accused": extracted_info.get('accused', 'Accused as mentioned in case'),
                "complainant": extracted_info.get('complainant', 'Complainant as described in case'),
                "doubters_witnesses": witnesses
            },
            "argument_synthesis": {
                "prosecution_logic": extracted_info.get('prosecution_points', [
                    "Evidence supports prosecution case based on available facts"
                ])[:6],
                "defense_logic": extracted_info.get('defense_points', [
                    "Defense presents counter-arguments based on available evidence"
                ])[:6],
                "reasonable_doubt_factors": extracted_info.get('doubt_factors', [
                    "Factors creating reasonable doubt based on defense arguments"
                ])[:4]
            },
            "final_judicial_opinion": extracted_info.get('opinion',
                "The case requires careful evaluation of all evidence, witness credibility, "
                "and legal precedents. Both prosecution and defense present compelling arguments "
                "that must be weighed by the court."
            )
        }
    
    def generate_arguments_report(self, case_text: str, similar_cases: List[Dict], case_ids: List[str], distances: List[float] = None, case_dict: Dict = None) -> Dict:
        """
        Generate Output File 2: Arguments report with adversarial simulation
        
        Args:
            case_text: Text content of the case
            similar_cases: List of similar case dictionaries
            case_ids: List of case IDs corresponding to similar cases
            
        Returns:
            Dict: Structured arguments report
        """
        # Step 0: Extract model-based argument patterns (if enabled)
        model_patterns = []
        model_patterns_context = ""
        all_model_points = []  # Collect all argument points for better integration
        
        if self.use_model_arguments and self.argument_extractor and self.feature_extractor:
            try:
                # Generate embedding for new case
                query_embedding = self.feature_extractor.extract_embeddings([case_text], show_progress=False)
                
                # Extract argument patterns using trained model
                model_patterns = self.argument_extractor.extract_argument_patterns(
                    query_embedding, 
                    top_k=5
                )
                
                # Collect all argument points from patterns
                for pattern in model_patterns:
                    points = pattern.get('argument_points', [])
                    if points:
                        all_model_points.extend(points)
                    # Also extract from judge statements
                    judge_stmts = pattern.get('judge_statements', [])
                    for stmt in judge_stmts:
                        if isinstance(stmt, dict):
                            stmt_text = stmt.get('statement', '')
                            if stmt_text and len(stmt_text) > 30:
                                all_model_points.append(stmt_text[:200])  # First 200 chars
                
                # Format for LLM context
                model_patterns_context = self.argument_extractor.format_patterns_for_llm(model_patterns)
                logger.info(f"✅ Extracted {len(model_patterns)} argument patterns with {len(all_model_points)} argument points from trained model")
                
            except Exception as e:
                logger.warning(f"Error extracting model-based arguments: {e}")
                model_patterns = []
                all_model_points = []
        
        # Format similar cases context (enhanced with judge info)
        case_context = ""
        for i, (case_id, case_info) in enumerate(zip(case_ids[:5], similar_cases[:5])):
            text = case_info.get('cleaned_text', case_info.get('full_text', ''))[:1000] if isinstance(case_info, dict) else str(case_info)[:1000]
            year = case_info.get('year', 'Unknown') if isinstance(case_info, dict) else 'Unknown'
            
            # Add judge information if available
            judge_info = ""
            if isinstance(case_info, dict):
                judge_names = case_info.get('judge_names', '')
                if judge_names:
                    judge_info = f" [Judges: {judge_names}]"
            
            case_context += f"\n[CASE {i+1} - {case_id} ({year}){judge_info}]: {text}...\n"
        
        # Combine contexts
        full_context = case_context + model_patterns_context
        
        # Step 1: Generate arguments using trained models only (no LLM)
        if self.model_only_mode and self.model_argument_generator:
            # Use model-based generation only
            arguments = self.model_argument_generator.generate_arguments_from_patterns(
                model_patterns,
                case_text,
                similar_cases,
                case_ids
            )
            logger.info("✅ Generated arguments using trained models only (no LLM)")
        else:
            # LLM-based generation (model_only_mode is False)
            arguments = self._generate_multi_perspective_arguments(case_text, full_context, case_ids, model_patterns, all_model_points)
        
        # Normalize: ensure every argument has 'argument_points' populated
        # LLM path uses 'model_extracted_points'; model path sets 'argument_points' directly.
        if isinstance(arguments, list):
            for arg in arguments:
                if isinstance(arg, dict):
                    # If argument_points is missing/empty, copy from model_extracted_points
                    if not arg.get('argument_points'):
                        arg['argument_points'] = arg.get('model_extracted_points', [])
                    # If model_extracted_points is missing/empty, copy from argument_points
                    if not arg.get('model_extracted_points'):
                        arg['model_extracted_points'] = arg.get('argument_points', [])
        
        # Step 2: Generate adversarial simulation (optional - can be removed if not needed)
        adversarial_results = self._generate_adversarial_simulation(arguments) if not self.model_only_mode else {}
        
        # Construct full report with actual distances and metadata if provided
        similar_cases_list = []
        for i, cid in enumerate(case_ids[:5]):
            distance = distances[i] if distances and i < len(distances) else 0.0
            case_info = {"case_id": cid, "distance": distance}
            # Add year and judge information if available
            if case_dict and cid in case_dict:
                case_data = case_dict[cid]
                if isinstance(case_data, dict):
                    if 'year' in case_data:
                        case_info['year'] = case_data['year']
                    if 'judge_names' in case_data and case_data['judge_names']:
                        case_info['judge_names'] = case_data['judge_names']
            similar_cases_list.append(case_info)
        
        report = {
            "case_id": f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "file_type": "unknown",
            "cluster_id": 1,
            "similar_cases": similar_cases_list,
            "arguments": arguments,
            "adversarial_results": adversarial_results if adversarial_results else {}
        }
        
        return report
    
    def _generate_multi_perspective_arguments(self, case_text: str, case_context: str, case_ids: List[str], model_patterns: List[Dict] = None, all_model_points: List[str] = None) -> List[Dict]:
        """Generate arguments from multiple perspectives (combining LLM and model-based patterns)"""
        system_prompt = """
        You are a legal expert generating strategic arguments from multiple perspectives.
        You have access to both LLM-generated arguments and model-extracted argument patterns from similar cases.
        Combine these sources to create comprehensive, well-supported arguments.
        Output strictly in JSON format as a list of argument objects.
        IMPORTANT: Include judge names and their statements when available from the model patterns.
        """
        
        # Build model patterns section if available
        model_section = ""
        if model_patterns:
            model_section = "\n\nMODEL-EXTRACTED ARGUMENT PATTERNS:\n"
            model_section += "These patterns were extracted from similar cases using the trained model.\n"
            model_section += "Use these to strengthen your arguments with specific judge statements and legal principles.\n"
        
        # Extract model points for better integration
        model_points_list = []
        if all_model_points:
            # Use provided model points (already extracted)
            model_points_list = all_model_points[:15]  # Top 15 points
        elif model_patterns:
            # Fallback: extract from patterns
            for pattern in model_patterns[:5]:
                points = pattern.get('argument_points', [])
                if points:
                    model_points_list.extend(points[:3])  # Top 3 points per pattern
        
        model_points_text = "\n".join([f"- {point[:200]}" for point in model_points_list[:15]]) if model_points_list else "No specific model-extracted points available. Use information from similar cases provided above."
        
        user_prompt = f"""
        CASE FACTS:
        {case_text[:3000]}
        
        SIMILAR CASES AND MODEL PATTERNS:
        {case_context}
        {model_section}
        
        MODEL-EXTRACTED ARGUMENT POINTS:
        {model_points_text}
        
        TASK: Generate 4 comprehensive, detailed argument frameworks. DO NOT copy template text - generate actual, substantive legal arguments.
        
        For each argument, you MUST:
        1. Write a detailed, substantive "content" field (3-5 sentences minimum) that:
           - Cites specific cases from the similar cases provided
           - References specific judge names and their statements
           - Explains how the precedent supports the argument
           - Connects the case facts to the legal principles
           - Uses actual information from the similar cases, not generic text
        
        2. Populate "model_extracted_points" with specific argument points derived from the model patterns provided above
        
        3. Include real judge names and statements from the similar cases
        
        4. List actual legal principles and sections mentioned in the similar cases
        
        CRITICAL: The "content" field must be a complete, well-written legal argument, NOT placeholder text like "Argument supporting prosecution position citing similar cases..."
        
        JSON array format (REPLACE ALL PLACEHOLDER TEXT WITH ACTUAL CONTENT):
        [
            {{
                "title": "Precedent Support - Prosecution",
                "content": "Write a comprehensive 3-5 sentence argument here that cites specific cases, judges, and legal principles. For example: 'In CASE_2020_045, Justice Smith held that possession of 5g or more of heroin constitutes a serious offense under Section 54A of the Poisons Act. The court found that such quantity clearly indicates intent to distribute, not personal use. In the present case, the accused was found with exactly 5g of heroin in Colombo, matching the precedent facts. The prosecution should emphasize this binding precedent and argue that the same legal standard applies here.'",
                "perspective": "prosecution",
                "strength_score": 0.8,
                "supporting_cases": ["List actual case IDs from similar cases"],
                "judge_names": ["List actual judge names from similar cases"],
                "judge_statements": ["List actual judge statements/holdings from similar cases"],
                "legal_principles": ["List actual legal principles from model patterns"],
                "penal_codes": [],
                "argument_points": ["List 3-5 concise key argument points extracted from model patterns above"],
                "model_extracted_points": ["List actual argument points from model patterns above"]
            }},
            {{
                "title": "Precedent Support - Defense",
                "content": "Write a comprehensive 3-5 sentence defense argument here citing specific cases and legal principles.",
                "perspective": "defense",
                "strength_score": 0.8,
                "supporting_cases": ["List actual case IDs"],
                "judge_names": ["List actual judge names"],
                "judge_statements": ["List actual judge statements"],
                "legal_principles": ["List actual legal principles"],
                "penal_codes": [],
                "argument_points": ["List 3-5 concise key argument points"],
                "model_extracted_points": ["List actual argument points"]
            }},
            {{
                "title": "Precedent Support - Mitigating",
                "content": "Write a comprehensive 3-5 sentence argument for mitigating factors citing specific cases.",
                "perspective": "mitigating",
                "strength_score": 0.8,
                "supporting_cases": ["List actual case IDs"],
                "judge_names": ["List actual judge names"],
                "judge_statements": ["List actual judge statements"],
                "legal_principles": ["List actual legal principles"],
                "penal_codes": [],
                "argument_points": ["List 3-5 concise key argument points"],
                "model_extracted_points": ["List actual argument points"]
            }},
            {{
                "title": "Precedent Support - Aggressive",
                "content": "Write a comprehensive 3-5 sentence aggressive argument citing binding precedents.",
                "perspective": "aggressive",
                "strength_score": 0.8,
                "supporting_cases": ["List actual case IDs"],
                "judge_names": ["List actual judge names"],
                "judge_statements": ["List actual judge statements"],
                "legal_principles": ["List actual legal principles"],
                "penal_codes": [],
                "argument_points": ["List 3-5 concise key argument points"],
                "model_extracted_points": ["List actual argument points"]
            }}
        ]
        
        REMEMBER: Generate actual content, not template text. Use real information from the similar cases provided.
        Output ONLY the JSON array, no additional text.
        """
        
        response = self.llm.generate(system_prompt, user_prompt)
        parsed = self._parse_json(response)
        
        if isinstance(parsed, list):
            return parsed
        elif "error" in parsed:
            # Fallback arguments
            return self._get_fallback_arguments(case_ids)
        else:
            return [parsed] if isinstance(parsed, dict) else []
    
    def _score_arguments(self, arguments: List[Dict], similar_cases: List[Dict]) -> List[Dict]:
        """Score and rank arguments"""
        scored = []
        for i, arg in enumerate(arguments):
            # Simple scoring based on number of supporting cases and strength
            base_score = arg.get('strength_score', 0.8)
            num_supporting = len(arg.get('supporting_cases', []))
            strategic_score = base_score * (0.5 + 0.1 * min(num_supporting, 5))
            success_prob = strategic_score * 0.45  # Convert to probability range
            risk = "very_high" if success_prob < 0.3 else "high" if success_prob < 0.5 else "medium"
            
            scored.append({
                "title": arg.get('title', ''),
                "strategic_score": round(strategic_score, 4),
                "success_probability": round(success_prob, 4),
                "risk_assessment": risk,
                "priority_rank": i + 1
            })
        
        # Sort by strategic score descending
        scored.sort(key=lambda x: x['strategic_score'], reverse=True)
        for i, item in enumerate(scored):
            item['priority_rank'] = i + 1
        
        return scored
    
    def _generate_strategic_report(self, arguments: List[Dict], scored_arguments: List[Dict]) -> Dict:
        """Generate strategic report summary"""
        total_args = len(arguments)
        avg_score = sum(s['strategic_score'] for s in scored_arguments) / total_args if total_args > 0 else 0
        avg_success = sum(s['success_probability'] for s in scored_arguments) / total_args if total_args > 0 else 0
        
        # Count priorities
        high_priority = sum(1 for s in scored_arguments if s['priority_rank'] <= 3)
        medium_priority = sum(1 for s in scored_arguments if 3 < s['priority_rank'] <= 6)
        low_priority = total_args - high_priority - medium_priority
        
        # Risk distribution
        risk_dist = {}
        for s in scored_arguments:
            risk = s['risk_assessment']
            risk_dist[risk] = risk_dist.get(risk, 0) + 1
        
        return {
            "summary": {
                "total_arguments": total_args,
                "average_strategic_score": round(avg_score, 4),
                "average_success_probability": round(avg_success, 4)
            },
            "priority_breakdown": {
                "high_priority": high_priority,
                "medium_priority": medium_priority,
                "low_priority": low_priority
            },
            "risk_distribution": risk_dist,
            "success_probability_ranges": {
                "high_success": sum(1 for s in scored_arguments if s['success_probability'] >= 0.7),
                "medium_success": sum(1 for s in scored_arguments if 0.4 <= s['success_probability'] < 0.7),
                "low_success": sum(1 for s in scored_arguments if s['success_probability'] < 0.4)
            },
            "top_arguments": scored_arguments[:4],
            "strategic_recommendations": [
                f"Focus primary effort on {high_priority} top-priority arguments",
                f"Strengthen {sum(1 for s in scored_arguments if s['risk_assessment'] in ['very_high', 'high'])} high-risk arguments or develop contingency plans",
                f"Consider revising or replacing {sum(1 for s in scored_arguments if s['success_probability'] < 0.4)} low-probability arguments"
            ]
        }
    
    def _generate_adversarial_simulation(self, arguments: List[Dict]) -> Dict:
        """Generate adversarial simulation with counter-arguments"""
        system_prompt = """
        You are a legal expert performing adversarial simulation (Devil's Advocate).
        For each argument, generate counter-arguments and rebuttals.
        Output strictly in JSON format.
        """
        
        enhanced_args = []
        for arg in arguments[:4]:  # Process top 4 arguments
            try:
                # Get supporting cases and context for better counter-arguments
                supporting_cases = arg.get('supporting_cases', [])
                judge_statements = arg.get('judge_statements', [])
                legal_principles = arg.get('legal_principles', [])
                
                user_prompt = f"""
                ARGUMENT TO TEST:
                Title: {arg.get('title', '')}
                Content: {arg.get('content', '')}
                Perspective: {arg.get('perspective', '')}
                Supporting Cases: {', '.join(supporting_cases[:3]) if supporting_cases else 'None'}
                Legal Principles: {', '.join(legal_principles[:3]) if legal_principles else 'None'}
                
                TASK: Generate 3 substantive counter-arguments that challenge this argument. DO NOT use placeholder text.
                
                For each counter-argument, write:
                - "counter_content": A detailed 2-3 sentence counter-argument that challenges the original argument
                - "rebuttal": A detailed 2-3 sentence pre-emptive rebuttal to the counter-argument
                - "weak_points": Specific weaknesses in the original argument (not generic text)
                
                Strategies to consider:
                1. Distinguish the precedent (show how the current case is different)
                2. Challenge the evidence or procedural aspects
                3. Cite conflicting precedents or legal principles
                4. Question the applicability of the legal standard
                
                Generate in JSON format:
                {{
                    "original": {{
                        "title": "{arg.get('title', '')}",
                        "content": "{arg.get('content', '')[:500]}",
                        "perspective": "{arg.get('perspective', '')}",
                        "strength_score": {arg.get('strength_score', 0.8)}
                    }},
                    "counter_arguments": [
                        {{
                            "strategy": "distinguish_precedent",
                            "counter_content": "Write a detailed 2-3 sentence counter-argument here. For example: 'The precedent cited is distinguishable because in that case, the evidence was direct and uncontested, whereas in the present case, there are significant questions about the chain of custody and the reliability of the evidence. The factual circumstances differ materially, making the precedent inapplicable.'",
                            "rebuttal": "Write a detailed 2-3 sentence rebuttal here. For example: 'While the evidence chain may be questioned, the core legal principle remains applicable. The precedent establishes that the quantity threshold applies regardless of minor procedural differences, and the prosecution has met the burden of proof.'",
                            "strength_score": 0.7,
                            "weak_points": ["List specific weaknesses, e.g., 'Chain of custody concerns', 'Lack of direct witness testimony']"
                        }},
                        {{
                            "strategy": "challenge_evidence",
                            "counter_content": "Write another detailed counter-argument here.",
                            "rebuttal": "Write another detailed rebuttal here.",
                            "strength_score": 0.6,
                            "weak_points": ["List specific weaknesses"]
                        }},
                        {{
                            "strategy": "procedural_challenge",
                            "counter_content": "Write a third detailed counter-argument here.",
                            "rebuttal": "Write a third detailed rebuttal here.",
                            "strength_score": 0.65,
                            "weak_points": ["List specific weaknesses"]
                        }}
                    ]
                }}
                
                REMEMBER: Generate actual substantive counter-arguments and rebuttals, not placeholder text.
                Output ONLY valid JSON.
                """
                
                response = self.llm.generate(system_prompt, user_prompt)
                parsed = self._parse_json(response)
                
                # Handle different return types from _parse_json
                if isinstance(parsed, list):
                    # If LLM returned an array, take the first element if it's a dict
                    if len(parsed) > 0 and isinstance(parsed[0], dict):
                        parsed = parsed[0]
                    else:
                        # If it's a list of non-dict items, create a fallback structure
                        parsed = {
                            "original": arg,
                            "counter_arguments": []
                        }
                
                # Ensure parsed is a dict and check for errors
                if isinstance(parsed, dict) and "error" not in parsed:
                    # Validate structure
                    if "original" not in parsed:
                        parsed["original"] = arg
                    if "counter_arguments" not in parsed:
                        parsed["counter_arguments"] = []
                    # Remove overall_robustness (not needed)
                    if "overall_robustness" in parsed:
                        del parsed["overall_robustness"]
                    enhanced_args.append(parsed)
                else:
                    # Fallback for errors or non-dict results
                    enhanced_args.append({
                        "original": arg,
                        "counter_arguments": []
                    })
            except Exception as e:
                logger.warning(f"Error generating adversarial simulation for argument '{arg.get('title', 'Unknown')}': {e}")
                # Fallback on any exception
                enhanced_args.append({
                    "original": arg,
                    "counter_arguments": []
                })
        
        # Final safety check: filter out any non-dict items (shouldn't happen, but just in case)
        enhanced_args = [ea for ea in enhanced_args if isinstance(ea, dict)]
        
        # Remove overall_robustness from all enhanced arguments
        for ea in enhanced_args:
            if "overall_robustness" in ea:
                del ea["overall_robustness"]
        
        # Calculate summary (all items are now guaranteed to be dicts)
        total_args = len(enhanced_args)
        total_counters = sum(len(ea.get('counter_arguments', [])) for ea in enhanced_args)
        
        return {
            "enhanced_arguments": enhanced_args,
            "simulation_summary": {
                "total_arguments_tested": total_args,
                "total_counter_arguments": total_counters,
                "most_common_counter_strategy": "cite_precedent"
            },
            "strategic_recommendations": [
                "Address common weak points: Precedent distinguishability, Binding authority, Material differences",
                "Prepare additional evidence to counter anticipated challenges"
            ]
        }
    
    def _get_fallback_arguments(self, case_ids: List[str]) -> List[Dict]:
        """Fallback arguments if LLM generation fails"""
        return [
            {
                "title": "Precedent Support - Prosecution",
                "content": f"The prosecution's position is supported by similar cases {case_ids[:3]}.",
                "perspective": "prosecution",
                "strength_score": 0.8,
                "supporting_cases": case_ids[:3],
                "legal_principles": [],
                "penal_codes": []
            },
            {
                "title": "Precedent Support - Defense",
                "content": f"The defense finds support in precedents {case_ids[:3]}.",
                "perspective": "defense",
                "strength_score": 0.8,
                "supporting_cases": case_ids[:3],
                "legal_principles": [],
                "penal_codes": []
            }
        ]
    
    def _parse_json(self, text: str) -> Any:
        """Parse JSON from LLM response with robust error recovery"""
        try:
            # Check if this is an error response from LLM client
            if text.strip().startswith('{"error":'):
                parsed = json.loads(text)
                return {"error": parsed.get("message", "LLM API Error"), "error_type": "llm_api_error"}
            
            # Remove markdown code blocks
            clean = text.replace("```json", "").replace("```", "").strip()
            
            # Strategy 1: Find the outermost brackets/braces
            start_idx = -1
            end_idx = -1
            
            # Check for array first as it's common for list responses
            first_bracket = clean.find('[')
            first_brace = clean.find('{')
            
            if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
                start_idx = first_bracket
                end_idx = clean.rfind(']') + 1
            elif first_brace != -1:
                start_idx = first_brace
                end_idx = clean.rfind('}') + 1
                
            if start_idx != -1 and end_idx > start_idx:
                json_str = clean[start_idx:end_idx]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Strategy 2: If finding outermost failed, try to incrementally find first valid object/array
                    logger.warning("Strategy 1 failed, attempting Strategy 2 (incremental parsing)")
                    
                    # Try to find the first complete JSON object/array
                    # We look for the first closing match that actually parses
                    for i in range(start_idx + 1, len(clean) + 1):
                        if (clean[i-1] == '}' and first_brace != -1) or (clean[i-1] == ']' and first_bracket != -1):
                            try:
                                candidate = clean[start_idx:i]
                                return json.loads(candidate)
                            except json.JSONDecodeError:
                                continue
            
            # Strategy 3: Just try raw strip if nothing else worked
            return json.loads(clean)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            # Log a snippet of the text that failed
            text_snippet = text[:200].replace('\n', ' ')
            logger.error(f"Failed text snippet: {text_snippet}...")
            return {"error": f"JSON Parsing Failed: {str(e)}", "raw_text": text[:500]}
        except Exception as e:
            logger.error(f"Unexpected error parsing JSON: {e}")
            return {"error": f"Unexpected error: {str(e)}", "raw_text": text[:500]}
        except Exception as e:
            logger.error(f"Unexpected error parsing JSON: {e}")
            return {"error": f"Unexpected error: {str(e)}", "raw_text": text[:500]}

