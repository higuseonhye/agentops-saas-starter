PRICE_PER_REQUEST = {
    "free": 0.0,
    "pro": 0.002,
    "team": 0.0015,
}

PRICE_PER_INPUT_TOKEN = 0.000001
PRICE_PER_OUTPUT_TOKEN = 0.000002


def calculate_cost(plan: str, input_tokens: int, output_tokens: int) -> float:
    request_cost = PRICE_PER_REQUEST.get(plan, PRICE_PER_REQUEST["pro"])
    token_cost = (input_tokens * PRICE_PER_INPUT_TOKEN) + (output_tokens * PRICE_PER_OUTPUT_TOKEN)
    return round(request_cost + token_cost, 8)
