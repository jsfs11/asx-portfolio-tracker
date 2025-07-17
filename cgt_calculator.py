#!/usr/bin/env python3
"""
Capital Gains Tax (CGT) Calculator for ASX Portfolio Tracker
Implements Australian CGT rules including discounts and loss offsetting
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class CGTEvent:
    """Represents a CGT event (sale of shares)"""
    stock: str
    sale_date: str
    quantity: int
    sale_price: float
    sale_total: float
    cost_base: float
    acquisition_date: str
    capital_gain: float
    discount_eligible: bool
    discounted_gain: float
    method: str  # 'FIFO', 'LIFO', 'Specific'


@dataclass
class CGTSummary:
    """Annual CGT summary for tax return"""
    tax_year: str
    total_capital_gains: float
    total_capital_losses: float
    discount_eligible_gains: float
    discounted_gains: float
    net_capital_gain: float
    carried_forward_losses: float


class CGTCalculator:
    """Calculate Capital Gains Tax for Australian investors"""
    
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_cgt_tables()
        
        # CGT parameters
        self.cgt_discount_rate = 0.5  # 50% discount
        self.cgt_holding_period_days = 365  # 12 months for discount
        
    def init_cgt_tables(self):
        """Initialize CGT-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # CGT events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cgt_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_year TEXT NOT NULL,
                stock TEXT NOT NULL,
                sale_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                sale_price REAL NOT NULL,
                sale_total REAL NOT NULL,
                cost_base REAL NOT NULL,
                acquisition_date TEXT NOT NULL,
                capital_gain REAL NOT NULL,
                discount_eligible BOOLEAN NOT NULL,
                discounted_gain REAL NOT NULL,
                method TEXT NOT NULL,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tax parcels table (for tracking individual purchases)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_parcels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock TEXT NOT NULL,
                acquisition_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                remaining_quantity INTEGER NOT NULL,
                unit_cost REAL NOT NULL,
                total_cost REAL NOT NULL,
                brokerage REAL NOT NULL,
                cost_base REAL NOT NULL,
                sold BOOLEAN DEFAULT 0
            )
        ''')
        
        # Capital losses carried forward
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS capital_losses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_year TEXT NOT NULL,
                loss_amount REAL NOT NULL,
                remaining_loss REAL NOT NULL,
                source TEXT,
                UNIQUE(tax_year)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_tax_parcels_from_transactions(self):
        """Convert existing transactions into tax parcels and process historical sales"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing CGT data to rebuild from scratch
        cursor.execute('DELETE FROM cgt_events')
        cursor.execute('DELETE FROM tax_parcels')
        cursor.execute('DELETE FROM capital_losses')
        
        # Get all transactions ordered by date
        cursor.execute('''
            SELECT date, stock, action, quantity, price, total, fees
            FROM transactions
            WHERE status = 'executed'
            ORDER BY date ASC, id ASC
        ''')
        
        transactions = cursor.fetchall()
        
        for transaction in transactions:
            date, stock, action, quantity, price, total, fees = transaction
            
            if action == 'buy':
                # Create new tax parcel
                unit_cost = price
                cost_base = total + fees  # Include brokerage in cost base
                
                cursor.execute('''
                    INSERT INTO tax_parcels
                    (stock, acquisition_date, quantity, remaining_quantity, 
                     unit_cost, total_cost, brokerage, cost_base)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (stock, date, quantity, quantity, unit_cost, 
                      total, fees, cost_base))
                      
            elif action == 'sell':
                # Process the sale and create CGT events
                try:
                    # Calculate CGT for this sale
                    sale_events = self._calculate_cgt_for_historical_sale(
                        cursor, stock, date, quantity, price, 'FIFO'
                    )
                    
                    # Store CGT events
                    tax_year = self.get_tax_year(date)
                    
                    for event in sale_events:
                        cursor.execute('''
                            INSERT INTO cgt_events
                            (tax_year, stock, sale_date, quantity, sale_price, sale_total,
                             cost_base, acquisition_date, capital_gain, discount_eligible,
                             discounted_gain, method)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (tax_year, event.stock, event.sale_date, event.quantity,
                              event.sale_price, event.sale_total, event.cost_base,
                              event.acquisition_date, event.capital_gain,
                              event.discount_eligible, event.discounted_gain, event.method))
                              
                except Exception as e:
                    print(f"Warning: Could not process sale of {quantity} {stock} on {date}: {e}")
                    continue
        
        conn.commit()
        conn.close()
    
    def _calculate_cgt_for_historical_sale(self, cursor, stock: str, sale_date: str, 
                                         quantity: int, sale_price: float,
                                         method: str = 'FIFO') -> List[CGTEvent]:
        """Calculate CGT for a historical sale using available parcels"""
        
        # Get available tax parcels for this stock up to the sale date
        if method == 'FIFO':
            order = 'acquisition_date ASC'
        elif method == 'LIFO':
            order = 'acquisition_date DESC'
        else:
            order = 'acquisition_date ASC'
        
        cursor.execute(f'''
            SELECT id, acquisition_date, remaining_quantity, cost_base, quantity
            FROM tax_parcels
            WHERE stock = ? AND remaining_quantity > 0 AND acquisition_date <= ?
            ORDER BY {order}
        ''', (stock, sale_date))
        
        parcels = cursor.fetchall()
        
        if not parcels:
            raise ValueError(f"No tax parcels found for {stock} before {sale_date}")
        
        cgt_events = []
        remaining_to_sell = quantity
        sale_total = quantity * sale_price
        
        for parcel in parcels:
            if remaining_to_sell <= 0:
                break
            
            parcel_id, acq_date, available_qty, parcel_cost_base, original_qty = parcel
            
            # Calculate how many shares to take from this parcel
            shares_from_parcel = min(remaining_to_sell, available_qty)
            
            # Calculate proportional cost base
            proportion = shares_from_parcel / original_qty
            proportional_cost_base = parcel_cost_base * proportion
            
            # Calculate capital gain
            sale_proceeds = shares_from_parcel * sale_price
            capital_gain = sale_proceeds - proportional_cost_base
            
            # Check if eligible for CGT discount
            holding_period = (datetime.strptime(sale_date, '%Y-%m-%d') - 
                            datetime.strptime(acq_date, '%Y-%m-%d')).days
            
            discount_eligible = holding_period > self.cgt_holding_period_days
            
            # Apply discount if eligible and gain is positive
            if discount_eligible and capital_gain > 0:
                discounted_gain = capital_gain * (1 - self.cgt_discount_rate)
            else:
                discounted_gain = capital_gain
            
            # Create CGT event
            event = CGTEvent(
                stock=stock,
                sale_date=sale_date,
                quantity=shares_from_parcel,
                sale_price=sale_price,
                sale_total=sale_proceeds,
                cost_base=proportional_cost_base,
                acquisition_date=acq_date,
                capital_gain=capital_gain,
                discount_eligible=discount_eligible,
                discounted_gain=discounted_gain,
                method=method
            )
            
            cgt_events.append(event)
            
            # Update tax parcel
            new_remaining = available_qty - shares_from_parcel
            cursor.execute('''
                UPDATE tax_parcels
                SET remaining_quantity = ?, sold = ?
                WHERE id = ?
            ''', (new_remaining, new_remaining == 0, parcel_id))
            
            remaining_to_sell -= shares_from_parcel
        
        if remaining_to_sell > 0:
            raise ValueError(f"Insufficient shares available for {stock}. Need {quantity}, but only {quantity - remaining_to_sell} available before {sale_date}.")
        
        return cgt_events
    
    def calculate_cgt_for_sale(self, stock: str, sale_date: str, 
                               quantity: int, sale_price: float,
                               method: str = 'FIFO') -> List[CGTEvent]:
        """Calculate CGT for a share sale using specified method"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get available tax parcels
        if method == 'FIFO':
            order = 'acquisition_date ASC'
        elif method == 'LIFO':
            order = 'acquisition_date DESC'
        else:  # Specific identification would need UI to select parcels
            order = 'acquisition_date ASC'
        
        cursor.execute(f'''
            SELECT id, acquisition_date, remaining_quantity, cost_base, quantity
            FROM tax_parcels
            WHERE stock = ? AND remaining_quantity > 0
            ORDER BY {order}
        ''', (stock,))
        
        parcels = cursor.fetchall()
        
        if not parcels:
            conn.close()
            raise ValueError(f"No tax parcels found for {stock}")
        
        cgt_events = []
        remaining_to_sell = quantity
        sale_total = quantity * sale_price
        
        for parcel in parcels:
            if remaining_to_sell <= 0:
                break
            
            parcel_id, acq_date, available_qty, parcel_cost_base, original_qty = parcel
            
            # Calculate how many shares to take from this parcel
            shares_from_parcel = min(remaining_to_sell, available_qty)
            
            # Calculate proportional cost base
            proportion = shares_from_parcel / original_qty
            proportional_cost_base = parcel_cost_base * proportion
            
            # Calculate capital gain
            sale_proceeds = shares_from_parcel * sale_price
            capital_gain = sale_proceeds - proportional_cost_base
            
            # Check if eligible for CGT discount
            holding_period = (datetime.strptime(sale_date, '%Y-%m-%d') - 
                            datetime.strptime(acq_date, '%Y-%m-%d')).days
            
            discount_eligible = holding_period > self.cgt_holding_period_days
            
            # Apply discount if eligible and gain is positive
            if discount_eligible and capital_gain > 0:
                discounted_gain = capital_gain * (1 - self.cgt_discount_rate)
            else:
                discounted_gain = capital_gain
            
            # Create CGT event
            event = CGTEvent(
                stock=stock,
                sale_date=sale_date,
                quantity=shares_from_parcel,
                sale_price=sale_price,
                sale_total=sale_proceeds,
                cost_base=proportional_cost_base,
                acquisition_date=acq_date,
                capital_gain=capital_gain,
                discount_eligible=discount_eligible,
                discounted_gain=discounted_gain,
                method=method
            )
            
            cgt_events.append(event)
            
            # Update tax parcel
            new_remaining = available_qty - shares_from_parcel
            cursor.execute('''
                UPDATE tax_parcels
                SET remaining_quantity = ?, sold = ?
                WHERE id = ?
            ''', (new_remaining, new_remaining == 0, parcel_id))
            
            remaining_to_sell -= shares_from_parcel
        
        if remaining_to_sell > 0:
            conn.close()
            raise ValueError(f"Insufficient shares available. Need {quantity}, but only {quantity - remaining_to_sell} available.")
        
        # Store CGT events
        tax_year = self.get_tax_year(sale_date)
        
        for event in cgt_events:
            cursor.execute('''
                INSERT INTO cgt_events
                (tax_year, stock, sale_date, quantity, sale_price, sale_total,
                 cost_base, acquisition_date, capital_gain, discount_eligible,
                 discounted_gain, method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (tax_year, event.stock, event.sale_date, event.quantity,
                  event.sale_price, event.sale_total, event.cost_base,
                  event.acquisition_date, event.capital_gain,
                  event.discount_eligible, event.discounted_gain, event.method))
        
        conn.commit()
        conn.close()
        
        return cgt_events
    
    def get_tax_year(self, date_str: str) -> str:
        """Get Australian tax year for a given date"""
        date = datetime.strptime(date_str, '%Y-%m-%d')
        if date.month >= 7:
            return f"{date.year}-{date.year + 1}"
        else:
            return f"{date.year - 1}-{date.year}"
    
    def calculate_annual_cgt(self, tax_year: str) -> CGTSummary:
        """Calculate total CGT for a tax year"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all CGT events for the tax year
        cursor.execute('''
            SELECT capital_gain, discount_eligible, discounted_gain
            FROM cgt_events
            WHERE tax_year = ?
        ''', (tax_year,))
        
        events = cursor.fetchall()
        
        total_gains = 0
        total_losses = 0
        discount_eligible_gains = 0
        discounted_gains = 0
        
        for capital_gain, is_discount_eligible, discounted_gain in events:
            if capital_gain > 0:
                total_gains += capital_gain
                if is_discount_eligible:
                    discount_eligible_gains += capital_gain
                    discounted_gains += discounted_gain
                else:
                    discounted_gains += capital_gain
            else:
                total_losses += abs(capital_gain)
        
        # Get carried forward losses
        cursor.execute('''
            SELECT SUM(remaining_loss) FROM capital_losses
            WHERE remaining_loss > 0
        ''')
        
        carried_losses = cursor.fetchone()[0] or 0
        
        # Calculate net capital gain
        # First offset current year losses against gains
        current_year_net = discounted_gains - total_losses
        
        # Then apply carried forward losses
        if current_year_net > 0:
            net_capital_gain = max(0, current_year_net - carried_losses)
            used_carried_losses = min(carried_losses, current_year_net)
            
            # Update carried forward losses
            if used_carried_losses > 0:
                cursor.execute('''
                    UPDATE capital_losses
                    SET remaining_loss = remaining_loss - ?
                    WHERE remaining_loss > 0
                ''', (used_carried_losses,))
        else:
            net_capital_gain = 0
            # Add to carried forward losses if net loss
            if current_year_net < 0:
                cursor.execute('''
                    INSERT OR REPLACE INTO capital_losses
                    (tax_year, loss_amount, remaining_loss, source)
                    VALUES (?, ?, ?, 'Current Year')
                ''', (tax_year, abs(current_year_net), abs(current_year_net)))
        
        conn.commit()
        conn.close()
        
        return CGTSummary(
            tax_year=tax_year,
            total_capital_gains=total_gains,
            total_capital_losses=total_losses,
            discount_eligible_gains=discount_eligible_gains,
            discounted_gains=discounted_gains,
            net_capital_gain=net_capital_gain,
            carried_forward_losses=carried_losses - (used_carried_losses if current_year_net > 0 else 0)
        )
    
    def get_unrealised_gains(self, current_prices: Dict[str, float]) -> List[Dict]:
        """Calculate unrealised gains for current holdings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all parcels with remaining shares
        cursor.execute('''
            SELECT stock, acquisition_date, remaining_quantity, 
                   cost_base, quantity
            FROM tax_parcels
            WHERE remaining_quantity > 0
        ''')
        
        parcels = cursor.fetchall()
        conn.close()
        
        unrealised = []
        
        for stock, acq_date, remaining_qty, cost_base, original_qty in parcels:
            if stock in current_prices:
                # Calculate proportional cost base
                proportion = remaining_qty / original_qty
                proportional_cost_base = cost_base * proportion
                
                # Calculate unrealised gain
                current_value = remaining_qty * current_prices[stock]
                unrealised_gain = current_value - proportional_cost_base
                
                # Check CGT discount eligibility
                holding_days = (datetime.now() - 
                              datetime.strptime(acq_date, '%Y-%m-%d')).days
                discount_eligible = holding_days > self.cgt_holding_period_days
                
                unrealised.append({
                    'stock': stock,
                    'acquisition_date': acq_date,
                    'quantity': remaining_qty,
                    'cost_base': proportional_cost_base,
                    'current_value': current_value,
                    'unrealised_gain': unrealised_gain,
                    'holding_period_days': holding_days,
                    'discount_eligible': discount_eligible,
                    'after_discount': unrealised_gain * 0.5 if discount_eligible and unrealised_gain > 0 else unrealised_gain
                })
        
        return unrealised
    
    def optimize_cgt_sale(self, stock: str, target_gain: float, 
                         current_price: float) -> List[Dict]:
        """Suggest which parcels to sell to achieve target capital gain"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all available parcels
        cursor.execute('''
            SELECT id, acquisition_date, remaining_quantity, cost_base, quantity
            FROM tax_parcels
            WHERE stock = ? AND remaining_quantity > 0
            ORDER BY acquisition_date ASC
        ''', (stock,))
        
        parcels = cursor.fetchall()
        conn.close()
        
        suggestions = []
        
        for parcel in parcels:
            parcel_id, acq_date, available_qty, parcel_cost_base, original_qty = parcel
            
            # Calculate gain per share
            cost_per_share = parcel_cost_base / original_qty
            gain_per_share = current_price - cost_per_share
            
            # Check discount eligibility
            holding_days = (datetime.now() - 
                          datetime.strptime(acq_date, '%Y-%m-%d')).days
            discount_eligible = holding_days > self.cgt_holding_period_days
            
            effective_gain_per_share = gain_per_share * 0.5 if discount_eligible and gain_per_share > 0 else gain_per_share
            
            suggestions.append({
                'parcel_id': parcel_id,
                'acquisition_date': acq_date,
                'available_quantity': available_qty,
                'cost_per_share': cost_per_share,
                'gain_per_share': gain_per_share,
                'discount_eligible': discount_eligible,
                'effective_gain_per_share': effective_gain_per_share,
                'shares_for_target': int(target_gain / effective_gain_per_share) if effective_gain_per_share > 0 else 0
            })
        
        return sorted(suggestions, key=lambda x: x['effective_gain_per_share'])


def generate_cgt_report(calculator: CGTCalculator, tax_year: str):
    """Generate comprehensive CGT report"""
    
    print(f"\n{'='*60}")
    print(f"CAPITAL GAINS TAX REPORT - {tax_year}")
    print(f"{'='*60}\n")
    
    # Get annual summary
    summary = calculator.calculate_annual_cgt(tax_year)
    
    print("SUMMARY:")
    print(f"Total Capital Gains:        ${summary.total_capital_gains:,.2f}")
    print(f"Total Capital Losses:       ${summary.total_capital_losses:,.2f}")
    print(f"Discount Eligible Gains:    ${summary.discount_eligible_gains:,.2f}")
    print(f"After CGT Discount:         ${summary.discounted_gains:,.2f}")
    print(f"Carried Forward Losses:     ${summary.carried_forward_losses:,.2f}")
    print(f"\nNET CAPITAL GAIN:          ${summary.net_capital_gain:,.2f}")
    
    # Get detailed events
    conn = sqlite3.connect(calculator.db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT stock, sale_date, quantity, sale_price, capital_gain,
               discount_eligible, discounted_gain, acquisition_date
        FROM cgt_events
        WHERE tax_year = ?
        ORDER BY sale_date
    ''', (tax_year,))
    
    events = cursor.fetchall()
    conn.close()
    
    if events:
        print(f"\nDETAILED CGT EVENTS:")
        print(f"{'Date':<12} {'Stock':<6} {'Qty':<6} {'Gain/Loss':<12} {'Discounted':<12} {'Held':<10}")
        print("-" * 70)
        
        for event in events:
            stock, sale_date, qty, price, gain, eligible, discounted, acq_date = event
            holding_days = (datetime.strptime(sale_date, '%Y-%m-%d') - 
                          datetime.strptime(acq_date, '%Y-%m-%d')).days
            
            print(f"{sale_date:<12} {stock:<6} {qty:<6} "
                  f"${gain:>10.2f} ${discounted:>10.2f} "
                  f"{holding_days:>6}d {'✓' if eligible else ''}")


if __name__ == "__main__":
    # Example usage
    calculator = CGTCalculator()
    
    # Initialize tax parcels from existing transactions
    calculator.create_tax_parcels_from_transactions()
    
    # Example: Calculate CGT for a sale
    try:
        events = calculator.calculate_cgt_for_sale(
            stock='CBA',
            sale_date='2025-08-01',
            quantity=4,
            sale_price=200.00,
            method='FIFO'
        )
        
        for event in events:
            print(f"CGT Event: Sold {event.quantity} {event.stock}")
            print(f"  Capital Gain: ${event.capital_gain:.2f}")
            print(f"  After Discount: ${event.discounted_gain:.2f}")
            print(f"  Held for: {(datetime.strptime(event.sale_date, '%Y-%m-%d') - datetime.strptime(event.acquisition_date, '%Y-%m-%d')).days} days")
        
    except ValueError as e:
        print(f"Error: {e}")
    
    # Generate annual report
    generate_cgt_report(calculator, '2025-2026')