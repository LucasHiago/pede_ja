import json

from django.utils import timezone
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from django.shortcuts import get_object_or_404, reverse
from django.contrib.auth.models import User
from django.template.loader import get_template

from rest_framework import permissions
from rest_framework import status
from rest_framework.authtoken.models import Token

from django_filters import rest_framework as filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
)

from oauth2_provider.models import (
    Application, 
    AccessToken, 
    RefreshToken
)
from oauthlib.common import generate_token

from fcm_django.models import FCMDevice

from allauth.socialaccount.providers.facebook.views import (
    FacebookOAuth2Adapter
)
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from rest_auth.registration.views import SocialLoginView

from noruh_backend.settings import STATIC_URL, BASE_URL
from noruh_backend.pusher import PusherNotification

from register.convert_json import objects_to_json
from register.models import Profile
from register.models import Employee
from register.models import CuisineType
from register.models import Establishment, EstablishmentPromotions
from register.models import Menu, MenuItem, MenuOffer
from register.models import Bill, BillMember, BillPayment
from register.models import Order
from register.models import Request
from register.models import UserRating
from register.models import Table
from register.models import TokenRecoverPassword
from register.api.exceptions import EstablishmentDoesNotAvaibleAPIException
from .filters import (
    EstablishmentFilter,
    BillMemberFilter
)
from .serializers import (
    ForgotMyPasswordSerializer,
    ProfileSerializerList,
    UserSerializerRegistration,
    UserSerializerResetPassword,
    UserBillSerializer,
    UserBillHistorySerializer,
    UserSerializer,
    EstablishmentSerializer,
    EstablishmentPromotionsSerializer,
    CuisineTypeSerializer,
    MenuSerializer,
    BillSerializerPost,
    BillMemberSerializerList,
    BillMemberSerializerPost,
    BillMemberSerializerConfirm,
    BillMemberSerializerConfirmAll,
    BillMemberSerializerExitWithouPayment,
    BillMemberCancelJoinSerializer,
    OrderSerializerList,
    MultipleOrderSerializer,
    OrderSerializerDiscountPost,
    OrderSerializerUpdateStatus,
    RequestSerializer,
    EvaluationSerializerPost,
    EvaluationSerializerList,
    EvaluationInfoSerializer,
    VerifyIfPromocodeExistsSerializer
)


# Views for Login and Users
class FacebookLogin(SocialLoginView):
    """
    Login with Facebook, needs a access token
    from app and code from user
    """
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):
    """
    Login with Google, needs a access token
    from app and code from user
    """
    adapter_class = GoogleOAuth2Adapter


class ResetPasswordUser(APIView):
    serializer_class = UserSerializerResetPassword
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        user = User.objects.get(id=self.request.user.id)
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user.set_password(serializer.data.get('password1'))
            user.save()
            return Response('Password changed', status=status.HTTP_200_OK)
        return Response('Something went wrong', status=status.HTTP_400_BAD_REQUEST)


class RegistrationUser(APIView):
    serializer_class = UserSerializerRegistration
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        user = self.serializer_class(data=request.data)
        user.is_valid(True)
        user.save()

        application = Application.objects.get()
        token = AccessToken.objects.create(
            user=user.instance,
            application=application,
            token=generate_token(),
            expires=timezone.now() + timezone.timedelta(days=30))
        refresh_token = RefreshToken.objects.create(
            user=user.instance,
            application=application,
            token=generate_token(),
            access_token=token
        )
        response = {
            'access_token': token.token,
            'expires_in': timezone.timedelta(days=30).total_seconds(),
            'token_type': 'Bearer',
            'refresh_token': refresh_token.token
        }
        return Response(response, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request):
        user = self.request.user
        FCMDevice.objects.filter(user=user).delete()
        AccessToken.objects.filter(user=user).delete()
        Token.objects.filter(user=user).delete()
        RefreshToken.objects.filter(user=user).delete()
        return Response("Logout Successfully", status=status.HTTP_200_OK)


class ForgotMyPasswordView(APIView):
    permission_classes = (permissions.AllowAny, )
    serializer_class = ForgotMyPasswordSerializer

    def post(self, request):
        serializer = ForgotMyPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(email=serializer.data.get('email'))
            expiration_time = timezone.now() + timezone.timedelta(days=2)

            token_object = TokenRecoverPassword.objects.create(
                user=user, expiration_time=expiration_time)

            url_path = f'{request.build_absolute_uri(reverse("register:change_password"))}?token_url={token_object.token.hex}'
            user.email_user(
                'Recuperar Senha',
                ' ',
                fail_silently=True,
                html_message=get_template('../templates/noruh_email_files/noruh_email.html').render(
                    {
                        'url_path': url_path,
                        'noruh_img': '{}{}'.format(BASE_URL, STATIC_URL)
                    }
                )
            )
            return Response('Password reset e-mail has been sent', status=status.HTTP_200_OK)
        return Response('Email not found', status=status.HTTP_400_BAD_REQUEST)


class UserLoggedAPIList(ListAPIView):
    """
    Get with infos about the user loged
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = ProfileSerializerList

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)


class UserAPIDetail(ListAPIView):
    """
    This view list a user with your bill active in the moment
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = UserBillSerializer

    def get_queryset(self):
        return BillMember.objects.filter(
            customer=self.request.user, leave_at__isnull=True)


class BillHistoryAPIList(ListAPIView):
    """
    Contains a list with all bills from the user logged
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = UserBillHistorySerializer

    def get_queryset(self):
        return BillMember.objects.filter(customer=self.request.user).order_by('-bill__opening_date')


class ProfileAPIUpdate(RetrieveUpdateAPIView):
    """
    The get and a put, when user can view and update their informations
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)

    def get_object(self):
        queryset = self.get_queryset()
        return get_object_or_404(queryset, id=self.request.user.id)


# Views for Establishments, Bills, Orders, Requests, Menu, and Evaluations
class EstablishmentListAPIView(ListAPIView):
    """
    This view list all establishments with geo_loc in radius from 20km.
    Without geo_loc, list all establishments when enabled=True
    """
    permission_classes = (permissions.AllowAny, )
    serializer_class = EstablishmentSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = EstablishmentFilter

    def get_queryset(self):
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')

        if lat and lng is not None:
            lat = float(lat)
            lng = float(lng)
            radius = 20   # 20km Radius
            point = Point(lng, lat)
            return Establishment.objects.filter(
                enabled=True, geo_loc__distance_lt=(
                    point, Distance(km=radius)))

        return Establishment.objects.filter(enabled=True)


class EstablishmentDetailAPIView(RetrieveAPIView):
    """
    Using the id from establishment on path, get the details from Establishment
    """
    permission_classes = (permissions.AllowAny, )
    serializer_class = EstablishmentSerializer
    queryset = Establishment.objects.all()


class CuisineTypeListAPIView(ListAPIView):
    """
    List all cuisine types from backend
    """
    permission_classes = (permissions.AllowAny, )
    serializer_class = CuisineTypeSerializer

    def get_queryset(self):
        return CuisineType.objects.all()


class MenuListAPIView(ListAPIView):
    """
    List Menu from establishment with all menu_items inside
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = MenuSerializer

    def get_queryset(self):
        id = self.kwargs['establishment_id']
        return Menu.objects.filter(establishment__id=id)


class BillAPIPost(CreateAPIView):
    """
    With this view can open a new Bill
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BillSerializerPost
    queryset = Bill.objects.filter()


class BillMemberAPIView(ListAPIView):
    """
    List all BillMembers from backend
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BillMemberSerializerList
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = BillMemberFilter
    queryset = BillMember.objects.all()


class BillMemberAPICreate(CreateAPIView):
    """
    For join in a bill, use this View
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BillMemberSerializerPost


class BillMemberAPIConfirm(APIView):
    """
    For accept guest in the bill, use this View
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BillMemberSerializerConfirm

    def post(self, request, format=None):
        serializer = BillMemberSerializerConfirm(data=request.data)

        if serializer.is_valid():
            customer_id = serializer['customer_id'].value
            bill_id = serializer['bill_id'].value
            answer = serializer['answer'].value

            bill_member = get_object_or_404(
                BillMember,
                customer__id=customer_id,
                bill__id=bill_id, joined_at=None)

            if BillMember.answer_to_bill_member(bill_member, answer):
                return Response("Member Accepted", status=status.HTTP_200_OK)
            return Response("Member Declined", status=status.HTTP_200_OK)


class BillMemberAPIConfirmAll(APIView):
    """
    For accept all billmembers from bill with
    `joined_at` None, use this View
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BillMemberSerializerConfirmAll

    def post(self, request, format=None):
        context = {'request': self.request}
        write_serializer = BillMemberSerializerConfirmAll(data=request.data,
                                                          context=context)
        write_serializer.is_valid(raise_exception=True)
        BillMember.objects.filter(
            bill_id=write_serializer.data.get('bill_id'),
            joined_at=None).update(
                joined_at=timezone.now())
        return Response('All Bill Members accepted',
                        status=status.HTTP_201_CREATED)


class BillMemberAPIExitWithouPayment(APIView):
    """
    If a Bill desire quit from a bill without payment,
    this View do this
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BillMemberSerializerExitWithouPayment

    def post(self, request, format=None):
        context = {'request': self.request}
        serializer = BillMemberSerializerExitWithouPayment(data=request.data,
                                                           context=context)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        bill_member = BillMember.objects.get(customer=user,
                                             leave_at__isnull=True)
        bill_members = BillMember.objects.filter(
            bill=bill_member.bill, leave_at__isnull=True).count()
        if bill_members == 1:
            bill_member.bill.payment_date = timezone.now()
            bill_member.bill.save()
        bill_member.leave_at = timezone.now()
        bill_member.save()
        return Response('Bill Member Out', status=status.HTTP_200_OK)


class BillMemberAPIJoinCancel(APIView):
    """
    If billmember desire cancel a request for join in a bill,
    can use this View
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BillMemberCancelJoinSerializer

    def post(self, request, format=None):
        serializer = BillMemberCancelJoinSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = self.request.user
            bill = serializer.validated_data
            bill_member = BillMember.objects.filter(bill=bill,
                                                    customer=user,
                                                    leave_at__isnull=True,
                                                    joined_at__isnull=True)
            if bill_member.exists():
                bill_member.delete()
                return Response('Join to Bill Cancelled',
                                status=status.HTTP_200_OK)
            return Response('Dont exists Requests to this Bill',
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors)


class OrderAPIPost(CreateAPIView):
    """
    For create a order, can use this View
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = MultipleOrderSerializer
    queryset = Order.objects

    def create(self, request, *args, **kwargs):
        context = {'request': self.request}
        write_serializer = MultipleOrderSerializer(
            data=request.data, context=context)
        write_serializer.is_valid(raise_exception=True)
        orders = write_serializer.data.get('items')
        orders = list(map(lambda order: Order.create_order(
            order, self.request.user), orders))
        read_serializer = list(map(
            lambda order: OrderSerializerList(order).data, orders))

        items = request.data.get('items')
        bill = Bill.objects.get(id=items[0].get('bill'))
        kitchens = User.objects.filter(
            id__in=Employee.objects.filter(
                establishment=bill.establishment,
                user_type=Employee.USER_KITCHEN).values('user'))
        list_kitchens = kitchens.values_list('id', flat=True)
        waiters = User.objects.filter(
            id__in=Employee.objects.filter(
                establishment=bill.establishment,
                user_type=Employee.USER_WAITER).values('user'))
        list_waiters = waiters.values_list('id', flat=True)
        devices = FCMDevice.objects.filter(
            user_id__in=BillMember.objects.filter(
                bill=bill).values('customer'))
        for order in orders:
            user_full_name = '{} {}'.format(order.user.first_name, order.user.last_name)
            order_dict = {'id': order.id, 'user': order.user.id,
                          'name': user_full_name,
                          'bill': order.bill.id, 'item_id': order.item.id,
                          'item_name': order.item.name,
                          'total_price': order.value_order,
                          'quantity': order.quantity, 
                          'created_at': order.created_at,
                          'canceled_at': order.canceled_at,
                          'kitchen_accepted_at': order.kitchen_accepted_at,
                          'kitchen_finished_at': order.kitchen_finished_at,
                          'status': order.status}
            order_dict = json.dumps(order_dict, default=objects_to_json)
            dict_data = {'key': 'new_order', 'data': order_dict}

            PusherNotification.send_notifications(
                list_kitchens, 'kitchen', 'makes_new_order', order_dict)
            PusherNotification.send_notifications(
                list_waiters, 'waiter', 'makes_new_order', order_dict)
            devices.send_message("Novo Pedido",
                                 "Foi Feito um novo Pedido na sua Conta",
                                 data=dict_data)
        return Response(read_serializer, status=status.HTTP_201_CREATED)


class OrderAPIDiscountPost(CreateAPIView):
    """
    This view, can create orders with discount
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = OrderSerializerDiscountPost
    queryset = Order.objects

    def create(self, request, *args, **kwargs):
        context = {'request': self.request}
        serializer = OrderSerializerDiscountPost(data=request.data,
                                                 context=context)

        if serializer.is_valid():
            # Create order with discount
            user = self.request.user
            bill = Bill.objects.get(id=serializer.data.get('bill_id'))
            menu_item = MenuItem.objects.get(id=serializer.data.get('item_id'))
            menu_offer_id = MenuOffer.objects.get(id=serializer.data.get(
                'menu_offer_id'))
            observation = serializer.data.get('observation')
            value_discount = menu_offer_id.calculate_discount(menu_item)
            order = Order.objects.create(
                user=user, bill=bill,
                item=menu_item, quantity=1, observation=observation,
                status=Order.STATUS_PENDING, value_order=value_discount)

            bill.offers_used_count += 1
            bill.save()

            # Send fcm notifications and pusher web notifications
            kitchens = User.objects.filter(
                id__in=Employee.objects.filter(
                    establishment=bill.establishment,
                    user_type=Employee.USER_KITCHEN).values('user'))
            list_kitchens = kitchens.values_list('id', flat=True)
            devices = FCMDevice.objects.filter(
                user_id__in=BillMember.objects.filter(
                    bill=bill).values('customer'))
            order_dict = {'id': order.id, 'user_id': order.user.id,
                          'bill_id': order.bill.id, 'item_id': order.item.id,
                          'item_name': order.item.name,
                          'quantity': order.quantity,
                          'observation': order.observation,
                          'created_at': order.created_at,
                          'canceled_at': order.canceled_at,
                          'kitchen_accepted_at': order.kitchen_accepted_at,
                          'kitchen_finished_at': order.kitchen_finished_at,
                          'status': order.status}
            order_dict = json.dumps(order_dict, default=objects_to_json)
            dict_data = {'key': 'new_order', 'data': order_dict}

            PusherNotification.send_notifications(
                list_kitchens, 'kitchen', 'makes_new_order', order_dict)
            devices.send_message("Novo Pedido",
                                 "Foi Feito um novo Pedido na sua Conta",
                                 dict_data)

            return Response('Order with Discount Created',
                            status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderAPIUpdate(RetrieveUpdateAPIView):
    """
    When user can change status from a order,
    can use this view
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = OrderSerializerUpdateStatus
    queryset = Order.objects.all()


class RequestAPIView(CreateAPIView):
    """
    For customer requeste a attendance from waiter,
    must use this View
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = RequestSerializer
    queryset = Request.objects.all()

    def perform_create(self, serializer):
        table = Table.objects.get(id=serializer.validated_data.get('table').id)
        if table.establishment.enabled is False:
            raise EstablishmentDoesNotAvaibleAPIException()
        waiters = User.objects.filter(id__in=Employee.objects.filter(
            establishment=table.establishment,
            user_type=Employee.USER_WAITER).values('user'))
        list_waiters = [waiter.id for waiter in waiters]
        data = {'table_name': table.name,
                'username': self.request.user.first_name,
                'table_zone_name': table.table_zone.name}
        PusherNotification.send_notifications(
            list_waiters, 'waiter', 'request_for_waiter', data)
        serializer.save(user=self.request.user)
        serializer.save(status=Request.STATUS_PENDING)


class EvaluationAPIPost(CreateAPIView):
    """
    Needs use this view for create a Evaluation
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = EvaluationSerializerPost
    queryset = UserRating.objects


class EvaluationAPIView(ListAPIView):
    """
    List all evaluations from establishment, needs
    pass the `establishment_id` to path
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = EvaluationSerializerList

    def get_queryset(self):
        id_establishment = self.kwargs['id_establishment']

        if id_establishment is not None:
            return UserRating.objects.filter(
                bill__establishment_id=id_establishment).order_by(
                    'bill__payment_date')
        return UserRating.objects.all()


class EvaluationStatus(APIView):
    """
    This View returns a dict with already_paid and already_rated
    variables. Through this the client(api), can decide if user can create
    a evaluation for establishment
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = EvaluationInfoSerializer

    def post(self, request, format=None):
        serializer = EvaluationInfoSerializer(data=request.data)
        if serializer.is_valid():
            user = self.request.user
            bill = Bill.objects.get(id=serializer.data.get('bill_id'))
            bill_member = get_object_or_404(
                BillMember, customer=user, bill=bill)
            # already_paid, and already_rated both starts False
            already_paid = False
            already_rated = False

            '''If payment_date for this bill exists, the total amount of the
            table account is paid, then all bill_members for this table, can
            create a evaluation for this establishment'''
            if bill.payment_date is not None:
                already_paid = True

            '''Condition for a user specific, if user made a payment, for that
            bill, he can create a evalution for this establishment.'''
            if BillPayment.objects.filter(bill=bill, bill_member_customer=user).exists():
                already_paid = True

            '''The user, only create a evaluation, if user have a evaluation,
            he cannot create another evaluation for this bill'''
            if UserRating.objects.filter(bill=bill, user=bill_member).exists():
                already_rated = True

            evaluation_info = {'already_paid': already_paid,
                               'already_rated': already_rated}
            return Response(evaluation_info, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyIfPromocodeIsEnabledView(APIView):
    """
    This view verify if promocode is enable or Not
    """
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = VerifyIfPromocodeExistsSerializer

    def post(self, request, format=None):
        serializer = VerifyIfPromocodeExistsSerializer(data=request.data)

        if serializer.is_valid():
            promocode_object = get_object_or_404(
                EstablishmentPromotions,
                establishment__id=serializer.data.get('establishment_id'),
                promocode__exact=serializer.data.get('promocode'))

            if not promocode_object.enabled:
                return Response('This promocode is Disable',
                                status=status.HTTP_406_NOT_ACCEPTABLE)

            promocode = EstablishmentPromotionsSerializer(
                promocode_object).data
            return Response(promocode, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
