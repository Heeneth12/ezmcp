from pydantic import BaseModel
from typing import Literal, Optional


class ItemModel(BaseModel):
    id: Optional[int] = None
    name: str
    itemCode: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    itemType: Literal["SERVICE", "PRODUCT"] = "PRODUCT"
    imageUrl: Optional[str] = None
    category: str
    unitOfMeasure: str
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    purchasePrice: float
    sellingPrice: float
    mrp: Optional[float] = None
    taxPercentage: Optional[float] = None
    discountPercentage: Optional[float] = None
    hsnSacCode: Optional[str] = None
    description: Optional[str] = None
    isActive: bool = True


class ItemSearchFilter(BaseModel):
    searchQuery: Optional[str] = None
    active: Optional[bool] = None
    itemType: Optional[Literal["SERVICE", "PRODUCT"]] = None
    brand: Optional[str] = None
    category: Optional[str] = None
