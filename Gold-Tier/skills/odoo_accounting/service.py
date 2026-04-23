"""
Odoo Accounting Service - Core Business Logic

Connects to Odoo via JSON-RPC API for:
- Creating customers and invoices
- Recording payments
- Getting account balances
- Listing transactions
- Generating financial reports

No agent-related code — pure business logic only.
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

load_dotenv()


class OdooClient:
    """Odoo JSON-R API client."""

    def __init__(self, url: str = "http://localhost:8069", db: str = "odoo",
                 username: str = "admin", password: str = "admin"):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.session = requests.Session()
        self.logger = logging.getLogger(self.__class__.__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError)),
        reraise=True
    )
    def authenticate(self) -> bool:
        try:
            resp = self.session.post(f"{self.url}/web/session/authenticate",
                                     json={"jsonrpc": "2.0", "method": "call",
                                           "params": {"db": self.db, "login": self.username, "password": self.password},
                                           "id": 1}, timeout=10)
            resp.raise_for_status()
            result = resp.json()
            if result.get("result", {}).get("uid"):
                self.uid = result["result"]["uid"]
                return True
            return False
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError, TimeoutError)),
        reraise=True
    )
    def execute_kw(self, model: str, method: str, args: List = None, kwargs: Dict = None) -> Any:
        if not self.uid and not self.authenticate():
            raise Exception("Not authenticated")
        try:
            resp = self.session.post(f"{self.url}/web/dataset/call_kw",
                                     json={"jsonrpc": "2.0", "method": "call",
                                           "params": {"model": model, "method": method,
                                                      "args": args or [], "kwargs": kwargs or {}},
                                           "id": 1}, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            if "error" in result:
                raise Exception(f"Odoo error: {result['error'].get('data', {}).get('message', result['error'].get('message', 'Unknown'))}")
            return result.get("result", {})
        except Exception as e:
            self.logger.error(f"Execute {method} on {model} failed: {e}")
            raise


class OdooAccountingService:
    """Core Odoo accounting service."""

    def __init__(self, odoo_url: str = None, odoo_db: str = None,
                 odoo_user: str = None, odoo_password: str = None):
        # Read from environment variables if not provided
        url = odoo_url or os.getenv("ODOO_URL", "http://localhost:8069")
        db = odoo_db or os.getenv("ODOO_DB", "odoo")
        user = odoo_user or os.getenv("ODOO_USERNAME", "admin")
        password = odoo_password or os.getenv("ODOO_PASSWORD", "admin")

        self.client = OdooClient(url=url, db=db, username=user, password=password)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_customer(self, name: str, email: str, phone: Optional[str] = None,
                        company: Optional[str] = None) -> Dict[str, Any]:
        try:
            existing = self.client.execute_kw("res.partner", "search_read",
                                              [[["email", "=", email]]],
                                              {"fields": ["id", "name", "email"], "limit": 1})
            if existing:
                return {"success": True, "customer_id": existing[0]["id"], "name": existing[0]["name"],
                        "email": existing[0]["email"], "message": "Customer already exists"}
            vals = {"name": name, "email": email, "customer_rank": 1}
            if phone: vals["phone"] = phone
            if company: vals["company_name"] = company
            cid = self.client.execute_kw("res.partner", "create", [vals])
            return {"success": True, "customer_id": cid, "name": name, "email": email}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_or_create_partner(self, name: str, email: str) -> Optional[int]:
        try:
            existing = self.client.execute_kw("res.partner", "search_read",
                                              [[["email", "=", email]]],
                                              {"fields": ["id", "name"], "limit": 1})
            if existing:
                return existing[0]["id"]
            return self.client.execute_kw("res.partner", "create", [{"name": name, "email": email}])
        except Exception as e:
            self.logger.error(f"Partner error: {e}")
            return None

    def create_invoice(self, partner_name: str, partner_email: str,
                       lines: List[Dict], invoice_type: str = "out_invoice") -> Dict[str, Any]:
        try:
            partner_id = self._get_or_create_partner(partner_name, partner_email)
            if not partner_id:
                return {"success": False, "error": f"Could not create partner {partner_name}"}
            invoice_vals = {"move_type": invoice_type, "partner_id": partner_id, "invoice_line_ids": []}
            for line in lines:
                invoice_vals["invoice_line_ids"].append([0, 0, {
                    "name": line.get("name", "Service"),
                    "quantity": line.get("quantity", 1),
                    "price_unit": line.get("price_unit", 0)
                }])
            invoice_id = self.client.execute_kw("account.move", "create", [invoice_vals])
            self.client.execute_kw("account.move", "action_post", [[invoice_id]])
            inv_data = self.client.execute_kw("account.move", "read", [[invoice_id]],
                                              {"fields": ["name", "amount_total", "amount_residual", "state"]})
            return {"success": True, "invoice_id": invoice_id,
                    "invoice_number": inv_data[0].get("name"),
                    "amount_total": inv_data[0].get("amount_total"),
                    "amount_due": inv_data[0].get("amount_residual"),
                    "state": inv_data[0].get("state")}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def record_payment(self, invoice_number: str, amount: float,
                       payment_reference: Optional[str] = None) -> Dict[str, Any]:
        try:
            invoice = self.client.execute_kw("account.move", "search_read",
                                             [[["name", "=", invoice_number]]],
                                             {"fields": ["id", "partner_id", "journal_id", "state"], "limit": 1})
            if not invoice:
                try:
                    iid = int(invoice_number)
                    invoice = self.client.execute_kw("account.move", "search_read",
                                                     [[["id", "=", iid]]],
                                                     {"fields": ["id", "partner_id", "journal_id", "state"], "limit": 1})
                except ValueError:
                    pass
            if not invoice:
                return {"success": False, "error": f"Invoice {invoice_number} not found"}
            if invoice[0].get("state") != "posted":
                return {"success": False, "error": f"Invoice not posted (state: {invoice[0].get('state')})"}
            payment_vals = {"payment_type": "inbound", "partner_type": "customer",
                            "partner_id": invoice[0]["partner_id"][0],
                            "amount": amount,
                            "payment_reference": payment_reference or f"Payment for {invoice_number}"}
            payment_id = self.client.execute_kw("account.payment", "create", [payment_vals])
            self.client.execute_kw("account.payment", "action_post", [[payment_id]])
            return {"success": True, "payment_id": payment_id, "invoice_number": invoice_number,
                    "amount": amount}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_account_balance(self, account_code: Optional[str] = None) -> Dict[str, Any]:
        try:
            domain = []
            if account_code: domain.append(("code", "=", account_code))
            accounts = self.client.execute_kw("account.account", "search_read", [domain],
                                              {"fields": ["code", "name", "account_type", "balance"], "limit": 100})
            return {"success": True, "accounts": [{"code": a["code"], "name": a["name"],
                      "type": a.get("account_type", ""), "balance": a.get("balance", 0)} for a in accounts],
                    "count": len(accounts)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_transactions(self, days: int = 30, limit: int = 100) -> Dict[str, Any]:
        try:
            date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            moves = self.client.execute_kw("account.move", "search_read",
                                           [[["date", ">=", date_from], ["state", "=", "posted"]]],
                                           {"fields": ["name", "date", "ref", "amount_total", "partner_id", "move_type", "state"],
                                            "limit": limit, "order": "date desc"})
            transactions = []
            for m in moves:
                transactions.append({"id": m["id"], "name": m.get("name", ""), "date": m.get("date", ""),
                    "reference": m.get("ref", ""), "amount": m.get("amount_total", 0),
                    "partner": m.get("partner_id", [None, ""])[1] if m.get("partner_id") else "",
                    "type": m.get("move_type", ""), "state": m.get("state", "")})
            return {"success": True, "transactions": transactions, "count": len(transactions), "period_days": days}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_financial_report(self, report_type: str = "profit_loss") -> Dict[str, Any]:
        try:
            if report_type == "profit_loss":
                income = self.client.execute_kw("account.account", "search_read", [[("account_type", "=", "income")]],
                                                {"fields": ["code", "name", "account_type"]})
                expense = self.client.execute_kw("account.account", "search_read", [[("account_type", "=", "expense")]],
                                                 {"fields": ["code", "name", "account_type"]})
                return {"success": True, "report_type": "profit_loss", "income": 0, "expenses": 0, "net_profit": 0,
                        "income_accounts": len(income), "expense_accounts": len(expense)}
            elif report_type == "balance_sheet":
                assets = self.client.execute_kw("account.account", "search_read", [[("account_type", "=", "asset")]],
                                                {"fields": ["code", "name", "account_type"]})
                liabilities = self.client.execute_kw("account.account", "search_read", [[("account_type", "=", "liability")]],
                                                     {"fields": ["code", "name", "account_type"]})
                return {"success": True, "report_type": "balance_sheet", "assets": 0, "liabilities": 0, "equity": 0,
                        "asset_accounts": len(assets), "liability_accounts": len(liabilities)}
            return {"success": False, "error": f"Unknown report type: {report_type}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_connection(self) -> Dict[str, Any]:
        try:
            ok = self.client.authenticate()
            return {"success": ok, "message": "Connected" if ok else "Authentication failed"}
        except Exception as e:
            return {"success": False, "error": str(e)}
