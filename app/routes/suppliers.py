from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.suppliers import CreateSupplierRequest, CreateSupplierResponse
from app.services.supplier_service import create_supplier_service
from app.dependencies.auth import get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/create-supplier", response_model=CreateSupplierResponse)
async def create_supplier(
    data: CreateSupplierRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Tạo nhà cung cấp mới
    
    - **supplier_name**: Tên nhà cung cấp
    - **address**: Địa chỉ nhà cung cấp
    """
    try:
        logger.info(f"Creating supplier for user: {current_user}")
        result = await create_supplier_service(data, current_user)
        logger.info(f"Successfully created supplier: {result.supplier_id}")
        return result
        
    except HTTPException as e:
        logger.error(f"HTTP error creating supplier: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error creating supplier: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi không mong muốn khi tạo nhà cung cấp: {str(e)}"
        )
