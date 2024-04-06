def wrap_response(payload):
    """Wrap the response payload in the api envelope."""
    return {"bma_request": {}, "bma_response": payload}
