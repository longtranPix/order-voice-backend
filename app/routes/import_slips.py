"""
Import slip routes
"""
from fastapi import APIRouter, Depends
from app.schemas.import_slips import CreateImportSlipRequest, ImportSlipResponse
from app.schemas.delivery_notes import CreateDeliveryNoteRequest, DeliveryNoteResponse
from app.services.import_slip_service import create_import_slip_service, create_delivery_note_service
from app.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/create-import-slip", response_model=ImportSlipResponse)
async def create_import_slip(
    data: CreateImportSlipRequest,
    current_user: str = Depends(get_current_user)
):
    """Create new import slip endpoint"""
    return await create_import_slip_service(data, current_user)

@router.post("/create-delivery-note", response_model=DeliveryNoteResponse)
async def create_delivery_note(
    data: CreateDeliveryNoteRequest,
    current_user: str = Depends(get_current_user)
):
    """Create new delivery note endpoint (linked to order)"""
    return await create_delivery_note_service(data, current_user)
