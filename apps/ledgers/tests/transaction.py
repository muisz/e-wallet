from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.ledgers.models import Transaction
from apps.ledgers.tests.factories import create_ledger
from apps.utils import messages
from apps.utils.decorators import assert_raise_error



class TransactionTestCase(TestCase):
    def setUp(self):
        self.ledger = create_ledger()
    
    def test_create_debit_transaction_method(self):
        self.ledger.balance = 50000
        transaction = Transaction.create_debit_transaction(
            ledger=self.ledger,
            amount=10000,
        )

        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.balance_after, 40000)
    
    def test_create_credit_transaction_method(self):
        self.ledger.balance = 50000
        transaction = Transaction.create_credit_transaction(
            ledger=self.ledger,
            amount=10000,
        )

        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.balance_after, 60000)
    
    def test_get_transactions_method(self):
        [Transaction.create_credit_transaction(ledger=self.ledger, amount=10000) for _ in range(5)]
        result = Transaction.get_transactions(self.ledger)

        self.assertEqual(len(result), 5)
    
    def test_get_transactions_method_with_type(self):
        self.ledger.balance = 1000000
        [Transaction.create_debit_transaction(ledger=self.ledger, amount=10000) for _ in range(5)]
        [Transaction.create_credit_transaction(ledger=self.ledger, amount=10000) for _ in range(5)]
        result = Transaction.get_transactions(self.ledger, type=Transaction.CREDIT)

        self.assertEqual(len(result), 5)
    
    def test_get_transactions_method_with_search_keyword(self):
        [Transaction.create_credit_transaction(ledger=self.ledger, amount=10000, notes='Top up') for _ in range(5)]
        [Transaction.create_credit_transaction(ledger=self.ledger, amount=10000, notes='Cashback') for _ in range(5)]
        result = Transaction.get_transactions(self.ledger, search_keyword='top up')

        self.assertEqual(len(result), 5)
    
    def test_get_transactions_method_with_type_and_search_keyword(self):
        self.ledger.balance = 1000000
        [Transaction.create_credit_transaction(ledger=self.ledger, amount=10000, notes='Top up') for _ in range(5)]
        [Transaction.create_credit_transaction(ledger=self.ledger, amount=10000) for _ in range(5)]
        [Transaction.create_debit_transaction(ledger=self.ledger, amount=10000, notes='Top up') for _ in range(5)]
        result = Transaction.get_transactions(self.ledger, search_keyword='top up', type=Transaction.CREDIT)

        self.assertEqual(len(result), 5)
    
    def test_get_transaction_method(self):
        transaction = Transaction.create_credit_transaction(ledger=self.ledger, amount=10000)
        result = Transaction.get_transaction(transaction.id)

        self.assertEqual(result, transaction)
    
    def test_get_transaction_method_return_none(self):
        result = Transaction.get_transaction('0')

        self.assertIsNone(result)
    
    @assert_raise_error(NotFound(messages.LEDGER_TRANSACTION_NOT_FOUND))
    def test_get_transaction_method_raise_error(self):
        Transaction.get_transaction('0', raise_exception=True)

    def test_set_id_method_with_no_transaction(self):
        transaction = Transaction(ledger=self.ledger)
        transaction.set_id()

        now = timezone.now()
        self.assertEqual(transaction.id, now.strftime("%Y%m%d0000001"))
        
    def test_set_id_method_with_no_transaction(self):
        Transaction.create_credit_transaction(
            ledger=self.ledger,
            amount=10000,
        )
        transaction = Transaction(ledger=self.ledger)
        transaction.set_id()

        now = timezone.now()
        self.assertEqual(transaction.id, now.strftime("%Y%m%d0000002"))
    
    @assert_raise_error(Exception(messages.LEDGER_TRANSACTION_ID_CANNOT_BE_CHANGED))
    def test_set_id_method_raise_error(self):
        transaction = Transaction(ledger=self.ledger)
        transaction.set_id()
        transaction.set_id()
    
    def test_set_reference_method(self):
        transaction = Transaction(ledger=self.ledger)
        transaction.set_reference(None)

        self.assertIsNotNone(transaction.reference)
    
    @assert_raise_error(Exception(messages.LEDGER_TRANSACTION_REFERENCE_CANNOT_BE_CHANGED))
    def test_set_id_method_raise_error(self):
        transaction = Transaction(ledger=self.ledger)
        transaction.set_reference(None)
        transaction.set_reference(None)
    
    def test_set_amount_method_for_debit(self):
        self.ledger.balance = 10000
        transaction = Transaction(ledger=self.ledger, type=Transaction.DEBIT)
        transaction.set_amount(5000)

        self.assertEqual(transaction.balance_before, 10000)
        self.assertEqual(transaction.amount, 5000)
        self.assertEqual(transaction.balance_after, 5000)

    def test_set_amount_method_for_credit(self):
        transaction = Transaction(ledger=self.ledger, type=Transaction.CREDIT)
        transaction.set_amount(50000)

        self.assertEqual(transaction.balance_before, 0)
        self.assertEqual(transaction.amount, 50000)
        self.assertEqual(transaction.balance_after, 50000)
    
    @assert_raise_error(Exception(messages.LEDGER_TRANSACTION_AMOUNT_CANNOT_BE_CHANGED))
    def test_set_amount_method_raise_error(self):
        transaction = Transaction(ledger=self.ledger, type=Transaction.CREDIT)
        transaction.set_amount(50000)
        transaction.set_amount(50000)
    
    def test_get_transaction_number_method(self):
        transaction = Transaction(ledger=self.ledger)
        transaction.set_id()

        self.assertEqual(1, transaction.get_transaction_number())
    
    def test_get_last_transaction_method(self):
        transaction = Transaction.create_credit_transaction(
            ledger=self.ledger,
            amount=10000,
        )
        ledger_transaction = Transaction(ledger=self.ledger)
        result = ledger_transaction.get_last_transaction(timezone.now())

        self.assertEqual(result, transaction)
    
    def test_is_debit_property(self):
        transaction = Transaction(type=Transaction.DEBIT)

        self.assertTrue(transaction.is_debit)
    
    def test_is_credit_propery(self):
        transaction = Transaction(type=Transaction.CREDIT)

        self.assertTrue(transaction.is_credit)

    def test_origin_property(self):
        bank_account = 'Bank 1'
        account_name = 'Someone'
        account_number = '01829232'
        transaction = Transaction.create_credit_transaction(
            ledger=self.ledger,
            amount=10000,
            bank_account_name=bank_account,
            account_name=account_name,
            account_number=account_number,
        )

        origin = f'{account_name} - {bank_account} {account_number}'
        self.assertEqual(origin, transaction.origin)
        
    def test_origin_property_without_bank(self):
        transaction = Transaction.create_credit_transaction(
            ledger=self.ledger,
            amount=10000,
        )

        self.assertEqual('-', transaction.origin)
        
    def test_destination_property(self):
        self.ledger.balance = 10000
        bank_account = 'Bank 1'
        account_name = 'Someone'
        account_number = '01829232'
        transaction = Transaction.create_debit_transaction(
            ledger=self.ledger,
            amount=10000,
            bank_account_name=bank_account,
            account_name=account_name,
            account_number=account_number,
        )

        destination = f'{account_name} - {bank_account} {account_number}'
        self.assertEqual(destination, transaction.destination)
        
    def test_destination_property_without_bank(self):
        self.ledger.balance = 10000
        transaction = Transaction.create_debit_transaction(
            ledger=self.ledger,
            amount=10000,
        )

        self.assertEqual('-', transaction.destination)

    def test_bank_property(self):
        bank_account = 'Bank 1'
        account_name = 'Someone'
        account_number = '01829232'
        transaction = Transaction.create_credit_transaction(
            ledger=self.ledger,
            amount=10000,
            bank_account_name=bank_account,
            account_name=account_name,
            account_number=account_number,
        )

        bank = f'{account_name} - {bank_account} {account_number}'
        self.assertEqual(bank, transaction.bank)
        
    def test_bank_property_without_bank(self):
        transaction = Transaction.create_credit_transaction(
            ledger=self.ledger,
            amount=10000,
        )

        self.assertEqual('-', transaction.bank)