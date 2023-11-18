from faker import Faker

from apps.ledgers.models import Ledger
from apps.users.tests.factories import create_user


def create_ledger(user=None, bank_code=None):
    if user is None:
        user = create_user()
    if bank_code is None:
        bank_code = 'BANK'
    ledger = Ledger.create(
        user=user,
        name=user.name,
        bank_code=bank_code,
    )
    return ledger
