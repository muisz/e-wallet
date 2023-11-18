from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.ledgers.api.v1.serializers import (
    CreateLedgerSerializer,
    CreateTransactionSerializer,
    DetailLedgerSerializer,
    DetailTransactionSerializer,
    ListLedgerSerializer,
    ListTransactionSerializer,
)
from apps.ledgers.models import Ledger, Transaction
from apps.modules.instamoney import RNE


class LedgerViewSet(GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DetailLedgerSerializer

    def get_queryset(self):
        query_params = self.request.query_params
        search_keyword = query_params.get('search')
        bank_code = query_params.get('bank_code')
        return Ledger.get_ledgers(search_keyword, bank_code)

    def create(self, request):
        serializer = CreateLedgerSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        ledger = Ledger.create(
            user=serializer.get_user(),
            name=validated_data['name'],
            bank_code=validated_data['bank_code'],
        )
        response_serializer = self.serializer_class(ledger, context=self.get_serializer_context())
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def list(self, request):
        ledgers = self.paginate_queryset(self.get_queryset())
        serializer = ListLedgerSerializer(ledgers, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, pk):
        ledger = Ledger.get_ledger(pk, raise_exception=True)
        serializer = self.serializer_class(ledger, context=self.get_serializer_context())
        return Response(serializer.data)
    
    @action(methods=['get'], detail=False, permission_classes=())
    def banks(self, request):
        banks = RNE().list_banks()
        return Response(banks)


class TransactionViewSet(GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ListTransactionSerializer

    def get_queryset(self):
        query_params = self.request.query_params
        search_keyword = query_params.get('search')
        type = query_params.get('type')
        
        ledger = Ledger.get_ledger(self.kwargs['ledger_id'], raise_exception=True)
        return ledger.get_transactions(search_keyword, type)
    
    def create(self, request, ledger_id):
        serializer = CreateTransactionSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        ledger = Ledger.get_ledger(ledger_id, raise_exception=True)
        if validated_data.get('type') == Transaction.CREDIT:
            ledger.create_credit_transaction(
                amount=validated_data['amount'],
                bank_account_name=validated_data['bank_account_name'],
                account_name=validated_data['account_name'],
                account_number=validated_data['account_number'],
                notes=validated_data['notes'],
            )
        elif validated_data.get('type') == Transaction.DEBIT:
            ledger.create_debit_transaction(
                amount=validated_data['amount'],
                bank_account_name=validated_data['bank_account_name'],
                account_name=validated_data['account_name'],
                account_number=validated_data['account_number'],
                notes=validated_data['notes'],
            )
        
        return Response(None, status=status.HTTP_201_CREATED)

    def list(self, request, ledger_id):
        transactions = self.paginate_queryset(self.get_queryset())
        serializer = self.serializer_class(transactions, many=True, context=self.get_serializer_context())
        return self.get_paginated_response(serializer.data)
    
    def retrieve(self, request, ledger_id, pk):
        transaction = Transaction.get_transaction(pk, raise_exception=True)
        serializer = DetailTransactionSerializer(transaction, context=self.get_serializer_context())
        return Response(serializer.data)
    

ledger_view = LedgerViewSet
transaction_view = TransactionViewSet
