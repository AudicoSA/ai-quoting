# backend/app/routers/training_center.py (ENHANCED VERSION)
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from app.services.gpt4_document_processor import GPT4DocumentProcessor
from app.services.smart_column_detector import SmartColumnDetector
from app.core.config import settings
import pandas as pd
import json
import logging
from typing import Dict, Any, List
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/training-center", tags=["training-center"])

# Store processing sessions in memory (use Redis in production)
processing_sessions = {}

@router.post("/upload/advanced")
async def advanced_upload_with_enhanced_preview(
    file: UploadFile = File(...),
    pricing_config: str = None
):
    """
    Enhanced upload with comprehensive preview and validation
    """
    session_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Starting advanced upload for session {session_id}")
        
        # Initialize processors
        gpt4_processor = GPT4DocumentProcessor(settings.OPENAI_API_KEY)
        
        # Read and validate file
        file_data = await _read_and_validate_file(file)
        
        # Phase 1: Quick structure detection for immediate feedback
        quick_analysis = await _quick_structure_analysis(file_data, gpt4_processor)
        
        # Phase 2: Detailed analysis and sample extraction
        detailed_analysis = await _detailed_analysis_with_samples(file_data, gpt4_processor, quick_analysis)
        
        # Phase 3: Processing validation and recommendations
        processing_validation = await _validate_processing_readiness(detailed_analysis)
        
        # Phase 4: Generate configuration recommendations
        config_recommendations = await _generate_smart_config(detailed_analysis, pricing_config)
        
        # Store session data for processing
        session_data = {
            "session_id": session_id,
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "file_data": file_data,  # Store for processing
            "analysis": detailed_analysis,
            "config": config_recommendations,
            "status": "ready_for_processing"
        }
        processing_sessions[session_id] = session_data
        
        # Create comprehensive preview response
        preview_response = {
            "session_id": session_id,
            "status": "analysis_complete",
            "message": f"Successfully analyzed {detailed_analysis['total_products']} products across {len(detailed_analysis['brands_detected'])} brands",
            "preview_data": {
                "structure_analysis": detailed_analysis["structure_analysis"],
                "brands_detected": detailed_analysis["brands_detected"],
                "total_products": detailed_analysis["total_products"],
                "sample_products": detailed_analysis["sample_products"],
                "extraction_summary": detailed_analysis["extraction_summary"],
                "processing_validation": processing_validation,
                "config_recommendations": config_recommendations,
                "file_info": {
                    "filename": file.filename,
                    "size_mb": round(len(await file.read()) / 1024 / 1024, 2),
                    "format": file.filename.split('.')[-1].upper()
                }
            },
            "processing_ready": processing_validation["ready_to_process"],
            "estimated_processing_time": _estimate_processing_time(detailed_analysis["total_products"])
        }
        
        logger.info(f"Preview generated for session {session_id}: {preview_response['message']}")
        return preview_response
        
    except Exception as e:
        logger.error(f"Advanced upload failed for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

async def _read_and_validate_file(file: UploadFile) -> pd.DataFrame:
    """
    Read and validate uploaded file
    """
    try:
        # Reset file pointer
        await file.seek(0)
        
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file.file, header=None)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file.file, header=None)
        else:
            raise ValueError("Unsupported file format. Please upload .xlsx or .csv files.")
        
        if df.empty:
            raise ValueError("File is empty or contains no readable data")
        
        if df.shape[1] < 2:
            raise ValueError("File must contain at least 2 columns")
        
        logger.info(f"File validated: {df.shape[0]} rows x {df.shape[1]} columns")
        return df
        
    except Exception as e:
        raise ValueError(f"File reading failed: {str(e)}")

async def _quick_structure_analysis(df: pd.DataFrame, processor: GPT4DocumentProcessor) -> Dict[str, Any]:
    """
    Quick initial analysis for immediate user feedback
    """
    try:
        # Quick brand detection using Smart Column Detector
        detector = SmartColumnDetector()
        quick_structure = detector.detect_horizontal_structure(df)
        
        return {
            "layout_detected": quick_structure.get("layout_type", "unknown"),
            "brands_found": len(quick_structure.get("brands_detected", [])),
            "structure_valid": quick_structure.get("is_valid", False),
            "analysis_time": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Quick analysis failed: {str(e)}")
        return {
            "layout_detected": "unknown",
            "brands_found": 0,
            "structure_valid": False,
            "error": str(e)
        }

async def _detailed_analysis_with_samples(df: pd.DataFrame, processor: GPT4DocumentProcessor, quick_analysis: Dict) -> Dict[str, Any]:
    """
    Detailed analysis with sample product extraction
    """
    try:
        # Full structure analysis
        structure_analysis = await processor.analyze_pricelist_structure(df)
        
        # Extract sample products (limit to 20 for preview)
        all_products = await processor.extract_products_with_gpt4(df, structure_analysis)
        sample_products = all_products[:20] if len(all_products) > 20 else all_products
        
        # Calculate statistics
        successful_extractions = len([p for p in sample_products if p.get("parsed_price") is not None])
        failed_extractions = len(sample_products) - successful_extractions
        
        # Estimate total products
        estimated_total = len(all_products) if len(all_products) <= 20 else _estimate_total_products(df, structure_analysis)
        
        return {
            "structure_analysis": structure_analysis,
            "brands_detected": structure_analysis.get("brands_detected", []),
            "total_products": estimated_total,
            "sample_products": sample_products,
            "extraction_summary": {
                "successful_extractions": successful_extractions,
                "failed_extractions": failed_extractions,
                "brands_found": len(set([p.get("brand") for p in sample_products if p.get("brand")])),
                "success_rate": round((successful_extractions / len(sample_products) * 100), 1) if sample_products else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Detailed analysis failed: {str(e)}")
        raise

def _estimate_total_products(df: pd.DataFrame, structure_analysis: Dict[str, Any]) -> int:
    """
    Estimate total products based on structure analysis
    """
    try:
        data_start_row = structure_analysis.get("data_start_row", 2)
        data_rows = max(0, len(df) - data_start_row)
        brands_count = len(structure_analysis.get("brands_detected", []))
        
        # Estimate products per brand based on data rows
        estimated_per_brand = data_rows * 0.7  # Assume 70% of rows have products
        total_estimate = int(estimated_per_brand * brands_count)
        
        return min(total_estimate, 50000)  # Cap at 50k for safety
        
    except Exception:
        return 1000  # Default estimate

async def _validate_processing_readiness(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate if the data is ready for full processing
    """
    validation = {
        "ready_to_process": False,
        "issues": [],
        "warnings": [],
        "recommendations": []
    }
    
    try:
        structure = analysis["structure_analysis"]
        extraction_summary = analysis["extraction_summary"]
        
        # Check structure validity
        if not structure.get("is_valid", False):
            validation["issues"].append("File structure not recognized")
            validation["recommendations"].append("Consider manual column mapping")
        
        # Check brand detection
        if len(analysis["brands_detected"]) == 0:
            validation["issues"].append("No brands detected")
            validation["recommendations"].append("Verify file format and brand placement")
        
        # Check extraction success rate
        success_rate = extraction_summary.get("success_rate", 0)
        if success_rate < 50:
            validation["issues"].append(f"Low extraction success rate: {success_rate}%")
            validation["recommendations"].append("Review price formatting and column structure")
        elif success_rate < 80:
            validation["warnings"].append(f"Moderate extraction success rate: {success_rate}%")
            validation["recommendations"].append("Some price parsing may fail")
        
        # Check total products
        if analysis["total_products"] == 0:
            validation["issues"].append("No products detected")
        elif analysis["total_products"] > 20000:
            validation["warnings"].append(f"Large dataset: {analysis['total_products']} products")
            validation["recommendations"].append("Processing may take several minutes")
        
        # Determine readiness
        validation["ready_to_process"] = len(validation["issues"]) == 0
        
        return validation
        
    except Exception as e:
        validation["issues"].append(f"Validation error: {str(e)}")
        return validation

async def _generate_smart_config(analysis: Dict[str, Any], user_config: str = None) -> Dict[str, Any]:
    """
    Generate smart configuration recommendations
    """
    config = {
        "pricing": {
            "supplier": "auto_detected",
            "currency": "ZAR",
            "price_type": "excl_vat",
            "vat_rate": 15,
            "markup_percentage": 10,
            "include_vat": False
        },
        "processing": {
            "batch_size": min(1000, max(100, analysis["total_products"] // 10)),
            "enable_price_validation": True,
            "skip_invalid_prices": True,
            "auto_categorize_brands": True
        },
        "validation": {
            "require_brand": True,
            "require_product_code": True,
            "require_price": False,  # Allow P.O.R products
            "min_price": 0,
            "max_price": 1000000
        }
    }
    
    # Apply user configuration if provided
    if user_config:
        try:
            user_settings = json.loads(user_config)
            config["pricing"].update(user_settings.get("pricing", {}))
            config["processing"].update(user_settings.get("processing", {}))
        except json.JSONDecodeError:
            logger.warning("Invalid user configuration provided")
    
    # Smart adjustments based on analysis
    structure = analysis["structure_analysis"]
    if structure.get("analysis_method") == "smart_detection_enhanced_by_gpt4":
        config["processing"]["confidence_score"] = "high"
    elif "fallback" in structure.get("analysis_method", ""):
        config["processing"]["confidence_score"] = "low"
        config["validation"]["require_price"] = False
    
    return config

def _estimate_processing_time(total_products: int) -> str:
    """
    Estimate processing time based on product count
    """
    if total_products <= 1000:
        return "1-2 minutes"
    elif total_products <= 5000:
        return "3-5 minutes"
    elif total_products <= 10000:
        return "5-10 minutes"
    else:
        return "10+ minutes"

@router.post("/process/enhanced/{session_id}")
async def process_with_enhanced_validation(
    session_id: str,
    background_tasks: BackgroundTasks,
    config_overrides: Dict[str, Any] = None
):
    """
    Process the analyzed data with enhanced validation and monitoring
    """
    try:
        # Get session data
        if session_id not in processing_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = processing_sessions[session_id]
        
        # Update session status
        session_data["status"] = "processing"
        session_data["processing_start"] = datetime.now().isoformat()
        
        # Start background processing
        background_tasks.add_task(
            _process_products_background,
            session_id,
            session_data,
            config_overrides or {}
        )
        
        return {
            "status": "processing_started",
            "session_id": session_id,
            "message": "Processing started in background",
            "estimated_time": _estimate_processing_time(session_data["analysis"]["total_products"]),
            "monitor_endpoint": f"/training-center/status/{session_id}"
        }
        
    except Exception as e:
        logger.error(f"Processing initiation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/status/{session_id}")
async def get_processing_status(session_id: str):
    """
    Get real-time processing status
    """
    if session_id not in processing_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_data = processing_sessions[session_id]
    
    return {
        "session_id": session_id,
        "status": session_data.get("status", "unknown"),
        "progress": session_data.get("progress", {}),
        "message": session_data.get("current_message", "Processing..."),
        "started_at": session_data.get("processing_start"),
        "estimated_completion": session_data.get("estimated_completion")
    }

async def _process_products_background(session_id: str, session_data: Dict[str, Any], config_overrides: Dict[str, Any]):
    """
    Background task for processing products
    """
    try:
        logger.info(f"Background processing started for session {session_id}")
        
        # Initialize processor
        gpt4_processor = GPT4DocumentProcessor(settings.OPENAI_API_KEY)
        
        # Get data
        file_data = session_data["file_data"]
        structure_analysis = session_data["analysis"]["structure_analysis"]
        config = session_data["config"]
        
        # Apply config overrides
        config.update(config_overrides)
        
        # Update progress
        session_data["progress"] = {"stage": "extracting", "percent": 10}
        session_data["current_message"] = "Extracting products..."
        
        # Extract all products
        all_products = await gpt4_processor.extract_products_with_gpt4(file_data, structure_analysis)
        
        session_data["progress"] = {"stage": "processing", "percent": 50}
        session_data["current_message"] = f"Processing {len(all_products)} products..."
        
        # Apply configuration
        processed_products = _apply_processing_config(all_products, config)
        
        session_data["progress"] = {"stage": "saving", "percent": 80}
        session_data["current_message"] = "Saving to database..."
        
        # Save to database (implement your save logic)
        saved_count = await _save_products_to_database(processed_products, config)
        
        # Complete
        session_data["status"] = "completed"
        session_data["progress"] = {"stage": "completed", "percent": 100}
        session_data["current_message"] = f"Successfully processed {saved_count} products"
        session_data["result"] = {
            "total_processed": len(processed_products),
            "successfully_saved": saved_count,
            "completion_time": datetime.now().isoformat()
        }
        
        logger.info(f"Background processing completed for session {session_id}: {saved_count} products saved")
        
    except Exception as e:
        logger.error(f"Background processing failed for session {session_id}: {str(e)}")
        session_data["status"] = "failed"
        session_data["current_message"] = f"Processing failed: {str(e)}"

def _apply_processing_config(products: List[Dict], config: Dict) -> List[Dict]:
    """
    Apply processing configuration to products
    """
    processed = []
    pricing_config = config.get("pricing", {})
    validation_config = config.get("validation", {})
    
    for product in products:
        # Apply pricing configuration
        if product.get("parsed_price") is not None:
            base_price = product["parsed_price"]
            
            # Apply markup
            markup = pricing_config.get("markup_percentage", 0) / 100
            if markup > 0:
                base_price = base_price * (1 + markup)
            
            # Add VAT if configured
            if pricing_config.get("include_vat", False):
                vat_rate = pricing_config.get("vat_rate", 15) / 100
                base_price = base_price * (1 + vat_rate)
            
            product["final_price"] = round(base_price, 2)
            product["markup_applied"] = markup * 100
            product["vat_included"] = pricing_config.get("include_vat", False)
        
        # Apply validation
        is_valid = True
        
        if validation_config.get("require_brand", True) and not product.get("brand"):
            is_valid = False
        
        if validation_config.get("require_product_code", True) and not product.get("product_code"):
            is_valid = False
        
        if validation_config.get("require_price", False) and product.get("parsed_price") is None:
            is_valid = False
        
        product["is_valid"] = is_valid
        
        # Only include valid products or all if skip_invalid is False
        if is_valid or not config.get("processing", {}).get("skip_invalid_prices", True):
            processed.append(product)
    
    return processed

async def _save_products_to_database(products: List[Dict], config: Dict) -> int:
    """
    Save products to database (implement your database logic here)
    """
    # Placeholder for your database save logic
    # This should integrate with your existing SQLantern database
    
    saved_count = 0
    
    for product in products:
        try:
            # Your database save logic here
            # Example:
            # await db.products.create({
            #     "brand": product["brand"],
            #     "product_code": product["product_code"],
            #     "price": product.get("final_price"),
            #     "raw_data": product
            # })
            
            saved_count += 1
            
        except Exception as e:
            logger.error(f"Failed to save product {product.get('product_code', 'unknown')}: {str(e)}")
    
    return saved_count