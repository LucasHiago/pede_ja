# SerializerClasses for Payment
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .utils import int_max_length, int_min_length

from register.models import (
    UserCreditCard,
    Bill,
    BillMember,
    BillPayment,
    EstablishmentPromotions
)
from .exceptions import (
    UserHasBeenPaymentException,
    TheSameUUIDPaymentException,
    NotPartOfThisBillForPaymentException,
    MustPayTheValueFromAllBillPaymentException,
    YouCanOnlyPayWhatsMissingFromTheBill,
    LimitsForPayNoruhFee,
)


class CreateAppSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    site = serializers.CharField(required=True)
    redirect_uri = serializers.CharField(required=True)
    key = serializers.CharField(required=True)
    token = serializers.CharField(required=True)

    def validate(self, data):
        if data['name'] is None:
            raise serializers.ValidationError('You cannot create a APP without name')
        return data

    def create(self, validated_data):
        return super(CreateAppSerializer(**validated_data))


class MoipWirecardNoruhSerializer(serializers.Serializer):
    # personal informations
    email = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    birth_date = serializers.CharField(help_text='Padrão: aaaa-mm-dd')
    # cpf
    number_cpf = serializers.CharField(
        help_text='Numero do CPF, somente numeros. Ex: 11122233344',
        required=True)
    # id_document
    number_rg = serializers.CharField(
        help_text='Ex: Somente números', required=True)
    issuer = serializers.CharField()
    issue_date = serializers.CharField()
    # phone informations
    country_code = serializers.CharField(
        help_text='Ex: código do País. Ex: 55')
    area_code = serializers.CharField()
    phone_number = serializers.CharField()
    # address informations
    street = serializers.CharField()
    street_number = serializers.CharField()
    district = serializers.CharField()
    zip_code = serializers.CharField(help_text='Ex: Somente números')
    city = serializers.CharField()
    state = serializers.CharField(help_text='Ex: Sigla do Estado.')

    def create(self, validated_data):
        return super(MoipWirecardNoruhSerializer(**validated_data))


# CreditCard"
class CreateCreditCardSerializer(serializers.Serializer):
    # Credit Card informations
    expiration_month = serializers.CharField(
        validators=[int_min_length(2), int_max_length(2)])
    expiration_year = serializers.CharField(
        validators=[int_min_length(4), int_max_length(4)])
    number_card = serializers.CharField()
    cvc = serializers.CharField()

    # Personal informations
    full_name = serializers.CharField(max_length=65)
    birth_date = serializers.DateField()
    city = serializers.CharField(max_length=30)
    district = serializers.CharField(max_length=30)
    street = serializers.CharField(max_length=40)
    street_number = serializers.CharField(max_length=5)
    zip_code = serializers.CharField(max_length=15)
    state = serializers.CharField(max_length=30)
    country = serializers.CharField(max_length=30)

    # document: cpf or cnpj for type, and number has a number for document
    type_document = serializers.CharField(max_length=4, help_text='CPF or CNPJ')
    number_document = serializers.CharField(help_text='Can be CPF or CNPJ')

    def validate(self, data):
        if data['number_document'] is None:
            raise serializers.ValidationError(
                'You cannot create a Customer without CPF')
        return data

    def create(self, validated_data):
        return super(CreateCreditCardSerializer(**validated_data))


class CreditCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCreditCard
        fields = ['id', 'last_four_digits',
                  'brand_card', 'id_moip_card',
                  'user_payment']


class CreatePaymentOnlineSerializer(serializers.Serializer):
    # Payment Informations
    payment_uuid = serializers.CharField(required=True, max_length=65)
    bill_id = serializers.IntegerField(required=True)
    value = serializers.DecimalField(
        max_digits=6, decimal_places=2, required=True)
    user_id = serializers.IntegerField(required=True)
    credit_card_id = serializers.CharField(required=True)
    cvc = serializers.IntegerField(required=True)
    noruh_fee = serializers.DecimalField(max_digits=6, decimal_places=2)
    promocode = serializers.CharField(required=False)

    def validate(self, data):
        user = get_object_or_404(User, id=data.get('user_id'))
        bill = get_object_or_404(Bill, id=data.get('bill_id'))
        bill_member = get_object_or_404(
            BillMember, customer=user, bill=bill, leave_at__isnull=True)
        noruh_fee = data.get('noruh_fee')

        if not data.get('noruh_fee'):
            noruh_fee = 0.0

        if BillPayment.objects.filter(payment_uuid=data.get('payment_uuid')).exists():
            raise TheSameUUIDPaymentException()

        if BillPayment.objects.filter(
            bill=bill, bill_member=bill_member, status_payment__in=[
                BillPayment.STATUS_AUTHORIZED,
                BillPayment.STATUS_OFFLINE_APPROVED,
                BillPayment.STATUS_OFFLINE_PENDING,
                BillPayment.STATUS_IN_ANALYSIS]).exists():
            raise UserHasBeenPaymentException()

        if BillMember.objects.filter(bill=bill, leave_at__isnull=True).count() == 1:
            if data.get('value') < (((bill.orders_total() + bill.couvert_for_all()) - bill.value_paid_without_noruh_fee())):
                raise MustPayTheValueFromAllBillPaymentException()

        value = float(data.get('value')) + float(noruh_fee)
        all_value_bill = float("{:.2f}".format(bill.all_value_bill()))

        if value > (all_value_bill - float(bill.value_paid)):
            raise YouCanOnlyPayWhatsMissingFromTheBill()

        if data.get('noruh_fee'):
            if bill.bill_noruh_fee_count() >= bill.number_of_customers():
                raise LimitsForPayNoruhFee()

        if data.get('promocode') is not None:
            if EstablishmentPromotions.objects.filter(
                    establishment=bill.establishment, enabled=True,
                    promocode__exact=data.get('promocode')).exists():
                return data
            raise serializers.ValidationError('This promocode doesnt exists')

        return data

    def create(self, validated_data):
        return super(CreatePaymentOnlineSerializer(**validated_data))


class CreatePaymentOfflineSerializer(serializers.Serializer):
    bill_id = serializers.IntegerField(required=True)
    value = serializers.DecimalField(max_digits=6, decimal_places=2, required=True)
    noruh_fee = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
    promocode = serializers.CharField(required=False)

    def validate(self, data):
        user = self.context.get('request').user
        bill = get_object_or_404(Bill, id=data.get('bill_id'))
        bill_member = get_object_or_404(
            BillMember, customer=user, bill=bill, leave_at__isnull=True)
        noruh_fee = data.get('noruh_fee')

        if not data.get('noruh_fee'):
            noruh_fee = 0.0

        if not BillMember.objects.filter(bill=bill, customer=user):
            raise NotPartOfThisBillForPaymentException()

        if BillMember.objects.filter(bill=bill, leave_at__isnull=True).count() == 1:
            if data.get('value') < (((bill.orders_total() + bill.couvert_for_all()) - bill.value_paid_without_noruh_fee())):
                raise MustPayTheValueFromAllBillPaymentException()

        value = float(data.get('value')) + float(noruh_fee)
        all_value_bill = float("{:.2f}".format(bill.all_value_bill()))

        if value > (all_value_bill - float(bill.value_paid)):
            raise YouCanOnlyPayWhatsMissingFromTheBill()

        if BillPayment.objects.filter(
            bill_member=bill_member, bill=bill, status_payment__in=[
                BillPayment.STATUS_AUTHORIZED,
                BillPayment.STATUS_OFFLINE_APPROVED,
                BillPayment.STATUS_OFFLINE_PENDING,
                BillPayment.STATUS_IN_ANALYSIS]).exists():
            raise UserHasBeenPaymentException()

        if data.get('noruh_fee'):
            if bill.bill_noruh_fee_count() >= bill.number_of_customers():
                raise LimitsForPayNoruhFee()

        if data.get('promocode') is not None:
            if EstablishmentPromotions.objects.filter(
                    establishment=bill.establishment, enabled=True,
                    promocode__exact=data.get('promocode')).exists():
                return data
            raise serializers.ValidationError('This promocode doesnt exist')

        return data

    def create(self, validated_data):
        return super(CreatePaymentOfflineSerializer(**validated_data))


class PaymentStatusSerializer(serializers.ModelSerializer):
    credit_card_last_four_digits = serializers.SerializerMethodField()
    brand_card = serializers.SerializerMethodField()
    bill_table_name = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = BillPayment
        fields = ['establishment', 'status_payment',
                  'credit_card_last_four_digits',
                  'brand_card', 'bill_table_name',
                  'status_updated', 'date', 'bill',
                  'value', 'user_moip_id', 'user', 'id_payment_moip']

    def get_credit_card_last_four_digits(self, obj):
        if hasattr(obj.credit_card, 'last_four_digits'):
            return obj.credit_card.last_four_digits
        return None

    def get_brand_card(self, obj):
        if hasattr(obj.credit_card, 'brand_card'):
            return obj.credit_card.brand_card
        return None

    def get_bill_table_name(self, obj):
        return obj.bill.table.name

    def get_user(self, obj):
        return obj.bill_member.customer.id
