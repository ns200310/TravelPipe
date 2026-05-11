from fastapi import APIRouter
from controllers.mbta_service import mbta_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/kpis")
async def get_kpis():
    return await mbta_service.get_kpis()

@router.get("/charts")
async def get_charts():
    return await mbta_service.get_chart_data()

@router.get("/routes")
async def get_routes():
    return await mbta_service.get_routes_status()
