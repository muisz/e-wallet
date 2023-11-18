from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.ledgers.models import Ledger, Transaction
from apps.modules.instamoney import RNE
from apps.users.models import User as UserModel
from apps.utils import messages
from apps.utils.serializers import ChoiceDisplayFieldSerializer

User: UserModel = get_user_model()


class CreateLedgerSerializer(serializers.Serializer):
    user = serializers.IntegerField()
    name = serializers.CharField()
    bank_code = serializers.CharField()

    _user = None

    def validate_user(self, value):
        user = User.get_by_id(value, raise_exception=True)
        self._user = user
        return value

    def validate_bank_code(self, value):
        rne = RNE()
        if not rne.is_valid_bank_code(value):
            raise ValidationError(messages.LEDGER_INVALID_BANK_CODE)
        return value

    def get_user(self):
        return self._user


class DetailLedgerSerializer(serializers.ModelSerializer):
    status = ChoiceDisplayFieldSerializer(Ledger.STATUS_CHOICES)
    
    class Meta:
        model = Ledger
        fields = (
            "id",
            "name",
            "virtual_account",
            "balance",
            "reference",
            "bank_code",
            "status",
            "created_at",
        )


class ListLedgerSerializer(serializers.ModelSerializer):
    status = ChoiceDisplayFieldSerializer(Ledger.STATUS_CHOICES)

    class Meta:
        model = Ledger
        fields = (
            "id",
            "name",
            "virtual_account",
            "bank_code",
            "status",
            "created_at",
        )


class ListTransactionSerializer(serializers.ModelSerializer):
    origin = serializers.SerializerMethodField()
    destination = serializers.SerializerMethodField()
    type = ChoiceDisplayFieldSerializer(Transaction.TYPE_CHOICES)
    
    def get_origin(self, obj):
        return obj.origin
    
    def get_destination(self, obj):
        return obj.destination

    class Meta:
        model = Transaction
        fields = (
            "id",
            "ledger",
            "type",
            "balance_before",
            "amount",
            "balance_after",
            "origin",
            "destination",
            "notes",
            "created_at",
        )


class DetailTransactionSerializer(serializers.ModelSerializer):
    type = ChoiceDisplayFieldSerializer(Transaction.TYPE_CHOICES)

    class Meta:
        model = Transaction
        fields = (
            "id",
            "ledger",
            "type",
            "reference",
            "balance_before",
            "amount",
            "balance_after",
            "bank_account_name",
            "account_name",
            "account_number",
            "notes",
        )


class CreateTransactionSerializer(serializers.Serializer):
    type = serializers.ChoiceField(Transaction.TYPE_CHOICES)
    amount = serializers.IntegerField()
    bank_account_name = serializers.CharField(allow_null=True)
    account_name = serializers.CharField(allow_null=True)
    account_number = serializers.CharField(allow_null=True)
    notes = serializers.CharField(allow_null=True)
