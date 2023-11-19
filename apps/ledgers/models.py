import random
import string
import uuid
from datetime import datetime
from django.db import models
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import NotFound
from typing import Union

from apps.modules.instamoney import RNE
from apps.users.models import User as UserModel
from apps.utils import messages
from apps.utils.models import BaseModel

User: get_user_model() = UserModel


class Ledger(BaseModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ledgers')
    name = models.CharField(max_length=100)
    virtual_account = models.CharField(max_length=100, unique=True)
    balance = models.IntegerField()
    reference = models.CharField(max_length=100, unique=True)
    bank_code = models.CharField(max_length=20)
    external_id = models.CharField(max_length=100, null=True)

    ACTIVE = '1'
    INACTIVE = '2'
    PENDING = '3'
    STATUS_CHOICES = (
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
        (PENDING, 'Pending')
    )
    status = models.CharField(max_length=1)

    @classmethod
    def create(cls, user: User, name: str, bank_code: str):
        rne = RNE()
        external_id = str(uuid.uuid4())
        virtual_account = rne.create_virtual_account(
            name=name,
            bank_code=bank_code,
            external_id=external_id,
        )

        ledger = cls(
            user=user,
            name=name,
            virtual_account=virtual_account.get("account_number"),
            balance=0,
            reference=virtual_account.get("id"),
            status=Ledger.PENDING,
            bank_code=bank_code,
            external_id=external_id,
        )
        ledger.save()
        ledger.set_status(Ledger.PENDING, "Initial Ledger")
        return ledger
    
    @classmethod
    def get_ledgers(cls, search_keyword='', bank_code=''):
        ledgers = cls.objects.all()
        if bank_code:
            ledgers = ledgers.filter(bank_code=bank_code)
        if search_keyword:
            ledgers = ledgers.filter(
                Q(name__icontains=search_keyword) |
                Q(virtual_account__icontains=search_keyword) |
                Q(reference__icontains=search_keyword)
            )
        return ledgers.order_by('-id')

    @classmethod
    def get_ledger(cls, id, raise_exception: bool = False):
        ledger = cls.objects.filter(id=id).first()
        if not ledger and raise_exception:
            raise NotFound(messages.LEDGER_NOT_FOUND)
        return ledger
    
    def create_debit_transaction(
        self,
        amount: str,
        bank_account_name: Union[str, None] = None,
        account_name: Union[str, None] = None,
        account_number: Union[str, None] = None,
        reference: Union[str, None] = None,
        notes: Union[str, None] = None,
    ):
        if not self.is_balance_sufficient(amount):
            raise Exception(messages.LEDGER_INSUFFICIENT_BALANCE)
        
        transaction = Transaction.create_debit_transaction(
            ledger=self,
            amount=amount,
            bank_account_name=bank_account_name,
            account_name=account_name,
            account_number=account_number,
            reference=reference,
            notes=notes,
        )
        self.balance = transaction.balance_after
        self.save()
        return transaction
    
    @classmethod
    def get_ledger_from_reference(cls, value: str, raise_exception: bool = False):
        ledger = Ledger.objects.filter(reference=value).first()
        if not ledger and raise_exception:
            raise NotFound(messages.LEDGER_NOT_FOUND)
        return ledger
    
    def create_credit_transaction(
        self,
        amount: str,
        bank_account_name: Union[str, None] = None,
        account_name: Union[str, None] = None,
        account_number: Union[str, None] = None,
        reference: Union[str, None] = None,
        notes: Union[str, None] = None,
    ):  
        transaction = Transaction.create_credit_transaction(
            ledger=self,
            amount=amount,
            bank_account_name=bank_account_name,
            account_name=account_name,
            account_number=account_number,
            reference=reference,
            notes=notes,
        )
        self.balance = transaction.balance_after
        self.save()
        return transaction
    
    def get_transactions(self, search_keyword: Union[str, None], type: Union[str, None]):
        return Transaction.get_transactions(ledger=self, type=type, search_keyword=search_keyword)
    
    def is_balance_sufficient(self, amount: int):
        return self.balance >= amount
    
    def set_status(self, value: str, notes: Union[str, None] = None):
        self.status = value
        self.save()
        LedgerStatusHistory.create(self, value, notes)
    
    def send_to(self, other_ledger, amount):
        if not self.is_balance_sufficient(amount):
            raise Exception(messages.LEDGER_INSUFFICIENT_BALANCE)
        
        self.create_debit_transaction(
            amount=amount,
            bank_account_name=other_ledger.bank_code,
            account_name=other_ledger.name,
            account_number=other_ledger.virtual_account,
            notes='Send money',
        )
        other_ledger.create_credit_transaction(
            amount=amount,
            bank_account_name=self.bank_code,
            account_name=self.name,
            account_number=self.virtual_account,
            notes='Receive money',
        )
    
    def update_from_callback(self, data: dict):
        # https://docs.instamoney.co/apireference/#fixed-virtual-account-callback
        self.bank_code = data.get('bank_code')
        self.virtual_account = data.get('account_number')

        status = self.status
        status_from_callback = data.get('status')
        if status_from_callback == 'ACTIVE':
            status = self.ACTIVE
        elif status_from_callback == 'PENDING':
            status = self.PENDING
        elif status_from_callback == 'INACTIVE':
            status = self.INACTIVE
        
        if status != self.status:
            self.set_status(status, 'Callback from instamoney')
        self.save()


class Transaction(BaseModel):
    id = models.CharField(max_length=15, primary_key=True, db_index=True)
    ledger = models.ForeignKey(Ledger, on_delete=models.PROTECT, related_name='transactions')
    
    CREDIT = '1'
    DEBIT = '2'
    TYPE_CHOICES = (
        (CREDIT, 'Credit'),
        (DEBIT, 'Debit'),
    )
    type = models.CharField(max_length=1)
    reference = models.CharField(max_length=100, unique=True)
    balance_before = models.IntegerField()
    amount = models.IntegerField()
    balance_after = models.IntegerField()
    bank_account_name = models.CharField(max_length=100, null=True)
    account_name = models.CharField(max_length=100, null=True)
    account_number = models.CharField(max_length=100, null=True)
    notes = models.TextField(null=True)

    @classmethod
    def create_debit_transaction(
        cls,
        ledger: Ledger,
        amount: int,
        bank_account_name: Union[str, None] = None,
        account_name: Union[str, None] = None,
        account_number: Union[str, None] = None,
        reference: Union[str, None] = None,
        notes: Union[str, None] = None,
    ):
        transaction = cls(
            ledger=ledger,
            type=Transaction.DEBIT,
            bank_account_name=bank_account_name,
            account_name=account_name,
            account_number=account_number,
            notes=notes,
            created_at=timezone.now(),
        )
        transaction.set_id()
        transaction.set_reference(reference)
        transaction.set_amount(amount)
        transaction.save()
        return transaction
    
    @classmethod
    def create_credit_transaction(
        cls,
        ledger: Ledger,
        amount: int,
        bank_account_name: Union[str, None] = None,
        account_name: Union[str, None] = None,
        account_number: Union[str, None] = None,
        reference: Union[str, None] = None,
        notes: Union[str, None] = None,
    ):
        transaction = cls(
            ledger=ledger,
            type=Transaction.CREDIT,
            bank_account_name=bank_account_name,
            account_name=account_name,
            account_number=account_number,
            notes=notes,
            created_at=timezone.now(),
        )
        transaction.set_id()
        transaction.set_reference(reference)
        transaction.set_amount(amount)
        transaction.save()
        return transaction
    
    @classmethod
    def get_transactions(cls, ledger: Ledger, type: Union[str, None] = None, search_keyword: Union[str, None] = None):
        transactions = cls.objects.filter(ledger=ledger)
        if type:
            transactions = transactions.filter(type=type)
        if search_keyword:
            transactions = transactions.filter(
                Q(id__icontains=search_keyword) |
                Q(reference__icontains=search_keyword) |
                Q(bank_account_name__icontains=search_keyword) |
                Q(account_number__icontains=search_keyword) |
                Q(account_name__icontains=search_keyword) |
                Q(notes__icontains=search_keyword)
            )
        return transactions.order_by('-id')

    @classmethod
    def get_transaction(cls, id: str, raise_exception: bool = False):
        transaction = cls.objects.filter(id=id).first()
        if not transaction and raise_exception:
            raise NotFound(messages.LEDGER_TRANSACTION_NOT_FOUND)
        return transaction
    
    def set_id(self):
        if self.id:
            raise Exception(messages.LEDGER_TRANSACTION_ID_CANNOT_BE_CHANGED)
        
        # YYYYMMDD0000000
        now = timezone.now()
        last_transaction = self.get_last_transaction(now)
        last_number = 0
        if last_transaction is not None:
            last_number = last_transaction.get_transaction_number()
        
        self.id = now.strftime("%Y%m%d") + f"{last_number + 1:07d}"
    
    def set_reference(self, reference: Union[str, None]):
        if self.reference:
            raise Exception(messages.LEDGER_TRANSACTION_REFERENCE_CANNOT_BE_CHANGED)
        
        if reference is None:
            reference = str(uuid.uuid4()).replace('-', '')
        self.reference = reference
    
    def set_amount(self, value: int):
        if self.amount:
            raise Exception(messages.LEDGER_TRANSACTION_AMOUNT_CANNOT_BE_CHANGED)

        current_balance = self.ledger.balance
        balance_after = 0
        if self.is_debit:
            balance_after = current_balance - value
        elif self.is_credit:
            balance_after = current_balance + value
        
        self.balance_before = current_balance
        self.amount = value
        self.balance_after = balance_after

    def get_transaction_number(self):
        try:
            last_number = self.id[8:]
            return int(last_number)
        except ValueError:
            return 0
    
    def get_last_transaction(self, in_month: datetime):
        return Transaction.objects.filter(
            ledger=self.ledger,
            created_at__year=in_month.year,
            created_at__month=in_month.month,
        ).order_by('-id').first()

    @property
    def is_debit(self):
        return self.type == self.DEBIT
    
    @property
    def is_credit(self):
        return self.type == self.CREDIT
    
    @property
    def origin(self):
        if self.is_credit:
            return self.bank
        return '-'

    @property
    def destination(self):
        if self.is_debit:
            return self.bank
        return '-'
    
    @property
    def bank(self):
        account_name = self.account_name if self.account_name else ''
        bank_account_name = self.bank_account_name if self.bank_account_name else ''
        account_number = self.account_number if self.account_number else ''
        return f"{account_name} - {bank_account_name} {account_number}".strip()



class LedgerStatusHistory(BaseModel):
    ledger = models.ForeignKey(Ledger, on_delete=models.PROTECT, related_name='ledger_histories')
    status = models.CharField(max_length=1)
    notes = models.CharField(max_length=100, null=True)

    @classmethod
    def create(cls, ledger: Ledger, status: str, notes: Union[str, None] = None):
        return cls.objects.create(ledger=ledger, status=status, notes=notes)
