from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import tempfile
import os
import shutil
from datetime import datetime
import logging

from ..models.database import get_db, User, Supplier, Product, PricelistUpload
from ..services.document_processor import DocumentProcessor
from ..services.vector_store import VectorStore
from ..utils.security import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Initialize services
document_processor = DocumentProcessor(os.getenv("OPENAI_API_KEY"))
vector_store = VectorStore(os.getenv("OPENAI_API_KEY"))

@router.post("/suppliers")
async def create_supplier(
    name: str = Form(...),
    contact_email: str = Form(None),
    contact_phone: str = Form(None),
    markup_percentage: float = Form(0.0),
    vat_inclusive: bool = Form(False),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new supplier"""
    
    # Check if supplier already exists
    existing = db.query(Supplier).filter(Supplier.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Supplier already exists")
    
    supplier = Supplier(
        name=name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        markup_percentage=markup_percentage,
        vat_inclusive=vat_inclusive
    )
    
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    return {
        "message": "Supplier created successfully",
        "supplier": {
            "id": supplier.id,
            "name": supplier.name,
            "markup_percentage": supplier.markup_percentage,
            "vat_inclusive": supplier.vat_inclusive
        }
    }

@router.get("/suppliers")
async def get_suppliers(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all suppliers"""
    suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
    return {
        "suppliers": [
            {
                "id": s.id,
                "name": s.name,
                "contact_email": s.contact_email,
                "markup_percentage": s.markup_percentage,
                "vat_inclusive": s.vat_inclusive,
                "product_count": len(s.products)
            }
            for s in suppliers
        ]
    }

@router.post("/pricelist-upload")
async def upload_pricelist(
    file: UploadFile = File(...),
    supplier_id: int = Form(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Upload and process pricelist"""
    
    # Validate file type
    if not file.filename.lower().endswith(('.xlsx', '.xls', '.pdf')):
        raise HTTPException(
            status_code=400, 
            detail="Only Excel (.xlsx, .xls) and PDF files are supported"
        )
    
    # Check if supplier exists
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Create upload record
    upload_record = PricelistUpload(
        filename=file.filename,
        original_filename=file.filename,
        file_type="excel" if file.filename.lower().endswith(('.xlsx', '.xls')) else "pdf",
        supplier_id=supplier_id,
        status="processing"
    )
    
    db.add(upload_record)
    db.commit()
    db.refresh(upload_record)
    
    # Save uploaded file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{upload_record.id}_{file.filename}")
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        upload_record.file_path = file_path
        db.commit()
        
        # Process document
        logger.info(f"Processing {file.filename} for supplier {supplier.name}")
        result = await document_processor.process_document(file_path, supplier_id, db)
        
        if result.get("success"):
            # Save products to database
            products_added = 0
            products_updated = 0
            
            for product_data in result.get("products", []):
                # Check if product exists
                existing_product = db.query(Product).filter(
                    Product.supplier_id == supplier_id,
                    Product.stock_code == product_data["stock_code"],
                    Product.brand == product_data["brand"]
                ).first()
                
                if existing_product:
                    # Update existing product
                    for key, value in product_data.items():
                        setattr(existing_product, key, value)
                    existing_product.updated_at = datetime.utcnow()
                    products_updated += 1
                else:
                    # Create new product
                    product = Product(**product_data)
                    db.add(product)
                    products_added += 1
            
            db.commit()
            
            # Update upload record
            upload_record.status = "completed"
            upload_record.processed_at = datetime.utcnow()
            upload_record.total_products = len(result.get("products", []))
            upload_record.successful_products = products_added + products_updated
            upload_record.brands_detected = result.get("brands_detected", 0)
            upload_record.structure_type = result.get("structure_type", "unknown")
            upload_record.processing_log = {
                "products_added": products_added,
                "products_updated": products_updated,
                "processing_method": result.get("structure_type", "unknown")
            }
            
            db.commit()
            
            # Add to vector store in background
            if products_added > 0:
                new_products = db.query(Product).filter(
                    Product.supplier_id == supplier_id,
                    Product.updated_at >= upload_record.created_at
                ).all()
                
                background_tasks.add_task(
                    vector_store.add_products_to_vector_store,
                    new_products,
                    db
                )
            
            return {
                "success": True,
                "message": f"Successfully processed {upload_record.total_products} products",
                "upload_id": upload_record.id,
                "details": {
                    "products_added": products_added,
                    "products_updated": products_updated,
                    "brands_detected": upload_record.brands_detected,
                    "structure_type": upload_record.structure_type
                }
            }
        else:
            # Processing failed
            upload_record.status = "failed"
            upload_record.processing_log = {"error": result.get("error")}
            db.commit()
            
            raise HTTPException(
                status_code=400,
                detail=f"Processing failed: {result.get('error')}"
            )
            
    except Exception as e:
        # Update upload record with error
        upload_record.status = "failed"
        upload_record.processing_log = {"error": str(e)}
        db.commit()
        
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@router.get("/pricelist-uploads")
async def get_pricelist_uploads(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all pricelist uploads"""
    uploads = db.query(PricelistUpload).order_by(PricelistUpload.created_at.desc()).all()
    
    return {
        "uploads": [
            {
                "id": upload.id,
                "filename": upload.original_filename,
                "supplier": upload.supplier.name if upload.supplier else "Unknown",
                "status": upload.status,
                "total_products": upload.total_products,
                "successful_products": upload.successful_products,
                "brands_detected": upload.brands_detected,
                "structure_type": upload.structure_type,
                "created_at": upload.created_at.isoformat() if upload.created_at else None,
                "processed_at": upload.processed_at.isoformat() if upload.processed_at else None
            }
            for upload in uploads
        ]
    }

@router.get("/products")
async def get_products(
    supplier_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get products with pagination"""
    query = db.query(Product).filter(Product.is_active == True)
    
    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)
    
    products = query.offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "products": [
            {
                "id": p.id,
                "brand": p.brand,
                "stock_code": p.stock_code,
                "product_name": p.product_name,
                "price_excl_vat": p.price_excl_vat,
                "cost_price": p.cost_price,
                "markup_applied": p.markup_applied,
                "supplier": p.supplier.name if p.supplier else None,
                "parsed_by_ai": p.parsed_by_ai,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None
            }
            for p in products
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics"""
    
    # Basic stats
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_suppliers = db.query(Supplier).filter(Supplier.is_active == True).count()
    ai_parsed_products = db.query(Product).filter(Product.parsed_by_ai == True).count()
    
    # Recent uploads
    recent_uploads = db.query(PricelistUpload).order_by(
        PricelistUpload.created_at.desc()
    ).limit(5).all()
    
    # Vector store stats
    vector_stats = vector_store.get_training_stats()
    
    return {
        "overview": {
            "total_products": total_products,
            "total_suppliers": total_suppliers,
            "ai_parsed_products": ai_parsed_products,
            "vector_store_products": vector_stats.get("total_vectors", 0)
        },
        "recent_uploads": [
            {
                "filename": upload.original_filename,
                "supplier": upload.supplier.name if upload.supplier else "Unknown",
                "status": upload.status,
                "products": upload.successful_products,
                "created_at": upload.created_at.isoformat() if upload.created_at else None
            }
            for upload in recent_uploads
        ],
        "vector_store_status": vector_stats.get("status", "unknown")
    }

@router.post("/rebuild-vector-store")
async def rebuild_vector_store(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Rebuild the entire vector store"""
    
    # Get all active products
    products = db.query(Product).filter(Product.is_active == True).all()
    
    if not products:
        raise HTTPException(status_code=400, detail="No products found to index")
    
    # Add to background tasks
    background_tasks.add_task(
        vector_store.add_products_to_vector_store,
        products,
        db
    )
    
    return {
        "message": f"Vector store rebuild started for {len(products)} products",
        "products_to_index": len(products)
    }