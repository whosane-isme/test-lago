"""The one small request that sends measured usage to Lago."""

import httpx

from settings import (
    LAGO_API_KEY,
    LAGO_API_URL,
    LAGO_EVENT_CODE,
    LAGO_EXTERNAL_SUBSCRIPTION_ID,
)


def send_usage_to_lago(total_tokens, transaction_id):
    """Send one token event if a Lago key and subscription are configured."""

    if not LAGO_API_KEY or not LAGO_EXTERNAL_SUBSCRIPTION_ID:
        return {
            "sent": False,
            "message": "Lago is not configured yet. Usage is shown in this app only.",
        }

    event_url = f"{LAGO_API_URL.rstrip('/')}/events"
    request_headers = {
        "Authorization": f"Bearer {LAGO_API_KEY}",
        "Content-Type": "application/json",
    }
    request_body = {
        "event": {
            "transaction_id": transaction_id,
            "external_subscription_id": LAGO_EXTERNAL_SUBSCRIPTION_ID,
            "code": LAGO_EVENT_CODE,
            "properties": {"value": total_tokens},
        }
    }

    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(
                event_url,
                headers=request_headers,
                json=request_body,
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        return {
            "sent": False,
            "message": f"Lago returned HTTP {error.response.status_code}. Check the metric and subscription settings.",
        }
    except httpx.HTTPError:
        return {
            "sent": False,
            "message": "Could not connect to Lago. Check that the local container is running.",
        }

    return {
        "sent": True,
        "message": "The token event was accepted by Lago.",
        "transaction_id": transaction_id,
    }
