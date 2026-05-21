-- GridSense PostgreSQL Schema

-- ── Consumer accounts ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS accounts (
    premise_id      TEXT PRIMARY KEY,
    customer_name   TEXT        NOT NULL,
    address         TEXT        NOT NULL,
    meter_id        TEXT        NOT NULL,
    tariff_class    TEXT        NOT NULL DEFAULT 'residential',
    tariff_rules    JSONB       NOT NULL DEFAULT '{}',
    balance_eur     NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- GIN index on tariff_rules allows fast JSONB key/value lookups
CREATE INDEX IF NOT EXISTS idx_accounts_tariff_rules
    ON accounts USING GIN (tariff_rules);

CREATE INDEX IF NOT EXISTS idx_accounts_tariff_class
    ON accounts (tariff_class);

-- ── Invoices ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    premise_id      TEXT        NOT NULL REFERENCES accounts(premise_id),
    period_start    DATE        NOT NULL,
    period_end      DATE        NOT NULL,
    kwh_consumed    NUMERIC(10,3) NOT NULL,
    amount_eur      NUMERIC(12,2) NOT NULL,
    tax_eur         NUMERIC(12,2) NOT NULL,
    total_eur       NUMERIC(12,2) NOT NULL,
    -- Breakdown stored as JSONB: tariff bands applied, surcharges, adjustments
    line_items      JSONB       NOT NULL DEFAULT '[]',
    status          TEXT        NOT NULL DEFAULT 'draft',  -- draft|issued|paid|overdue
    issued_at       TIMESTAMPTZ,
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_premise
    ON invoices (premise_id);

CREATE INDEX IF NOT EXISTS idx_invoices_status
    ON invoices (status);

CREATE INDEX IF NOT EXISTS idx_invoices_period
    ON invoices (period_start, period_end);

-- ── Meter readings (daily aggregates for billing) ────────────────────────────
CREATE TABLE IF NOT EXISTS daily_meter_readings (
    premise_id      TEXT        NOT NULL REFERENCES accounts(premise_id),
    reading_date    DATE        NOT NULL,
    kwh_total       NUMERIC(10,3) NOT NULL,
    peak_kw         NUMERIC(8,3),
    quality         TEXT        NOT NULL DEFAULT 'measured',  -- measured|estimated|substituted
    PRIMARY KEY (premise_id, reading_date)
);

-- ── Trigger: keep updated_at current ─────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();