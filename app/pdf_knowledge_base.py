"""
PDF Knowledge Base Module for APE Pumps AI Chatbot
Implements Google Gemini File API for direct PDF processing and Q&A
Task 4.1.1 Implementation: Production-ready PDF ingestion system
"""

import os
import logging
import asyncio
import hashlib
import json
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

# Document Type Classifications for Pump Engineering
DOCUMENT_TYPES = {
    # Product Documentation
    "datasheet": "Product Datasheet",
    "performance_curve": "Performance Curves",
    "technical_spec": "Technical Specifications", 
    "product_catalog": "Product Catalog",
    "selection_guide": "Selection Guide",
    
    # Installation & Operations
    "installation_manual": "Installation Manual",
    "operation_manual": "Operation Manual", 
    "maintenance_guide": "Maintenance Guide",
    "troubleshooting": "Troubleshooting Guide",
    "commissioning": "Commissioning Procedures",
    
    # Engineering & Design
    "engineering_drawing": "Engineering Drawings",
    "cad_model": "CAD Models",
    "dimensional_drawing": "Dimensional Drawings",
    "cross_section": "Cross-sectional Views",
    "assembly_drawing": "Assembly Drawings",
    
    # Standards & Compliance
    "iso_standard": "ISO Standards",
    "api_standard": "API Standards", 
    "ansi_standard": "ANSI Standards",
    "din_standard": "DIN Standards",
    "compliance_cert": "Compliance Certificates",
    
    # Application Guidance
    "application_note": "Application Notes",
    "case_study": "Case Studies",
    "best_practices": "Best Practices",
    "sizing_guide": "Sizing Guidelines",
    "system_design": "System Design Guide",
    
    # Quality & Testing
    "test_report": "Test Reports",
    "quality_cert": "Quality Certificates",
    "performance_test": "Performance Test Data",
    "endurance_test": "Endurance Test Results",
    "certification": "Product Certifications"
}

DOCUMENT_CATEGORIES = {
    "product_info": "Product Information",
    "technical_docs": "Technical Documentation", 
    "manuals": "Manuals & Guides",
    "standards": "Standards & Compliance",
    "applications": "Applications & Case Studies",
    "quality": "Quality & Testing"
}

PUMP_TYPES = [
    "centrifugal", "positive_displacement", "axial", "mixed_flow", 
    "screw", "gear", "piston", "diaphragm", "peristaltic"
]

APPLICATIONS = [
    "water_supply", "wastewater", "irrigation", "industrial_process",
    "chemical_transfer", "oil_gas", "mining", "marine", "hvac", 
    "fire_protection", "municipal", "agriculture", "power_generation"
]

INDUSTRIES = [
    "municipal", "agriculture", "mining", "oil_gas", "chemical", 
    "pharmaceutical", "food_beverage", "pulp_paper", "power", 
    "marine", "construction", "manufacturing"
]

FLUID_TYPES = [
    "clean_water", "wastewater", "seawater", "chemicals", "hydrocarbons",
    "slurries", "abrasive_fluids", "corrosive_fluids", "high_temp_fluids",
    "viscous_fluids", "food_grade", "pharmaceutical"
]

TECHNICAL_TOPICS = [
    "performance_curves", "npsh_requirements", "efficiency_analysis",
    "cavitation", "installation", "alignment", "commissioning", 
    "maintenance", "troubleshooting", "vibration_analysis", 
    "seal_systems", "bearing_lubrication", "variable_speed_drives"
]

@dataclass
class DocumentMetadata:
    """Enhanced metadata structure for pump engineering documents"""
    # Core identification
    document_id: str
    filename: str
    file_path: str
    
    # Document categorization
    document_type: str  # See DOCUMENT_TYPES enum below
    document_category: str  # Primary category for organization
    document_subcategory: Optional[str] = None  # Detailed classification
    
    # Pump-specific metadata
    pump_model: Optional[str] = None
    pump_series: Optional[str] = None
    pump_type: str = "centrifugal"  # 'centrifugal', 'positive_displacement', 'axial', 'mixed_flow'
    manufacturer: str = "APE"
    
    # Technical specifications
    flow_range_m3hr: Optional[Dict[str, float]] = None  # {'min': 10, 'max': 500}
    head_range_m: Optional[Dict[str, float]] = None     # {'min': 5, 'max': 100}
    power_range_kw: Optional[Dict[str, float]] = None   # {'min': 1.5, 'max': 75}
    speed_rpm: Optional[int] = None
    
    # Application contexts
    applications: Optional[List[str]] = None  # ['water_supply', 'irrigation', 'industrial']
    industries: Optional[List[str]] = None    # ['municipal', 'agriculture', 'mining']
    fluid_types: Optional[List[str]] = None   # ['clean_water', 'wastewater', 'chemicals']
    
    # Content analysis
    keywords: Optional[List[str]] = None
    technical_topics: Optional[List[str]] = None  # ['performance_curves', 'installation', 'maintenance']
    summary: Optional[str] = None
    content_language: str = "english"
    
    # File properties
    file_size_mb: Optional[float] = None
    page_count: Optional[int] = None
    document_version: Optional[str] = None
    creation_date: Optional[str] = None
    
    # Processing metadata
    upload_timestamp: Optional[str] = None
    gemini_file_id: Optional[str] = None
    processing_status: str = "pending"  # 'pending', 'processing', 'indexed', 'error'
    confidence_score: Optional[float] = None  # AI extraction confidence 0-1
    
    # Quality indicators
    data_completeness: Optional[float] = None  # Percentage of filled fields
    technical_accuracy: Optional[str] = None   # 'high', 'medium', 'low', 'unverified'
    relevance_score: Optional[float] = None    # Relevance to pump selection 0-1

@dataclass
class QueryResponse:
    """Response structure for knowledge base queries"""
    query: str
    response: str
    source_documents: List[str]
    confidence_score: float
    processing_time: float
    cost_estimate: float
    suggestions: Optional[List[str]] = None

class PumpKnowledgeBase:
    """Advanced PDF knowledge base using Google Gemini File API"""
    
    def __init__(self):
        """Initialize Gemini client and knowledge base configuration"""
        self.gemini_model = None
        self.documents: Dict[str, DocumentMetadata] = {}
        self.chat_history: List[Dict[str, Any]] = []
        
        # Initialize Google Gemini
        try:
            gemini_key = os.environ.get('GOOGLE_API_KEY')
            if not gemini_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            genai.configure(api_key=gemini_key)
            
            # Use Gemini 1.5 Pro for superior PDF processing
            self.gemini_model = genai.GenerativeModel(
                'gemini-1.5-pro',
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            
            logger.info("Google Gemini File API initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def generate_document_id(self, filepath: str) -> str:
        """Generate unique document ID based on file content"""
        try:
            with open(filepath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            return f"doc_{file_hash[:16]}"
        except Exception as e:
            logger.error(f"Error generating document ID: {e}")
            return f"doc_{int(datetime.now().timestamp())}"
    
    def _categorize_document_type(self, document_type: str) -> str:
        """Categorize document type into main categories"""
        categorization_map = {
            # Product Information
            "datasheet": "product_info",
            "performance_curve": "product_info", 
            "technical_spec": "product_info",
            "product_catalog": "product_info",
            "selection_guide": "product_info",
            
            # Technical Documentation
            "engineering_drawing": "technical_docs",
            "cad_model": "technical_docs",
            "dimensional_drawing": "technical_docs",
            "cross_section": "technical_docs",
            "assembly_drawing": "technical_docs",
            
            # Manuals & Guides
            "installation_manual": "manuals",
            "operation_manual": "manuals",
            "maintenance_guide": "manuals", 
            "troubleshooting": "manuals",
            "commissioning": "manuals",
            
            # Standards & Compliance
            "iso_standard": "standards",
            "api_standard": "standards",
            "ansi_standard": "standards",
            "din_standard": "standards",
            "compliance_cert": "standards",
            
            # Applications & Case Studies
            "application_note": "applications",
            "case_study": "applications",
            "best_practices": "applications",
            "sizing_guide": "applications",
            "system_design": "applications",
            
            # Quality & Testing
            "test_report": "quality",
            "quality_cert": "quality", 
            "performance_test": "quality",
            "endurance_test": "quality",
            "certification": "quality"
        }
        
        return categorization_map.get(document_type, "technical_docs")
    
    async def upload_pdf_document(self, filepath: str, document_type: str = "datasheet", 
                                 pump_model: str = None) -> DocumentMetadata:
        """Upload PDF document to Gemini File API and create metadata"""
        logger.info(f"Uploading PDF document: {filepath}")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"PDF file not found: {filepath}")
        
        try:
            # Generate document metadata
            doc_id = self.generate_document_id(filepath)
            file_size = os.path.getsize(filepath) / (1024 * 1024)  # MB
            
            # Determine document category based on type
            document_category = self._categorize_document_type(document_type)
            
            metadata = DocumentMetadata(
                document_id=doc_id,
                filename=os.path.basename(filepath),
                file_path=filepath,
                document_type=document_type,
                document_category=document_category,
                pump_model=pump_model,
                file_size_mb=round(file_size, 2),
                upload_timestamp=datetime.now().isoformat(),
                processing_status="processing"
            )
            
            # Upload file to Gemini with timeout optimization
            logger.info(f"Uploading {metadata.filename} to Gemini File API...")
            
            # Clean filename for Gemini compatibility (lowercase alphanumeric and dashes only)
            clean_filename = re.sub(r'[^a-z0-9\-]', '-', metadata.filename.lower())
            clean_filename = re.sub(r'-+', '-', clean_filename)  # Remove multiple dashes
            clean_filename = clean_filename.strip('-')  # Remove leading/trailing dashes
            
            uploaded_file = genai.upload_file(
                path=filepath,
                display_name=clean_filename,
                mime_type="application/pdf"
            )
            
            metadata.gemini_file_id = uploaded_file.name
            
            # File mapping will be saved in _persist_document_metadata
            
            # For large files (>10MB), defer metadata extraction to prevent timeout
            if file_size > 10.0:
                logger.info(f"Large file detected ({file_size:.1f}MB), deferring metadata extraction")
                metadata.processing_status = "indexed"
                metadata.document_summary = f"Large technical document: {metadata.filename}"
            else:
                # Generate initial summary and extract metadata for smaller files
                metadata.processing_status = "processing"
                await self._extract_document_metadata(metadata, uploaded_file)
                metadata.processing_status = "indexed"
            
            # Store in knowledge base and persist to database
            self.documents[doc_id] = metadata
            await self._persist_document_metadata(metadata)
            
            logger.info(f"Successfully uploaded and indexed: {metadata.filename}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error uploading PDF document: {e}")
            if 'metadata' in locals():
                metadata.processing_status = "error"
            raise
    
    async def _extract_document_metadata(self, metadata: DocumentMetadata, 
                                       uploaded_file: Any) -> None:
        """Extract metadata and summary from uploaded PDF"""
        try:
            # Create extraction prompt
            extraction_prompt = f"""
            Analyze this APE Pumps technical document and extract the following information in JSON format:

            {{
                "pump_model": "exact pump model name if this is a datasheet",
                "pump_series": "pump series/family name",
                "pump_type": "centrifugal/positive_displacement/mixed_flow/etc",
                "specifications": {{
                    "flow_range_m3hr": [min_flow, max_flow],
                    "head_range_m": [min_head, max_head],
                    "power_range_kw": [min_power, max_power],
                    "efficiency_range_pct": [min_eff, max_eff],
                    "impeller_sizes_mm": [list of available sizes],
                    "suction_size_mm": inlet_diameter,
                    "discharge_size_mm": outlet_diameter
                }},
                "applications": ["list", "of", "suitable", "applications"],
                "keywords": ["technical", "terms", "and", "concepts"],
                "summary": "concise 2-3 sentence summary of the document content"
            }}

            Focus on extracting exact numerical values from performance tables and charts.
            If this is not a pump datasheet, focus on the technical content and applications covered.
            """
            
            response = await asyncio.to_thread(
                self.gemini_model.generate_content,
                [uploaded_file, extraction_prompt]
            )
            
            # Parse extracted metadata
            try:
                extracted_data = json.loads(response.text)
                
                metadata.pump_model = extracted_data.get("pump_model")
                metadata.pump_series = extracted_data.get("pump_series") 
                metadata.pump_type = extracted_data.get("pump_type")
                metadata.specifications = extracted_data.get("specifications")
                metadata.applications = extracted_data.get("applications")
                metadata.keywords = extracted_data.get("keywords")
                metadata.summary = extracted_data.get("summary")
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse extracted metadata as JSON, using raw response")
                metadata.summary = response.text[:500]  # Truncated summary
                
        except Exception as e:
            logger.error(f"Error extracting document metadata: {e}")
            metadata.summary = f"Error extracting metadata: {str(e)}"
    
    async def query_knowledge_base(self, query: str, max_documents: int = 2) -> QueryResponse:
        """Query the knowledge base using uploaded documents"""
        logger.info(f"Processing query: {query}")
        start_time = datetime.now()
        
        try:
            # Find relevant documents based on query analysis
            relevant_docs = await self._find_relevant_documents(query, max_documents)
            
            if not relevant_docs:
                return QueryResponse(
                    query=query,
                    response="I don't have any relevant pump documentation to answer this question. Please upload APE pump datasheets or technical documents.",
                    source_documents=[],
                    confidence_score=0.0,
                    processing_time=0.0,
                    cost_estimate=0.0
                )
            
            # Prepare context with uploaded files
            file_references = []
            source_names = []
            
            for doc_id in relevant_docs:
                metadata = self.documents[doc_id]
                if metadata.gemini_file_id:
                    # Get file reference for Gemini
                    uploaded_file = genai.get_file(metadata.gemini_file_id)
                    file_references.append(uploaded_file)
                    source_names.append(metadata.filename)
            
            # Create comprehensive prompt for pump expertise
            pump_expert_prompt = f"""
            You are an expert APE Pumps technical specialist. Answer the following question based ONLY on the information contained in the provided PDF documents.

            Question: {query}

            Instructions:
            1. Provide accurate, specific answers based on the document content
            2. Reference specific pump models, specifications, and performance data when relevant
            3. If the question involves performance curves or charts, interpret the visual data
            4. Include specific numerical values, ranges, and technical specifications
            5. If comparing pumps, provide detailed technical justification
            6. Cite which document(s) contain the information
            7. If the documents don't contain sufficient information, state this clearly

            Technical Focus Areas:
            - Pump specifications (flow, head, power, efficiency)
            - Performance curve analysis and interpolation
            - Application suitability and recommendations
            - Installation and operational requirements
            - Material specifications and compatibility
            - NPSH requirements and cavitation analysis

            Format your response as a knowledgeable pump engineer would, with technical precision and practical insights.
            """
            
            # Limit file references to prevent timeout (max 2 most relevant documents)
            limited_files = file_references[:2]
            limited_sources = source_names[:2]
            
            # Generate response using Gemini with timeout protection
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.gemini_model.generate_content,
                        limited_files + [pump_expert_prompt]
                    ),
                    timeout=25.0  # 25-second timeout
                )
            except asyncio.TimeoutError:
                return QueryResponse(
                    query=query,
                    response="Query processing timed out. Please try a more specific question or contact support for complex technical queries.",
                    source_documents=limited_sources,
                    confidence_score=0.5,
                    processing_time=25.0,
                    cost_estimate=0.001
                )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Calculate confidence score based on response quality indicators
            confidence_score = self._calculate_confidence_score(response.text, query)
            
            # Generate related suggestions
            suggestions = await self._generate_suggestions(query, relevant_docs)
            
            return QueryResponse(
                query=query,
                response=response.text,
                source_documents=source_names,
                confidence_score=confidence_score,
                processing_time=processing_time,
                cost_estimate=self._estimate_query_cost(response),
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return QueryResponse(
                query=query,
                response=f"I encountered an error processing your question: {str(e)}. Please try rephrasing your question or contact support.",
                source_documents=[],
                confidence_score=0.0,
                processing_time=processing_time,
                cost_estimate=0.0
            )
    
    async def _find_relevant_documents(self, query: str, max_docs: int) -> List[str]:
        """Find most relevant documents for the query using semantic analysis"""
        
        # Use vector database to find relevant documents and get Gemini file IDs
        from app.vector_knowledge_index import VectorKnowledgeIndex
        import sqlite3
        
        index = VectorKnowledgeIndex()
        
        # Search for relevant documents
        search_results = await index.search_documents(query, max_docs)
        
        if not search_results:
            return []
        
        # Get stored Gemini file IDs from a simple file mapping
        gemini_file_mapping = self._load_gemini_file_mapping()
        
        available_docs = []
        for result in search_results:
            # Get actual Gemini file ID from persistent storage
            gemini_file_id = gemini_file_mapping.get(result.document_id)
            
            if gemini_file_id:
                # Reconstruct document metadata
                self.documents[result.document_id] = DocumentMetadata(
                    document_id=result.document_id,
                    filename=result.filename,
                    file_path="",
                    document_type=result.document_type,
                    document_category="technical_docs",  # Default category
                    pump_model=result.pump_model,
                    pump_series=result.pump_series,
                    pump_type=result.pump_type,
                    applications=result.applications,
                    keywords=result.keywords,
                    summary=result.summary,
                    processing_status="indexed",
                    gemini_file_id=gemini_file_id
                )
                available_docs.append(result.document_id)
        
        # Prioritize documents based on query keywords
        scored_docs = []
        query_lower = query.lower()
        
        for doc_id in available_docs:
            metadata = self.documents[doc_id]
            score = 0.0
            
            # Score based on pump model match
            if metadata.pump_model and metadata.pump_model.lower() in query_lower:
                score += 50.0
            
            # Score based on keywords
            if metadata.keywords:
                for keyword in metadata.keywords:
                    if keyword.lower() in query_lower:
                        score += 10.0
            
            # Score based on document type relevance
            if "datasheet" in query_lower and metadata.document_type == "datasheet":
                score += 20.0
            elif "manual" in query_lower and metadata.document_type == "manual":
                score += 20.0
            
            # Default relevance for any indexed document
            score += 5.0
            
            scored_docs.append((doc_id, score))
        
        # Sort by score and return top documents
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc_id for doc_id, _ in scored_docs[:max_docs]]
    
    def _calculate_confidence_score(self, response: str, query: str) -> float:
        """Calculate confidence score based on response quality indicators"""
        score = 0.5  # Base score
        
        # Check for specific technical indicators
        technical_indicators = [
            "m³/hr", "m³/h", "kW", "rpm", "mm", "bar", "°C", 
            "efficiency", "NPSH", "impeller", "discharge", "suction"
        ]
        
        for indicator in technical_indicators:
            if indicator in response:
                score += 0.05
        
        # Check for numerical values (suggests specific data)
        import re
        numbers = re.findall(r'\d+\.?\d*', response)
        score += min(len(numbers) * 0.02, 0.2)
        
        # Check response length (more detailed responses often more confident)
        if len(response) > 200:
            score += 0.1
        if len(response) > 500:
            score += 0.1
        
        # Check for uncertainty phrases
        uncertainty_phrases = ["not sure", "unclear", "cannot determine", "insufficient"]
        for phrase in uncertainty_phrases:
            if phrase in response.lower():
                score -= 0.2
        
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
    
    async def _persist_document_metadata(self, metadata: DocumentMetadata):
        """Persist document metadata and Gemini file ID for retrieval"""
        import json
        
        # Save Gemini file ID mapping
        mapping_file = "gemini_file_mapping.json"
        try:
            # Load existing mapping
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    file_mapping = json.load(f)
            else:
                file_mapping = {}
            
            # Add new document
            file_mapping[metadata.document_id] = metadata.gemini_file_id
            
            # Save updated mapping
            with open(mapping_file, 'w') as f:
                json.dump(file_mapping, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error persisting document metadata: {e}")
    
    def _load_gemini_file_mapping(self) -> Dict[str, str]:
        """Load Gemini file ID mapping from persistent storage"""
        import json
        
        mapping_file = "gemini_file_mapping.json"
        try:
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading file mapping: {e}")
        
        return {}
    
    async def _generate_suggestions(self, query: str, relevant_docs: List[str]) -> List[str]:
        """Generate suggested follow-up questions"""
        
        suggestions = []
        
        # Query-based suggestions
        if "flow" in query.lower():
            suggestions.append("What is the efficiency at this flow rate?")
            suggestions.append("What power is required for this operation?")
        
        if "efficiency" in query.lower():
            suggestions.append("What is the best efficiency point (BEP)?")
            suggestions.append("How does efficiency vary across the flow range?")
        
        if "pump" in query.lower() and len(relevant_docs) > 1:
            suggestions.append("How do these pumps compare in terms of efficiency?")
            suggestions.append("Which pump is most suitable for my application?")
        
        # Document-based suggestions
        for doc_id in relevant_docs[:2]:  # Limit to first 2 docs
            metadata = self.documents.get(doc_id)
            if metadata and metadata.pump_model:
                suggestions.append(f"What are the technical specifications of {metadata.pump_model}?")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _estimate_query_cost(self, response: Any) -> float:
        """Estimate cost for the query based on token usage"""
        # Simplified cost estimation for Gemini
        # Actual costs would need to be tracked via API usage metrics
        estimated_input_tokens = 2000  # Includes PDF context
        estimated_output_tokens = len(response.text.split()) * 1.3  # Rough token estimate
        
        # Gemini Pro pricing (approximate)
        input_cost = (estimated_input_tokens / 1000) * 0.00125
        output_cost = (estimated_output_tokens / 1000) * 0.00375
        
        return round(input_cost + output_cost, 4)
    
    def get_knowledge_base_status(self) -> Dict[str, Any]:
        """Get current status of the knowledge base"""
        status_counts = {}
        for metadata in self.documents.values():
            status = metadata.processing_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "document_status": status_counts,
            "available_models": [meta.pump_model for meta in self.documents.values() 
                               if meta.pump_model and meta.processing_status == "indexed"],
            "document_types": list(set(meta.document_type for meta in self.documents.values())),
            "last_upload": max([meta.upload_timestamp for meta in self.documents.values()], 
                              default="None")
        }
    
    def export_knowledge_base_index(self, filepath: str = "knowledge_base_index.json") -> None:
        """Export knowledge base index for backup and analysis"""
        index_data = {
            "export_timestamp": datetime.now().isoformat(),
            "documents": {doc_id: asdict(metadata) for doc_id, metadata in self.documents.items()}
        }
        
        with open(filepath, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        logger.info(f"Knowledge base index exported to {filepath}")
    
    def list_uploaded_files(self) -> List[Dict[str, Any]]:
        """List all uploaded files for the admin interface"""
        files = []
        
        # Load file mapping to get current documents
        file_mapping = self._load_gemini_file_mapping()
        
        try:
            # Get list of files from Gemini API
            import google.generativeai as genai
            gemini_files = genai.list_files()
            
            for file in gemini_files:
                # Create document entry
                doc_info = {
                    'id': file.name,
                    'name': file.display_name or 'Unknown',
                    'size': getattr(file, 'size_bytes', 0),
                    'upload_time': getattr(file, 'create_time', 'Unknown'),
                    'status': 'indexed',
                    'type': 'PDF Document'
                }
                files.append(doc_info)
                
        except Exception as e:
            logger.error(f"Error listing files from Gemini: {e}")
            
        return files
    
    def upload_document(self, filepath: str, filename: str) -> Dict[str, Any]:
        """Upload a document synchronously for the admin interface"""
        try:
            # Create async wrapper
            import asyncio
            
            # Run the async upload method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                metadata = loop.run_until_complete(
                    self.upload_pdf_document(filepath, document_type="datasheet")
                )
                
                return {
                    'success': True,
                    'file_id': metadata.gemini_file_id,
                    'document_id': metadata.document_id,
                    'filename': metadata.filename,
                    'status': metadata.processing_status
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def query_documents(self, query: str) -> Dict[str, Any]:
        """Query documents synchronously for the admin interface"""
        try:
            import asyncio
            
            # Create async wrapper
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Load existing documents if not already loaded
                if not self.documents:
                    file_mapping = self._load_gemini_file_mapping()
                    for doc_id, file_id in file_mapping.items():
                        # Create basic metadata for existing files
                        self.documents[doc_id] = DocumentMetadata(
                            document_id=doc_id,
                            filename=f"document_{doc_id}",
                            file_path="",
                            document_type="datasheet",
                            gemini_file_id=file_id,
                            processing_status="indexed"
                        )
                
                response = loop.run_until_complete(
                    self.query_knowledge_base(query)
                )
                
                return {
                    'response': response.response,
                    'source_documents': response.source_documents,
                    'confidence_score': response.confidence_score,
                    'processing_time': response.processing_time
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            return {
                'response': f"Error processing query: {str(e)}",
                'source_documents': [],
                'confidence_score': 0.0,
                'processing_time': 0.0
            }

# Example usage and testing functions
async def test_with_sample_pdf(knowledge_base: PumpKnowledgeBase, pdf_path: str):
    """Test the knowledge base with a sample PDF"""
    logger.info(f"Testing knowledge base with PDF: {pdf_path}")
    
    try:
        # Upload document
        metadata = await knowledge_base.upload_pdf_document(
            pdf_path, 
            document_type="datasheet",
            pump_model="Test_Pump_Model"
        )
        
        print(f"Uploaded: {metadata.filename}")
        print(f"Summary: {metadata.summary}")
        
        # Test queries
        test_queries = [
            "What is the maximum flow rate of this pump?",
            "What are the efficiency characteristics?", 
            "What applications is this pump suitable for?",
            "What are the physical dimensions and connections?"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            response = await knowledge_base.query_knowledge_base(query)
            print(f"Response: {response.response[:200]}...")
            print(f"Confidence: {response.confidence_score:.2f}")
            print(f"Sources: {response.source_documents}")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    # Initialize knowledge base
    kb = PumpKnowledgeBase()
    print("APE Pumps PDF Knowledge Base initialized successfully")
    print("Ready to process pump datasheets and technical documents")
    print("\nUsage:")
    print("1. Upload PDF: await kb.upload_pdf_document('path/to/pump_datasheet.pdf')")
    print("2. Query: await kb.query_knowledge_base('What is the pump efficiency?')")
    print("3. Status: kb.get_knowledge_base_status()")