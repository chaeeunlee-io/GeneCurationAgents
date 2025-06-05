import httpx
import asyncio
from typing import List, Dict, Optional

class TMVarClient:
    """Client for the TMVar API for mutation extraction from text"""
    
    def __init__(self):
        self.base_url = "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/tmVar.cgi"
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def extract_mutations(self, text: str) -> List[Dict]:
        """
        Extract mutations from text using TMVar API
        
        Args:
            text: The text to analyze
            
        Returns:
            List of mutation dictionaries with keys:
            - mutation_id: TMVar ID
            - type: Mutation type (e.g., SNP, deletion)
            - text: Original text mention
            - normalized: Normalized mutation format
            - position: Character position in text
        """
        try:
            params = {
                "content": text[:5000],  # Limit text length
                "format": "json"
            }
            
            response = await self.client.get(self.base_url, params=params)
            data = response.json()
            
            mutations = []
            if "denotations" in data:
                for item in data["denotations"]:
                    mutation = {
                        "mutation_id": item.get("id", ""),
                        "type": item.get("obj", "mutation"),
                        "text": text[item["span"]["begin"]:item["span"]["end"]],
                        "normalized": "",  # TMVar doesn't always provide normalized form
                        "position": {
                            "start": item["span"]["begin"],
                            "end": item["span"]["end"]
                        }
                    }
                    mutations.append(mutation)
            
            return mutations
        except Exception as e:
            print(f"TMVar API error: {str(e)}")
            return []  # Return empty list on error
        
    async def batch_extract_mutations(self, texts: List[str]) -> List[List[Dict]]:
        """Extract mutations from multiple texts in parallel"""
        tasks = [self.extract_mutations(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append([])
            else:
                processed_results.append(result)
                
        return processed_results
