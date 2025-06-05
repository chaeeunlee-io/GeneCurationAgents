import sys
import re
from typing import List, Dict, Any

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

def main():
    """Main entry point"""
    # Sample text about SCN1A and Dravet syndrome
    sample_text = """
    SCN1A mutations are the main cause of Dravet syndrome, an epileptic encephalopathy 
    characterized by refractory seizures, cognitive impairment, and increased mortality. 
    The p.Thr1174Ser variant in SCN1A was found in multiple affected patients. 
    GABA-ergic interneurons show reduced sodium currents in mouse models.
    """
    
    # Use command line argument if provided
    if len(sys.argv) > 1:
        sample_text = " ".join(sys.argv[1:])
    
    extractor = SimpleEntityExtractor()
    entities = extractor.extract_entities(sample_text)
    
    print("Extracted entities:")
    for entity in entities:
        print(f"- {entity['text']} ({entity['type']})")
        print(f"  Position: {entity['start']}-{entity['end']}")
        print(f"  Confidence: {entity['confidence']:.2f}")
        print()

if __name__ == "__main__":
    main()