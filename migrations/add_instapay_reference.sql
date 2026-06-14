-- Add instapay_reference column to payments table for manual InstaPay flow
ALTER TABLE payments ADD COLUMN IF NOT EXISTS instapay_reference VARCHAR;
CREATE INDEX IF NOT EXISTS ix_payments_instapay_reference ON payments (instapay_reference);
