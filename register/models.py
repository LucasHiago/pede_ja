import calendar
import os
import json
import datetime
import uuid

from unipath import Path
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Func, Avg, Count, Sum
from django.contrib.gis.db import models as gis_models
from django.utils.translation import gettext as _
from django.contrib.auth.models import User, Group
from django.db.models.signals import pre_save, post_save, post_delete
from django.shortcuts import get_object_or_404
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from django.core.validators import FileExtensionValidator

from fcm_django.models import FCMDevice
from noruh_backend.pusher import PusherNotification
from noruh_backend.settings import ORDER_REMOTE, ORDER_REMOTE_TABLE_ZONE
from noruh_backend.firestore_connect import NoruhFireStore

from register.exceptions import (
    OpenBillException,
    CannotLeaveBillException,
    CannotCancelOrderException,
)
from register.convert_json import objects_to_json

DAYS_OF_WEEK = (
    (calendar.SUNDAY, _('Sunday')),
    (calendar.MONDAY, _('Monday')),
    (calendar.TUESDAY, _('Tuesday')),
    (calendar.WEDNESDAY, _('Wednesday')),
    (calendar.THURSDAY, _('Thursday')),
    (calendar.FRIDAY, _('Friday')),
    (calendar.SATURDAY, _('Saturday'))
)


def upload_to(instance, filename):
    """
    Set path to Profile Image
    """
    USER_ID = str(instance.id)
    FILE_NAME = 'image'
    FILE_EXT = Path(filename).ext
    name = f'user/{USER_ID}/{FILE_NAME}{FILE_EXT}'

    full_path_name = os.path.join(settings.MEDIA_ROOT, name)

    # Verify if exists image from user, remove and put a new image
    if os.path.exists(full_path_name):
        os.remove(full_path_name)
    return name


def decode_files(instance, filename):
    """
    encode the name of files
    """
    file_name = Path(filename).ext
    file_name = file_name.encode('utf8')
    name = f'{file_name}'
    return name


class TokenRecoverPassword(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4)
    expiration_time = models.DateTimeField()

    def __str__(self):
        return self.token.hex


class Month(Func):
    function = 'EXTRACT'
    template = '%(function)s(MONTH from %(expressions)s)'
    output_field = models.IntegerField()


class Year(Func):
    function = 'EXTRACT'
    template = '%(function)s(YEAR from %(expressions)s)'
    output_field = models.IntegerField()


class Profile(models.Model):
    ANDROID = 'android'
    IOS = 'ios'

    GENDER_MALE = 'GENDER_MALE'
    GENDER_FEMALE = 'GENDER_FEMALE'
    GENDER_OTHER = 'GENDER_OTHER'

    DEVICE_OS_CHOICES = (
        (ANDROID, 'android'),
        (IOS, 'ios'),
    )

    PROFILE_SEX_CHOICES = (
        (GENDER_MALE, 'GENDER_MALE'),
        (GENDER_FEMALE, 'GENDER_FEMALE'),
        (GENDER_OTHER, 'GENDER_OTHER'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cpf = models.CharField(max_length=14, null=True, blank=True)
    gender = models.CharField(
        max_length=25, choices=PROFILE_SEX_CHOICES, null=True)
    image_url = models.ImageField(
        blank=True, null=True, upload_to=upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['jpg'])])
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    device_id = models.TextField(null=True, blank=True)
    device_os = models.CharField(
        max_length=25, choices=DEVICE_OS_CHOICES, null=True)
    phone_number = models.CharField(max_length=13, null=True, blank=True)
    average_value_spent = models.FloatField(default=0.00)
    visited_establishments_count = models.PositiveSmallIntegerField(
        null=True, blank=True)


    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(id=instance.id, user=instance)

    @receiver(post_save, sender=User)
    def save_user_profile(sender, instance, **kwargs):
        instance.profile.save()

    def __str__(self):
        return f'{self.user.first_name} - {self.user.email}'


class UserPayment(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    moip_user_id = models.CharField(max_length=200, null=True, blank=True)
    moip_user_token = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        verbose_name = _('User Payment')
        verbose_name_plural = _('Users Payments')

    def __str__(self):
        return f'{self.moip_user_id} - {self.user.first_name}'


class UserCreditCard(models.Model):
    last_four_digits = models.CharField(max_length=4)
    brand_card = models.CharField(max_length=50)
    id_moip_card = models.CharField(max_length=40)
    user_payment = models.ForeignKey(
        UserPayment, on_delete=models.CASCADE, null=True, blank=True,
        related_name='user_payment')
    full_name = models.CharField(max_length=100, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    type_doc = models.CharField(
        max_length=4, null=True, blank=True)  # Type Doc = CPF or CNPJ
    number_doc = models.CharField(
        max_length=15, null=True, blank=True)  # Number = CPF or CNPJ

    class Meta:
        verbose_name = ('User Credit Card')
        verbose_name_plural = ('Users Credit Cards')

    def __str__(self):
        return self.last_four_digits


class Amenity(models.Model):
    '''
    Based on RF002
    '''
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('Amenity')
        verbose_name_plural = _('Amenities')
        permissions = (
            ("can_create_amenities", "Can Create Amenities"),
            ("can_delete_amenities", "Can Delete Amenities"),
        )

    def __str__(self) -> str:
        return self.name


class CuisineType(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Cousine type')
        verbose_name_plural = _('Cousine types')
        permissions = (
            ("can_create_cuisinetype", "Can Create Cuisine Type"),
            ("can_delete_cuisinetype", "Can Delete Cuisine Type"),
        )


class MoipWirecardAPP(models.Model):
    app_id = models.CharField(max_length=64, unique=True)
    website = models.CharField(max_length=100, unique=True)
    access_token = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=64, unique=True)
    secret = models.CharField(max_length=64, unique=True)
    redirect_uri = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self):
        return self.app_id

    class Meta:
        verbose_name = _('APP Moip MoipWirecard')
        verbose_name_plural = _('APP Moip Wirecards')


class Establishment(models.Model):
    '''
    Based on RF002
    '''
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(null=True, blank=True)
    address = models.TextField()
    geo_loc = gis_models.PointField()
    amenities = models.ManyToManyField(Amenity,
                                       related_name='establishments')
    cuisine_type = models.ForeignKey(CuisineType,
                                     on_delete=models.SET_NULL,
                                     null=True,
                                     blank=True)
    enabled = models.BooleanField(default=True)
    opened = models.BooleanField(default=True)
    gps_restriction = models.BooleanField(default=False)
    logo_url = models.ImageField(
        verbose_name=_('Photo'), upload_to=decode_files)
    featured = models.BooleanField(default=False)
    offer_range_value = models.DecimalField(
        max_digits=4, decimal_places=2, default=50.00,
        help_text='Valor usado para controlar as ofertas liberadas')
    offline_percentage = models.DecimalField(
        max_digits=2, decimal_places=2, default=Decimal("00.02")
    )
    offer_count_limit = models.PositiveIntegerField(default=10)
    # Taxes and Fees for Payment in Establishment
    noruh_fee = models.DecimalField(max_digits=4, decimal_places=2)
    pays_payment_tax = models.BooleanField(default=False)
    moip_fee = models.DecimalField(
        max_digits=2, decimal_places=2, default=Decimal("00.69"))
    payment_tax = models.DecimalField(
        max_digits=4, decimal_places=4, default=Decimal("00.0549"))
    taxe_service = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("00.10"))
    taxe_couvert = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal("00.00"))

    class Meta:
        verbose_name = _('Establishment')
        verbose_name_plural = _('Establishments')
        permissions = (
            ("can_create_establishment", "Can Create Establishment"),
            ("can_update_description_establishment", "Can Update Description Establishment"),
            ("can_update_amenities_establishment", "Can Update Amenities Establishment"),
            ("can_update_taxes_establishment", "Can Update Taxes Establishment"),
            ("can_update_couvert_taxe_establishment", "Can Update Couvert Taxe Establishment"),
            ("can_update_offer_range_value", "Can Update Offer Range Value Establishment"),
            ("can_update_functions_establishment", "Can Update Functions Establishment"),
            ("can_update_location_establishment", "Can Update Location Establishment"),
            ("can_update_opened", "Can Update Opened"),
            ("can_view_establishment", "Can View Establishment"),
            ("can_view_all_establishments", "Can View All Establishments"),
            ("can_delete_establishment", "Can Delete Establishment"),
            ("can_view_dashboard_from_establishment", "Can View Dashboard From Establishment"),
            ("can_view_qr_codes", "Can View QR Codes"),
        )

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        return reverse("register:establishment_base", kwargs={"pk": self.pk})

    def calculate_evaluations(self):
        all_evaluations = UserRating.objects.filter(
            bill__establishment__id=self.id)
        obj_count = all_evaluations.count()
        evaluation_excellent = 0
        evaluation_good = 0
        evaluation_bad = 0

        for evaluation in all_evaluations:
            media = (evaluation.environment +
                     evaluation.food + evaluation.service) / 3
            if media >= 9 <= 10:
                evaluation_excellent = evaluation_excellent + 1
            elif media >= 6 < 9:
                evaluation_good = evaluation_good + 1
            elif media >= 0 < 6:
                evaluation_bad = evaluation_bad + 1

        evaluations = {"number": obj_count,
                       "excellent": evaluation_excellent,
                       "good": evaluation_good,
                       "bad": evaluation_bad}
        return evaluations

    def average_bills(self, current_month=None):
        if current_month:
            bills_for_average_ticket = BillPayment.objects.filter(
                establishment=self,
                date__month=current_month.month,
                date__year=current_month.year,
                status_payment__in=[
                    BillPayment.STATUS_OFFLINE_APPROVED,
                    BillPayment.STATUS_AUTHORIZED])
        else:
            bills_for_average_ticket = BillPayment.objects.filter(
                establishment=self)

        bills_average_value = bills_for_average_ticket.aggregate(
            Sum('value'))
        bills_average_value = bills_average_value.get('value__sum')

        if bills_average_value is None:
            return 0
        value = "{0:.2f}".format(bills_average_value / bills_for_average_ticket.count())

        return Decimal(value)

    def number_of_orders(self):
        orders = Order.objects.filter(bill__establishment=self,
                                      kitchen_finished_at__isnull=False)
        return orders.count()

    def noruh_tax_to_super_admin(self):
        payments = BillPayment.objects.filter(
            establishment=self, status_payment__in=[
                BillPayment.STATUS_AUTHORIZED, BillPayment.STATUS_OFFLINE_APPROVED])
        return payments.count() * self.noruh_fee

    def report_offline_payment(self):
        bill_payments = BillPayment.objects.filter(
            establishment=self,
            status_payment=BillPayment.STATUS_OFFLINE_APPROVED).annotate(
                m=Month('date'), y=Year(
                    'date'),).values('m', 'y').annotate(total=Sum(
                        'value')).order_by('-y', '-m')

        for payment in bill_payments:
            payment['compensation_value'] = payment.get('total') * self.offline_percentage
            payment['establishment_id'] = self.id
            payment['date'] = datetime.datetime(payment.get('y'), payment.get('m'), datetime.datetime.today().day)
            compensation = OfflineCompensations.objects.filter(
                establishment=self, month=payment.get('m'), year=payment.get('y'))
            if compensation.exists():
                obj = compensation.first()
                payment['compensation'] = obj.date_compensation
            else:
                payment['compensation'] = False

        return bill_payments

    def report_offline_payment_with_month(self, current_month):
        bill_payments = BillPayment.objects.filter(
            establishment=self,
            status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
            date__month=current_month.month,
            date__year=current_month.year).aggregate(
                Sum('value'))

        value_payment = bill_payments.get('value__sum')

        if not value_payment:
            value_payment = Decimal(0.0)

        payment_compensation = "%.2f" % (value_payment * self.offline_percentage)
        return Decimal(payment_compensation)

    def report_offline_all_establishments(current_month):
        establishments = Establishment.objects.all()
        all_compensation = 0
        for establishment in establishments:
            bill_payments = BillPayment.objects.filter(
                establishment=establishment,
                status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
                date__month=current_month.month,
                date__year=current_month.year).aggregate(
                    Sum('value'))

            value_payment = bill_payments.get('value__sum')

            if not value_payment:
                value_payment = Decimal(0.0)

            payment_compensation = "%.2f" % (value_payment * establishment.offline_percentage)
            all_compensation = all_compensation + Decimal(payment_compensation)

        return Decimal(all_compensation)


class Employee(models.Model):
    USER_WAITER = 'USER_WAITER'
    USER_KITCHEN = 'USER_KITCHEN'
    USER_MANAGER = 'USER_MANAGER'
    USER_DOOR_MAN = 'USER_DOOR_MAN'

    USER_TYPE_CHOICES = (
        (USER_MANAGER, 'Gerente'),
        (USER_WAITER, 'Garçom(nete)'),
        (USER_KITCHEN, 'Cozinheiro(a)'),
        (USER_DOOR_MAN, 'Atendente'),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='employee',
        verbose_name='Usuário')
    user_type = models.CharField(
        max_length=25, choices=USER_TYPE_CHOICES,
        verbose_name='Tipo de Usuário')
    establishment = models.ForeignKey(
        Establishment, on_delete=models.CASCADE, verbose_name='Estabelecimento')
    cpf = models.CharField(max_length=14, unique=True, verbose_name='CPF')
    image = models.ImageField(
        null=True, blank=True, verbose_name='Imagem', upload_to=decode_files)

    class Meta:
        verbose_name = _('Funcionário')
        verbose_name_plural = _('Funcionários')
        permissions = (
            ("can_create_employee", "Can Create Employee"),
            ("can_view_employee", "Can View Employee"),
            ("can_alter_employee", "Can Alter Employee"),
            ("can_delete_employee", "Can Delete Employee"),
        )

    def __str__(self) -> str:
        return str(self.user)


class EstablishmentManager(models.Model):
    establishment = models.ForeignKey(
        Establishment, on_delete=models.CASCADE, related_name='manager')
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True,
        unique=True, related_name='manager')

    class Meta:
        verbose_name = _('Establishment manager')
        verbose_name_plural = _('Establishment managers')

    def __str__(self) -> str:
        return str(self.user)


class MoipWirecardCustomer(models.Model):
    # Wirecard Informations
    observation = models.CharField(max_length=50, default='Establishment')
    establishment = models.OneToOneField(
        Establishment, on_delete=models.CASCADE, null=True, blank=True)
    id_wirecard = models.CharField(max_length=64, null=True, blank=True)
    login = models.CharField(max_length=64, null=True, blank=True)
    access_token = models.CharField(max_length=64, null=True, blank=True)
    channel_id = models.ForeignKey(
        MoipWirecardAPP, on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=64, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    # Personal informations
    name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=64, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    number_cpf = models.CharField(
        max_length=14, null=True, blank=True)  # Ex: 981.139.390-75
    # Address informations
    street = models.CharField(max_length=64, null=True, blank=True)
    street_number = models.CharField(max_length=4, null=True, blank=True)
    district = models.CharField(max_length=50, null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    city = models.CharField(max_length=64, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)
    # Telephone Informations
    country_code = models.CharField(max_length=5, null=True, blank=True)
    area_code = models.CharField(max_length=3, null=True, blank=True)
    number = models.CharField(max_length=10, null=True, blank=True)
    # Identity Document Informations
    number_rg = models.CharField(max_length=20, null=True, blank=True)
    issuer = models.CharField(max_length=10, null=True,
                              blank=True)  # Like SSP-AL
    issue_date = models.CharField(max_length=20, null=True, blank=True)
    # Company Informations
    business_name = models.CharField(max_length=64, null=True, blank=True)
    opening_date = models.CharField(max_length=64, null=True, blank=True)
    number_cnpj = models.CharField(max_length=64, null=True, blank=True)
    number_cnae = models.CharField(max_length=64, null=True, blank=True)
    description_activity = models.CharField(max_length=64, null=True, blank=True)

    '''Created At'''
    created_at = models.DateTimeField(null=True, blank=True)
    '''Links'''
    link_account = models.CharField(max_length=200, null=True, blank=True)
    set_password = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Establishment WireCard')
        verbose_name_plural = _('Establishment Wirecards')
        permissions = (
            ("can_create_wirecard", "Can Create Wirecard"),
            ("can_view_wirecard", "Can View Wirecard"),
        )


class EstablishmentPhoto(models.Model):
    '''
    Based on RF002
    '''
    establishment = models.ForeignKey(Establishment,
                                      related_name='photos',
                                      on_delete=models.CASCADE)
    photo = models.ImageField(upload_to=decode_files)

    class Meta:
        verbose_name = _('Establishment photo')
        verbose_name_plural = _('Establishment photos')
        permissions = (
            ("can_add_photo_establishment", "Can Add Photo On Establishment"),
            ("can_delete_photo_establishment", "Can Delete Photo On Establishment"),
            ("can_view_photo_establishment", "Can View Photo On Establishment")
        )


class EstablishmentOperatingHours(models.Model):
    establishment = models.ForeignKey(Establishment,
                                      related_name='operating_hours',
                                      on_delete=models.CASCADE)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    dow = models.IntegerField(choices=DAYS_OF_WEEK)  # Days of Week

    class Meta:
        verbose_name = _('Establishment operating hour')
        verbose_name_plural = _('Establishment operating hours')
        unique_together = ('establishment', 'dow')
        permissions = (
            ("can_create_operating_hour", "Can Create Operating Hours"),
            ("can_list_operating_hour", "Can List Operating Hours"),
            ("can_update_operating_hour", "Can Update Operating Hours"),
            ("can_delete_operating_hour", "Can Delete Operating Hours"),
        )

    def __str__(self) -> str:
        return f'{self.get_dow_display()}({self.opening_time} - {self.closing_time})'


class EstablishmentStatistics(models.Model):
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE)
    period_start = models.DateTimeField(auto_now_add=True)
    period_end = models.DateTimeField(null=True)
    rating_average = models.DecimalField(max_digits=3, decimal_places=1)


class EstablishmentEvents(models.Model):
    establishment = models.ForeignKey(
        Establishment, related_name='events', on_delete=models.CASCADE)
    description = models.CharField(max_length=64, unique=True)
    date = models.DateTimeField()

    class Meta:
        verbose_name = _('Establishment Event')
        verbose_name_plural = _('Establishment Events')
        permissions = (
            ("can_create_events", "Can Create Events"),
            ("can_view_events", "Can View Events"),
            ("can_delete_events", "Can Change Events"),
        )

    def __str__(self) -> str:
        return f'{self.establishment.name}({self.description})'


class EstablishmentPromotions(models.Model):
    establishment = models.ForeignKey(
        Establishment, related_name='promotions', on_delete=models.CASCADE)
    promocode = models.CharField(max_length=20, unique=True)
    value = models.DecimalField(max_digits=4, decimal_places=2)
    description = models.CharField(max_length=64, unique=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Establishment Promotion')
        verbose_name_plural = _('Establishment Promotions')
        permissions = (
            ("can_create_promocode", "Can Create Promocode"),
            ("can_view_promotions", "Can View Promocodes"),
            ("can_delete_promotions", "Can Change Promocodes"),
        )

    def __str__(self) -> str:
        return f'{self.establishment.name}({self.promocode})'


class Menu(models.Model):
    establishment = models.ForeignKey(Establishment,
                                      related_name='menu',
                                      on_delete=models.CASCADE)
    name = models.CharField(max_length=64,
                            verbose_name=_('Name'))
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Menu')
        verbose_name_plural = _('Menus')
        unique_together = ('establishment', 'name')
        permissions = (
            ("can_create_menu", "Can Create Menu"),
            ("can_view_menu", "Can View Menu"),
            ("can_update_menu", "Can Update Menu"),
            ("can_delete_menu", "Can Delete Menu"),
        )

    def __str__(self) -> str:
        return self.name


class ItemCategory(models.Model):
    name = models.CharField(max_length=64)
    establishment = models.ForeignKey(
        Establishment, related_name='category', on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Item Category')
        verbose_name_plural = _('Item Categorys')
        unique_together = ('establishment', 'name')
        permissions = (
            ("can_create_category", "Can Create Category"),
            ("can_view_category", "Can View Category"),
            ("can_update_category", "Can Update Category"),
            ("can_delete_category", "Can Delete Category"),
        )

    def __str__(self) -> str:
        return f'{self.name}'


class ItemObservations(models.Model):
    observation = models.TextField(null=True, blank=True)
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Item Observation')
        verbose_name_plural = _('Item Observations')
        permissions = (
            ("can_create_item_observation", "Can Item Observation"),
            ("can_view_item_observation", "Can Item Observation"),
            ("can_update_item_observation", "Can Item Observation"),
            ("can_delete_item_observation", "Can Item Observation"),
        )

    def __str__(self):
        return str(self.observation)


class MenuOffer(models.Model):
    name = models.CharField(max_length=64,
                            verbose_name=_('Name'))
    category = models.OneToOneField(
        ItemCategory, related_name='category', on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=2, decimal_places=2)

    def __str__(self):
        discount_percentage = self.discount * 100
        return '{}% - {}'.format(discount_percentage, self.category)

    class Meta:
        verbose_name = _('Menu Offer')
        verbose_name_plural = _('Menu Offer')
        permissions = (
            ("can_create_menu_offer", "Can Create Menu Offer"),
            ("can_view_menu_offer", "Can View Menu Offer"),
            ("can_update_menu_offer", "Can Update Menu Offer"),
            ("can_delete_menu_offer", "Can Delete Menu Offer"),
        )

    def percentage(self):
        return int(self.discount * 100)

    def calculate_discount(self, menu_item):
        discount = menu_item.price * self.discount
        return menu_item.price - discount


class MenuItem(models.Model):
    menu = models.ForeignKey(Menu,
                             related_name='items',
                             on_delete=models.CASCADE,
                             verbose_name='Menu')
    name = models.CharField(max_length=64,
                            verbose_name=_('Name'))
    description = models.TextField()
    available = models.BooleanField(default=True,
                                    verbose_name=_('Available'))
    price = models.DecimalField(max_digits=8,
                                decimal_places=2,
                                verbose_name=_('Price'))
    photo = models.ImageField(
        verbose_name=_('Photo'), upload_to=decode_files)
    category = models.ForeignKey(
        ItemCategory, on_delete=models.SET_NULL, null=True)
    # serve up to N peoples
    serve_up = models.PositiveIntegerField(default=1, verbose_name='Serve up')
    preparation_time = models.TimeField()
    observations = models.ManyToManyField(ItemObservations, blank=True)
    offer = models.ForeignKey(
        MenuOffer, related_name='offer',
        on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = _('Menu item')
        verbose_name_plural = _('Menu items')
        unique_together = ('menu', 'name')
        permissions = (
            ("can_create_item_on_menu", "Can Create Item On Menu"),
            ("can_view_item_on_menu", "Can View Item On Menu"),
            ("can_change_item_on_menu", "Can Change Item On Menu"),
            ("can_delete_item_on_menu", "Can Delete Item On Menu"),
        )

    def __str__(self) -> str:
        return f'{self.name}({self.price})'


class TableZone(models.Model):
    name = models.CharField(max_length=64, verbose_name=_('Name'))
    establishment = models.ForeignKey(
        Establishment, related_name='table_zone', on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Table zone')
        verbose_name_plural = _('Tables zones')
        permissions = (
            ("can_create_table_zone", "Can Create Table Zone"),
            ("can_view_table_zone", "Can View Table Zone"),
            ("can_change_table_zone", "Can Change Table Zone"),
            ("can_desactive_table_zone", "Can Desactive Table Zone"),
            ("can_delete_table_zone", "Can Delete Table Zone"),
        )

    def __str__(self) -> str:
        return self.name

    def tables_from_table_zone(self):
        return Table.objects.filter(table_zone=self)


class Table(models.Model):
    establishment = models.ForeignKey(
        Establishment, related_name='table', on_delete=models.CASCADE)
    table_zone = models.ForeignKey(
        TableZone, on_delete=models.CASCADE, related_name='zone')
    name = models.CharField(max_length=64, verbose_name=_('Name'))
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('Table')
        verbose_name_plural = _('Tables')
        unique_together = ('establishment', 'name')
        permissions = (
            ("can_create_table", "Can Create Table"),
            ("can_view_table", "Can View Table"),
            ("can_update_table", "Can Update Table"),
            ("can_delete_table", "Can Delete Table"),
        )

    def __str__(self) -> str:
        return self.name

    @property
    def is_available(self):
        if Bill.objects.filter(table=self, payment_date__isnull=True).exists() is False or self.name == ORDER_REMOTE:
            return True
        return False

    @property
    def current_bill(self):
        current_bill = Bill.objects.filter(
            table=self, payment_date__isnull=True)
        if current_bill.exists():
            return current_bill.first()


class Bill(models.Model):
    '''
    RF005
    '''
    customers = models.ManyToManyField(User, through='BillMember')
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(null=True, blank=True)
    opening_date = models.DateTimeField(auto_now_add=True)
    value_paid = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00)
    offers_made_count = models.IntegerField(default=0)
    offers_used_count = models.IntegerField(default=0)
    last_offer_used = models.IntegerField(default=0)

    class Meta:
        verbose_name = _('Bill')
        verbose_name_plural = _('Bills')
        permissions = (
            ("can_view_bill", "Can View Bill"),
            ("can_delete_bill", "Can Delete Bill"),
        )

    def __str__(self):
        return f'{self.table.name}({self.id})'

    @property
    def number_of_orders(self):
        orders = Order.objects.filter(
            bill__id=self.id, kitchen_accepted_at__isnull=False)
        return orders.count()

    @property
    def owner(self):
        owner = self.customers.filter(
            billmember__leave_at__isnull=True).order_by(
            'billmember__joined_at').first()
        return owner

    def value_paid_without_noruh_fee(self):
        payments = BillPayment.objects.filter(
            bill_id=self.id,
            status_payment__in=[
                BillPayment.STATUS_OFFLINE_APPROVED,
                BillPayment.STATUS_AUTHORIZED,
                BillPayment.STATUS_IN_ANALYSIS,
                BillPayment.STATUS_OFFLINE_PENDING])
        value_paid = 0
        for payment in payments:
            value_paid = value_paid + (payment.value - payment.noruh_fee)

        return value_paid

    def bill_noruh_fee_count(self):
        payments = BillPayment.objects.filter(
            bill_id=self.id,
            status_payment__in=[
                BillPayment.STATUS_OFFLINE_APPROVED,
                BillPayment.STATUS_AUTHORIZED,
                BillPayment.STATUS_IN_ANALYSIS,
                BillPayment.STATUS_OFFLINE_PENDING])
        payments_noruh_fee = 0
        for payment in payments:
            payments_noruh_fee = payments_noruh_fee + payment.noruh_fee

        return float(payments_noruh_fee / self.establishment.noruh_fee)

    def number_of_customers(self):
        if self.customers.all().count() == 0:
            return 0
        return self.customers.all().count()

    def couvert_value(self):
        return self.establishment.taxe_couvert

    def noruh_tax(self):
        return self.establishment.noruh_fee

    def couvert_for_all(self):
        return self.establishment.taxe_couvert * self.customers.all().count()

    def noruh_fee_for_all(self):
        return self.establishment.noruh_fee * self.customers.all().count()

    # Only value for orders
    def orders_total(self):
        orders = Order.objects.filter(
            bill=self,
            status__in=[
                Order.STATUS_PENDING,
                Order.STATUS_PREPARING, Order.STATUS_DONE])
        return sum(order.total_price() for order in orders)

    # Value for orders and Couvert
    def orders_with_couvert_for_all(self):
        return self.orders_total() + self.couvert_for_all()

    # Value for orders, taxe service and couvert for all bill members
    def all_value_bill(self):
        tax_percentage = Decimal(self.orders_total()) * self.establishment.taxe_service
        all_value = Decimal(self.orders_total()) + Decimal(self.couvert_for_all()) + tax_percentage + self.noruh_fee_for_all()
        return float("%.2f" % (all_value))

    # All value from bill withou taxe service
    def all_value_bill_without_taxe_service(self):
        couvert_for_all = self.customers.count() * self.establishment.taxe_couvert
        return Decimal(self.orders_total()) + couvert_for_all

    # how much still have to pay
    def still_have_to_pay(self):
        taxe_service = self.orders_total() * self.establishment.taxe_service
        all_value = self.orders_total() + self.couvert_for_all() + taxe_service + self.noruh_fee_for_all()
        still_have_to_pay = all_value - self.value_paid

        if still_have_to_pay <= 0:
            still_have_to_pay = 0.00
        return still_have_to_pay


class BillMember(models.Model):
    '''
    We use this model to know when each member joined to the bill.

    To know more details see item: RF015
    '''
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    bill_owner = models.BooleanField(default=False)
    joined_at = models.DateTimeField(null=True, blank=True)
    leave_at = models.DateTimeField(null=True, blank=True)
    couvert_value = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = _('Bill member')
        verbose_name_plural = _('Bill members')
        permissions = (
            ("can_create_bill_member", "Can Create Bill Member"),
        )

    def __str__(self):
        return str(self.customer)

    def leave(self):
        self.leave_at = timezone.now()
        self.save()

    def value_consumed(self):
        orders_bm = Order.objects.filter(
            user=self.customer, bill=self.bill, status__in=[
                Order.STATUS_PENDING, Order.STATUS_PREPARING,
                Order.STATUS_DONE])
        value_consumed = 0
        for order in orders_bm:
            value_consumed = value_consumed + order.total_price()
        taxe_service = value_consumed * self.bill.establishment.taxe_service
        all_value = value_consumed + self.bill.establishment.taxe_couvert
        return (all_value + taxe_service + self.bill.establishment.noruh_fee)

    def value_consumed_without_tax_percentage(self):
        orders_bm = Order.objects.filter(
            user=self.customer, bill=self.bill, status__in=[
                Order.STATUS_PENDING, Order.STATUS_PREPARING,
                Order.STATUS_DONE])
        value_consumed = 0
        for order in orders_bm:
            value_consumed = value_consumed + order.total_price()
        return (value_consumed + self.bill.establishment.taxe_couvert)

    def value_consumed_without_taxes(self):
        orders_bm = Order.objects.filter(
            user=self.customer, bill=self.bill, status__in=[
                Order.STATUS_PENDING, Order.STATUS_PREPARING,
                Order.STATUS_DONE])
        value_consumed = 0
        for order in orders_bm:
            value_consumed = value_consumed + order.total_price()
        return value_consumed

    def calc_service_tax(self):
        return Decimal(self.value_consumed_without_taxes()) * self.bill.establishment.taxe_service

    def order(self):
        return Order.objects.filter(user=self.customer, bill=self.bill)

    def has_paid(self):
        return BillPayment.objects.filter(
            bill_member=self, bill=self.bill).order_by('-date').first()

    def answer_to_bill_member(bill_member, answer):
        device = FCMDevice.objects.filter(user=bill_member.customer)

        customer_name = '{} {}'.format(
            bill_member.customer.first_name,
            bill_member.customer.last_name)
        data = {"id": bill_member.id,
                "bill": bill_member.bill.id,
                "customer_id": bill_member.customer.id,
                "customer_name": customer_name,
                "joined_at": bill_member.joined_at,
                "leave_at": bill_member.leave_at,
                "couvert_value": bill_member.couvert_value}
        data = json.dumps(data, default=objects_to_json)

        if answer:
            dict_data = {'key': 'bill_join_accepted', 'data': data}
            body_msg = "Você já pode fazer pedidos no estabelecimento "f'{bill_member.bill.establishment.name}'
            device.send_message("Pode Começar a pedir",
                                body_msg, data=dict_data)
            bill_member.joined_at = timezone.now()
            bill_member.save()
            return True

        else:
            dict_data = {'key': 'bill_join_refused', 'data': data}
            device.send_message("Solicitação Negada",
                                "Sua entrada na conta não foi autorizada",
                                data=dict_data)
            BillMember.objects.get(id=bill_member.id).delete()
            return False

    def send_fcm_notification_to_owner(self, user_join):
        owner = BillMember.objects.filter(
            bill=self.bill, leave_at__isnull=True).order_by('joined_at').first()
        device = FCMDevice.objects.filter(user=owner.customer)

        customer_name = '{} {}'.format(
            self.customer.first_name,
            self.customer.last_name)

        body_msg = "O usuario "f'{user_join.first_name}' " quer entrar na comanda do estabelecimento "f'{self.bill.establishment.name}'
        data = {"id": self.id,
                "bill": self.bill.id,
                "customer_id": self.customer.id,
                "customer_name": customer_name}

        data = json.dumps(data, default=objects_to_json)
        dict_data = {'key': 'new_bill_member', 'data': data}
        device.send_message("Solicitação para entrar na sua conta",
                            body_msg, data=dict_data)
        return True


class Request(models.Model):
    '''
    Model about RF026
    '''
    STATUS_PENDING = 'STATUS_PENDING'
    STATUS_REQUESTED = 'STATUS_REQUESTED'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'STATUS_PENDING'),
        (STATUS_REQUESTED, 'STATUS_REQUESTED'),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=25, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        verbose_name = _('Request')
        verbose_name_plural = _('Requests')
        permissions = (
            ("can_view_status_request", "Can View Status Request"),
            ("can_change_status_request", "Can Change Status Request"),
        )

    def __str__(self):
        return f'{self.table.name}({self.user})'


class Order(models.Model):
    '''
    Model about RF008
    '''
    STATUS_PENDING = 'STATUS_PENDING'
    STATUS_REJECTED = 'STATUS_REJECTED'
    STATUS_PREPARING = 'STATUS_PREPARING'
    STATUS_DONE = 'STATUS_DONE'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'STATUS_PENDING'),
        (STATUS_REJECTED, 'STATUS_REJECTED'),
        (STATUS_PREPARING, 'STATUS_PREPARING'),
        (STATUS_DONE, 'STATUS_DONE'),
    )

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    bill = models.ForeignKey(Bill, related_name='order',
                             on_delete=models.CASCADE)
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    observation = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    kitchen_accepted_at = models.DateTimeField(null=True, blank=True)
    kitchen_finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=25, choices=STATUS_CHOICES, default=STATUS_PENDING)
    value_order = models.DecimalField(
        null=True, blank=True, max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        permissions = (
            ("can_change_order_status", "Can Change Order Status"),
            ("can_view_order", "Can View Order"),
            ("can_change_order", "Can Change Order"),
            ("can_create_order", "Can Create Order"),
        )

    def __str__(self):
        return f'{self.bill.table}({self.item})'

    def total_price(self):
        return Decimal(self.value_order or 0.00)

    def cancel_order(self):
        self.status = Order.STATUS_REJECTED
        self.canceled_at = timezone.now()
        body_msg = "O restaurante " f'{self.bill.establishment.name}' " cancelou o seu pedido"
        self.send_fcm_push_notifications(
            'Pedido Recusado',
            'order_refused',
            body_msg)
        self.save()

    def create_order(item, user):
        bill = get_object_or_404(Bill, id=item.get('bill'))
        menu_item = get_object_or_404(MenuItem, id=item.get('item'))
        quantity = item.get('quantity')
        observation = item.get('observation')

        return Order.objects.create(
            user=user, bill=bill, item=menu_item,
            quantity=quantity, observation=observation,
            status=Order.STATUS_PENDING)

    def send_pusher_notification(self):
        kitchens = User.objects.filter(id__in=Employee.objects.filter(
            establishment=self.bill.establishment,
            user_type=Employee.USER_KITCHEN).values('user'))
        list_kitchens = [kitchen.id for kitchen in kitchens]
        return PusherNotification.send_notifications(
            list_kitchens, 'kitchen', 'cancels_existing_order',
            {'order_id': self.id})

    def send_fcm_push_notifications(self, title, key, body_msg):
        devices = FCMDevice.objects.filter(
            user_id__in=BillMember.objects.filter(
                bill=self.bill).values('customer'))

        user_full_name = '{} {}'.format(self.user.first_name, self.user.last_name)
        order_dict = {'id': self.id, 'user': self.user.id,
                      'name': user_full_name,
                      'bill': self.bill.id, 'item_id': self.item.id,
                      'item_name': self.item.name,
                      'total_price': self.value_order,
                      'quantity': self.quantity,
                      'created_at': self.created_at,
                      'canceled_at': self.canceled_at,
                      'kitchen_accepted_at': self.kitchen_accepted_at,
                      'kitchen_finished_at': self.kitchen_finished_at,
                      'status': self.status}
        order_dict = json.dumps(order_dict, default=objects_to_json)
        dict_data = {'key': key, 'data': order_dict}
        devices.send_message(title, body_msg,
                             icon=self.bill.establishment.logo_url.url,
                             data=dict_data)


class BillPayment(models.Model):

    STATUS_IN_ANALYSIS = 'IN_ANALYSIS'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_AUTHORIZED = 'AUTHORIZED'
    STATUS_OFFLINE_PENDING = 'OFFLINE_PENDING'
    STATUS_OFFLINE_APPROVED = 'OFFLINE_APPROVED'
    STATUS_OFFLINE_CANCELLED = 'OFFLINE_CANCELLED'

    STATUS_PAYMENT_CHOICES = (
        (STATUS_IN_ANALYSIS, 'Sob análise'),
        (STATUS_CANCELLED, 'Cancelado'),
        (STATUS_AUTHORIZED, 'Autorizado'),
        (STATUS_OFFLINE_PENDING, 'Offline Pendente'),
        (STATUS_OFFLINE_APPROVED, 'Offline Aprovado'),
        (STATUS_OFFLINE_CANCELLED, 'Offline Cancelado'),
    )

    payment_uuid = models.CharField(max_length=65, unique=True)
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE)
    status_payment = models.CharField(
        max_length=40, choices=STATUS_PAYMENT_CHOICES, null=True, blank=True)
    status_updated = models.DateTimeField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    bill = models.ForeignKey(
        Bill, on_delete=models.CASCADE, related_name='bill_payment')
    value = models.DecimalField(max_digits=8, decimal_places=2)
    user_moip_id = models.ForeignKey(
        UserPayment, on_delete=models.SET_NULL, null=True, blank=True)
    bill_member = models.ForeignKey(
        BillMember, on_delete=models.SET_NULL, null=True, blank=True)
    credit_card = models.ForeignKey(
        UserCreditCard, on_delete=models.SET_NULL, null=True, blank=True)
    id_payment_moip = models.CharField(
        max_length=20, unique=True, null=True, blank=True)
    promocode = models.ForeignKey(
        EstablishmentPromotions, on_delete=models.CASCADE,
        null=True, blank=True)
    noruh_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00)
    moip_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default=0.00)

    class Meta:
        verbose_name = _('Bill payment')
        verbose_name_plural = _('Bill payments')
        permissions = (
            ("can_view_payment", "Can View Payment"),
            ("can_change_status_payment", "Can Change Status Payment"),
            ("can_accept_payment", "Can Accpet Payment"),
            ("can_create_payment", "Can Create Payment"),
            ("can_update_payment", "Can Update Payment"),
            ("can_delete_payment", "Can Delete Payment"),
        )

    def __str__(self):
        return f'{self.bill}({self.user_moip_id})'

    def notification_payload(self, key):
        ''' 
        This method is responsible to send data to firestore when
        create payments. We use camelCase on data dict payload for google convention
        '''
        user_full_name = '{} {}'.format(
            self.bill_member.customer.first_name,
            self.bill_member.customer.last_name)

        data = {
            'userName': user_full_name,
            'userUid': self.bill_member.customer.id,
            'value': float(self.value),
            'lastFour': getattr(self.credit_card, 'last_four_digits', None),
            'brand': getattr(self.credit_card, 'brand_card', None),
            'paymentStatus': self.status_payment,
            'noruhTip': float(self.noruh_fee)
        }
        return {
            'action': key,
            'userUid': self.bill_member.customer.id,
            'billId': self.bill.id,
            'createdAt': self.date.timestamp(),
            'payment': data,
        }

    def send_pusher_notification(self, bill, user):
        waiters = User.objects.filter(id__in=Employee.objects.filter(
            establishment=bill.establishment,
            user_type=Employee.USER_WAITER).values('user'))
        list_waiters = [waiter.id for waiter in waiters]
        data = {'bill_id': bill.id, 'username': user.first_name,
                'status': BillPayment.STATUS_OFFLINE_PENDING}
        return PusherNotification.send_notifications(
            list_waiters, 'waiter', 'payment_verification', data)

    def reject_offline_payment(self):
        self.status_updated = timezone.now()
        self.status_payment = BillPayment.STATUS_OFFLINE_CANCELLED
        devices = FCMDevice.objects.filter(
            user__in=BillMember.objects.filter(
                bill=self.bill, leave_at__isnull=False).values('customer'))
        self.save()

        user_full_name = '{} {}'.format(self.bill_member.customer.first_name, self.bill_member.customer.last_name)
        body_msg = "O pagamento de R$" f'{self.value}' " foi recusado"
        data_payment = {"bill_id": self.bill.id,
                        "user_name": user_full_name,
                        "user_id": self.bill_member.customer.id,
                        "status_payment": self.status_payment,
                        "value": self.value}
        data_payment = json.dumps(data_payment, default=objects_to_json)
        payment_dict = {"key": "payment_refused", "data": data_payment}

        devices.send_message("Pagamento Recusado", body_msg,
                             icon=self.bill.establishment.logo_url.url,
                             data=payment_dict)

        noruh_firestore = NoruhFireStore()
        data_notification = self.notification_payload(key='payment_refused')
        noruh_firestore.add_data_on_collection(data_notification)

    def approve_offline_payment(self):
        self.status_updated = timezone.now()
        self.status_payment = BillPayment.STATUS_OFFLINE_APPROVED
        devices = FCMDevice.objects.filter(
            user__in=BillMember.objects.filter(
                bill=self.bill, leave_at__isnull=True).values('customer'))
        self.save()

        bill = self.bill
        bill.value_paid = self.bill.value_paid + self.value
        bill.save()

        user_full_name = '{} {}'.format(self.bill_member.customer.first_name, self.bill_member.customer.last_name)
        body_msg = "O pagamento de R$" f'{self.value}' " foi aprovado"
        data_payment = {"bill_id": self.bill.id,
                        "user_name": user_full_name,
                        "user_id": self.bill_member.customer.id,
                        "status_payment": self.status_payment,
                        "value": self.value}
        data_payment = json.dumps(data_payment, default=objects_to_json)
        payment_dict = {"key": "payment_accepted", "data": data_payment}

        devices.send_message("Pagamento Aprovado", body_msg,
                             icon=self.bill.establishment.logo_url.url,
                             data=payment_dict)

        noruh_firestore = NoruhFireStore()
        data_notification = self.notification_payload(key='payment_accepted')
        noruh_firestore.add_data_on_collection(data_notification)

        if self.promocode is not None:
            all_value_bill = (all_value_bill - self.promocode.value)

        if float(bill.value_paid) >= float(bill.all_value_bill_without_taxe_service()) and float(bill.value_paid) <= bill.all_value_bill():
            door_mans = User.objects.filter(
                id__in=Employee.objects.filter(
                    establishment=self.bill.establishment,
                    user_type=Employee.USER_DOOR_MAN).values('user'))

            list_door_mans = [door_man.id for door_man in door_mans]
            data = {"bill_id": self.bill.id,
                    "username": self.bill_member.customer.first_name,
                    "payment_status": self.status_payment,
                    "table": self.bill.table.name}

            PusherNotification.send_notifications(
                list_door_mans, "door_man", "payment_confirm", data)

            self.bill.payment_date = timezone.now()
            BillMember.objects.filter(
                bill=self.bill.id, leave_at__isnull=True).update(
                leave_at=timezone.now())
            self.save()
            self.bill.save()
            noruh_firestore = NoruhFireStore()
            data_notification = {
                'action': 'bill_closed',
                'billId': bill.id,
                'createdAt': timezone.now().isoformat()
            }
            noruh_firestore.add_data_on_collection(data_notification)

        BillMember.objects.filter(
            bill=self.bill, customer=self.bill_member.customer,
            leave_at__isnull=True).update(leave_at=timezone.now())


class UserRating(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    user = models.ForeignKey(BillMember, on_delete=models.CASCADE)
    environment = models.PositiveSmallIntegerField(null=True, blank=True)
    food = models.PositiveSmallIntegerField(null=True, blank=True)
    service = models.PositiveSmallIntegerField(null=True, blank=True)
    observation = models.TextField(null=True, blank=True)
    average = models.DecimalField(
        null=True, blank=True, max_digits=5, decimal_places=1)

    class Meta:
        verbose_name = _('User rating')
        verbose_name_plural = _('User ratings')
        unique_together = ('bill', 'user')
        permissions = (
            ("can_delete_evaluation", "Can Delete Evaluation"),
            ("can_view_evaluation", "Can View Evaluation"),
        )

    def __str__(self):
        return f'{self.user}'


class AnswerEvaluation(models.Model):
    evaluation = models.OneToOneField(UserRating, on_delete=models.CASCADE,
                                      related_name='establishment_answer')
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE,
                                      related_name='answers')
    answer = models.TextField()

    class Meta:
        verbose_name = _('Answer To Evaluation')
        verbose_name_plural = _('Answers to Evaluations')
        unique_together = ('evaluation', 'establishment')
        permissions = (
            ("can_answer_evaluation", "Can Answer a Evaluation"),
        )

    def __str__(self):
        return f'{self.answer}'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('User profile')
        verbose_name_plural = _('Users profile')

    def __str__(self):
        return str(self.user)


class OfflineCompensations(models.Model):
    establishment = models.ForeignKey(Establishment, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    value = models.DecimalField(max_digits=8, decimal_places=2)
    date_compensation = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = _('Offline Compensation')
        verbose_name_plural = _('Offline Compensations')

    def __str__(self):
        month_name = calendar.month_name[self.month]
        return "{} - {} - {} ".format(self.establishment, month_name, self.value)


@receiver(post_save, sender=BillPayment)
def update_values_profile(sender, created, instance, **kwargs):
    if created:
        if instance.status_payment == BillPayment.STATUS_OFFLINE_APPROVED or instance.status_payment == BillPayment.STATUS_AUTHORIZED:
            establishments_count = BillPayment.objects.filter(
                bill_member=instance.bill_member).values('establishment').annotate(
                    Count('id')).count()
            average_spent = BillPayment.objects.filter(
                bill_member=instance.bill_member).aggregate(Avg('value'))

            profile = instance.bill_member.customer.profile
            profile.visited_establishments_count = establishments_count
            profile.average_value_spent = average_spent.get('value__avg')
            profile.save()


@receiver(post_save, sender=Employee)
def add_employee_to_group(sender, created, instance, **kwargs):
    if created:
        user = instance.user
        if instance.user_type == Employee.USER_MANAGER:
            group_manager = Group.objects.get(id=1)
            group_manager.user_set.add(user)
            EstablishmentManager.objects.create(
                user=user, establishment=instance.establishment)
        if instance.user_type == Employee.USER_KITCHEN:
            group_kitchen = Group.objects.get(id=2)
            group_kitchen.user_set.add(user)
        if instance.user_type == Employee.USER_WAITER:
            group_waiter = Group.objects.get(id=3)
            group_waiter.user_set.add(user)
        if instance.user_type == Employee.USER_DOOR_MAN:
            group_door_man = Group.objects.get(id=4)
            group_door_man.user_set.add(user)


@receiver(post_save, sender=Establishment)
def create_first_table(sender, created, instance, **kwargs):
    if created:
        establishment = instance
        table_zone = TableZone.objects.create(
            name=ORDER_REMOTE_TABLE_ZONE + str(instance),
            establishment=establishment, enabled=True)
        Table.objects.create(establishment=establishment,
                             table_zone=table_zone, name=ORDER_REMOTE,
                             enabled=True)


@receiver(post_save, sender=Establishment)
def create_first_menu(sender, created, instance, **kwargs):
    if created:
        establishment = instance
        menu = Menu.objects.create(establishment=establishment,
                                   name='Menu {}'.format(instance.name), enabled=True)


@receiver(post_delete, sender=Employee)
def delete_user(sender, instance, **kwargs):
    user_id = instance.user_id
    User.objects.filter(id=user_id).delete()


@receiver(post_save, sender=UserRating)
def update_average(sender, created, instance, **kwargs):
    if created:
        average = (instance.food + instance.service + instance.environment) / 3
        instance.average = average
        instance.save()

'''
@receiver(pre_save, sender=BillMember)
def check_opened_bill(sender, instance, **_):
   
    # Check if user have an open bill.
   
    if sender.objects.exclude(
        id=instance.id).filter(
            customer=instance.customer, leave_at__isnull=True).exists():
        raise OpenBillException()


@receiver(pre_save, sender=BillMember)
def check_can_leave_bill(sender, instance, **_):

    # Check if user can leave the current bill.

    total_active_members = sender.objects.filter(bill=instance.bill,
                                                 leave_at__isnull=True,
                                                 joined_at__isnull=False).count()
    if total_active_members == 1 and instance.leave_at is None and instance.bill.value_paid < instance.bill.orders_total():
        raise CannotLeaveBillException()
'''

@receiver(post_save, sender=Order)
def update_value_order(sender, created, instance, **kwargs):
    if created:
        if not instance.value_order:
            value_order = instance.item.price * instance.quantity
            instance.value_order = value_order
            instance.save()


@receiver(pre_save, sender=Order)
def check_can_cancel_order(sender, instance, **_):
    if instance.canceled_at is not None and instance.kitchen_finished_at:
        raise CannotCancelOrderException()
