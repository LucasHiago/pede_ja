import datetime
import json

from django.db.models import Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import validate_password

from register.convert_json import objects_to_json

from noruh_backend.settings import ORDER_REMOTE
from noruh_backend.pusher import PusherNotification

from fcm_django.models import FCMDevice
from rest_framework import serializers
from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField
)

from register.api.exceptions import (
    TableDoesNotExistsAPIException,
    TableDoesntAvaibleAPIException,
    OpenBillAPIException,
    NotPartOfThisBillException,
    BillDoestNotAvaibleForJoinAPIException,
    EstablishmentDoesNotAvaibleAPIException,
    BillAlreadyBeenPaidException,
    LimitDiscountAmoutIsOverAPIException,
    ItemDoesntBelongToCategoryOffer,
)

from django.contrib.auth.models import User
from register.models import Amenity, CuisineType
from register.models import Establishment
from register.models import Menu, MenuItem, MenuOffer, ItemCategory
from register.models import Bill, BillMember, BillPayment, Order
from register.models import Request
from register.models import UserRating
from register.models import Profile, Employee
from register.models import EstablishmentOperatingHours
from register.models import EstablishmentPromotions
from register.models import EstablishmentEvents
from register.models import EstablishmentPhoto
from register.models import Table


class ForgotMyPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, data):
        get_object_or_404(User, email=data.get('email'))
        return data


class UserSerializerResetPassword(serializers.Serializer):
    password1 = serializers.CharField(required=True)
    password2 = serializers.CharField(required=True)

    def validate(self, data):
        password1 = data.get('password1')
        password2 = data.get('password2')

        if not (password1 and password2):
            raise serializers.ValidationError('The password fields cannot be null')

        if password1 != password2:
            raise serializers.ValidationError('The passwords are differents')

        validate_password(password1)
        return data


class ProfileSerializerList(ModelSerializer):
    user_id = SerializerMethodField()
    username = SerializerMethodField()
    email = SerializerMethodField()
    first_name = SerializerMethodField()
    last_name = SerializerMethodField()
    date_joined = SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['user_id', 'username', 'email',
                  'first_name', 'last_name',
                  'date_joined', 'cpf', 'gender',
                  'image_url', 'fcm_token',
                  'phone_number', 'average_value_spent',
                  'visited_establishments_count']

    def get_user_id(self, obj):
        return obj.user.id

    def get_username(self, obj):
        return obj.user.username

    def get_email(self, obj):
        return obj.user.email

    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name

    def get_date_joined(self, obj):
        return obj.user.date_joined


class ProfileSerializer(ModelSerializer):

    class Meta:
        model = Profile
        fields = ['image_url', 'cpf', 'gender',
                  'fcm_token', 'device_id',
                  'device_os',
                  'phone_number']


class UserSerializerRegistration(serializers.Serializer):
    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)
    password1 = serializers.CharField(required=True)
    password2 = serializers.CharField(required=True)

    def validate(self, data):
        password1 = data.get('password1')
        password2 = data.get('password2')

        if User.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError('A user already exists with this username')

        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError('A user already exists with this email')

        if not (password1 and password2):
            raise serializers.ValidationError('The password fields cannot be null')

        if password1 != password2:
            raise serializers.ValidationError('The passwords are differents')

        validate_password(password1)
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            password=validated_data.get('password1'))
        user.save()
        return user


class UserSerializer(ModelSerializer):
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name',
                  'last_name', 'email', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        image_url = profile_data.get('image_url')
        fcm_token = profile_data.get('fcm_token')
        device_id = profile_data.get('device_id')
        device_os = profile_data.get('device_os')
        profile = instance.profile

        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        field_image = profile_data.get('image_url', image_url)
        field_fcm = profile_data.get('fcm_token', fcm_token)
        field_device_id = profile_data.get('device_id', device_id)
        field_device_os = profile_data.get('device_os', device_os)

        if field_image:
            profile.image_url = profile_data.get('image_url', profile.image_url)

        if field_fcm and field_device_id:
            device = FCMDevice.objects.filter(
                user=instance, active=True,
                device_id=profile.device_id,
                registration_id=profile.fcm_token)

            if device.exists():
                profile.fcm_token = profile_data.get(
                    'fcm_token', profile.fcm_token)
                profile.device_id = profile_data.get(
                    'device_id', profile.device_id)
                device.update(
                    device_id=field_device_id, registration_id=field_fcm,
                    type=field_device_os, active=True)
            else:
                profile.fcm_token = profile_data.get(
                    'fcm_token', profile.fcm_token)
                profile.device_id = profile_data.get(
                    'device_id', profile.device_id)
                FCMDevice.objects.create(
                    name=instance.email, active=True,
                    user=instance, device_id=field_device_id,
                    registration_id=field_fcm, type=field_device_os)

        profile.cpf = profile_data.get('cpf', profile.cpf)
        profile.gender = profile_data.get('gender', profile.gender)
        profile.phone_number = profile_data.get('phone_number', profile.phone_number)
        profile.fcm_token = profile_data.get('fcm_token', profile.fcm_token)
        profile.device_os = profile_data.get('device_os', profile.device_os)
        profile.device_id = profile_data.get('device_id', profile.device_id)
        profile.save()

        return instance


class AmenitySerializer(ModelSerializer):

    class Meta:
        model = Amenity
        fields = ['name', 'description']


class CuisineTypeSerializer(ModelSerializer):

    class Meta:
        model = CuisineType
        fields = ['name']


class EstablishmentOperatingHoursSerializer(ModelSerializer):

    class Meta:
        model = EstablishmentOperatingHours
        fields = ['opening_time', 'closing_time', 'dow']


class EstablishmentPromotionsSerializer(ModelSerializer):
    establishment_id = SerializerMethodField()

    class Meta:
        model = EstablishmentPromotions
        fields = ['establishment_id', 'id', 'promocode',
                  'value', 'description', 'enabled']

    def get_establishment_id(self, obj):
        return obj.establishment.id


class VerifyIfPromocodeExistsSerializer(serializers.Serializer):
    establishment_id = serializers.IntegerField(required=True)
    promocode = serializers.CharField(required=True)

    def create(self, validated_data):
        return super(BillMemberSerializerConfirm(**validated_data))


class EstablishmentEventsSerializer(ModelSerializer):

    class Meta:
        model = EstablishmentEvents
        fields = ['description']


class EstablishmentPhotosSerializer(ModelSerializer):

    class Meta:
        model = EstablishmentPhoto
        fields = ['photo']


class TableSerializer(ModelSerializer):

    class Meta:
        model = Table
        fields = ['id']


class EstablishmentLocation(ModelSerializer):
    lat = SerializerMethodField()
    lng = SerializerMethodField()

    class Meta:
        model = Establishment
        fields = ['lat', 'lng']

    def get_lat(self, obj):
        return obj.y

    def get_lng(self, obj):
        return obj.x


class EstablishmentSerializer(ModelSerializer):
    amenities = AmenitySerializer(many=True, read_only=True)
    cuisine_type = CuisineTypeSerializer()
    photos = EstablishmentPhotosSerializer(many=True, read_only=True)
    geo_loc = EstablishmentLocation()
    average_avg = SerializerMethodField()
    average_environment = SerializerMethodField()
    average_food = SerializerMethodField()
    average_service = SerializerMethodField()
    number_of_evaluations = SerializerMethodField()
    excellent_evaluations = SerializerMethodField()
    good_evaluations = SerializerMethodField()
    bad_evaluations = SerializerMethodField()
    promotions = EstablishmentPromotionsSerializer(many=True, read_only=True)
    events = EstablishmentEventsSerializer(many=True, read_only=True)
    operating_hours = EstablishmentOperatingHoursSerializer(
        many=True, read_only=True)
    table_order_remote_id = SerializerMethodField()

    class Meta:
        model = Establishment
        fields = ['id', 'name', 'description',
                  'logo_url', 'address', 'geo_loc',
                  'amenities', 'cuisine_type', 'featured',
                  'enabled', 'noruh_fee', 'promotions',
                  'events', 'photos', 'opened', 'table_order_remote_id',
                  'operating_hours', 'gps_restriction',
                  'average_avg', 'average_environment',
                  'average_food', 'average_service',
                  'number_of_evaluations', 'excellent_evaluations',
                  'good_evaluations', 'bad_evaluations', ]

    def get_cuisine_type(self, obj):
        return obj.cuisine_type.name

    def get_table_order_remote_id(self, obj):
        query = Table.objects.get(name=ORDER_REMOTE, establishment__id=obj.id)
        if query is not None:
            return query.id
        raise TableDoesNotExistsAPIException()

    def get_average_avg(self, obj):
        average = UserRating.objects.filter(
            bill__establishment__id=obj.id).aggregate(Avg('average'))
        return average['average__avg']

    def get_average_environment(self, obj):
        enviroment = UserRating.objects.filter(
            bill__establishment__id=obj.id).aggregate(Avg('environment'))
        return enviroment['environment__avg']

    def get_average_food(self, obj):
        food = UserRating.objects.filter(
            bill__establishment__id=obj.id).aggregate(Avg('food'))
        return food['food__avg']

    def get_average_service(self, obj):
        service = UserRating.objects.filter(
            bill__establishment__id=obj.id).aggregate(Avg('service'))
        return service['service__avg']

    def get_number_of_evaluations(self, obj):
        number = obj.calculate_evaluations()
        return number['number']

    def get_excellent_evaluations(self, obj):
        excellent = obj.calculate_evaluations()
        return excellent['excellent']

    def get_good_evaluations(self, obj):
        good = obj.calculate_evaluations()
        return good['good']

    def get_bad_evaluations(self, obj):
        bad = obj.calculate_evaluations()
        return bad['bad']


class MenuOfferSerializerList(ModelSerializer):
    category_id = SerializerMethodField()
    discount_percentage = SerializerMethodField()

    class Meta:
        model = MenuOffer
        fields = ['id', 'name', 'category_id', 'discount_percentage']

    def get_category_id(self, obj):
        return obj.category.id

    def get_discount_percentage(self, obj):
        return obj.discount


class ItemCategorySerializerList(ModelSerializer):

    class Meta:
        model = ItemCategory
        fields = ['id', 'name']


class MenuItemSerializer(ModelSerializer):
    observations = SerializerMethodField()
    category = ItemCategorySerializerList()
    preparation_time = SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ['id', 'menu', 'name', 'description', 'available',
                  'price', 'photo', 'category', 'serve_up',
                  'preparation_time', 'observations']

    def get_observations(self, obj):
        observations_list = []
        all_observations = obj.observations.get_queryset()
        list(map(lambda observation: observations_list.append(observation.observation), all_observations))
        return observations_list

    def get_preparation_time(self, obj):
        return obj.preparation_time.minute

    def get_category(self, obj):
        return obj.category.name


class MenuSerializer(ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Menu
        fields = ['name', 'establishment', 'enabled', 'items']


class OrderSerializerPost(ModelSerializer):

    class Meta:
        model = Order
        fields = ['bill', 'item', 'quantity', 'observation']

    def validate(self, data):
        if data.get('bill').payment_date:
            raise BillAlreadyBeenPaidException()
        if MenuItem.objects.filter(id=data.get('item').id,
                                   menu__establishment=data.get('bill').establishment).exists() is False:
            raise serializers.ValidationError('This item does not belong to this Establishment')

        user = self.context.get('request').user
        if not user.billmember_set.filter(bill=data.get('bill')).exists():
            raise NotPartOfThisBillException()
        return data


class OrderSerializerDiscountPost(serializers.Serializer):
    bill_id = serializers.IntegerField(required=True)
    item_id = serializers.IntegerField(required=True)
    observation = serializers.CharField(required=False)
    menu_offer_id = serializers.IntegerField(required=True)

    def create(self, validated_data):
        return super(BillMemberSerializerConfirm(**validated_data))

    def validate(self, data):
        bill = get_object_or_404(Bill, id=data.get('bill_id'))
        menu_item = get_object_or_404(MenuItem, id=data.get('item_id'))
        menu_offer = get_object_or_404(MenuOffer, id=data.get('menu_offer_id'))

        if bill.offers_used_count >= bill.offers_made_count:
            raise LimitDiscountAmoutIsOverAPIException()

        if not MenuItem.objects.filter(id=menu_item.id, category=menu_offer.category).exists():
            raise ItemDoesntBelongToCategoryOffer()

        if bill.payment_date:
            raise BillAlreadyBeenPaidException()
        if MenuItem.objects.filter(id=menu_item.id,
                                   menu__establishment=bill.establishment).exists() is False:
            raise serializers.ValidationError('This item does not belong to this Establishment')

        user = self.context.get('request').user
        if not user.billmember_set.filter(bill=bill).exists():
            raise NotPartOfThisBillException()

        return data


class OrderSerializerList(ModelSerializer):
    item = MenuItemSerializer(read_only=True)
    name = SerializerMethodField()
    offer = SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'bill', 'user', 'name', 'item', 'offer',
                  'quantity', 'observation', 'created_at',
                  'total_price', 'status', 'kitchen_accepted_at',
                  'kitchen_finished_at', 'canceled_at']

    def get_offer(self, obj):
        if obj.item.offer:
            '''
            getting all orders from that bill, and dont filter if has been accept,
            in the future, this will change for orders only accept for the kitchen,
            and then, change `value_from_orders` to `bill.orders_total()`
            '''
            orders = Order.objects.filter(bill=obj.bill)
            value_from_orders = sum(order.total_price() for order in orders)

            if (value_from_orders - obj.bill.establishment.offer_range_value) >= obj.bill.last_offer_used:
                if obj.bill.offers_made_count <= obj.bill.establishment.offer_count_limit:
                    obj.bill.last_offer_used = int(value_from_orders / obj.bill.establishment.offer_range_value) * obj.bill.establishment.offer_range_value
                    obj.bill.offers_made_count += 1
                    obj.bill.save()
                    return MenuOfferSerializerList(obj.item.offer).data
                return None
            return None
        return None

    def get_name(self, obj):
        first_name = obj.user.first_name
        last_name = obj.user.last_name
        return '{} {}'.format(first_name, last_name)


class MultipleOrderSerializer(ModelSerializer):
    items = OrderSerializerPost(many=True)

    class Meta:
        model = Order
        fields = ['items']


class OrderSerializerUpdateStatus(ModelSerializer):

    class Meta:
        model = Order
        fields = ['status']

    def validate(self, data):
        status = data.get('status')
        order = Order.objects.get(id=self.instance.id)
        user = self.context.get('request').user

        if user != order.user:
            raise serializers.ValidationError('You cannot Change Status from This Order')

        if status == Order.STATUS_REJECTED:
            if order.kitchen_accepted_at is not None:
                raise serializers.ValidationError('The order has been prepared')
            self.instance.canceled_at = timezone.now()
            self.instance.save()
            return data
        raise serializers.ValidationError('You can only change Status for Rejected')

    def update(self, instance, validated_data):
        instance.status = validated_data.get('status')
        instance.send_pusher_notification()
        instance.save()
        return instance


class RequestSerializer(ModelSerializer):

    class Meta:
        model = Request
        fields = ['table']


class BillMemberSerializerList(ModelSerializer):
    customer = UserSerializer()

    class Meta:
        model = BillMember
        fields = ['id', 'bill', 'customer',
                  'joined_at', 'leave_at',
                  'couvert_value']


class BillMemberSerializerUpdate(ModelSerializer):

    class Meta:
        model = BillMember
        fields = ['bill']

    def save(self):
        auto_now = datetime.datetime.now()
        BillMember.objects.update(leave_at=auto_now)


class BillMemberSerializerPost(serializers.Serializer):
    establishment_id = serializers.IntegerField(required=True)
    table_id = serializers.IntegerField(required=True)

    def validate(self, data):
        establishment_id = data.get('establishment_id')
        table_id = data.get('table_id')
        bill = get_object_or_404(
            Bill, establishment__id=establishment_id,
            table__id=table_id, payment_date__isnull=True)
        user = self.context.get('request').user

        if bill.table.is_available:
            raise BillDoestNotAvaibleForJoinAPIException()

        if BillMember.objects.filter(
                customer=user, bill=bill,
                leave_at__isnull=True).exists():
            raise OpenBillAPIException()

        data['bill'] = bill
        return data

    def create(self, validated_data):
        user_join = self.context.get('request').user
        bill = validated_data['bill']
        couvert_value = bill.establishment.taxe_couvert
        bill_member = BillMember.objects.create(
            bill=bill, customer=user_join, couvert_value=couvert_value)
        bill_member.send_fcm_notification_to_owner(user_join)
        return bill_member

    def to_representation(self, instance):
        return BillMemberSerializerList(instance).data


class BillMemberSerializerConfirm(serializers.Serializer):
    answer = serializers.BooleanField(required=True)
    bill_id = serializers.CharField(required=True)
    customer_id = serializers.CharField(required=True)

    def create(self, validated_data):
        return super(BillMemberSerializerConfirm(**validated_data))


class BillMemberSerializerExitWithouPayment(serializers.Serializer):

    def create(self, validated_data):
        return super(BillMemberSerializerExitWithouPayment(**validated_data))

    def validate(self, data):
        user = self.context.get('request').user
        bill_member = BillMember.objects.get(customer=user, leave_at__isnull=True)
        orders = Order.objects.filter(bill=bill_member.bill)

        if not orders.count() or orders.count() == orders.filter(status=Order.STATUS_REJECTED).count():
            return super().validate(data)

        raise serializers.ValidationError('You cannot exit from this Bill')


class BillMemberCancelJoinSerializer(serializers.Serializer):
    bill_id = serializers.IntegerField(required=True)

    def create(self, validated_data):
        return super(BillMemberCancelJoinSerializer(**validated_data))

    def validate(self, data):
        bill = get_object_or_404(Bill, id=data.get('bill_id'))
        return bill


class BillMemberSerializerConfirmAll(serializers.Serializer):
    bill_id = serializers.CharField(required=True)

    def validate(self, data):
        bill = get_object_or_404(Bill, id=data.get('bill_id'))
        user = self.context.get('request').user

        if bill.billmember_set.filter(customer=user, bill_owner=True):
            return super().validate(data)

        raise serializers.ValidationError('You arent owner from this bill')


class BillPaymentSerializerList(ModelSerializer):
    user_name = SerializerMethodField()
    user_id = SerializerMethodField()
    credit_card_last_four_digits = SerializerMethodField()
    brand_card = SerializerMethodField()
    bill_table_name = SerializerMethodField()
    noruh_fee_total = SerializerMethodField()

    class Meta:
        model = BillPayment
        fields = ['user_name', 'user_id',
                  'value', 'status_payment',
                  'credit_card_last_four_digits',
                  'brand_card', 'bill_table_name',
                  'noruh_fee_total']

    def get_user_name(self, obj):
        if hasattr(obj.bill_member, 'customer'):
            first_name = obj.bill_member.customer.first_name
            last_name = obj.bill_member.customer.last_name
            return '{} {}'.format(first_name, last_name)
        else:
            return None

    def get_noruh_fee_total(self, obj):
        return obj.noruh_fee

    def get_user_id(self, obj):
        if hasattr(obj.bill_member, 'customer'):
            return obj.bill_member.customer.id
        return None

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


class BillSerializerList(ModelSerializer):
    order = OrderSerializerList(many=True, read_only=True)
    bill_payment = BillPaymentSerializerList(many=True, read_only=True)
    customers = PrimaryKeyRelatedField(many=True, read_only=True)
    establishment = EstablishmentSerializer()
    service_tax_percentage = SerializerMethodField()
    noruh_fee_count = SerializerMethodField()

    class Meta:
        model = Bill
        fields = ['id', 'customers', 'establishment', 'table',
                  'payment_date', 'value_paid', 'opening_date',
                  'order', 'couvert_value',
                  'service_tax_percentage', 'noruh_tax',
                  'orders_total', 'noruh_fee_count',
                  'bill_payment']

    def get_noruh_fee_count(self, obj):
        return obj.bill_noruh_fee_count()

    def get_service_tax_percentage(self, obj):
        return obj.establishment.taxe_service


class BillSerializerPost(ModelSerializer):

    class Meta:
        model = Bill
        fields = ['establishment', 'table']

    def validate(self, data):
        user = self.context.get('request').user
        establishment = data.get('establishment')

        if not establishment.enabled:
            raise EstablishmentDoesNotAvaibleAPIException()

        if BillMember.objects.filter(customer=user, leave_at__isnull=True).exists():
            raise OpenBillAPIException()

        table = Table.objects.filter(id=data.get('table').id, establishment=data.get('establishment')).first()
        if not table:
            raise TableDoesNotExistsAPIException()

        if not table.is_available:
            raise TableDoesntAvaibleAPIException()

        return super().validate(data)

    def save(self):
        user = self.context.get('request').user
        bill = super().save()
        auto_now = datetime.datetime.now()
        couvert_value = bill.establishment.taxe_couvert
        BillMember.objects.create(bill=bill, customer=user, joined_at=auto_now,
                                  bill_owner=True, couvert_value=couvert_value)
        waiters = User.objects.filter(id__in=Employee.objects.filter(establishment=bill.establishment,
                                      user_type=Employee.USER_WAITER).values('user'))
        list_waiters = [waiter.id for waiter in waiters]
        data = {'establishment': bill.establishment.name,
                'table': bill.table.name,
                'opening_date': bill.opening_date}
        data_json = json.dumps(data, default=objects_to_json)
        PusherNotification.send_notifications(list_waiters, 'waiter', 'new_bill_waiter', data_json)


class UserBillSerializer(ModelSerializer):
    bill = BillSerializerList()
    bill_member_id = SerializerMethodField()
    customer = SerializerMethodField()

    class Meta:
        model = BillMember
        fields = ['joined_at', 'bill_member_id', 'bill',
                  'customer', 'leave_at', 'bill_owner',
                  'couvert_value']

    def get_bill_member_id(self, obj):
        return obj.id

    def get_customer(self, obj):
        return obj.customer.id


class UserBillHistorySerializer(ModelSerializer):
    bill = BillSerializerList()

    class Meta:
        model = BillMember
        fields = ['bill', 'customer', 'bill_owner',
                  'joined_at', 'leave_at']


class EvaluationSerializerPost(ModelSerializer):

    class Meta:
        model = UserRating
        fields = ['bill', 'environment', 'food',
                  'service', 'observation']

    def validate(self, data):
        bill_member = get_object_or_404(
            BillMember, customer=self.context.get('request').user,
            bill=data.get('bill'), leave_at__isnull=False)
        if UserRating.objects.filter(bill=data.get('bill'), user=bill_member).exists():
            raise serializers.ValidationError('You cannot create Rating for this Bill')
        return data

    def create(self, validated_data):
        user = self.context.get('request').user
        bill_member = BillMember.objects.get(
            customer=user, bill=validated_data.get('bill'))
        user_rating = UserRating.objects.create(
            user=bill_member, bill=bill_member.bill,
            environment=validated_data.get('environment'),
            food=validated_data.get('food'),
            service=validated_data.get('service'),
            observation=validated_data.get('observation'))
        return user_rating


class EvaluationSerializerList(ModelSerializer):
    user_name = SerializerMethodField()
    user_id = SerializerMethodField()
    establishment_answer = SerializerMethodField()

    class Meta:
        model = UserRating
        fields = ['user_name', 'user_id',
                  'observation', 'average',
                  'establishment_answer']

    def get_user_name(self, obj):
        first_name = obj.user.customer.first_name
        last_name = obj.user.customer.last_name
        return '{} {}'.format(first_name, last_name)

    def get_user_id(self, obj):
        return obj.user.customer.id

    def get_establishment_answer(self, obj):
        if hasattr(obj, 'establishment_answer'):
            return obj.establishment_answer.answer
        return None


class EvaluationInfoSerializer(serializers.Serializer):
    bill_id = serializers.IntegerField(required=True)

    def create(self, validated_data):
        return super(EvaluationInfoSerializer**(validated_data))

    def validate(self, data):
        bill = get_object_or_404(Bill, id=data.get('bill_id'))
        return data
