import asyncio
import sys
import uuid
import os
import argparse
from datetime import datetime

from gene_disease_curation.config import setup_environment
from gene_disease_curation.graph.workflow import build_curation_graph
from gene_disease_curation.models.state import CurationState
from gene_disease_curation.utils.helpers import create_initial_state, print_results

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Run gene-disease curation workflow")
    parser.add_argument("gene", help="Gene symbol (e.g., BRCA1)")
    parser.add_argument("disease", help="Disease name (e.g., 'breast cancer')")
    parser.add_argument("--simple-ner", action="store_true", 
                        help="Use simple regex-based NER instead of ML models")
    return parser.parse_args()

async def run_curation(gene: str, disease: str, use_simple_ner=False):
    """Run the gene-disease curation workflow"""
    start_time = datetime.now()
    
    setup_environment()
    
    if use_simple_ner:
        os.environ["USE_SIMPLE_NER"] = "true"
        print("Using simple regex-based NER instead of ML models")
    

    initial_state = create_initial_state(gene, disease)
    workflow = build_curation_graph()
    
    # unique thread ID for this run
    thread_id = str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await workflow.ainvoke(
        initial_state,
        config
    )

    # try:
    #     # Fix the config parameter format
    #     config = {"configurable": {"thread_id": thread_id}}
    #     final_state = await workflow.ainvoke(
    #         initial_state,
    #         config
    #     )
    # except ValueError as e:
    #     if "Checkpointer requires" in str(e):
    #         # If error is about checkpointer but workflow doesn't need it,
    #         # try without config
    #         final_state = await workflow.ainvoke(initial_state)
    #     else:
    #         # Re-raise if it's a different error
    #         raise
    # except Exception as e:
    #     print(f"Error during workflow execution: {e}")
    #     # Try without any config as a last resort
    #     final_state = await workflow.ainvoke(initial_state)
    
    final_state["processing_time"] = (datetime.now() - start_time).total_seconds()
    
    return final_state

def main():

    args = parse_arguments()
    
    # python run_curation.py "BRCA1" "breast cancer"
    results = asyncio.run(run_curation(args.gene, args.disease, args.simple_ner))
    print_results(results)

if __name__ == "__main__":
    main()
