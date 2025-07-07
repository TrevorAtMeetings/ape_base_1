"""
Quick Query System for AI Chatbot
Provides fast responses about document availability and basic queries
"""

import os
import sqlite3
import json
from typing import Dict, List, Any

class QuickQuerySystem:
    """Lightweight query system for immediate responses"""
    
    def __init__(self):
        self.db_path = "pump_knowledge_index.db"
        self.mapping_file = "gemini_file_mapping.json"
    
    def get_document_summary(self) -> Dict[str, Any]:
        """Get summary of available documents"""
        try:
            # Get documents from vector database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT document_id, filename, COUNT(*) as chunk_count 
                FROM document_index 
                GROUP BY document_id, filename
            """)
            
            documents = []
            for doc_id, filename, chunks in cursor.fetchall():
                documents.append({
                    'id': doc_id,
                    'filename': filename,
                    'chunks': chunks,
                    'type': self._classify_document_type(filename)
                })
            
            conn.close()
            
            # Get file mapping status
            mapping_count = 0
            try:
                with open(self.mapping_file, 'r') as f:
                    mapping = json.load(f)
                    mapping_count = len(mapping)
            except:
                pass
            
            return {
                'total_documents': len(documents),
                'queryable_documents': mapping_count,
                'documents': documents,
                'status': 'operational' if mapping_count > 0 else 'indexing'
            }
            
        except Exception as e:
            return {
                'total_documents': 0,
                'queryable_documents': 0,
                'documents': [],
                'status': 'error',
                'error': str(e)
            }
    
    def _classify_document_type(self, filename: str) -> str:
        """Classify document type based on filename"""
        filename_lower = filename.lower()
        
        if 'api' in filename_lower and '610' in filename_lower:
            return 'API Standard'
        elif 'gulich' in filename_lower:
            return 'Technical Reference'
        elif 'guideline' in filename_lower:
            return 'Design Guide'
        elif 'course' in filename_lower:
            return 'Training Material'
        elif 'datasheet' in filename_lower:
            return 'Pump Datasheet'
        else:
            return 'Technical Document'
    
    def handle_quick_queries(self, query: str) -> Dict[str, Any]:
        """Handle simple queries that don't require full document processing"""
        query_lower = query.lower()
        
        # Document availability queries
        if any(phrase in query_lower for phrase in ['what documents', 'available documents', 'how many', 'list documents']):
            summary = self.get_document_summary()
            
            if summary['total_documents'] == 0:
                response = "No documents are currently uploaded. Please upload pump datasheets or technical documents via the AI Expert interface."
            else:
                doc_list = []
                for doc in summary['documents']:
                    doc_list.append(f"• {doc['filename']} ({doc['type']})")
                
                response = f"I have access to {summary['total_documents']} technical documents:\n\n" + "\n".join(doc_list)
                
                if summary['queryable_documents'] < summary['total_documents']:
                    response += f"\n\nNote: {summary['total_documents'] - summary['queryable_documents']} documents are still processing and will be available shortly."
            
            return {
                'query': query,
                'response': response,
                'source_documents': [doc['filename'] for doc in summary['documents']],
                'confidence_score': 0.9,
                'processing_time': 0.1,
                'cost_estimate': 0.0,
                'suggestions': ["What are the key specifications for pump bearings?", "Explain centrifugal pump design principles from Gulich"]
            }
        
        # System status queries
        elif any(phrase in query_lower for phrase in ['status', 'working', 'available', 'ready']):
            summary = self.get_document_summary()
            
            if summary['status'] == 'operational':
                response = f"The AI Expert system is operational with {summary['queryable_documents']} technical documents ready for queries. You can ask specific questions about pump specifications, design principles, or API standards."
            elif summary['status'] == 'indexing':
                response = f"The system is processing {summary['total_documents']} uploaded documents. Basic queries are available now, with full technical analysis available shortly."
            else:
                response = "The system is initializing. Please try uploading technical documents via the AI Expert interface."
            
            return {
                'query': query,
                'response': response,
                'source_documents': [],
                'confidence_score': 0.8,
                'processing_time': 0.1,
                'cost_estimate': 0.0
            }
        
        # Return None for complex queries that need full processing
        return None