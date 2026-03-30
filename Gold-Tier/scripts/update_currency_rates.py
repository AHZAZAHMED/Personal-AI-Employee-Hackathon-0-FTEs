"""
Currency Rate Updater for AI Employee

Fetches live exchange rates from European Central Bank (free API).
Updates CURRENCY_RATES in email_to_invoice.py

Usage:
    python scripts/update_currency_rates.py
"""

import requests
import json
from datetime import datetime
from pathlib import Path


def fetch_ecb_rates():
    """
    Fetch latest exchange rates from European Central Bank.
    Free API, no authentication required.
    
    Returns:
        Dictionary of currency rates relative to EUR
    """
    try:
        # ECB API endpoint
        url = "https://api.exchangerate.host/latest?base=EUR"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' in data:
            print(f"✅ Fetched rates from ECB ({data.get('date', 'today')})")
            return data['rates']
        else:
            print("⚠️  No rates in response")
            return None
            
    except Exception as e:
        print(f"❌ Failed to fetch ECB rates: {e}")
        return None


def convert_to_usd_base(eur_rates):
    """
    Convert EUR-based rates to USD-based rates.
    
    Args:
        eur_rates: Dictionary of rates relative to EUR
        
    Returns:
        Dictionary of rates relative to USD
    """
    if not eur_rates:
        return None
    
    # Get EUR to USD rate
    eur_usd = eur_rates.get('USD', 1.08)  # Default if missing
    
    # Convert all rates to USD base
    usd_rates = {}
    
    for currency, rate in eur_rates.items():
        # Convert: 1 EUR = rate units of currency
        # We want: 1 currency = ? USD
        # Formula: (1 / rate) * eur_usd
        if currency == 'USD':
            usd_rates[currency] = 1.0
        else:
            usd_rates[currency] = (1.0 / rate) * eur_usd
    
    return usd_rates


def update_currency_file(usd_rates):
    """
    Update CURRENCY_RATES in email_to_invoice.py
    
    Args:
        usd_rates: Dictionary of USD-based rates
    """
    if not usd_rates:
        print("⚠️  No rates to update")
        return
    
    script_path = Path(__file__).parent / 'email_to_invoice.py'
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return
    
    # Read current file
    content = script_path.read_text(encoding='utf-8')
    
    # Generate new CURRENCY_RATES dictionary
    rates_text = "# Currency conversion rates (to USD) - Auto-updated\n"
    rates_text += f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    rates_text += "CURRENCY_RATES = {\n"
    
    # Add USD first
    rates_text += "    'USD': 1.0,\n"
    
    # Add other currencies alphabetically
    for currency in sorted(usd_rates.keys()):
        if currency != 'USD':
            rate = usd_rates[currency]
            rates_text += f"    '{currency}': {rate:.4f},  # 1 {currency} = {rate:.4f} USD\n"
    
    rates_text += "}\n"
    
    # Find and replace CURRENCY_RATES block
    import re
    
    # Pattern to match existing CURRENCY_RATES block
    pattern = r"# Currency conversion rates.*?CURRENCY_RATES = \{[^}]+\}"
    
    # Replace with new rates
    new_content = re.sub(pattern, rates_text, content, flags=re.DOTALL)
    
    if new_content == content:
        print("⚠️  Could not find CURRENCY_RATES block")
        return False
    
    # Write updated file
    script_path.write_text(new_content, encoding='utf-8')
    print(f"✅ Updated {script_path}")
    
    return True


def show_rate_comparison(old_rates, new_rates):
    """
    Show comparison of old vs new rates.
    
    Args:
        old_rates: Current rates
        new_rates: New rates from API
    """
    print("\n" + "=" * 60)
    print("CURRENCY RATE CHANGES")
    print("=" * 60)
    print()
    
    print(f"{'Currency':<10} {'Old Rate':<15} {'New Rate':<15} {'Change':<15}")
    print("-" * 60)
    
    for currency in sorted(set(list(old_rates.keys()) + list(new_rates.keys()))):
        if currency == 'USD':
            continue
        
        old = old_rates.get(currency, 0)
        new = new_rates.get(currency, 0)
        
        if old > 0:
            change = ((new - old) / old) * 100
            change_str = f"{change:+.2f}%"
        else:
            change_str = "N/A"
        
        print(f"{currency:<10} {old:<15.4f} {new:<15.4f} {change_str:<15}")
    
    print("=" * 60)


def main():
    """Update currency rates."""
    print("=" * 60)
    print("CURRENCY RATE UPDATER")
    print("=" * 60)
    print()
    
    # Current rates (backup)
    current_rates = {
        'USD': 1.0,
        'PKR': 0.0036,
        'EUR': 1.08,
        'GBP': 1.27,
        'INR': 0.012,
        'CAD': 0.74,
        'AUD': 0.65,
        'JPY': 0.0067,
        'CNY': 0.14,
        'AED': 0.27,
        'SAR': 0.27,
    }
    
    # Fetch new rates from ECB
    print("Step 1: Fetching latest rates from European Central Bank...")
    eur_rates = fetch_ecb_rates()
    
    if not eur_rates:
        print("\n⚠️  Using fallback rates")
        eur_rates = {
            'USD': 1.08,
            'PKR': 300.0,
            'GBP': 0.85,
            'INR': 90.0,
            'CAD': 1.45,
            'AUD': 1.65,
            'JPY': 160.0,
            'CNY': 7.8,
            'AED': 3.96,
            'SAR': 4.05,
        }
    
    # Convert to USD base
    print("\nStep 2: Converting to USD base rates...")
    usd_rates = convert_to_usd_base(eur_rates)
    
    if usd_rates:
        print(f"✅ Converted {len(usd_rates)} currencies to USD base")
    else:
        print("❌ Conversion failed")
        return
    
    # Show comparison
    show_rate_comparison(current_rates, usd_rates)
    
    # Update file
    print("\nStep 3: Updating email_to_invoice.py...")
    if update_currency_file(usd_rates):
        print("\n✅ Currency rates updated successfully!")
        print("\nNext steps:")
        print("1. Test with a foreign currency email")
        print("2. Verify conversion uses new rates")
        print("3. Schedule this script to run daily (optional)")
    else:
        print("\n⚠️  Update failed - rates not changed")


if __name__ == '__main__':
    main()
