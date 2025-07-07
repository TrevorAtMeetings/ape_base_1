"""
Vector Knowledge Index for APE Pumps AI Chatbot
Task 4.1.2: Metadata & Indexing Strategy Implementation
Lightweight vector database using OpenAI embeddings for document retrieval
"""

import os
import json
import sqlite3
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

from openai import OpenAI

logger = logging.getLogger(__name__)

@dataclass
class DocumentIndex:
    """Document index entry for vector database"""
    document_id: str
    filename: str
    document_type: str
    pump_model: Optional[str]
    pump_series: Optional[str]
    pump_type: Optional[str]
    keywords: List[str]
    summary: str
    specifications: Dict[str, Any]
    applications: List[str]
    embedding_vector: Optional[List[float]]
    relevance_score: float = 0.0
    last_updated: str = ""

class VectorKnowledgeIndex:
    """Intelligent indexing system for pump documentation using vector embeddings"""
    
    def __init__(self, db_path: str = "pump_knowledge_index.db"):
        """Initialize vector knowledge index with SQLite backend"""
        self.db_path = db_path
        self.openai_client = None
        self.embedding_dimension = 1536  # OpenAI ada-002 embedding dimension
        
        # Initialize OpenAI for embeddings
        try:
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info("OpenAI embeddings client initialized")
            else:
                logger.warning("OPENAI_API_KEY not available - using fallback indexing")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Create SQLite database schema for vector index"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Documents metadata table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_index (
                        document_id TEXT PRIMARY KEY,
                        filename TEXT NOT NULL,
                        document_type TEXT NOT NULL,
                        pump_model TEXT,
                        pump_series TEXT,
                        pump_type TEXT,
                        keywords TEXT,  -- JSON array
                        summary TEXT,
                        specifications TEXT,  -- JSON object
                        applications TEXT,  -- JSON array
                        embedding_vector TEXT,  -- JSON array of floats
                        relevance_score REAL DEFAULT 0.0,
                        last_updated TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Query analytics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_analytics (
                        query_id TEXT PRIMARY KEY,
                        query_text TEXT NOT NULL,
                        matched_documents TEXT,  -- JSON array
                        processing_time REAL,
                        relevance_scores TEXT,  -- JSON array
                        user_feedback INTEGER,  -- 1-5 rating
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        metric_id TEXT PRIMARY KEY,
                        total_documents INTEGER,
                        avg_query_time REAL,
                        accuracy_score REAL,
                        last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Vector knowledge index database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding vector for text using OpenAI"""
        if not self.openai_client:
            return None
        
        try:
            # Clean and prepare text
            clean_text = text.replace('\n', ' ').strip()
            if len(clean_text) > 8000:  # OpenAI embedding limit
                clean_text = clean_text[:8000]
            
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=clean_text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def create_searchable_text(self, doc_metadata: Dict[str, Any]) -> str:
        """Create comprehensive searchable text from document metadata"""
        text_parts = []
        
        # Add basic information
        if doc_metadata.get('pump_model'):
            text_parts.append(f"Pump model: {doc_metadata['pump_model']}")
        
        if doc_metadata.get('pump_series'):
            text_parts.append(f"Series: {doc_metadata['pump_series']}")
        
        if doc_metadata.get('pump_type'):
            text_parts.append(f"Type: {doc_metadata['pump_type']}")
        
        # Add specifications
        specs = doc_metadata.get('specifications', {})
        if specs:
            if specs.get('flow_range_m3hr'):
                flow_range = specs['flow_range_m3hr']
                text_parts.append(f"Flow range: {flow_range[0]} to {flow_range[1]} m³/hr")
            
            if specs.get('head_range_m'):
                head_range = specs['head_range_m']
                text_parts.append(f"Head range: {head_range[0]} to {head_range[1]} meters")
            
            if specs.get('power_range_kw'):
                power_range = specs['power_range_kw']
                text_parts.append(f"Power range: {power_range[0]} to {power_range[1]} kW")
            
            if specs.get('efficiency_range_pct'):
                eff_range = specs['efficiency_range_pct']
                text_parts.append(f"Efficiency range: {eff_range[0]} to {eff_range[1]} percent")
        
        # Add applications
        applications = doc_metadata.get('applications', [])
        if applications:
            text_parts.append(f"Applications: {', '.join(applications)}")
        
        # Add keywords
        keywords = doc_metadata.get('keywords', [])
        if keywords:
            text_parts.append(f"Keywords: {', '.join(keywords)}")
        
        # Add summary
        if doc_metadata.get('summary'):
            text_parts.append(f"Summary: {doc_metadata['summary']}")
        
        return ' '.join(text_parts)
    
    async def index_document(self, doc_metadata: Dict[str, Any]) -> DocumentIndex:
        """Add document to vector index with embeddings"""
        logger.info(f"Indexing document: {doc_metadata.get('filename', 'Unknown')}")
        
        try:
            # Create searchable text
            searchable_text = self.create_searchable_text(doc_metadata)
            
            # Generate embedding
            embedding = await self.generate_embedding(searchable_text)
            
            # Create document index entry
            doc_index = DocumentIndex(
                document_id=doc_metadata['document_id'],
                filename=doc_metadata['filename'],
                document_type=doc_metadata['document_type'],
                pump_model=doc_metadata.get('pump_model'),
                pump_series=doc_metadata.get('pump_series'),
                pump_type=doc_metadata.get('pump_type'),
                keywords=doc_metadata.get('keywords', []),
                summary=doc_metadata.get('summary', ''),
                specifications=doc_metadata.get('specifications', {}),
                applications=doc_metadata.get('applications', []),
                embedding_vector=embedding,
                last_updated=datetime.now().isoformat()
            )
            
            # Store in database
            await self._store_document_index(doc_index)
            
            logger.info(f"Successfully indexed: {doc_index.filename}")
            return doc_index
            
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            raise
    
    async def _store_document_index(self, doc_index: DocumentIndex):
        """Store document index in SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO document_index 
                    (document_id, filename, document_type, pump_model, pump_series, pump_type,
                     keywords, summary, specifications, applications, embedding_vector, 
                     relevance_score, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_index.document_id,
                    doc_index.filename,
                    doc_index.document_type,
                    doc_index.pump_model,
                    doc_index.pump_series,
                    doc_index.pump_type,
                    json.dumps(doc_index.keywords),
                    doc_index.summary,
                    json.dumps(doc_index.specifications),
                    json.dumps(doc_index.applications),
                    json.dumps(doc_index.embedding_vector) if doc_index.embedding_vector else None,
                    doc_index.relevance_score,
                    doc_index.last_updated
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing document index: {e}")
            raise
    
    async def search_documents(self, query: str, max_results: int = 5) -> List[DocumentIndex]:
        """Search for relevant documents using hybrid vector + keyword search"""
        logger.info(f"Searching for: {query}")
        start_time = datetime.now()
        
        try:
            # Generate query embedding
            query_embedding = await self.generate_embedding(query)
            
            # Get all indexed documents
            documents = await self._get_all_documents()
            
            if not documents:
                logger.warning("No indexed documents found")
                return []
            
            # Calculate relevance scores
            scored_documents = []
            query_lower = query.lower()
            
            for doc in documents:
                total_score = 0.0
                
                # Vector similarity score (if embeddings available)
                if query_embedding and doc.embedding_vector:
                    similarity = self._cosine_similarity(query_embedding, doc.embedding_vector)
                    total_score += similarity * 0.6  # 60% weight for semantic similarity
                
                # Keyword matching score
                keyword_score = self._calculate_keyword_score(query_lower, doc)
                total_score += keyword_score * 0.25  # 25% weight for keywords
                
                # Metadata matching score
                metadata_score = self._calculate_metadata_score(query_lower, doc)
                total_score += metadata_score * 0.15  # 15% weight for metadata
                
                doc.relevance_score = total_score
                scored_documents.append(doc)
            
            # Sort by relevance and return top results
            scored_documents.sort(key=lambda x: x.relevance_score, reverse=True)
            results = scored_documents[:max_results]
            
            # Log search analytics
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._log_search_analytics(query, results, processing_time)
            
            logger.info(f"Found {len(results)} relevant documents in {processing_time:.3f}s")
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            # Convert to numpy arrays
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            # Calculate cosine similarity
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
            
            similarity = dot_product / (norm_v1 * norm_v2)
            return max(0.0, similarity)  # Ensure non-negative
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _calculate_keyword_score(self, query: str, doc: DocumentIndex) -> float:
        """Calculate keyword matching score"""
        score = 0.0
        
        # Check pump model exact match
        if doc.pump_model and doc.pump_model.lower() in query:
            score += 0.5
        
        # Check keywords
        if doc.keywords:
            for keyword in doc.keywords:
                if keyword and keyword.lower() in query:
                    score += 0.1
        
        # Check applications
        if doc.applications:
            for app in doc.applications:
                if app and app.lower() in query:
                    score += 0.1
        
        # Check document type
        if doc.document_type.lower() in query:
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_metadata_score(self, query: str, doc: DocumentIndex) -> float:
        """Calculate metadata-based relevance score"""
        score = 0.0
        
        # Specification matching
        specs = doc.specifications
        
        # Flow rate matching
        if "flow" in query and specs.get('flow_range_m3hr'):
            score += 0.2
        
        # Head matching
        if "head" in query and specs.get('head_range_m'):
            score += 0.2
        
        # Power matching
        if "power" in query and specs.get('power_range_kw'):
            score += 0.2
        
        # Efficiency matching
        if "efficiency" in query and specs.get('efficiency_range_pct'):
            score += 0.2
        
        # NPSH matching
        if "npsh" in query:
            score += 0.2
        
        return min(score, 1.0)
    
    async def _get_all_documents(self) -> List[DocumentIndex]:
        """Retrieve all indexed documents from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM document_index")
                rows = cursor.fetchall()
                
                documents = []
                for row in rows:
                    doc = DocumentIndex(
                        document_id=row[0],
                        filename=row[1],
                        document_type=row[2],
                        pump_model=row[3],
                        pump_series=row[4],
                        pump_type=row[5],
                        keywords=json.loads(row[6]) if row[6] else [],
                        summary=row[7] or "",
                        specifications=json.loads(row[8]) if row[8] else {},
                        applications=json.loads(row[9]) if row[9] else [],
                        embedding_vector=json.loads(row[10]) if row[10] else None,
                        relevance_score=row[11] or 0.0,
                        last_updated=row[12] or ""
                    )
                    documents.append(doc)
                
                return documents
                
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    async def _log_search_analytics(self, query: str, results: List[DocumentIndex], 
                                  processing_time: float):
        """Log search analytics for performance monitoring"""
        try:
            query_id = hashlib.md5(f"{query}{datetime.now()}".encode()).hexdigest()
            
            matched_docs = [doc.document_id for doc in results]
            relevance_scores = [doc.relevance_score for doc in results]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO query_analytics 
                    (query_id, query_text, matched_documents, processing_time, relevance_scores)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    query_id,
                    query,
                    json.dumps(matched_docs),
                    processing_time,
                    json.dumps(relevance_scores)
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging search analytics: {e}")
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the vector index"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Document counts by type
                cursor.execute("""
                    SELECT document_type, COUNT(*) 
                    FROM document_index 
                    GROUP BY document_type
                """)
                doc_types = dict(cursor.fetchall())
                
                # Total documents
                cursor.execute("SELECT COUNT(*) FROM document_index")
                total_docs = cursor.fetchone()[0]
                
                # Documents with embeddings
                cursor.execute("SELECT COUNT(*) FROM document_index WHERE embedding_vector IS NOT NULL")
                embedded_docs = cursor.fetchone()[0]
                
                # Average query time
                cursor.execute("SELECT AVG(processing_time) FROM query_analytics")
                avg_query_time = cursor.fetchone()[0] or 0.0
                
                # Recent queries count
                cursor.execute("""
                    SELECT COUNT(*) FROM query_analytics 
                    WHERE timestamp > datetime('now', '-24 hours')
                """)
                recent_queries = cursor.fetchone()[0]
                
                return {
                    "total_documents": total_docs,
                    "embedded_documents": embedded_docs,
                    "embedding_coverage": (embedded_docs / total_docs * 100) if total_docs > 0 else 0,
                    "document_types": doc_types,
                    "average_query_time": round(avg_query_time, 3),
                    "queries_24h": recent_queries,
                    "index_efficiency": "High" if embedded_docs > total_docs * 0.8 else "Medium"
                }
                
        except Exception as e:
            logger.error(f"Error getting index statistics: {e}")
            return {}
    
    def export_index_backup(self, filepath: str = "pump_index_backup.json") -> bool:
        """Export complete index for backup and analysis"""
        try:
            documents = asyncio.run(self._get_all_documents())
            statistics = self.get_index_statistics()
            
            backup_data = {
                "export_timestamp": datetime.now().isoformat(),
                "statistics": statistics,
                "documents": [asdict(doc) for doc in documents]
            }
            
            with open(filepath, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Index backup exported to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting index backup: {e}")
            return False

# Integration functions for the main application
async def initialize_knowledge_index() -> VectorKnowledgeIndex:
    """Initialize the vector knowledge index for the application"""
    index = VectorKnowledgeIndex()
    logger.info("Vector knowledge index initialized")
    return index

async def search_pump_documentation(index: VectorKnowledgeIndex, query: str, 
                                  max_results: int = 3) -> List[str]:
    """Search pump documentation and return relevant document IDs"""
    results = await index.search_documents(query, max_results)
    return [doc.document_id for doc in results]

if __name__ == "__main__":
    import asyncio
    
    async def test_vector_index():
        """Test the vector knowledge index"""
        index = VectorKnowledgeIndex()
        
        # Test document indexing
        test_doc = {
            "document_id": "test_pump_001",
            "filename": "test_pump_datasheet.pdf",
            "document_type": "datasheet",
            "pump_model": "6/8 ALE",
            "pump_series": "ALE Series",
            "pump_type": "centrifugal",
            "specifications": {
                "flow_range_m3hr": [0, 408],
                "head_range_m": [15, 37],
                "power_range_kw": [45, 120],
                "efficiency_range_pct": [60, 82]
            },
            "applications": ["water_supply", "industrial", "cooling"],
            "keywords": ["centrifugal", "high_efficiency", "variable_speed"],
            "summary": "High efficiency centrifugal pump suitable for water supply applications"
        }
        
        # Index the document
        doc_index = await index.index_document(test_doc)
        print(f"Indexed: {doc_index.filename}")
        
        # Test search
        results = await index.search_documents("What pumps are suitable for water supply?")
        print(f"Search results: {len(results)} documents found")
        
        for result in results:
            print(f"- {result.filename} (Score: {result.relevance_score:.3f})")
        
        # Show statistics
        stats = index.get_index_statistics()
        print(f"Index statistics: {stats}")
    
    asyncio.run(test_vector_index())