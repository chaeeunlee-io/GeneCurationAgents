from typing import List, Dict, Any
import spacy
from transformers import pipeline
import re
import os

class SimpleEntityExtractor:
    """Simple entity extractor using regex patterns"""
    
    def __init__(self):
        """Initialize the extractor with regex patterns"""
        self.patterns = {
            "gene": [
                r'\b[A-Z][A-Z0-9]{1,5}\b',  # Gene symbols like BRCA1, TP53
                r'\b[A-Z][a-z]+\d+\b'       # Gene names like Sonic2
            ],
            "disease": [
                r'\b[A-Z][a-z]+ (syndrome|disease|disorder)\b',  # Named syndromes
                r'\b[a-z]+ (cancer|tumor)\b'                     # Cancers
            ],
            "mutation": [
                r'\bp\.[A-Z][a-z]{2}\d+[A-Z][a-z]{2}\b',  # p.Thr1174Ser format
                r'\b[A-Z]\d+[A-Z]\b',                     # T174S format
                r'\bc\.\d+[ACGT]>[ACGT]\b'                # c.123A>G format
            ],
            "chemical": [
                r'\b[A-Z][a-z]+in\b',       # Chemicals ending in -in
                r'\b[A-Z][a-z]+ide\b',      # Chemicals ending in -ide
                r'\b[A-Z][a-z]+ate\b'       # Chemicals ending in -ate
            ]
        }
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text using regex patterns"""
        entities = []
        
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    entities.append({
                        "text": match.group(0),
                        "start": match.start(),
                        "end": match.end(),
                        "type": entity_type,
                        "confidence": 0.8  # Fixed confidence
                    })
        
        # Sort by position
        entities.sort(key=lambda x: x["start"])
        
        return entities

class BiomedicalNER:
    """Named Entity Recognition for biomedical text"""
    
    def __init__(self, model_name="dmis-lab/biobert-base-cased-v1.1", use_simple=None):
        """Initialize the NER model"""
        # Check if USE_SIMPLE_NER environment variable is set
        if use_simple is None:
            use_simple = os.environ.get("USE_SIMPLE_NER", "").lower() in ("true", "1", "yes")
        
        self.use_simple = use_simple
        
        if self.use_simple:
            # Use the simple regex-based extractor
            self.simple_extractor = SimpleEntityExtractor()
            print("Using SimpleEntityExtractor for NER (regex-based)")
        else:
            try:
                # Try to load spaCy model first (faster)
                self.nlp = spacy.load("en_core_sci_md")
                self.use_spacy = True
                print("Using spaCy model for NER")
            except:
                # Fall back to transformers pipeline
                print(f"Loading transformer model {model_name} for NER...")
                self.ner = pipeline("ner", model=model_name)
                self.use_spacy = False
                print("Using transformers pipeline for NER")
        
        # Entity categories of interest
        self.categories = {
            "GENE": "gene",
            "DISEASE": "disease",
            "CHEMICAL": "chemical",
            "MUTATION": "mutation",
            "SPECIES": "species",
            "CELL_LINE": "cell_line",
            "CELL_TYPE": "cell_type"
        }
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract biomedical entities from text"""
        if self.use_simple:
            return self.simple_extractor.extract_entities(text)
        elif self.use_spacy:
            return self._extract_with_spacy(text)
        else:
            return self._extract_with_transformers(text)
    
    def _extract_with_spacy(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using spaCy"""
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in self.categories:
                entities.append({
                    "text": ent.text,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "type": self.categories.get(ent.label_, ent.label_),
                    "confidence": 1.0  # spaCy doesn't provide confidence scores
                })
        
        return entities
    
    def _extract_with_transformers(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using transformers pipeline"""
        # Split text into chunks to avoid token limit
        max_length = 512
        chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        all_entities = []
        offset = 0
        
        for chunk in chunks:
            results = self.ner(chunk)
            
            # Group by entity
            current_entity = None
            
            for item in results:
                # Adjust positions based on chunk offset
                item["start"] += offset
                item["end"] += offset
                
                # Map entity types
                entity_type = item["entity_group"]
                mapped_type = self.categories.get(entity_type, entity_type)
                
                all_entities.append({
                    "text": item["word"],
                    "start": item["start"],
                    "end": item["end"],
                    "type": mapped_type,
                    "confidence": item["score"]
                })
            
            offset += len(chunk)
        
        return all_entities
