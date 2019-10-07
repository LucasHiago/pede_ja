from django.contrib import admin
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import *


class EstablishmentOperatingHoursInline(admin.TabularInline):
    model = EstablishmentOperatingHours
    extra = 0

class EstablishmentPromotionsInline(admin.TabularInline):
    model = EstablishmentPromotions
    extra = 0

class EstablishmentEventsInline(admin.TabularInline):
    model = EstablishmentEvents
    extra = 0

class EstablishmentPhotoInline(admin.TabularInline):
    model = EstablishmentPhoto
    extra = 0


class EstablishmentManagerInline(admin.TabularInline):
    model = EstablishmentManager
    extra = 0


class TableInline(admin.TabularInline):
    model = Table
    extra = 0


class EstablishmentAdmin(admin.ModelAdmin):
    model = Establishment
    inlines = (
        EstablishmentOperatingHoursInline,
        EstablishmentPromotionsInline,
        EstablishmentEventsInline,
        EstablishmentPhotoInline,
        EstablishmentManagerInline,
        TableInline,
        )
    list_display = (
        'name',
        'cuisine_type',
        'enabled',
        'opened',
    )


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 0


class MenuAdmin(admin.ModelAdmin):
    model = Menu
    inlines = (
        MenuItemInline,
        )
    list_display = ('name', 'establishment', 'menu_items_count')

    def menu_items_count(self, obj) -> int:
        return obj.items.count()
    menu_items_count.short_description = _('Menu items')


class MenuItemAdmin(admin.ModelAdmin):
    model = MenuItem
    list_display = ('name', 'establishment', 'price', 'category', 'serve_up', 'available')

    def establishment(self, obj) -> Establishment:
        return obj.menu.establishment
    establishment.short_description = _('Establishment')
    establishment.admin_order_field = 'menu__establishment'


class OrderInline(admin.TabularInline):
    model = Order
    extra = 0


class BillPaymentInline(admin.TabularInline):
    model = BillPayment
    extra = 0


class UserRatingInline(admin.TabularInline):
    model = UserRating
    extra = 0


class BillAdmin(admin.ModelAdmin):
    model = Bill
    inlines = (
        OrderInline,
        BillPaymentInline,
        UserRatingInline,
    )
    readonly_fields = (
        'table',
        'customers',
        'establishment',
        'payment_date',
        'opening_date',
    )
    list_display = (
        'table',
        'establishment',
        'payment_date',
        'opening_date',
    )


class TableAdmin(admin.ModelAdmin):
    model = Table
    list_display = ('name', 'establishment',
                    'table_zone', 'enabled', 'is_available')

    def establishment(self, obj) -> Establishment:
        return obj.menu.establishment
    establishment.short_description = _('Establishment')
    establishment.admin_order_field = 'menu__establishment'

    def is_available(self, obj) -> bool:
        return obj.is_available
    is_available.short_description = _('Available')
    is_available.admin_order_field = 'bill__payment_date'
    is_available.boolean = True


class TableZoneAdmin(admin.ModelAdmin):
    model = TableZone
    list_display = ('name', 'enabled', 'tables_count')

    def tables_count(self, obj) -> int:
        return obj.zone.count()
    tables_count.short_description = _('# tables')
    tables_count.admin_order_field = 'zone__name'


class EmployeeAdmin(admin.ModelAdmin):
    model = Employee
    list_display = ('user', 'establishment', 'user_type', 'cpf')


class OfflineCompensationsAdmin(admin.ModelAdmin):
    model = OfflineCompensations
    list_display = ('establishment', 'month', 'value', 'date_compensation')


class UserProfileInline(admin.TabularInline):
    model = UserProfile


class UserAdmin(BaseUserAdmin):
    model = User


admin.site.register(Establishment, EstablishmentAdmin)
admin.site.register(Amenity)
admin.site.register(Menu, MenuAdmin)
admin.site.register(ItemObservations)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(ItemCategory)
admin.site.register(TableZone, TableZoneAdmin)
admin.site.register(Table, TableAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(OfflineCompensations, OfflineCompensationsAdmin)
admin.site.register(CuisineType)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserPayment)
admin.site.register(MoipWirecardAPP)
admin.site.register(MoipWirecardCustomer)
admin.site.register(UserCreditCard)
admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Profile)
