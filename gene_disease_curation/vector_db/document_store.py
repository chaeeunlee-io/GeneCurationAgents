from typing import List, Dict, Any, Optional, Union
import os
import json
import numpy as np
import faiss
from .embeddings import EmbeddingModel

class VectorDocumentStore:
    """Vector database for document storage and retrieval"""
    
    def __init__(
        self, 
        embedding_model: Optional[EmbeddingModel] = None,
        index_path: Optional[str] = None,
        dimension: int = 768
    ):
        """
        Initialize the vector document store
        
        Args:
            embedding_model: Model for generating embeddings
            index_path: Path to load existing index
            dimension: Embedding dimension if no model or index provided
        """
        self.embedding_model = embedding_model
        
        # Initialize document storage
        self.documents = {}  # id -> document
        self.doc_ids = []    # List of document IDs in order
        
        # Initialize FAISS index
        if index_path and os.path.exists(index_path):
            self._load_index(index_path)
        else:
            if embedding_model:
                dimension = embedding_model.embedding_dim
            try:
                self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine) index
                self.dimension = dimension
            except Exception as e:
                print(f"Error initializing FAISS index: {str(e)}")
                # Create a dummy index for fallback
                self.index = None
                self.dimension = dimension
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add documents to the vector store
        
        Args:
            documents: List of document dictionaries with 'id', 'text', and optional 'metadata'
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Extract texts for embedding
        texts = [doc.get("text", "") for doc in documents]
        
        # Generate embeddings
        if self.embedding_model and self.index is not None:
            try:
                embeddings = self.embedding_model.embed_texts(texts)
                
                # Add to FAISS index
                if len(embeddings) > 0:
                    faiss.normalize_L2(embeddings)  # Normalize for cosine similarity
                    self.index.add(embeddings)
                
                # Store documents
                doc_ids = []
                for i, doc in enumerate(documents):
                    doc_id = doc.get("id", f"doc_{len(self.documents)}")
                    self.documents[doc_id] = {
                        "text": doc.get("text", ""),
                        "metadata": doc.get("metadata", {})
                    }
                    self.doc_ids.append(doc_id)
                    doc_ids.append(doc_id)
                
                return doc_ids
            except Exception as e:
                print(f"Error adding documents to vector store: {str(e)}")
        
        # Fallback: just store documents without embeddings
        doc_ids = []
        for doc in documents:
            doc_id = doc.get("id", f"doc_{len(self.documents)}")
            self.documents[doc_id] = {
                "text": doc.get("text", ""),
                "metadata": doc.get("metadata", {})
            }
            self.doc_ids.append(doc_id)
            doc_ids.append(doc_id)
        
        return doc_ids
    
    def search(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Query text
            k: Number of results to return
            filter_dict: Dictionary of metadata filters
            
        Returns:
            List of document dictionaries with similarity scores
        """
        if not self.embedding_model or self.index is None or self.index.ntotal == 0:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.embed_text(query)
            query_embedding = query_embedding.reshape(1, -1)
            faiss.normalize_L2(query_embedding)
            
            # Search index
            scores, indices = self.index.search(query_embedding, k=min(k * 4, self.index.ntotal))
            
            # Get document IDs
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.doc_ids):
                    doc_id = self.doc_ids[idx]
                    doc = self.documents.get(doc_id)
                    
                    if doc:
                        # Apply metadata filter
                        if filter_dict and not self._matches_filter(doc.get("metadata", {}), filter_dict):
                            continue
                        
                        results.append({
                            "id": doc_id,
                            "text": doc.get("text", ""),
                            "metadata": doc.get("metadata", {}),
                            "score": float(scores[0][i])
                        })
            
            # Sort by score and limit to k
            results = sorted(results, key=lambda x: x["score"], reverse=True)[:k]
            return results
        except Exception as e:
            print(f"Error searching vector store: {str(e)}")
            return []
    
    def _matches_filter(self, metadata: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        """Check if metadata matches filter criteria"""
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def _load_index(self, index_path: str) -> None:
        """Load FAISS index from file"""
        try:
            self.index = faiss.read_index(index_path)
            self.dimension = self.index.d
            
            # Load documents
            docs_path = index_path + ".docs.json"
            if os.path.exists(docs_path):
                with open(docs_path, "r") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", {})
                    self.doc_ids = data.get("doc_ids", [])
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            self.index = faiss.IndexFlatIP(self.dimension)
    
    def save_index(self, index_path: str) -> None:
        """Save FAISS index to file"""
        if self.index is not None:
            try:
                faiss.write_index(self.index, index_path)
                
                # Save documents
                docs_path = index_path + ".docs.json"
                with open(docs_path, "w") as f:
                    json.dump({
                        "documents": self.documents,
                        "doc_ids": self.doc_ids
                    }, f)
            except Exception as e:
                print(f"Error saving index: {str(e)}")
