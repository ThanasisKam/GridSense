from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AccountOut(BaseModel):
    premise_id: str
    customer_name: str
    address: str
    meter_id: str
    tariff_class: str
    tariff_rules: Dict[str, Any]
    balance_eur: Decimal
    created_at: datetime


class InvoiceIn(BaseModel):
    premise_id: str
    period_start: date
    period_end: date
    kwh_consumed: Decimal


class InvoiceOut(BaseModel):
    invoice_id: str
    premise_id: str
    period_start: date
    period_end: date
    kwh_consumed: Decimal
    amount_eur: Decimal
    tax_eur: Decimal
    total_eur: Decimal
    line_items: List[Dict[str, Any]]
    status: str
    created_at: datetime