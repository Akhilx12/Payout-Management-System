from fastapi import APIRouter, Depends, HTTPException 
from sqlalchemy.orm import Session 

from app.database import get_db
from app.models import Sale, SaleStatus
from app.schemas import SaleCreate, SaleOut

router=APIRouter(prefix="/sales", tags=["sales"])

@router.post("",response_model=SaleOut, status_code=201)
def create_sale(payload: SaleCreate, db:Session=Depends(get_db)):
    sale=Sale(
        user_id=payload.user_id,
        brand_id=payload.brand_id,
        earning=payload.earning,
        status=SaleStatus.pending,
    )
    db.add(sale)
    db.commit()
    db.refresh(sale)
    return sale

@router.get("/{sale.id}",response_model=SaleOut)
def get_sale(sale_id:str,db:Session=Depends(get_db)):
    sale=db.query(Sale).filter(Sale.id==sale_id).first()
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale