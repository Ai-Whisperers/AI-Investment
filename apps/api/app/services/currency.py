import logging

from .twelvedata import get_exchange_rate as td_get_exchange_rate

logger = logging.getLogger(__name__)

# Supported currencies (TwelveData uses standard 3-letter codes)
SUPPORTED_CURRENCIES = [
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "CAD",
    "AUD",
    "CHF",
    "CNY",
    "INR",
    "MXN",
    "BRL",
    "SEK",
    "NOK",
    "DKK",
    "SGD",
    "HKD",
    "KRW",
    "TWD",
    "NZD",
    "ZAR",
]


def get_exchange_rate(from_currency: str, to_currency: str = "USD") -> float | None:
    """
    Get current exchange rate between two currencies using TwelveData.
    Returns the rate to convert from_currency to to_currency.
    """
    try:
        # Validate currencies are supported
        if (
            from_currency not in SUPPORTED_CURRENCIES
            or to_currency not in SUPPORTED_CURRENCIES
        ):
            logger.warning(f"Unsupported currency pair: {from_currency}/{to_currency}")
            return None

        # Use TwelveData service
        return td_get_exchange_rate(from_currency, to_currency)

    except Exception as e:
        logger.error(
            f"Error fetching exchange rate {from_currency} to {to_currency}: {e}"
        )
        return None


def convert_amount(
    amount: float, from_currency: str, to_currency: str = "USD"
) -> float | None:
    """
    Convert an amount from one currency to another.
    Returns None if conversion fails.
    """
    if from_currency == to_currency:
        return amount

    rate = get_exchange_rate(from_currency, to_currency)
    if rate:
        return amount * rate
    return None


def get_supported_currencies() -> dict[str, str]:
    """
    Return dictionary of supported currency codes and their names.
    """
    return {
        "USD": "US Dollar",
        "EUR": "Euro",
        "GBP": "British Pound",
        "JPY": "Japanese Yen",
        "CAD": "Canadian Dollar",
        "AUD": "Australian Dollar",
        "CHF": "Swiss Franc",
        "CNY": "Chinese Yuan",
        "INR": "Indian Rupee",
        "MXN": "Mexican Peso",
        "BRL": "Brazilian Real",
        "SEK": "Swedish Krona",
        "NOK": "Norwegian Krone",
        "DKK": "Danish Krone",
        "SGD": "Singapore Dollar",
        "HKD": "Hong Kong Dollar",
        "KRW": "South Korean Won",
        "TWD": "Taiwan Dollar",
        "NZD": "New Zealand Dollar",
        "ZAR": "South African Rand",
    }
