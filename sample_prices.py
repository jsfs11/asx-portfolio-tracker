"""
Sample ASX prices for demo purposes when API is unavailable
These are approximate prices and should be replaced with real API data
"""

SAMPLE_ASX_PRICES = {
    "WAX": 1.18,  # Warnex Mining
    "WAM": 1.65,  # WAM Capital
    "HLI": 5.02,  # Helloworld Travel
    "YMAX": 7.75,  # Ymax Group
    "WOW": 32.10,  # Woolworths
    "CBA": 185.20,  # Commonwealth Bank
    "CSL": 245.80,  # CSL Limited
    "LNW": 155.40,  # LendLease
    "DTR": 0.092,  # DTek Resources
    "SDR": 4.52,  # SiteOne Landscape Supply
    "BHP": 39.10,  # BHP Group
    "NXT": 14.25,  # NextDC
    "XRO": 180.50,  # Xero
}


def get_sample_price(stock: str) -> float:
    """Get sample price for demo purposes"""
    return SAMPLE_ASX_PRICES.get(stock, 0.0)
