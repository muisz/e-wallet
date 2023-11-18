from django.test import TestCase
from faker import Faker
from rest_framework.exceptions import NotFound

from apps.ledgers.models import Ledger
from apps.ledgers.tests.factories import create_ledger
from apps.users.tests.factories import create_user
from apps.utils import messages
from apps.utils.decorators import assert_raise_error

fake = Faker()


class LedgerTestCase(TestCase):
    def setUp(self):
        self.user = create_user()
    
    def test_create_method(self):
        ledger = Ledger.create(
            user=self.user,
            name=self.user.name,
            bank_code='BNI',
        )

        self.assertIsNotNone(ledger.virtual_account)

    def test_get_ledgers_method(self):
        [create_ledger() for _ in range(10)]
        ledgers = Ledger.get_ledgers()

        self.assertEqual(len(ledgers), 10)
    
    def test_get_ledgers_method_with_search_keyword(self):
        [create_ledger(self.user) for _ in range(10)]
        ledgers = Ledger.get_ledgers(search_keyword=self.user.name[:3])

        self.assertEqual(len(ledgers), 10)
    
    def test_get_ledgers_method_with_bank_code(self):
        [create_ledger(user=None, bank_code='Bank 1') for _ in range(5)]
        [create_ledger(user=None, bank_code='Bank 2') for _ in range(5)]
        ledgers = Ledger.get_ledgers(bank_code='Bank 1')

        self.assertEqual(len(ledgers), 5)
    
    def test_get_ledgers_method_with_bank_code_and_search_keyword(self):
        [create_ledger(user=self.user, bank_code='Bank 1') for _ in range(5)]
        [create_ledger(user=self.user, bank_code='Bank 2') for _ in range(5)]
        ledgers = Ledger.get_ledgers(search_keyword=self.user.name[:3], bank_code='Bank 1')

        self.assertEqual(len(ledgers), 5)
    
    def test_get_ledger_method(self):
        ledger = create_ledger()
        result = Ledger.get_ledger(ledger.id)

        self.assertEqual(result, ledger)
    
    def test_get_ledger_method_return_none(self):
        result = Ledger.get_ledger(0)

        self.assertIsNone(result)

    @assert_raise_error(NotFound(messages.LEDGER_NOT_FOUND))
    def test_get_ledger_raise_error(self):
        Ledger.get_ledger(0, raise_exception=True)

    def test_create_debit_transaction_method(self):
        ledger = create_ledger()
        ledger.balance = 20000
        transaction = ledger.create_debit_transaction(
            amount=10000,
            notes='Buy food',
        )

        self.assertIsNotNone(transaction)
        self.assertEqual(ledger.balance, 10000)

    @assert_raise_error(Exception(messages.LEDGER_CANNOT_INSUFFICIENT_BALANCE))
    def test_create_debit_transaction_method_raise_error(self):
        ledger = create_ledger()
        ledger.balance = 20000
        ledger.create_debit_transaction(
            amount=50000,
            notes='Buy food',
        )

    def test_create_credit_transaction_method(self):
        ledger = create_ledger()
        transaction = ledger.create_credit_transaction(
            amount=50000,
            notes='Top up',
        )

        self.assertIsNotNone(transaction)
        self.assertEqual(ledger.balance, 50000)

    def test_is_balance_sufficient_method(self):
        ledger = Ledger(balance=10000)

        self.assertTrue(ledger.is_balance_sufficient(5000))
        self.assertFalse(ledger.is_balance_sufficient(100000))
