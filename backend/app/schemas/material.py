from typing import Optional
from decimal import Decimal
import re
import html

from pydantic import BaseModel, Field, field_validator
from app.models.material import MaterialUnit


class MaterialValidators:
    @field_validator('unit_price')
    @classmethod
    def validate_unit_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Unit price cannot be negative')
        if v is not None and v > 999999999.99:
            raise ValueError('Unit price exceeds maximum allowed value')
        return v

    @field_validator('min_stock_level')
    @classmethod
    def validate_min_stock_level(cls, v):
        if v is not None and v < 0:
            raise ValueError('Minimum stock level cannot be negative')
        if v is not None and v > 999999999:
            raise ValueError('Minimum stock level exceeds maximum allowed value')
        return v

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        if v is None:
            return v
        
        # Remove leading/trailing whitespace
        v = v.strip()
        if v == '':
            return None

        # Max length check
        if len(v) > 100:
            raise ValueError('Category must be 100 characters or less')
        
        # Allow only alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩάέήίόύώΆΈΉΊΌΎΏ]+$', v):
            raise ValueError('Category contains invalid characters')
        
        return v
    
    @field_validator('name', 'sku')
    @classmethod
    def validate_alphanumeric_fields(cls, v, info):
        if v is None:
            return v
        
        v = v.strip()
        
        # Prevent SQL injection patterns
        dangerous_patterns = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM',
            r'UNION\s+SELECT',
            r'<script',
            r'javascript:',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f'{info.field_name} contains suspicious content')
        
        return v

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        if v is None:
            return v
        
        v = v.strip()
        
        # HTML escape to prevent XSS
        v = html.escape(v)
        
        # Max length check after escaping
        if len(v) > 1000:
            raise ValueError('Description must be 1000 characters or less')
        
        return v
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v):
        if v is None:
            return v
        
        # HTML escape (XSS patterns already checked by validate_alphanumeric_fields)
        return html.escape(v.strip())

    @field_validator('barcode')
    @classmethod
    def validate_string_fields(cls, v, info):
        if v is not None and v.strip() == '':
            return None  # Convert empty strings to None
        return v


class MaterialBase(MaterialValidators, BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    sku: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    unit: MaterialUnit = MaterialUnit.PIECE
    unit_price: Optional[Decimal] = Field(None, ge=0, description="Must be non-negative")
    min_stock_level: int = Field(0, ge=0, description="Must be non-negative")
    barcode: Optional[str] = Field(None, max_length=100)
    supplier: Optional[str] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(MaterialValidators, BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=100)
    unit: Optional[MaterialUnit] = None
    unit_price: Optional[Decimal] = Field(None, ge=0)
    min_stock_level: Optional[int] = Field(None, ge=0)
    barcode: Optional[str] = Field(None, max_length=100)
    supplier: Optional[str] = None


class MaterialResponse(MaterialBase):
    id: int

    class Config:
        from_attributes = True
