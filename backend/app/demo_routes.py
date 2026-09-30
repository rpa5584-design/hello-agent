"""HTTP adapter for the fixed ZIP demonstration."""

from fastapi import APIRouter, HTTPException

from app.controllers import geoapify_controller
from app.models import HotelSearchResponse


router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/hotels", response_model_exclude_none=True)
def get_hotels(zip_code: str) -> HotelSearchResponse:
    try:
        return geoapify_controller.search_hotels(zip_code)
    except geoapify_controller.InvalidZipError:
        raise HTTPException(422, "Enter exactly five digits for a U.S. ZIP code.") from None
    except geoapify_controller.UnresolvedZipError:
        raise HTTPException(404, "ZIP could not be resolved.") from None
    except geoapify_controller.MissingGeoapifyConfigurationError:
        raise HTTPException(503, "Geoapify key is not configured.") from None
    except geoapify_controller.GeoapifyServiceError:
        raise HTTPException(502, "Hotel service is unavailable.") from None


@router.get("/zip-location")
def get_demo_zip_location(zip_code: str = "16802") -> geoapify_controller.ZipLocation:
    try:
        return geoapify_controller.lookup_demo_zip(zip_code)
    except geoapify_controller.InvalidZipError:
        raise HTTPException(status_code=422, detail="Enter exactly five digits for a U.S. ZIP code.") from None
    except geoapify_controller.MissingGeoapifyConfigurationError:
        raise HTTPException(
            status_code=503, detail="Geoapify key is not configured."
        ) from None
    except geoapify_controller.UnresolvedZipError:
        raise HTTPException(
            status_code=404, detail="ZIP could not be resolved."
        ) from None
    except geoapify_controller.GeoapifyServiceError:
        raise HTTPException(
            status_code=502, detail="Geoapify service is unavailable."
        ) from None
