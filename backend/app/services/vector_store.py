from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import openai
import logging
from sqlalchemy.orm import Session
from ..models.database import Product, AITrainingData
import json

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, openai_api_key: str, persist_directory: str = "chromadb"):
        self.openai_client = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="audico_products",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_products_to_vector_store(self, products: List[Product], db: Session) -> Dict[str, Any]:
        """Add products to vector database"""
        try:
            if not self.openai_client:
                return {"success": False, "error": "OpenAI API key not configured"}
            
            documents = []
            metadatas = []
            ids = []
            
            for product in products:
                # Create document text
                doc_text = f"""
                Brand: {product.brand}
                Product: {product.product_name}
                Stock Code: {product.stock_code}
                Category: {product.category or 'General'}
                Price: R{product.price_excl_vat:.2f} (excl VAT)
                Description: {product.description or ''}
                Supplier: {product.supplier.name if product.supplier else 'Unknown'}
                """
                
                documents.append(doc_text)
                metadatas.append({
                    "product_id": product.id,
                    "brand": product.brand,
                    "stock_code": product.stock_code,
                    "price": product.price_excl_vat,
                    "category": product.category,
                    "supplier": product.supplier.name if product.supplier else None
                })
                ids.append(f"product_{product.id}")
            
            # Generate embeddings
            embeddings = self._generate_embeddings(documents)
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            # Save to training data table
            for i, doc in enumerate(documents):
                training_data = AITrainingData(
                    content=doc,
                    content_type="product",
                    vector_id=ids[i],
                    metadata=metadatas[i]
                )
                db.add(training_data)
            
            db.commit()
            
            return {
                "success": True,
                "products_added": len(products),
                "message": f"Successfully added {len(products)} products to vector store"
            }
            
        except Exception as e:
            logger.error(f"Vector store error: {e}")
            return {"success": False, "error": str(e)}
    
    def search_products(self, query: str, customer_group: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
        """Search products using vector similarity"""
        try:
            if not self.openai_client:
                return []
            
            # Generate query embedding
            query_embedding = self._generate_embeddings([query])[0]
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=['metadatas', 'documents', 'distances']
            )
            
            products = []
            
            for i, metadata in enumerate(results['metadatas'][0]):
                distance = results['distances'][0][i]
                
                # Apply customer group pricing
                base_price = metadata.get('price', 0)
                if customer_group == 8:
                    final_price = 15990.0  # Special Audico pricing
                elif customer_group == 7:
                    final_price = base_price * 0.9
                else:
                    final_price = base_price
                
                products.append({
                    "product_id": metadata.get('product_id'),
                    "brand": metadata.get('brand'),
                    "stock_code": metadata.get('stock_code'),
                    "price_excl_vat": final_price,
                    "price_incl_vat": final_price * 1.15,
                    "category": metadata.get('category'),
                    "supplier": metadata.get('supplier'),
                    "relevance_score": 1 - distance,  # Convert distance to similarity
                    "special_pricing": customer_group == 8 and final_price == 15990.0
                })
            
            return products
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                input=texts,
                model="text-embedding-3-small"
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return []
    
    def update_product_in_vector_store(self, product: Product, db: Session) -> bool:
        """Update a single product in vector store"""
        try:
            # Remove existing
            self.collection.delete(ids=[f"product_{product.id}"])
            
            # Add updated
            result = self.add_products_to_vector_store([product], db)
            return result.get("success", False)
            
        except Exception as e:
            logger.error(f"Vector update error: {e}")
            return False
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get vector store statistics"""
        try:
            collection_count = self.collection.count()
            return {
                "total_vectors": collection_count,
                "status": "active" if collection_count > 0 else "empty"
            }
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {"total_vectors": 0, "status": "error"}