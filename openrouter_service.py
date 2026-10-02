"""Small HTTP requests to OpenRouter."""

import httpx

from settings import OPENROUTER_API_KEY, OPENROUTER_API_URL


def get_free_models():
    """Return text chat models whose input and output prices are both zero."""

    catalog_url = f"{OPENROUTER_API_URL}/models"
    with httpx.Client(timeout=30) as client:
        response = client.get(catalog_url)
        response.raise_for_status()

    catalog = response.json()
    free_models = []

    for model in catalog.get("data", []):
        pricing = model.get("pricing", {})
        architecture = model.get("architecture", {})
        input_types = architecture.get("input_modalities", [])
        output_types = architecture.get("output_modalities", [])
        model_modality = architecture.get("modality", "")

        try:
            input_price_is_zero = float(pricing.get("prompt", -1)) == 0
            output_price_is_zero = float(pricing.get("completion", -1)) == 0
        except (TypeError, ValueError):
            input_price_is_zero = False
            output_price_is_zero = False

        model_can_chat_with_text = (
            "text" in input_types
            and "text" in output_types
            and model_modality.endswith("->text")
        )

        if input_price_is_zero and output_price_is_zero and model_can_chat_with_text:
            free_models.append(
                {
                    "id": model.get("id", ""),
                    "name": model.get("name", model.get("id", "Unknown model")),
                    "context_length": model.get("context_length"),
                }
            )

    # This route chooses an available free model for us. The user can also
    # select any exact free model listed above.
    free_models.insert(
        0,
        {
            "id": "openrouter/free",
            "name": "Automatic: choose a free model",
            "context_length": None,
        },
    )
    return free_models


def ask_openrouter(message, model_id):
    """Send one chat message and return the answer and token counts."""

    chat_url = f"{OPENROUTER_API_URL}/chat/completions"
    request_headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    request_body = {
        "model": model_id,
        "messages": [{"role": "user", "content": message}],
    }

    with httpx.Client(timeout=90) as client:
        response = client.post(
            chat_url,
            headers=request_headers,
            json=request_body,
        )
        response.raise_for_status()

    result = response.json()
    choices = result.get("choices", [])
    if not choices:
        raise ValueError("OpenRouter returned no answer choices.")

    answer = choices[0].get("message", {}).get("content", "")
    if isinstance(answer, list):
        answer = "".join(
            part.get("text", "") for part in answer if isinstance(part, dict)
        )

    usage = result.get("usage", {})
    input_tokens = int(usage.get("prompt_tokens", 0))
    output_tokens = int(usage.get("completion_tokens", 0))
    total_tokens = int(usage.get("total_tokens", input_tokens + output_tokens))

    return {
        "answer": answer,
        "model_id": result.get("model", model_id),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "request_id": result.get("id", ""),
    }
