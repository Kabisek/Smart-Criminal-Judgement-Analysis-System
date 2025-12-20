"""
CSV Storage Module
Handles saving extracted information to CSV files
"""

import csv
import os
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class CSVStorage:
    """Class to handle CSV file creation and data storage"""
    
    # Default columns for criminal judgment data
    # Default columns for criminal judgment data
    DEFAULT_COLUMNS = [
        'timestamp',
        'filename',
        
        # CASE IDENTIFICATION
        'source_file_name',
        'court_of_appeal_case_no',
        'high_court_case_no',
        'high_court_location',
        
        # DATES
        'judgment_date_coa',
        'judgment_date_hc',
        'date_of_offence',
        
        # PARTIES
        'judges',
        
        # OFFENCE DETAILS
        'offence_sections',
        'offence_category',
        'location_of_offence',
        
        # CASE TYPE
        'language_of_criminal',
        
        # FACTS & EVIDENCE
        'brief_facts_summary',
        'evidence_type_primary',
        'evidence_type_secondary',
        
        # HIGH COURT DECISION
        'hc_offence_of_conviction_sections',
        'hc_sentence_type',
        'hc_fine_amount',
        'hc_compensation_amount',
        'hc_judgment_summary',
        
        # GROUNDS OF APPEAL
        'grounds_of_appeal_raw_text_summary',
        'grounds_of_appeal_structured_notes',
        'gnd_contradictions',
        'gnd_chain_of_custody',
        'gnd_illegal_search_or_raid',
        'gnd_wrong_identification',
        'gnd_dying_declaration_validity',
        'gnd_circumstantial_insufficient',
        'gnd_medical_inconsistency',
        'gnd_misdirection_on_law',
        'gnd_procedural_error',
        'gnd_new_evidence',
        'gnd_sentence_excessive_or_inadequate',
        'gnd_delay_prejudice',
        'gnd_judicial_bias_or_unfair_trial',
        'gnd_other',
        'gnd_other_description',
        
        # WITNESS & EVIDENCE ANALYSIS
        'witness_evidence_analysis_summary',
        'num_prosecution_witnesses',
        'num_defence_witnesses',
        'eyewitness_present',
        'child_witness_present',
        'expert_evidence_present',
        'medical_evidence_strength',
        'forensic_evidence_present',
        'chain_of_custody_quality',
        'dying_declaration_present',
        'dying_declaration_reliability',
        'confession_present',
        'circumstantial_case',
        'probability_assessment_by_court',
        
        # DEFENCE
        'defence_version_summary',
        
        # LEGAL ANALYSIS
        'legal_errors_identified',
        'legal_errors_description',
        'procedural_defects_present',
        'procedural_defects_description',
        'directions_on_burden_of_proof_correct',
        
        # COURT OF APPEAL ANALYSIS
        'court_of_appeal_analysis_summary',
        
        # FINAL OUTCOME
        'coa_final_outcome_class',
        'coa_conviction_status',
        'coa_sentence_type',
        'coa_fine_amount',
        'coa_compensation_amount',
        
        # TEXT
        'full_text_judgment'
    ]

    
    def __init__(self, output_folder: str = './output'):
        """
        Initialize CSV Storage
        
        Args:
            output_folder: Path where CSV files will be saved
        """
        self.output_folder = output_folder
        os.makedirs(output_folder, exist_ok=True)
    
    def create_csv_file(self, filename: str, columns: List[str] = None) -> Tuple[bool, str]:
        """
        Create a new CSV file with headers
        
        Args:
            filename: Name of the CSV file (without .csv extension)
            columns: List of column headers (uses defaults if None)
            
        Returns:
            Tuple of (success, file_path)
        """
        try:
            if columns is None:
                columns = self.DEFAULT_COLUMNS
            
            file_path = os.path.join(self.output_folder, f"{filename}.csv")
            
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns)
                writer.writeheader()
            
            return True, file_path
        
        except Exception as e:
            return False, str(e)
    
    def save_data(self, csv_path: str, data: Dict, filename: str = None) -> Tuple[bool, str]:
        """
        Save extracted data to CSV file
        
        Args:
            csv_path: Path to the CSV file
            data: Dictionary containing extracted information
            filename: Original PDF filename
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Add timestamp and filename to data
            row_data = {
                'timestamp': datetime.now().isoformat(),
                'filename': filename or 'unknown'
            }
            
            # Add all fields from extracted data
            for key, value in data.items():
                if key in self.DEFAULT_COLUMNS:
                    row_data[key] = value
            
            # Ensure all columns exist in the row
            for col in self.DEFAULT_COLUMNS:
                if col not in row_data:
                    row_data[col] = ''
            
            # Append to CSV file
            file_exists = os.path.exists(csv_path)
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.DEFAULT_COLUMNS)
                writer.writerow(row_data)
            
            return True, "Data saved successfully"
        
        except Exception as e:
            return False, f"Error saving data: {str(e)}"
    
    def save_batch_data(self, csv_path: str, data_list: List[Dict], filename: str = None) -> Tuple[bool, str]:
        """
        Save multiple extracted records to CSV file
        
        Args:
            csv_path: Path to the CSV file
            data_list: List of dictionaries containing extracted information
            filename: Original PDF filename
            
        Returns:
            Tuple of (success, message)
        """
        try:
            file_exists = os.path.exists(csv_path)
            
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.DEFAULT_COLUMNS)
                
                if not file_exists:
                    writer.writeheader()
                
                for data in data_list:
                    row_data = {
                        'timestamp': datetime.now().isoformat(),
                        'filename': filename or 'unknown'
                    }
                    
                    for key, value in data.items():
                        if key in self.DEFAULT_COLUMNS:
                            row_data[key] = value
                    
                    for col in self.DEFAULT_COLUMNS:
                        if col not in row_data:
                            row_data[col] = ''
                    
                    writer.writerow(row_data)
            
            return True, f"Batch data saved successfully ({len(data_list)} records)"
        
        except Exception as e:
            return False, f"Error saving batch data: {str(e)}"
    
    def get_csv_list(self) -> List[str]:
        """
        Get list of all CSV files in output folder
        
        Returns:
            List of CSV file names
        """
        csv_files = []
        try:
            for file in os.listdir(self.output_folder):
                if file.endswith('.csv'):
                    csv_files.append(file)
        except:
            pass
        
        return sorted(csv_files)
    
    def get_csv_stats(self, csv_path: str) -> Dict:
        """
        Get statistics about a CSV file
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            Dictionary with statistics
        """
        try:
            stats = {
                'file_exists': os.path.exists(csv_path),
                'file_size_kb': 0,
                'row_count': 0
            }
            
            if stats['file_exists']:
                stats['file_size_kb'] = round(os.path.getsize(csv_path) / 1024, 2)
                
                with open(csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    stats['row_count'] = sum(1 for _ in reader)
            
            return stats
        
        except Exception as e:
            return {'error': str(e)}
