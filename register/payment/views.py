# Classes for Payment
import json
import uuid

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status

from fcm_django.models import FCMDevice

from noruh_backend.settings import MOIP_TAX_PERCENTAGE, WEBSITE_NORUH
from noruh_backend.firestore_connect import NoruhFireStore

from register.models import (
    Bill,
    BillMember,
    BillPayment,
    EstablishmentPromotions,
    MoipWirecardAPP,
    MoipWirecardCustomer,
    Profile,
    UserPayment,
    UserCreditCard,
)
from .moip import Moip, MoipAPP
from .tasks import verify_payment
from .serializers import (
    CreateAppSerializer,
    CreateCreditCardSerializer,
    CreditCardSerializer,
    CreatePaymentOnlineSerializer,
    CreatePaymentOfflineSerializer,
    MoipWirecardNoruhSerializer,
    PaymentStatusSerializer,
)
from .utils import (
    create_app,
    create_credit_card_on_moip,
    create_customer_on_moip,
    create_order_parse_moip,
    create_order_establishment_parse_moip,
    create_payment_parse_moip,
    create_wirecard_noruh,
)
# EndPoints for Payment


class CreateAppAPIPost(APIView):
    serializer_class = CreateAppSerializer
    permission_classes = (permissions.IsAdminUser, )

    def post(self, request, format=None):
        serializer = CreateAppSerializer(data=request.data)

        if serializer.is_valid():
            parameters = create_app(serializer.data)

            moip = MoipAPP(token=serializer.data[
                           'token'], key=serializer.data['key'])
            app = moip.create_app(parameters)
            app = json.loads(app)

            if 'ERROR' in app:
                return Response(app, status=status.HTTP_400_BAD_REQUEST)

            app_id = app['id']
            website = app['website']
            access_token = app['accessToken']
            description = app['description']
            name = app['name']
            secret = app['secret']
            redirect_uri = app['redirectUri']
            created_at = app['createdAt']
            updated_at = app['updatedAt']

            MoipWirecardAPP.objects.create(app_id=app_id, website=website, access_token=access_token,
                                           description=description, name=name, secret=secret, redirect_uri=redirect_uri,
                                           created_at=created_at, updated_at=updated_at)
            return Response(app, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateWirecardNoruhAPIPost(APIView):
    serializer_class = MoipWirecardNoruhSerializer
    permission_classes = (permissions.IsAdminUser, )

    def post(self, request, format=None):
        serializer = MoipWirecardNoruhSerializer(data=request.data)

        if serializer.is_valid():
            parameters = create_wirecard_noruh(serializer.data)

            app = MoipWirecardAPP.objects.get(website=WEBSITE_NORUH)
            moip = Moip(app.access_token)

            customer = moip.create_wirecard(parameters)
            customer = json.loads(customer)

            if 'errors' in customer:
                return Response(customer, status=status.HTTP_400_BAD_REQUEST)

            id_wirecard = customer['id']
            login = customer['login']
            access_token = customer['accessToken']
            type = customer['type']
            name = customer['person']['name']
            last_name = customer['person']['lastName']
            birth_date = customer['person']['birthDate']
            number_cpf = customer['person']['taxDocument']['number']
            street = customer['person']['address']['street']
            street_number = customer['person']['address']['streetNumber']
            district = customer['person']['address']['district']
            zip_code = customer['person']['address']['zipCode']
            city = customer['person']['address']['city']
            state = customer['person']['address']['state']
            country_code = customer['person']['phone']['countryCode']
            area_code = customer['person']['phone']['areaCode']
            number = customer['person']['phone']['number']
            number_rg = customer['person']['identityDocument']['number']
            issuer = customer['person']['identityDocument']['issuer']
            issue_date = customer['person']['identityDocument']['issueDate']
            created_at = customer['createdAt']
            link_account = customer['_links']['self']['href']
            set_password = customer['_links']['setPassword']['href']

            MoipWirecardCustomer.objects.create(observation='Noruh', id_wirecard=id_wirecard, login=login, access_token=access_token,
                                                channel_id=app, type=type, email=login, name=name, last_name=last_name,
                                                birth_date=birth_date, number_cpf=number_cpf, street=street,
                                                street_number=street_number, district=district, zip_code=zip_code,
                                                city=city, state=state, country_code=country_code, area_code=area_code,
                                                number=number, number_rg=number_rg, issuer=issuer, issue_date=issue_date,
                                                created_at=created_at, link_account=link_account, set_password=set_password)

            return Response(customer, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListCustomerAPIGet(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request, format=None):
        user = UserPayment.objects.get(user__id=self.request.user.id)
        parameters = user.moip_user_id

        app = MoipWirecardAPP.objects.get(website=WEBSITE_NORUH)
        wirecard = MoipWirecardCustomer.objects.get(channel_id=app)
        moip = Moip(wirecard.access_token)
        customer = moip.get_customer(parameters)
        customer = json.loads(customer)

        return Response(customer)


class CreateCreditCardPost(APIView):
    serializer_class = CreateCreditCardSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request, format=None):
        serializer = CreateCreditCardSerializer(data=request.data)

        if serializer.is_valid():
            user = User.objects.get(id=self.request.user.id)

            if not user.profile.phone_number:
                return Response('You cannot create a Credit Card Without phone Number',
                                status=status.HTTP_412_PRECONDITION_FAILED)

            MoipWirecardAPP.objects.get(website=WEBSITE_NORUH)
            noruh_wirecard = MoipWirecardCustomer.objects.get(
                observation='Noruh')
            access_token = noruh_wirecard.access_token
            moip = Moip(access_token)

            if not UserPayment.objects.filter(user=user).exists():
                user_payment = create_customer_on_moip(
                    moip, serializer.data, user)
                if user_payment.get('status') == 400:
                    return Response(user_payment.get('response'), status=status.HTTP_400_BAD_REQUEST)

                credit_card = create_credit_card_on_moip(
                    moip, serializer.data, user,
                    user_payment.get('user_payment'))
                if credit_card.get('status') == 400:
                    return Response(credit_card.get('response'), status=status.HTTP_400_BAD_REQUEST)
                return Response(credit_card.get('credit_card'), status=status.HTTP_201_CREATED)

            user_payment = UserPayment.objects.get(user=user)
            credit_card = create_credit_card_on_moip(
                moip, serializer.data, user, user_payment)
            if credit_card.get('status') == 400:
                return Response(credit_card.get('response'), status=status.HTTP_400_BAD_REQUEST)

            return Response(credit_card.get('credit_card'),
                            status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ListCreditCards(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = CreditCardSerializer

    def get_queryset(self):
        return UserCreditCard.objects.filter(
            user_payment__user=self.request.user)


class DeleteCreditCard(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = CreditCardSerializer

    def delete(self, request, pk, format=None):
        credit_card = UserCreditCard.objects.get(id=self.kwargs.get('pk'))

        app = MoipWirecardAPP.objects.get(website=WEBSITE_NORUH)
        wirecard = get_object_or_404(
            MoipWirecardCustomer, channel_id=app, observation='Noruh')
        moip = Moip(wirecard.access_token)

        customer = moip.delete_creditcard(credit_card.id_moip_card)
        if customer != 200:
            return Response(customer)
        credit_card.delete()
        return Response(customer, status=status.HTTP_200_OK)


class CreatePaymentPostOnline(APIView):
    serializer_class = CreatePaymentOnlineSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request, format=None):
        serializer = CreatePaymentOnlineSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.data
            bill_id = data.get('bill_id')
            value = data.get('value')
            user_id = data.get('user_id')
            credit_card_id = data.get('credit_card_id')
            cvc = data.get('cvc')
            noruh_fee = data.get('noruh_fee')
            promocode = data.get('promocode')
            payment_uuid = data.get('payment_uuid')

            if BillMember.objects.filter(bill__id=bill_id, customer__id=user_id).exists() is False:
                return Response('Dont exists Bill with this User', status=status.HTTP_412_PRECONDITION_FAILED)

            if not noruh_fee:
                noruh_fee = 0.0

            noruh_fee = (float(noruh_fee))
            value = (float(value))

            own_id = str('Noruh_' + str(uuid.uuid4()))

            bill = get_object_or_404(Bill, id=bill_id)
            value_paid = bill.value_paid
            establishment = bill.establishment
            value_establishment = value
            id_moip_wirecard = get_object_or_404(
                MoipWirecardCustomer, establishment=establishment)
            id_moip_wirecard_establishment = id_moip_wirecard.id_wirecard
            noruh_wirecard = get_object_or_404(
                MoipWirecardCustomer, observation='Noruh')
            id_moip_wirecard_noruh = noruh_wirecard.id_wirecard
            customer_moip_instance = get_object_or_404(
                UserPayment, user_id=user_id)
            customer_moip = customer_moip_instance.moip_user_id

            if value_paid is None:
                value_paid = 0

            value = value + noruh_fee

            if establishment.pays_payment_tax is False:
                fee_payor_est = False
                fee_payor_noruh = True
                value_establishment = (value - noruh_fee)
                value_noruh_fee = noruh_fee
            if establishment.pays_payment_tax is True:
                fee_payor_est = True
                fee_payor_noruh = False
                if establishment.payment_tax > MOIP_TAX_PERCENTAGE:
                    value = value - noruh_fee
                    tax_noruh = float(establishment.payment_tax) - \
                        float(MOIP_TAX_PERCENTAGE)

                    tax_noruh_value = tax_noruh * value
                    value_noruh_fee = noruh_fee + tax_noruh_value
                    value_establishment = value - value_noruh_fee
                else:
                    value_noruh_fee = noruh_fee
                    value_establishment = value - noruh_fee

            value_noruh_fee = round(value_noruh_fee, 2)
            value_establishment = round(value_establishment, 2)
            value = int(value * (100))
            value_noruh_fee = int(value_noruh_fee * (100))
            value_establishment = int(value_establishment * (100))

            promocode_obj = None
            if promocode is not None:
                promocode_obj = get_object_or_404(
                    EstablishmentPromotions,
                    establishment=bill.establishment,
                    promocode__exact=promocode)

                if BillPayment.objects.filter(
                        bill=bill, promocode=promocode_obj,
                        status_payment__in=[
                            BillPayment.STATUS_OFFLINE_APPROVED,
                            BillPayment.STATUS_AUTHORIZED]).exists():
                    return Response(
                        'This promocode has been used on this Bill',
                        status=status.HTTP_406_NOT_ACCEPTABLE)

                value = (value - (float(promocode_obj.value) * 100))
                value_establishment = (value_establishment - float(promocode_obj.value) * 100)

            user_logged = get_object_or_404(User, id=self.request.user.id)
            user_credit_card = get_object_or_404(
                UserCreditCard, id_moip_card=credit_card_id)

            full_name = user_credit_card.full_name
            birth_date = user_credit_card.birth_date
            number_doc = user_credit_card.number_doc
            type_doc = user_credit_card.type_doc

            profile = get_object_or_404(Profile, user=user_logged)
            phone = profile.phone_number
            country_code = int(str(phone)[:2])
            area_code = int(str(phone)[2:4])
            phone_number = int(str(phone)[4:13])

            if value_noruh_fee <= 0.0:
                data_order = {"payment_uuid": payment_uuid, "value": value,
                              "customer_moip": customer_moip,
                              "id_moip_wirecard_establishment": id_moip_wirecard_establishment,
                              "value_establishment": value_establishment}

                parameters_order = create_order_establishment_parse_moip(
                    data_order)
            else:
                data_order = {"payment_uuid": payment_uuid, "value": value,
                              "customer_moip": customer_moip,
                              "fee_payor_est": fee_payor_est,
                              "id_moip_wirecard_establishment": id_moip_wirecard_establishment,
                              "value_establishment": value_establishment,
                              "fee_payor_noruh": fee_payor_noruh,
                              "id_moip_wirecard_noruh": id_moip_wirecard_noruh,
                              "value_noruh_fee": value_noruh_fee}

                parameters_order = create_order_parse_moip(data_order)

            access_token = noruh_wirecard.access_token
            moip = Moip(access_token)

            order = moip.post_order(parameters_order)
            order = json.loads(order)

            data_payment = {"credit_card_id": credit_card_id, "cvc": cvc,
                            "full_name": full_name,
                            "birth_date": str(birth_date),
                            "type_doc": type_doc,
                            "number_document": number_doc,
                            "country_code": country_code,
                            "area_code": area_code,
                            "phone_number": phone_number,
                            "lat": establishment.geo_loc.x,
                            "lng": establishment.geo_loc.y}

            parameters_payment = create_payment_parse_moip(data_payment)
            payment = moip.post_payment(order.get('id'), parameters_payment)
            payment = json.loads(payment)

            id_payment_moip = payment.get('id')
            status_payment = payment.get('status')

            value_noruh_fee = (value_noruh_fee / 100)
            value = (value / 100)
            moip_percentage = value * MOIP_TAX_PERCENTAGE
            moip_fee = (value - moip_percentage) - 0.69
            moip_fee = value - moip_fee

            bill_member = get_object_or_404(
                BillMember, customer=user_logged,
                bill=bill, leave_at__isnull=True)

            bill_payment = BillPayment.objects.create(
                payment_uuid=payment_uuid, establishment=establishment,
                status_payment=status_payment, bill=bill, value=value,
                bill_member=bill_member, credit_card=user_credit_card,
                user_moip_id=customer_moip_instance,
                id_payment_moip=id_payment_moip,
                promocode=promocode_obj, noruh_fee=value_noruh_fee,
                moip_fee=moip_fee)
            user_id = user_logged.id
            verify_payment.delay(
                id_payment_moip, bill_id, value_paid, value, user_id)
            return Response(payment, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreatePaymentPostOffline(APIView):
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = CreatePaymentOfflineSerializer

    def post(self, request, format=None):
        context = {'request': self.request}
        serializer = CreatePaymentOfflineSerializer(data=request.data, context=context)

        if serializer.is_valid():
            data = serializer.data
            bill_id = data.get('bill_id')
            noruh_fee = data.get('noruh_fee')
            promocode = data.get('promocode')
            value = data.get('value')
            value = float(value)

            if not noruh_fee:
                noruh_fee = 0.0

            bill = get_object_or_404(Bill, id=bill_id)
            value = value + float(noruh_fee)

            bill_member = get_object_or_404(
                BillMember, customer=self.request.user,
                bill=bill, leave_at__isnull=True)

            promocode_obj = None
            if promocode is not None:
                promocode_obj = get_object_or_404(
                    EstablishmentPromotions,
                    establishment=bill.establishment,
                    promocode__exact=promocode)

                if BillPayment.objects.filter(
                        bill=bill, promocode=promocode_obj,
                        status_payment__in=[
                            BillPayment.STATUS_OFFLINE_APPROVED,
                            BillPayment.STATUS_AUTHORIZED]).exists():
                    return Response(
                        'This promocode has been used on this Bill',
                        status=status.HTTP_406_NOT_ACCEPTABLE)

                value = (value - float(promocode_obj.value))

            payment_uuid = str('Noruh_' + str(uuid.uuid4()))

            bill_payment = BillPayment.objects.create(
                payment_uuid=payment_uuid, establishment=bill.establishment,
                status_payment=BillPayment.STATUS_OFFLINE_PENDING,
                date=timezone.now(), bill=bill, value=value,
                noruh_fee=noruh_fee, bill_member=bill_member,
                promocode=promocode_obj)

            data_notification = bill_payment.notification_payload(key='payment_created')

            devices = FCMDevice.objects.filter(
                user__in=BillMember.objects.filter(
                    bill=bill_payment.bill,
                    leave_at__isnull=True).values('customer'))
            devices.send_message(
                "Pagamento em Analise",
                f'Pagamento offline de {bill_payment.value} criado e em analise pelo garçom',
                icon=bill_payment.bill.establishment.logo_url.url,
                data=data_notification)

            bill_payment.send_pusher_notification(bill, self.request.user)

            noruh_firestore = NoruhFireStore()
            noruh_firestore.add_data_on_collection(data_notification)

            return Response(
                'Payment under review', status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StatusBillPaymentApiView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = PaymentStatusSerializer

    def get_queryset(self):
        return BillPayment.objects.filter(
            bill__id=self.kwargs.get('bill_id')).order_by('-status_updated')


class StatusUserPaymentApiView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = PaymentStatusSerializer

    def get_queryset(self):
        return BillPayment.objects.filter(
            user__id=self.kwargs.get('user_id')).order_by('-status_updated')
