from fastapi import APIRouter, Depends
from ..dependencies import get_api_key
from ..models import APIKey

router = APIRouter()

@router.get("/protected")
def protected_route(api_key: APIKey = Depends(get_api_key)):
    return {"message": "You have access", "user_id": api_key.user_id}

@router.get("/gateway/users")
def get_users(api_key: APIKey = Depends(get_api_key)):
    return {"service": "user-service", "data": [{"id": 1, "name": "Amy"}, {"id": 2, "name": "Ben"}]}

@router.get("/gateway/orders")
def get_orders(api_key: APIKey = Depends(get_api_key)):
    return {"service": "order-service", "data": [{"order_id": 101, "status": "shipped"}, {"order_id": 102, "status": "pending"}]}

@router.get("/gateway/products")
def get_products(api_key: APIKey = Depends(get_api_key)):
    return {"service": "product-service", "data": [{"product_id": 1, "name": "Laptop", "price": 999}, {"product_id": 2, "name": "Mouse", "price": 29}]}