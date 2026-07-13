from django.dispatch import Signal

account_created = Signal()
account_deactivated = Signal()

journal_entry_posted = Signal()
journal_entry_reversed = Signal()

invoice_created = Signal()
invoice_posted = Signal()
invoice_paid = Signal()
invoice_voided = Signal()

payment_received = Signal()
payment_applied = Signal()

bill_created = Signal()
bill_posted = Signal()
bill_paid = Signal()
bill_voided = Signal()

inventory_received = Signal()
inventory_issued = Signal()
inventory_transfered = Signal()
inventory_adjusted = Signal()

batch_created = Signal()
batch_expired = Signal()
batch_expiring_soon = Signal()

low_stock_alert = Signal()
