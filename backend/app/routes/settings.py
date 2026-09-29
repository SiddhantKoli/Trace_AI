from fastapi import APIRouter
from app.config import settings
from app.jev_client import jev_client
from app.schemas import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings & Configuration"])


@router.get("", response_model=SettingsOut)
def get_current_settings():
    """
    Returns current active configuration without exposing secret keys.
    """
    api_key = settings.JEV_API_KEY.strip()
    is_configured = bool(api_key)
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else ("Configured" if is_configured else "Not Set")

    return SettingsOut(
        jev_api_key_configured=is_configured,
        jev_api_key_masked=masked_key,
        jev_api_url=settings.JEV_API_URL,
        demo_mode=settings.DEMO_MODE,
        default_contamination=settings.DEFAULT_CONTAMINATION,
        default_correlation_window_seconds=settings.DEFAULT_CORRELATION_WINDOW_SECONDS,
        max_file_size_mb=settings.MAX_FILE_SIZE_MB
    )


@router.post("", response_model=SettingsOut)
def update_settings(update_data: SettingsUpdate):
    """
    Updates runtime settings and updates Jev client state.
    """
    if update_data.jev_api_key is not None:
        settings.JEV_API_KEY = update_data.jev_api_key.strip()
        jev_client.api_key = settings.JEV_API_KEY
        if settings.JEV_API_KEY:
            settings.DEMO_MODE = False
            jev_client.demo_mode = False

    if update_data.demo_mode is not None:
        settings.DEMO_MODE = update_data.demo_mode
        jev_client.demo_mode = update_data.demo_mode

    if update_data.default_contamination is not None:
        settings.DEFAULT_CONTAMINATION = max(0.01, min(0.3, update_data.default_contamination))

    if update_data.default_correlation_window_seconds is not None:
        settings.DEFAULT_CORRELATION_WINDOW_SECONDS = max(10, min(1800, update_data.default_correlation_window_seconds))

    return get_current_settings()
