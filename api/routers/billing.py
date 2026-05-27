import json
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from db.postgres import get_pool
from models.postgres import AccountOut, InvoiceIn, InvoiceOut

router = APIRouter(prefix="/billing", tags=["Billing (PostgreSQL)"])

# Tax rate applied to all invoices
VAT_RATE = Decimal("0.13")


@router.get("/account/{premise_id}", response_model=AccountOut)
async def get_account(premise_id: str):
    """Retrieve account details and current balance."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM accounts WHERE premise_id = $1", premise_id
        )
    if not row:
        raise HTTPException(status_code=404, detail=f"Account '{premise_id}' not found")
    data = dict(row)
    # asyncpg returns JSONB as string — parse it
    if isinstance(data.get("tariff_rules"), str):
        data["tariff_rules"] = json.loads(data["tariff_rules"])
    return AccountOut(**data)


@router.post("/invoice", response_model=InvoiceOut, status_code=201)
async def generate_invoice(invoice_in: InvoiceIn):
    """
    Generate a monthly invoice inside a single ACID transaction.
    Reads the account's tariff_rules from PostgreSQL (JSONB) to apply
    progressive tariff bands. Updates account balance atomically.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # 1. Fetch account + tariff rules
            account = await conn.fetchrow(
                "SELECT * FROM accounts WHERE premise_id = $1 FOR UPDATE",
                invoice_in.premise_id
            )
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            tariff_rules = account["tariff_rules"]
            if isinstance(tariff_rules, str):
                tariff_rules = json.loads(tariff_rules)

            # 2. Calculate amount using tariff bands
            kwh = invoice_in.kwh_consumed
            amount = _apply_tariff(kwh, tariff_rules)
            tax = (amount * VAT_RATE).quantize(Decimal("0.01"))
            total = amount + tax

            line_items = [
                {"description": "Energy consumption", "kwh": str(kwh), "amount": str(amount)},
                {"description": f"VAT {int(VAT_RATE * 100)}%", "amount": str(tax)},
            ]

            # 3. Insert invoice
            row = await conn.fetchrow("""
                INSERT INTO invoices
                    (premise_id, period_start, period_end, kwh_consumed,
                     amount_eur, tax_eur, total_eur, line_items, status, issued_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'issued',NOW())
                RETURNING *
            """, invoice_in.premise_id, invoice_in.period_start, invoice_in.period_end,
                kwh, amount, tax, total, json.dumps(line_items))

            # 4. Update account balance (debit)
            await conn.execute(
                "UPDATE accounts SET balance_eur = balance_eur + $1 WHERE premise_id = $2",
                total, invoice_in.premise_id
            )

    data = dict(row)
    data["invoice_id"] = str(data["invoice_id"])
    if isinstance(data.get("line_items"), str):
        data["line_items"] = json.loads(data["line_items"])
    return InvoiceOut(**data)


def _apply_tariff(kwh: Decimal, rules: dict) -> Decimal:
    """Apply progressive tariff bands from JSONB rules."""
    bands = rules.get("bands", [])
    if not bands:
        # Flat rate fallback
        return (kwh * Decimal("0.15")).quantize(Decimal("0.01"))

    total = Decimal("0")
    remaining = kwh
    prev_limit = Decimal("0")

    for band in bands:
        limit = Decimal(str(band.get("up_to_kwh", 999999)))
        rate = Decimal(str(band["rate"]))
        band_kwh = min(remaining, limit - prev_limit)
        total += band_kwh * rate
        remaining -= band_kwh
        prev_limit = limit
        if remaining <= 0:
            break

    return total.quantize(Decimal("0.01"))