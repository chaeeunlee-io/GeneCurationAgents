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

from dotenv import load_dotenv
load_dotenv()




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
    # import pdb; pdb.set_trace()
    # png_bytes = workflow.get_graph().draw_mermaid_png()
    # with open("gene_disease_curation/assets/visualisation.png", "wb") as f:
    #     f.write(png_bytes)
    # import pdb; pdb.set_trace()
    
    # unique thread ID for this run
    thread_id = str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await workflow.ainvoke(
        initial_state,
        config
    )
    
    final_state["processing_time"] = (datetime.now() - start_time).total_seconds()
    
    return final_state

def main():

    args = parse_arguments()
    
    # python run_curation.py "BRCA1" "breast cancer"
    results = asyncio.run(run_curation(args.gene, args.disease, args.simple_ner))
    print_results(results)

if __name__ == "__main__":
    main()
