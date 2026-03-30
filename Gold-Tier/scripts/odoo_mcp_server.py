"""
Odoo Accounting MCP Server for AI Employee - Gold Tier

Provides accounting capabilities via Model Context Protocol (MCP).
Connects to Odoo Community Edition via JSON-RPC API.

Features:
- Create invoices
- Record payments
- Get account balances
- List transactions
- Generate financial reports

Usage:
    python scripts/odoo_mcp_server.py --odoo-url http://localhost:8069 --odoo-db odoo --odoo-user admin --odoo-password admin
"""

import json
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import argparse


# ============================================================================
# ODOO JSON-RPC CLIENT
# ============================================================================

class OdooClient:
    """Client for Odoo JSON-RPC API."""
    
    def __init__(
        self,
        url: str = 'http://localhost:8069',
        db: str = 'odoo',
        username: str = 'admin',
        password: str = 'admin'
    ):
        """
        Initialize Odoo client.
        
        Args:
            url: Odoo server URL
            db: Database name
            username: Odoo username (email)
            password: Odoo password
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.session = requests.Session()
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def authenticate(self) -> bool:
        """
        Authenticate with Odoo.
        
        Returns:
            True if successful
        """
        endpoint = f'{self.url}/web/session/authenticate'
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'db': self.db,
                'login': self.username,
                'password': self.password
            },
            'id': 1
        }
        
        try:
            response = self.session.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('result', {}).get('uid'):
                self.uid = result['result']['uid']
                self.logger.info(f"Authenticated as user {self.uid}")
                return True
            else:
                self.logger.error("Authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False
    
    def execute_kw(
        self,
        model: str,
        method: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None
    ) -> Any:
        """
        Execute a method on an Odoo model.
        
        Args:
            model: Model name (e.g., 'account.move')
            method: Method name
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Method result
        """
        if not self.uid:
            if not self.authenticate():
                raise Exception("Not authenticated")
        
        endpoint = f'{self.url}/web/dataset/call_kw'
        
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'model': model,
                'method': method,
                'args': args or [],
                'kwargs': kwargs or {}
            },
            'id': 1
        }
        
        try:
            response = self.session.post(endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if 'error' in result:
                error = result['error']
                raise Exception(f"Odoo error: {error.get('data', {}).get('message', error.get('message', 'Unknown error'))}")
            
            return result.get('result', {})
            
        except Exception as e:
            self.logger.error(f"Execute {method} on {model} failed: {e}")
            raise


# ============================================================================
# ODOO ACCOUNTING MCP SERVER
# ============================================================================

class OdooAccountingMCP:
    """MCP Server for Odoo Accounting."""
    
    def __init__(self, odoo_config: Dict[str, str]):
        """
        Initialize Odoo Accounting MCP.
        
        Args:
            odoo_config: Odoo configuration dictionary
        """
        self.client = OdooClient(
            url=odoo_config.get('url', 'http://localhost:8069'),
            db=odoo_config.get('db', 'odoo'),
            username=odoo_config.get('username', 'admin'),
            password=odoo_config.get('password', 'admin')
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_customer(
        self,
        name: str,
        email: str,
        phone: Optional[str] = None,
        company: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a customer in Odoo.
        
        Args:
            name: Customer name
            email: Customer email
            phone: Customer phone (optional)
            company: Company name (optional)
            
        Returns:
            Customer details
        """
        try:
            # Check if customer already exists
            existing = self.client.execute_kw(
                'res.partner',
                'search_read',
                [[['email', '=', email]]],
                {'fields': ['id', 'name', 'email'], 'limit': 1}
            )
            
            if existing:
                self.logger.info(f"Customer already exists: {existing[0]['id']}")
                return {
                    'success': True,
                    'customer_id': existing[0]['id'],
                    'name': existing[0]['name'],
                    'email': existing[0]['email'],
                    'message': f"Customer {existing[0]['name']} already exists"
                }
            
            # Create new customer
            customer_vals = {
                'name': name,
                'email': email,
                'customer_rank': 1  # Mark as customer
            }
            
            if phone:
                customer_vals['phone'] = phone
            
            if company:
                customer_vals['company_name'] = company
            
            customer_id = self.client.execute_kw(
                'res.partner',
                'create',
                [customer_vals]
            )
            
            self.logger.info(f"Created customer {customer_id}: {name}")
            
            return {
                'success': True,
                'customer_id': customer_id,
                'name': name,
                'email': email,
                'message': f"Customer {name} created successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Create customer failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_invoice(
        self,
        partner_name: str,
        partner_email: str,
        lines: List[Dict],
        invoice_type: str = 'out_invoice'
    ) -> Dict[str, Any]:
        """
        Create a customer invoice.
        
        Args:
            partner_name: Customer name
            partner_email: Customer email
            lines: Invoice lines [{'name': 'Service', 'quantity': 1, 'price_unit': 100}]
            invoice_type: 'out_invoice' (customer) or 'in_invoice' (vendor)
            
        Returns:
            Invoice details
        """
        try:
            # First, find or create partner
            partner_id = self._get_or_create_partner(partner_name, partner_email)
            
            if not partner_id:
                return {
                    'success': False,
                    'error': f'Could not create partner {partner_name}'
                }
            
            # Create invoice
            invoice_vals = {
                'move_type': invoice_type,
                'partner_id': partner_id,
                'invoice_line_ids': []
            }
            
            # Add invoice lines
            for line in lines:
                invoice_vals['invoice_line_ids'].append([
                    0, 0, {
                        'name': line.get('name', 'Service'),
                        'quantity': line.get('quantity', 1),
                        'price_unit': line.get('price_unit', 0)
                    }
                ])
            
            # Create invoice
            invoice_id = self.client.execute_kw(
                'account.move',
                'create',
                [invoice_vals]
            )
            
            # Post invoice (confirm)
            self.client.execute_kw(
                'account.move',
                'action_post',
                [[invoice_id]]
            )
            
            # Get invoice details (Odoo 19 compatible)
            invoice_data = self.client.execute_kw(
                'account.move',
                'read',
                [[invoice_id]],
                {
                    'fields': ['name', 'amount_total', 'amount_residual', 'state']
                }
            )
            
            self.logger.info(f"Created invoice {invoice_data[0].get('name')}")
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'invoice_number': invoice_data[0].get('name'),
                'partner_name': partner_name,
                'amount_total': invoice_data[0].get('amount_total'),
                'amount_due': invoice_data[0].get('amount_residual'),
                'state': invoice_data[0].get('state'),
                'message': f"Invoice {invoice_data[0].get('name')} created for {partner_name}"
            }
            
        except Exception as e:
            self.logger.error(f"Create invoice failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_partner(self, name: str, email: str) -> Optional[int]:
        """Get or create a business partner."""
        try:
            # Search for existing partner
            existing = self.client.execute_kw(
                'res.partner',
                'search_read',
                [[['email', '=', email]]],
                {'fields': ['id', 'name'], 'limit': 1}
            )
            
            if existing:
                return existing[0]['id']
            
            # Create new partner
            partner_id = self.client.execute_kw(
                'res.partner',
                'create',
                [{
                    'name': name,
                    'email': email
                }]
            )
            
            return partner_id
            
        except Exception as e:
            self.logger.error(f"Get/create partner failed: {e}")
            return None
    
    def record_payment(
        self,
        invoice_number: str,
        amount: float,
        payment_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a payment for an invoice.
        
        Args:
            invoice_number: Invoice number (e.g., 'INV/2026/0001')
            amount: Payment amount
            payment_reference: Payment reference/note
            
        Returns:
            Payment details
        """
        try:
            # Find invoice by name or ID
            invoice = None
            
            # Try searching by name first
            invoice = self.client.execute_kw(
                'account.move',
                'search_read',
                [[['name', '=', invoice_number]]],
                {'fields': ['id', 'partner_id', 'journal_id', 'state'], 'limit': 1}
            )
            
            # If not found, try searching by ID (in case invoice_number is actually an ID)
            if not invoice:
                try:
                    invoice_id = int(invoice_number)
                    invoice = self.client.execute_kw(
                        'account.move',
                        'search_read',
                        [[['id', '=', invoice_id]]],
                        {'fields': ['id', 'partner_id', 'journal_id', 'state'], 'limit': 1}
                    )
                except ValueError:
                    pass
            
            if not invoice:
                return {
                    'success': False,
                    'error': f'Invoice {invoice_number} not found'
                }
            
            invoice_id = invoice[0]['id']
            invoice_state = invoice[0].get('state', '')
            
            # Check if invoice is posted
            if invoice_state != 'posted':
                return {
                    'success': False,
                    'error': f'Invoice {invoice_number} is not posted (state: {invoice_state})'
                }
            
            # Create payment (Odoo 19 compatible)
            payment_vals = {
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice[0]['partner_id'][0],
                'amount': amount,
                'payment_reference': payment_reference or f'Payment for {invoice_number}'
            }
            
            # Create payment
            payment_id = self.client.execute_kw(
                'account.payment',
                'create',
                [payment_vals]
            )
            
            # Confirm payment (posts it)
            self.client.execute_kw(
                'account.payment',
                'action_post',
                [[payment_id]]
            )
            
            # For Odoo 19, the payment is automatically reconciled when posted
            # if the partner and amount match
            self.logger.info(f"Recorded payment {payment_id} for invoice {invoice_number}")
            self.logger.info(f"Note: You may need to manually reconcile in Odoo UI")
            self.logger.info(f"Go to: Invoicing → Customers → {invoice_number} → Register Payment")
            
            return {
                'success': True,
                'payment_id': payment_id,
                'invoice_number': invoice_number,
                'invoice_id': invoice_id,
                'amount': amount,
                'message': f"Payment of {amount} recorded for invoice {invoice_number}"
            }
            
        except Exception as e:
            self.logger.error(f"Record payment failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_balance(
        self,
        account_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get account balance(s).
        
        Args:
            account_code: Account code (e.g., '1000' for cash)
            
        Returns:
            Account balance details
        """
        try:
            domain = []
            
            if account_code:
                domain.append(('code', '=', account_code))
            
            # Get accounts (Odoo 19 compatible)
            accounts = self.client.execute_kw(
                'account.account',
                'search_read',
                [domain],
                {
                    'fields': ['code', 'name', 'account_type', 'balance'],
                    'limit': 100
                }
            )
            
            return {
                'success': True,
                'accounts': [
                    {
                        'code': acc['code'],
                        'name': acc['name'],
                        'type': acc.get('account_type', ''),
                        'balance': acc.get('balance', 0)
                    }
                    for acc in accounts
                ],
                'count': len(accounts)
            }
            
        except Exception as e:
            self.logger.error(f"Get account balance failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_transactions(
        self,
        days: int = 30,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List recent transactions.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of transactions
            
        Returns:
            Transaction list
        """
        try:
            from datetime import timedelta
            date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            # Get journal entries
            domain = [
                ('date', '>=', date_from),
                ('state', '=', 'posted')
            ]
            
            moves = self.client.execute_kw(
                'account.move',
                'search_read',
                [domain],
                {
                    'fields': [
                        'name', 'date', 'ref', 'amount_total',
                        'partner_id', 'move_type', 'state'
                    ],
                    'limit': limit,
                    'order': 'date desc'
                }
            )
            
            transactions = []
            for move in moves:
                transactions.append({
                    'id': move['id'],
                    'name': move.get('name', ''),
                    'date': move.get('date', ''),
                    'reference': move.get('ref', ''),
                    'amount': move.get('amount_total', 0),
                    'partner': move.get('partner_id', [None, ''])[1] if move.get('partner_id') else '',
                    'type': move.get('move_type', ''),
                    'state': move.get('state', '')
                })
            
            return {
                'success': True,
                'transactions': transactions,
                'count': len(transactions),
                'period_days': days
            }
            
        except Exception as e:
            self.logger.error(f"List transactions failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_financial_report(
        self,
        report_type: str = 'profit_loss'
    ) -> Dict[str, Any]:
        """
        Generate financial report.
        
        Args:
            report_type: 'profit_loss' or 'balance_sheet'
            
        Returns:
            Report data
        """
        try:
            if report_type == 'profit_loss':
                # Get income and expense accounts (Odoo 19 compatible)
                income_accounts = self.client.execute_kw(
                    'account.account',
                    'search_read',
                    [[('account_type', '=', 'income')]],
                    {'fields': ['code', 'name', 'account_type']}
                )
                
                expense_accounts = self.client.execute_kw(
                    'account.account',
                    'search_read',
                    [[('account_type', '=', 'expense')]],
                    {'fields': ['code', 'name', 'account_type']}
                )
                
                # Note: Balance calculation requires querying account.move.line
                # For now, return account counts
                return {
                    'success': True,
                    'report_type': 'profit_loss',
                    'income': 0,  # Requires balance calculation from moves
                    'expenses': 0,
                    'net_profit': 0,
                    'income_accounts': len(income_accounts),
                    'expense_accounts': len(expense_accounts),
                    'note': 'Balance calculation requires Odoo 19 specific API'
                }
            
            elif report_type == 'balance_sheet':
                # Get assets and liabilities (Odoo 19 compatible)
                asset_accounts = self.client.execute_kw(
                    'account.account',
                    'search_read',
                    [[('account_type', '=', 'asset')]],
                    {'fields': ['code', 'name', 'account_type']}
                )
                
                liability_accounts = self.client.execute_kw(
                    'account.account',
                    'search_read',
                    [[('account_type', '=', 'liability')]],
                    {'fields': ['code', 'name', 'account_type']}
                )
                
                return {
                    'success': True,
                    'report_type': 'balance_sheet',
                    'assets': 0,  # Requires balance calculation from moves
                    'liabilities': 0,
                    'equity': 0,
                    'asset_accounts': len(asset_accounts),
                    'liability_accounts': len(liability_accounts),
                    'note': 'Balance calculation requires Odoo 19 specific API'
                }
            
            else:
                return {
                    'success': False,
                    'error': f'Unknown report type: {report_type}'
                }
            
        except Exception as e:
            self.logger.error(f"Generate financial report failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# ============================================================================
# MAIN - TEST CONNECTION
# ============================================================================

def main():
    """Test Odoo MCP Server connection."""
    parser = argparse.ArgumentParser(description='Odoo Accounting MCP Server')
    parser.add_argument('--odoo-url', default='http://localhost:8069', help='Odoo URL')
    parser.add_argument('--odoo-db', default='odoo', help='Odoo database')
    parser.add_argument('--odoo-user', default='admin', help='Odoo username')
    parser.add_argument('--odoo-password', default='admin', help='Odoo password')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('OdooMCP')
    logger.info("Testing Odoo Connection...")
    
    # Initialize Odoo client
    odoo_config = {
        'url': args.odoo_url,
        'db': args.odoo_db,
        'username': args.odoo_user,
        'password': args.odoo_password
    }
    
    mcp_server = OdooAccountingMCP(odoo_config)
    
    # Test connection
    try:
        if mcp_server.client.authenticate():
            logger.info("✅ Connected to Odoo successfully!")
            
            # Test get account balance
            logger.info("Testing account balance query...")
            result = mcp_server.get_account_balance()
            if result.get('success'):
                logger.info(f"✅ Found {result.get('count')} accounts")
            else:
                logger.warning(f"⚠️ Could not get accounts: {result.get('error')}")
            
            # Test list transactions
            logger.info("Testing transactions query...")
            result = mcp_server.list_transactions(days=7, limit=10)
            if result.get('success'):
                logger.info(f"✅ Found {result.get('count')} recent transactions")
            
            logger.info("=" * 60)
            logger.info("ODOO MCP SERVER READY")
            logger.info("=" * 60)
            logger.info("")
            logger.info("Available methods:")
            logger.info("  - create_invoice(partner_name, partner_email, lines)")
            logger.info("  - record_payment(invoice_number, amount)")
            logger.info("  - get_account_balance(account_code)")
            logger.info("  - list_transactions(days, limit)")
            logger.info("  - generate_financial_report(report_type)")
            logger.info("")
            logger.info("Example usage in Python:")
            logger.info("  from odoo_mcp_server import OdooAccountingMCP")
            logger.info("  mcp = OdooAccountingMCP(odoo_config)")
            logger.info("  result = mcp.create_invoice('Test Customer', 'test@example.com', [{'name': 'Service', 'price_unit': 100}])")
            logger.info("")
        else:
            logger.error("❌ Failed to authenticate with Odoo")
            logger.error("Check your credentials and make sure Odoo is running")
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        logger.error("Make sure Odoo is running at http://localhost:8069")


if __name__ == '__main__':
    main()
