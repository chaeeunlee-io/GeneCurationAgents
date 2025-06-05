import httpx
import asyncio
from typing import List, Dict, Any
import re
from datetime import datetime

class PubMedManager:
    """Manages interactions with PubMed API"""
    
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def search_papers(self, gene: str, disease: str, max_results: int = 30) -> List[str]:
        """Search PubMed for papers about a gene-disease relationship"""

        query = f"{gene}[Title/Abstract] AND {disease}[Title/Abstract]"
        

        url = f"{self.base_url}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "sort": "relevance"
        }
        
        try:

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])
            
            return pmids
        except Exception as e:
            print(f"Error searching PubMed: {e}")
            return []
    
    async def fetch_abstracts(self, pmids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch abstracts for a list of PMIDs"""
        if not pmids:
            return {}
        
        url = f"{self.base_url}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract"
        }
        
        try:

            response = await self.client.get(url, params=params)
            response.raise_for_status()
    
            xml_data = response.text
            
            abstracts = {}
            for pmid in pmids:
                # Find abstract text
                abstract_match = re.search(
                    f'<PubmedArticle>.*?<PMID.*?>{pmid}</PMID>.*?<AbstractText>(.*?)</AbstractText>',
                    xml_data, re.DOTALL
                )
                
                # Find title
                title_match = re.search(
                    f'<PubmedArticle>.*?<PMID.*?>{pmid}</PMID>.*?<ArticleTitle>(.*?)</ArticleTitle>',
                    xml_data, re.DOTALL
                )
                
                # Find year
                year_match = re.search(
                    f'<PubmedArticle>.*?<PMID.*?>{pmid}</PMID>.*?<PubDate>.*?<Year>(\\d+)</Year>',
                    xml_data, re.DOTALL
                )
                
                # Find first author
                author_match = re.search(
                    f'<PubmedArticle>.*?<PMID.*?>{pmid}</PMID>.*?<Author.*?>.*?<LastName>(.*?)</LastName>',
                    xml_data, re.DOTALL
                )
                
                if abstract_match:
                    abstract_text = abstract_match.group(1)
                    title = title_match.group(1) if title_match else "Unknown Title"
                    year = int(year_match.group(1)) if year_match else None
                    first_author = author_match.group(1) if author_match else "Unknown"
                    
                    abstracts[pmid] = {
                        "pmid": pmid,
                        "title": title,
                        "abstract": abstract_text,
                        "year": year,
                        "first_author": first_author
                    }
            # import pdb; pdb.set_trace()
            return abstracts
        except Exception as e:
            print(f"Error fetching abstracts: {e}")
            return {}
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
