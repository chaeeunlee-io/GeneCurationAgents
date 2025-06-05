from typing import List, Dict, Any, Union
import numpy as np
from sentence_transformers import SentenceTransformer

class EmbeddingModel:
    """Model for generating text embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model
        
        Args:
            model_name: Name of the sentence-transformers model to use
        """
        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.model_name = model_name
        except Exception as e:
            print(f"Error loading embedding model: {str(e)}")
            # Fallback to simple averaging of word vectors
            import spacy
            self.model = spacy.load("en_core_web_md")
            self.embedding_dim = 300
            self.model_name = "spacy-en_core_web_md"
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            Array of embeddings with shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])
        
        try:
            if hasattr(self.model, 'encode'):
                # SentenceTransformer model
                embeddings = self.model.encode(texts, convert_to_numpy=True)
                return embeddings
            else:
                # spaCy fallback
                embeddings = np.zeros((len(texts), self.embedding_dim))
                for i, text in enumerate(texts):
                    doc = self.model(text)
                    if doc.vector.any():  # Check if vector exists
                        embeddings[i] = doc.vector
                return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            # Return zero vectors as fallback
            return np.zeros((len(texts), self.embedding_dim))
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text
        
        Args:
            text: Text string to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.embed_texts([text])
        return embeddings[0] if len(embeddings) > 0 else np.zeros(self.embedding_dim)
    
    def embed_documents(self, documents: List[Dict]) -> Dict[str, np.ndarray]:
        """
        Generate embeddings for a list of documents
        
        Args:
            documents: List of document dictionaries with 'id' and 'text' keys
            
        Returns:
            Dictionary mapping document IDs to embeddings
        """
        texts = [doc["text"] for doc in documents]
        ids = [doc["id"] for doc in documents]
        
        embeddings = self.embed_texts(texts)
        
        return {doc_id: embedding for doc_id, embedding in zip(ids, embeddings)}
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
