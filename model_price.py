# model_price.py
# This module contains the logic that calculates the price
# based on the form data received from Shiny.

def calculate_price(data: dict) -> int:
    """
    form_data: dictionary containing all form fields collected from Shiny.
    Returns: integer price in euros.
    """

    # Example simple pricing formula (placeholder):
    area = data.get("area") or 0
    rooms = data.get("rooms") or 0

    # Very basic example calculation:
    price = 100_000 + area * 1500 + rooms * 10_000

    return int(price)
