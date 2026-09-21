from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health", summary="Get backend health", description="Returns service and sandbox availability.")
async def health_check(request: Request) -> dict[str, str | bool]:
    execution_service = request.app.state.execution_service
    mode = getattr(execution_service, "get_mode", lambda: "docker")()
    return {
        "status": "ok",
        "environment": request.app.state.settings.app_env,
        "execution_sandbox_available": execution_service.is_available(),
        "sandbox_mode": mode,
    }

