#!/usr/bin/env python3
"""
Franking Credit Calculator for ASX Portfolio Tracker
Provides tax calculations and franking credit analysis for Australian investors
"""

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests


@dataclass
class FrankingData:
    stock: str
    franking_rate: float  # 0-100%
    sector: str
    reliability: str  # 'high', 'medium', 'low'
    last_updated: str


class StaticFrankingDatabase:
    """Static database of franking rates for major ASX stocks"""

    def __init__(self):
        self.franking_data = {
            # Big 4 Banks - Typically 100% franked
            "CBA": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "WBC": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "ANZ": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "NAB": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            # Major Miners - Usually 100% franked
            "BHP": {"franking_rate": 100, "sector": "Materials", "reliability": "high"},
            "RIO": {"franking_rate": 100, "sector": "Materials", "reliability": "high"},
            "FMG": {"franking_rate": 100, "sector": "Materials", "reliability": "high"},
            "NCM": {"franking_rate": 100, "sector": "Materials", "reliability": "high"},
            # Major Retailers - Usually 100% franked
            "WOW": {
                "franking_rate": 100,
                "sector": "Consumer Staples",
                "reliability": "high",
            },
            "COL": {
                "franking_rate": 100,
                "sector": "Consumer Staples",
                "reliability": "high",
            },
            "WES": {
                "franking_rate": 100,
                "sector": "Consumer Staples",
                "reliability": "high",
            },
            # Telecommunications - Usually 100% franked
            "TLS": {
                "franking_rate": 100,
                "sector": "Telecommunications",
                "reliability": "high",
            },
            "TPG": {
                "franking_rate": 100,
                "sector": "Telecommunications",
                "reliability": "medium",
            },
            # Utilities - Usually 100% franked
            "AGL": {"franking_rate": 100, "sector": "Utilities", "reliability": "high"},
            "ORG": {"franking_rate": 100, "sector": "Utilities", "reliability": "high"},
            "APA": {
                "franking_rate": 100,
                "sector": "Utilities",
                "reliability": "medium",
            },
            # Insurance - Usually 100% franked
            "IAG": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "SUN": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "QBE": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            # REITs - Often 0% franked (distributions)
            "SCG": {"franking_rate": 0, "sector": "Real Estate", "reliability": "high"},
            "GMG": {"franking_rate": 0, "sector": "Real Estate", "reliability": "high"},
            "VCX": {"franking_rate": 0, "sector": "Real Estate", "reliability": "high"},
            "BWP": {"franking_rate": 0, "sector": "Real Estate", "reliability": "high"},
            "CHC": {"franking_rate": 0, "sector": "Real Estate", "reliability": "high"},
            # Growth/Tech stocks - Often 0% or low franking
            "CSL": {"franking_rate": 0, "sector": "Healthcare", "reliability": "high"},
            "XRO": {"franking_rate": 0, "sector": "Technology", "reliability": "high"},
            "APT": {"franking_rate": 0, "sector": "Technology", "reliability": "high"},
            "WTC": {"franking_rate": 0, "sector": "Technology", "reliability": "high"},
            "NXT": {
                "franking_rate": 0,
                "sector": "Technology",
                "reliability": "medium",
            },
            # Healthcare - Mixed
            "COH": {
                "franking_rate": 100,
                "sector": "Healthcare",
                "reliability": "high",
            },
            "RHC": {
                "franking_rate": 100,
                "sector": "Healthcare",
                "reliability": "medium",
            },
            "SHL": {
                "franking_rate": 100,
                "sector": "Healthcare",
                "reliability": "medium",
            },
            # Industrial - Usually 100% franked
            "TCL": {
                "franking_rate": 100,
                "sector": "Industrials",
                "reliability": "high",
            },
            "ALL": {
                "franking_rate": 100,
                "sector": "Industrials",
                "reliability": "high",
            },
            "BXB": {
                "franking_rate": 100,
                "sector": "Industrials",
                "reliability": "medium",
            },
            # Energy - Usually 100% franked
            "WPL": {"franking_rate": 100, "sector": "Energy", "reliability": "high"},
            "STO": {"franking_rate": 100, "sector": "Energy", "reliability": "high"},
            "OSH": {"franking_rate": 100, "sector": "Energy", "reliability": "medium"},
            # Consumer Discretionary - Mixed
            "JBH": {
                "franking_rate": 100,
                "sector": "Consumer Discretionary",
                "reliability": "high",
            },
            "HVN": {
                "franking_rate": 100,
                "sector": "Consumer Discretionary",
                "reliability": "high",
            },
            "SUL": {
                "franking_rate": 100,
                "sector": "Consumer Discretionary",
                "reliability": "medium",
            },
            # LICs/LITs - Usually 100% franked
            "AFI": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "ARG": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "MLT": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "WAM": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "WAX": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            # Additional stocks with proper sector classifications
            "HLI": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },  # Helia Group - Mortgage Insurance
            "YMAX": {
                "franking_rate": 70,
                "sector": "Financials",
                "reliability": "medium",
            },  # BetaShares YMAX ETF - Yield Maximizer
            "LNW": {
                "franking_rate": 0,
                "sector": "Consumer Discretionary",
                "reliability": "high",
            },  # Light & Wonder - Gaming/Entertainment
            "DTR": {
                "franking_rate": 0,
                "sector": "Materials",
                "reliability": "medium",
            },  # Dateline Resources Ltd - Mining/Mineral Exploration
            "SDR": {
                "franking_rate": 0,
                "sector": "Technology",
                "reliability": "high",
            },  # SiteMinder Ltd - SaaS/Technology
            "PME": {
                "franking_rate": 100,
                "sector": "Healthcare",
                "reliability": "high",
            },  # Pro Medicus - Medical Imaging Software
            # ETFs - Variable
            "VAS": {
                "franking_rate": 70,
                "sector": "Financials",
                "reliability": "medium",
            },
            "VTS": {"franking_rate": 0, "sector": "Financials", "reliability": "high"},
            "VEU": {"franking_rate": 0, "sector": "Financials", "reliability": "high"},
            "IOZ": {
                "franking_rate": 70,
                "sector": "Financials",
                "reliability": "medium",
            },
            # Other major stocks
            "MQG": {
                "franking_rate": 100,
                "sector": "Financials",
                "reliability": "high",
            },
            "REA": {
                "franking_rate": 100,
                "sector": "Technology",
                "reliability": "high",
            },
            "CAR": {
                "franking_rate": 100,
                "sector": "Technology",
                "reliability": "medium",
            },
            "SEK": {
                "franking_rate": 100,
                "sector": "Technology",
                "reliability": "medium",
            },
        }

    def get_franking_rate(self, stock: str) -> float:
        """Get franking rate for a stock (0-100)"""
        return self.franking_data.get(stock, {}).get(
            "franking_rate", 50.0
        )  # Default 50%

    def get_sector(self, stock: str) -> str:
        """Get sector for a stock"""
        return self.franking_data.get(stock, {}).get("sector", "Unknown")

    def get_reliability(self, stock: str) -> str:
        """Get reliability rating for franking data"""
        return self.franking_data.get(stock, {}).get("reliability", "low")

    def get_franking_info(self, stock: str) -> Dict:
        """Get complete franking information for a stock"""
        if stock in self.franking_data:
            data = self.franking_data[stock].copy()
            data["stock"] = stock
            return data
        else:
            # Estimate based on sector patterns
            return {
                "stock": stock,
                "franking_rate": 50.0,  # Conservative estimate
                "sector": "Unknown",
                "reliability": "estimated",
            }

    def update_franking_from_api(
        self, stock: str, api_key: Optional[str] = None
    ) -> Optional[Dict]:
        """Update franking information from ASX announcements API"""
        try:
            # Try to get recent dividend announcements for the stock
            announcements = self._fetch_recent_announcements(stock, api_key)

            if announcements:
                franking_info = self._parse_franking_from_announcements(announcements)
                if franking_info:
                    # Update static database with API data
                    self.franking_data[stock] = {
                        "franking_rate": franking_info["franking_rate"],
                        "sector": franking_info.get(
                            "sector",
                            self.franking_data.get(stock, {}).get("sector", "Unknown"),
                        ),
                        "reliability": "api_updated",
                    }
                    return franking_info

            # If no API data available, show demo mode message
            print(f"⚠️  No API data available for {stock} - using static database")

        except Exception as e:
            print(f"API update failed for {stock}: {e}")

        return None

    def _fetch_recent_announcements(
        self, stock: str, api_key: Optional[str] = None
    ) -> List[Dict]:
        """Fetch recent ASX announcements for a stock using web scraping approach"""
        try:
            # Method 1: Try ASX undocumented API
            url = f"https://asx.api.markitdigital.com/asx-research/1.0/companies/{stock}/announcements"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
                "Referer": "https://www.asx.com.au/",
            }

            params: Dict[str, str] = {"access_token": "anonymous", "limit": "20"}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            # Handle both JSON and string responses
            try:
                data = response.json()
                if isinstance(data, dict):
                    announcements = data.get("data", [])
                else:
                    print(f"Unexpected response format for {stock}")
                    return []
            except ValueError:
                print(f"Non-JSON response for {stock}")
                return []

            # Filter for recent dividend-related announcements
            recent_announcements = []
            for announcement in announcements:
                if isinstance(announcement, dict):
                    title = announcement.get("title", "").lower()
                    if any(
                        keyword in title
                        for keyword in [
                            "dividend",
                            "distribution",
                            "franking",
                            "interim",
                            "final",
                        ]
                    ):
                        recent_announcements.append(announcement)

            return recent_announcements

        except requests.exceptions.RequestException as e:
            print(f"Network error fetching announcements for {stock}: {e}")
            return []
        except Exception as e:
            print(f"Error fetching announcements for {stock}: {e}")
            return []

    def _parse_franking_from_announcements(
        self, announcements: List[Dict]
    ) -> Optional[Dict]:
        """Parse franking information from ASX announcements"""
        for announcement in announcements:
            # Handle different announcement formats
            text = announcement.get("text", announcement.get("summary", "")).lower()
            title = announcement.get("title", announcement.get("header", "")).lower()

            # Combine text and title for comprehensive search
            combined_text = f"{title} {text}"

            # Look for dividend and franking keywords
            if any(
                keyword in combined_text
                for keyword in ["dividend", "franking", "franked", "distribution"]
            ):
                # Extract franking percentage using regex patterns
                franking_patterns = [
                    r"(\d+)%\s*franked",
                    r"franked\s*(\d+)%",
                    r"franking\s*rate\s*(\d+)%",
                    r"franking\s*credit\s*(\d+)%",
                    r"fully\s*franked",  # Implies 100%
                    r"unfranked",  # Implies 0%
                    r"no\s*franking",  # Implies 0%
                ]

                for pattern in franking_patterns:
                    match = re.search(pattern, combined_text)
                    if match:
                        if "fully" in pattern:
                            franking_rate = 100.0
                        elif "unfranked" in pattern or "no" in pattern:
                            franking_rate = 0.0
                        else:
                            franking_rate = float(match.group(1))

                        print(
                            f"Found franking info: {franking_rate}% from announcement: {title[:50]}..."
                        )

                        return {
                            "franking_rate": franking_rate,
                            "last_updated": datetime.now().strftime("%Y-%m-%d"),
                            "source": "asx_announcement",
                            "announcement_title": title,
                        }

        return None

    def get_sector_average_franking(self, sector: str) -> float:
        """Get average franking rate for a sector"""
        sector_stocks = [
            data for data in self.franking_data.values() if data["sector"] == sector
        ]
        if sector_stocks:
            return sum(stock["franking_rate"] for stock in sector_stocks) / len(
                sector_stocks
            )
        return 50.0  # Default

    def bulk_update_franking_from_api(
        self, stocks: List[str], api_key: Optional[str] = None
    ) -> Dict[str, Dict]:
        """Bulk update franking information for multiple stocks"""
        results = {}

        print("🔄 Attempting to update franking data from live sources...")
        print("📊 Note: This is a demonstration of API integration capability")
        print("🔗 In production, this would connect to real ASX announcement feeds")
        print()

        for stock in stocks:
            print(f"Updating franking data for {stock}...")
            result = self.update_franking_from_api(stock, api_key)
            if result:
                results[stock] = result
                print(f"✅ Updated {stock}: {result['franking_rate']}% franked")
            else:
                # Show current static data info
                current_info = self.get_franking_info(stock)
                print(
                    f"📋 Static data: {current_info['franking_rate']}% franked ({current_info['reliability']})"
                )

        if not results:
            print("\n💡 Demo Mode: The API integration framework is ready!")
            print("🎯 To enable live updates, configure access to:")
            print("   • ASX MarketSource API")
            print("   • Company announcement feeds")
            print("   • Third-party dividend data providers")
            print(
                "\n📈 Current system uses high-quality static data for 50+ major stocks"
            )

        return results


class FrankingTaxCalculator:
    """Calculate franking credit tax benefits for Australian investors"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.franking_db = StaticFrankingDatabase()

        # Australian tax brackets for 2024-25
        self.tax_brackets = [
            (18200, 0.0),  # Tax-free threshold
            (45000, 0.19),  # 19% tax bracket
            (120000, 0.325),  # 32.5% tax bracket
            (180000, 0.37),  # 37% tax bracket
            (float("inf"), 0.45),  # 45% tax bracket
        ]

        self.medicare_levy_rate = 0.02  # 2% Medicare levy
        self.company_tax_rate = 0.30  # 30% company tax rate

    def get_tax_bracket(self, taxable_income: float) -> float:
        """Get marginal tax rate for given income"""
        for threshold, rate in self.tax_brackets:
            if taxable_income <= threshold:
                return rate * 100  # Return as percentage
        return 45.0  # Top bracket

    def calculate_tax_on_income(self, taxable_income: float) -> float:
        """Calculate total tax on income including Medicare levy"""
        if taxable_income <= 18200:
            return 0.0

        tax = 0.0
        previous_threshold = 0.0

        for threshold, rate in self.tax_brackets:
            if taxable_income <= threshold:
                tax += (taxable_income - previous_threshold) * rate
                break
            else:
                tax += (threshold - previous_threshold) * rate
                previous_threshold = float(threshold)

        # Add Medicare levy (simplified - no low income thresholds)
        if taxable_income > 23226:  # Medicare levy threshold 2024-25
            medicare_levy = taxable_income * self.medicare_levy_rate
            tax += medicare_levy

        return tax

    def calculate_franking_benefit(
        self,
        positions: Dict,
        taxable_income: float = 85000,
        estimated_yield: float = 0.04,
    ) -> Dict:
        """Calculate franking credit tax benefit for portfolio"""

        total_dividend_income = 0.0
        total_franking_credits = 0.0
        stock_details = []

        for stock, position in positions.items():
            # Get franking information
            franking_info = self.franking_db.get_franking_info(stock)
            franking_rate = franking_info["franking_rate"] / 100

            # Estimate annual dividend income
            market_value = getattr(position, "market_value", 0)
            if market_value == 0:
                market_value = getattr(position, "quantity", 0) * getattr(
                    position, "current_price", 0
                )

            annual_dividend = market_value * estimated_yield

            # Calculate franking credits
            # Franking credit = (dividend × franking rate × company tax rate) / (1 - company tax rate)
            franking_credit = (
                annual_dividend * franking_rate * self.company_tax_rate
            ) / (1 - self.company_tax_rate)

            total_dividend_income += annual_dividend
            total_franking_credits += franking_credit

            # Calculate effective yield including franking
            effective_yield = (
                (annual_dividend + franking_credit) / market_value * 100
                if market_value > 0
                else 0
            )

            stock_details.append(
                {
                    "stock": stock,
                    "market_value": market_value,
                    "annual_dividend": annual_dividend,
                    "franking_rate": franking_info["franking_rate"],
                    "franking_credit": franking_credit,
                    "effective_yield": effective_yield,
                    "sector": franking_info["sector"],
                    "reliability": franking_info["reliability"],
                }
            )

        # Calculate tax scenarios
        marginal_tax_rate = self.get_tax_bracket(taxable_income) / 100

        # Scenario 1: Without franking credits
        tax_without_franking = self.calculate_tax_on_income(
            taxable_income + total_dividend_income
        )
        tax_on_other_income = self.calculate_tax_on_income(taxable_income)
        tax_on_dividends_without_franking = tax_without_franking - tax_on_other_income

        # Scenario 2: With franking credits
        assessable_income = (
            taxable_income + total_dividend_income + total_franking_credits
        )
        total_tax_before_franking = self.calculate_tax_on_income(assessable_income)
        tax_after_franking_offset = max(
            0.0, total_tax_before_franking - total_franking_credits
        )

        # Calculate benefit
        tax_benefit = tax_without_franking - tax_after_franking_offset
        franking_refund = max(0.0, total_franking_credits - total_tax_before_franking)

        # Calculate effective tax rate on dividend income
        effective_tax_rate = (
            (
                (
                    total_dividend_income
                    + total_franking_credits
                    - tax_benefit
                    - franking_refund
                )
                / (total_dividend_income + total_franking_credits)
                * 100
            )
            if (total_dividend_income + total_franking_credits) > 0
            else 0.0
        )

        return {
            "total_dividend_income": total_dividend_income,
            "total_franking_credits": total_franking_credits,
            "assessable_income": total_dividend_income + total_franking_credits,
            "tax_benefit": tax_benefit,
            "franking_refund": franking_refund,
            "net_benefit": tax_benefit + franking_refund,
            "effective_tax_rate": effective_tax_rate,
            "marginal_tax_rate": marginal_tax_rate * 100,
            "franking_efficiency": (
                (total_franking_credits / total_dividend_income * 100)
                if total_dividend_income > 0
                else 0
            ),
            "stock_details": stock_details,
            "calculation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def get_optimization_suggestions(
        self, positions: Dict, taxable_income: float = 85000
    ) -> List[Dict]:
        """Get suggestions for optimizing franking credits"""
        suggestions = []

        current_franking = self.calculate_franking_benefit(positions, taxable_income)

        # Find low-franking stocks that could be replaced
        for stock_detail in current_franking["stock_details"]:
            if (
                stock_detail["franking_rate"] < 50
                and stock_detail["market_value"] > 1000
            ):
                # Suggest high-franking alternatives in same sector
                sector = stock_detail["sector"]
                high_franking_stocks = [
                    stock
                    for stock, data in self.franking_db.franking_data.items()
                    if data["sector"] == sector and data["franking_rate"] >= 80
                ]

                if high_franking_stocks:
                    suggestions.append(
                        {
                            "type": "replace_low_franking",
                            "current_stock": stock_detail["stock"],
                            "current_franking": stock_detail["franking_rate"],
                            "suggested_alternatives": high_franking_stocks[:3],
                            "potential_benefit": stock_detail["market_value"]
                            * 0.04
                            * 0.3,  # Rough estimate
                            "priority": (
                                "high"
                                if stock_detail["market_value"] > 5000
                                else "medium"
                            ),
                        }
                    )

        # Suggest increasing high-franking positions
        high_franking_stocks = [
            detail
            for detail in current_franking["stock_details"]
            if detail["franking_rate"] >= 80
        ]

        if high_franking_stocks:
            best_franking_stock = max(
                high_franking_stocks, key=lambda x: x["franking_rate"]
            )
            suggestions.append(
                {
                    "type": "increase_high_franking",
                    "stock": best_franking_stock["stock"],
                    "current_franking": best_franking_stock["franking_rate"],
                    "suggested_increase": 5000,  # Suggest $5k increase
                    "potential_benefit": 5000
                    * 0.04
                    * (best_franking_stock["franking_rate"] / 100)
                    * 0.3,
                    "priority": "medium",
                }
            )

        return suggestions


def get_yahoo_dividend_data(stock: str) -> Dict:
    """Get basic dividend data from Yahoo Finance (optional integration)"""
    try:
        import yfinance as yf  # type: ignore

        ticker = yf.Ticker(f"{stock}.AX")
        info = ticker.info

        return {
            "dividend_yield": (
                info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0
            ),
            "trailing_annual_dividend": info.get("trailingAnnualDividendRate", 0),
            "ex_dividend_date": info.get("exDividendDate", None),
            "payout_ratio": info.get("payoutRatio", 0),
        }
    except Exception as e:
        print(f"Yahoo Finance error for {stock}: {e}")
        return {
            "dividend_yield": 0,
            "trailing_annual_dividend": 0,
            "ex_dividend_date": None,
            "payout_ratio": 0,
        }


if __name__ == "__main__":
    # Test the franking calculator
    calculator = FrankingTaxCalculator("test.db")

    # Test data
    test_positions = {
        "CBA": type(
            "Position",
            (),
            {"market_value": 10000, "quantity": 50, "current_price": 200},
        )(),
        "CSL": type(
            "Position", (), {"market_value": 5000, "quantity": 20, "current_price": 250}
        )(),
        "BHP": type(
            "Position", (), {"market_value": 8000, "quantity": 200, "current_price": 40}
        )(),
    }

    result = calculator.calculate_franking_benefit(test_positions, taxable_income=85000)

    print("=== Franking Credit Analysis ===")
    print(f"Total Dividend Income: ${result['total_dividend_income']:,.2f}")
    print(f"Total Franking Credits: ${result['total_franking_credits']:,.2f}")
    print(f"Tax Benefit: ${result['tax_benefit']:,.2f}")
    print(f"Franking Refund: ${result['franking_refund']:,.2f}")
    print(f"Net Benefit: ${result['net_benefit']:,.2f}")
    print(f"Franking Efficiency: {result['franking_efficiency']:.1f}%")
