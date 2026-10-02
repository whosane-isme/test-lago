"""FastAPI app for a small AI billing lesson.

Read README.md first, then follow each request from the browser to the service
that handles it. The code intentionally uses small, direct functions.
"""

from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from lago_service import send_usage_to_lago
from openrouter_service import ask_openrouter, get_free_models
from settings import (
    DEMO_PRICE_PER_1000_TOKENS,
    LAGO_API_KEY,
    LAGO_EXTERNAL_SUBSCRIPTION_ID,
    OPENROUTER_API_KEY,
)


PROJECT_FOLDER = Path(__file__).parent
STATIC_FOLDER = PROJECT_FOLDER / "static"

app = FastAPI(title="AI Billing Beginner Project")
app.mount("/static", StaticFiles(directory=STATIC_FOLDER), name="static")


class ChatRequest(BaseModel):
    """The two values sent by the chat page."""

    message: str = Field(min_length=1, max_length=4000)
    model_id: str = "openrouter/free"


@app.get("/")
def show_home_page():
    """Send the browser the HTML page."""

    return FileResponse(STATIC_FOLDER / "index.html")


@app.get("/api/status")
def show_connection_status():
    """Tell the page which integrations have their required settings."""

    return {
        "openrouter_ready": bool(OPENROUTER_API_KEY),
        "lago_ready": bool(LAGO_API_KEY and LAGO_EXTERNAL_SUBSCRIPTION_ID),
    }


@app.get("/api/models")
def list_free_models():
    """Get the current free text chat models from OpenRouter's catalog."""

    try:
        models = get_free_models()
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail="Could not load the OpenRouter model list. Try again later.",
        ) from error

    return {"models": models}


@app.post("/api/chat")
def chat_with_a_model(request: ChatRequest):
    """Ask the selected free model, then measure and optionally bill usage."""

    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY is missing from the local .env file.",
        )

    # Check the catalog again before sending the request. This stops the page
    # from choosing a model that currently has a non-zero token price.
    if request.model_id != "openrouter/free":
        try:
            free_models = get_free_models()
        except httpx.HTTPError as error:
            raise HTTPException(
                status_code=502,
                detail="Could not verify that this model is still free.",
            ) from error

        model_is_free = any(
            model["id"] == request.model_id for model in free_models
        )
        if not model_is_free:
            raise HTTPException(
                status_code=400,
                detail="That model is not listed as free right now. Reload the model list.",
            )

    try:
        model_reply = ask_openrouter(request.message, request.model_id)
    except httpx.HTTPStatusError as error:
        status_code = error.response.status_code
        if status_code == 429:
            raise HTTPException(
                status_code=429,
                detail="OpenRouter's free model rate limit was reached. Wait and try again.",
            ) from error
        if status_code == 402:
            raise HTTPException(
                status_code=402,
                detail="OpenRouter did not accept this request as free. No model response was returned.",
            ) from error
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter returned HTTP {status_code}. Check its API status.",
        ) from error
    except httpx.HTTPError as error:
        raise HTTPException(
            status_code=502,
            detail="Could not connect to OpenRouter.",
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail="OpenRouter returned a response this example cannot read.",
        ) from error

    total_tokens = model_reply["total_tokens"]
    example_charge = total_tokens * DEMO_PRICE_PER_1000_TOKENS / 1000

    # A free model has no provider token charge. This separate amount is a
    # made-up customer price to make the Lago billing lesson visible.
    lago_result = send_usage_to_lago(
        total_tokens=total_tokens,
        transaction_id=model_reply["request_id"],
    )

    return {
        "answer": model_reply["answer"],
        "model_id": model_reply["model_id"],
        "usage": {
            "input_tokens": model_reply["input_tokens"],
            "output_tokens": model_reply["output_tokens"],
            "total_tokens": total_tokens,
        },
        "provider_cost": 0,
        "demo_customer_charge": round(example_charge, 8),
        "lago": lago_result,
    }
