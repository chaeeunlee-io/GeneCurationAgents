from datetime import datetime
from typing import Dict
from ..models.state import CurationState

def print_results(results: CurationState):
    """Pretty print the curation results"""
    print(f"\n{'='*60}")
    print(f"Gene-Disease Analysis: {results['gene']} - {results['disease']}")
    print(f"{'='*60}")
    
    print(f"\nAbstracts Analyzed: {results['abstracts_analyzed']}")
    print(f"Evidence Items Found: {len(results['evidence_items'])}")
    
    if results['publication_years']:
        print(f"Publication Years: {results['publication_years'][0]} - {results['publication_years'][-1]}")
    
    print(f"\nEvidence Scores:")
    print(f"  Variant: {results['variant_score']:.2f}")
    print(f"  Functional: {results['functional_score']:.2f}")
    print(f"  Segregation: {results['segregation_score']:.2f}")
    print(f"  Cohort: {results['cohort_score']:.2f}")
    print(f"  TOTAL: {results['total_score']:.2f}")
    
    print(f"\nClassification: {results['classification_suggestion']}")
    print(f"Confidence: {results['confidence_level']:.2%}")
    
    print(f"\nProcessing Time: {results['processing_time']:.2f}s")

def create_initial_state(gene: str, disease: str) -> CurationState:
    """Create an initial state for the curation process"""
    return CurationState(
        gene=gene,
        disease=disease,
        pmids=[],
        abstracts={},
        evidence_items=[],
        variant_score=0.0,
        functional_score=0.0,
        segregation_score=0.0,
        cohort_score=0.0,
        total_score=0.0,
        publication_years=[],
        independent_groups=0,
        abstracts_analyzed=0,
        classification_suggestion="",
        confidence_level=0.0,
        current_stage="start",
        errors=[],
        processing_time=0.0,
        messages=[]
    )