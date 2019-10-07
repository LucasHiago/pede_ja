import json
import datetime
import uuid
import csv
import re

from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.db.models import Q, Sum
from django.views import generic, View
from django.views.generic.base import TemplateView
from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect, render
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin
)
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from fcm_django.models import FCMDevice
from .models import (
    Establishment,
    EstablishmentManager,
    EstablishmentPhoto,
)
from .models import (
    Menu,
    MenuItem,
    ItemObservations,
    ItemCategory,
    MenuOffer
)
from .models import (
    Order,
    Bill,
    BillMember,
    BillPayment,
    Table,
    TableZone,
    Request
)
from .utils import (
    all_establishments_revenues,
    establishment_revenues,
    establishments_performance,
    get_variable_name_filter
)
from .models import MoipWirecardCustomer, MoipWirecardAPP
from .models import EstablishmentOperatingHours
from .models import EstablishmentEvents
from .models import UserRating, AnswerEvaluation
from .models import Employee, Profile
from .models import EstablishmentPromotions
from .models import OfflineCompensations
from .models import TokenRecoverPassword
from .forms import (
    AnswerToEvaluationForm,
    EmployeeForm,
    UpdatePasswordForm,
    EstablishmentForm,
    EstablishmentPhotoForm,
    EstablishmentLocationForm,
    EstablishmentDescriptionForm,
    EstablishmentAmenitiesForm,
    EstablishmentTaxesForm,
    EstablishmentTaxeCouvertForm,
    EstablishmentOfferRangeValueForm,
    EstablishmentPromocodeForm,
    EstablishmentEventsForm,
    EstablishmentOperatingHoursForm,
    ItemCategoryForm,
    MenuForm,
    MenuItemForm,
    MenuOfferForm,
    MoipWirecardCustomerForm,
    MoipWirecardCompanyForm,
    ObservationItemForm,
    OrderForm,
    PaymentOfflineForm,
    TableForm,
    TableZoneForm,
    UserEmployeeForm,
)
from noruh_backend.firestore_connect import NoruhFireStore
from .mixin import PassRequestUserMixin, checker_permissions
from .payment.utils import (
    create_wirecard_personal_establishment, 
    create_wirecard_company_establishment
)
from .payment.moip import Moip


class Login(LoginView):

    def post(self, request, *args, **kwargs):
        if not request.POST.get('remember_me', None):
            request.session.set_expiry(0)
        return super().post(request, *args, **kwargs)


class RecoverPasswordByApi(TemplateView):
    template_name = 'reset_password_api_forms.html'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token_filter = TokenRecoverPassword.objects.filter(
            token=self.request.GET.get('token_url'))
        if not token_filter.exists():
            raise PermissionDenied

        token_object = token_filter.first()
        context['form'] = UpdatePasswordForm(user=token_object.user)
        return context

    def post(self, request, *args, **kwargs):
        token_url = self.request.GET.get('token_url')
        if not TokenRecoverPassword.objects.filter(token=token_url):
            raise PermissionDenied
        token_object = TokenRecoverPassword.objects.get(token=token_url)
        forms = UpdatePasswordForm(token_object.user, request.POST)

        if forms.is_valid():
            forms.save()
            token_object.delete()
            return HttpResponseRedirect(reverse_lazy('register:reset_password_complete'))

        return render(request, self.template_name, context)


class RecoverPasswordByApiComplete(TemplateView):
    template_name = 'reset_password_api_complete.html'


class TermsAndContions(TemplateView):
    template_name = 'terms_and_conditions.html'


class Home(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        user = self.request.user

        if user.is_superuser:
            return HttpResponseRedirect(reverse_lazy('register:dashboard_all_establishments'))

        if not hasattr(user, 'employee'):
            raise PermissionDenied

        establishment_id = user.employee.establishment.id
        user_type = user.employee.user_type
        specific_view = ''

        if user.employee.establishment.enabled is False:
            raise PermissionDenied

        if user_type == Employee.USER_MANAGER:
            specific_view = 'establishment_dashboard'

        if user_type == Employee.USER_KITCHEN:
            specific_view = 'orders_list_kitchen_pending'

        if user_type == Employee.USER_WAITER or user_type == Employee.USER_DOOR_MAN:
            specific_view = 'bill_list'

        return HttpResponseRedirect(reverse_lazy('register:{}'.format(specific_view),
                                                 kwargs={'establishment_id': establishment_id}))


# View for Load links to create Amenity and Cuisine Type, only super admin can access
class CreateWirecard(LoginRequiredMixin, TemplateView):
    template_name = './components/forms/establishment_wirecard_create_form.html'
    permission_required = "register.can_create_wirecard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MoipWirecardCustomerForm()
        return context

    def post(self, request, *args, **kwargs):
        form = MoipWirecardCustomerForm(request.POST)

        if form.is_valid():
            form = form.cleaned_data
            parameters = create_wirecard_personal_establishment(form)

            app = MoipWirecardAPP.objects.get(
                website='http://noruh.ilhasoft.mobi/')
            establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
            moip = Moip(app.access_token)

            customer = moip.create_wirecard(parameters)
            customer = json.loads(customer)

            if MoipWirecardCustomer.objects.filter(establishment=establishment).exists():
                return HttpResponse('Você não pode criar outra Conta Moip para o Mesmo Estabelecimento')

            if customer.get('errors') is not None:
                return HttpResponse(json.dumps(customer))
            else:
                id_wirecard = customer['id']
                login = customer['login']
                access_token = customer['accessToken']
                type_customer = customer['type']
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
                issue_date = customer['person'][
                    'identityDocument']['issueDate']
                created_at = customer['createdAt']
                link_account = customer['_links']['self']['href']
                set_password = customer['_links']['setPassword']['href']

                wirecard = MoipWirecardCustomer.objects.create(
                    establishment=establishment, id_wirecard=id_wirecard,
                    login=login, access_token=access_token,
                    channel_id=app, type=type_customer, email=login, name=name,
                    last_name=last_name, birth_date=birth_date,
                    number_cpf=number_cpf, street=street,
                    street_number=street_number, district=district,
                    zip_code=zip_code, city=city, state=state,
                    country_code=country_code, area_code=area_code,
                    number=number, number_rg=number_rg, issuer=issuer,
                    issue_date=issue_date, created_at=created_at,
                    link_account=link_account, set_password=set_password)

                return redirect('register:establishment_configurations', **{'id': establishment.id})


class CreateCompanyWirecard(LoginRequiredMixin, TemplateView):
    template_name = './components/forms/establishment_wirecard_company_create_form.html'
    permission_required = "register.can_create_wirecard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = MoipWirecardCompanyForm()
        return context

    def post(self, request, *args, **kwargs):
        form = MoipWirecardCompanyForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data

            data['remote_addr'] = request.META.get('REMOTE_ADDR')
            data['user_agent'] = request.META.get('HTTP_USER_AGENT')
            parameters = create_wirecard_company_establishment(data)

            app = MoipWirecardAPP.objects.get(
                website='http://noruh.ilhasoft.mobi/')
            establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
            moip = Moip(app.access_token)

            customer = moip.create_wirecard(parameters)
            customer = json.loads(customer)

            if MoipWirecardCustomer.objects.filter(establishment=establishment).exists():
                return HttpResponse('Você não pode criar outra Conta Moip para o Mesmo Estabelecimento')

            if customer.get('errors') is not None:
                return HttpResponse(json.dumps(customer))
            else:
                id_wirecard = customer['id']
                login = customer['login']
                access_token = customer['accessToken']
                type_customer = customer['type']

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

                business_name = customer['company']['businessName']
                opening_date = customer['company']['openingDate']
                number_cnpj = customer['company']['taxDocument']['number']

                created_at = customer['createdAt']
                link_account = customer['_links']['self']['href']
                set_password = customer['_links']['setPassword']['href']

                wirecard = MoipWirecardCustomer.objects.create(
                    establishment=establishment, id_wirecard=id_wirecard,
                    login=login, access_token=access_token,
                    channel_id=app, type=type_customer, email=login, name=name,
                    last_name=last_name, birth_date=birth_date,
                    number_cpf=number_cpf, street=street,
                    street_number=street_number, district=district,
                    zip_code=zip_code, city=city, state=state,
                    country_code=country_code, area_code=area_code,
                    number=number, business_name=business_name,
                    opening_date=opening_date, number_cnpj=number_cnpj,
                    created_at=created_at,
                    link_account=link_account, set_password=set_password)

                return redirect('register:establishment_configurations', **{'id': establishment.id})


class DetailWirecard(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = MoipWirecardCustomer
    context_object_name = 'item'
    permission_required = "register.can_view_wirecard"
    template_name = 'wirecard_detail.html'

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True
        wirecard_est = MoipWirecardCustomer.objects.filter(id=self.kwargs['pk'],
                                                           establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, wirecard_est):
            return True


class CreateEmployee(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'employee_form.html'
    permission_required = "register.can_create_employee"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        establishment_id = self.request.GET.get('establishment_id', None)
        if establishment_id:
            context['establishment'] = Establishment.objects.get(id=establishment_id)

        context['establishments'] = Establishment.objects.all()
        context['form_user'] = UserEmployeeForm(prefix='user')
        context['form_employee'] = EmployeeForm(
            establishment_id, user=self.request.user, prefix='employee')
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        establishment = context.get('establishment')

        user_form = UserEmployeeForm(request.POST, prefix='user')
        employee_form = EmployeeForm(
            getattr(establishment, 'id', None),
            request.POST, files=request.FILES,
            prefix='employee', user=self.request.user)

        if user_form.is_valid() and employee_form.is_valid():
            obj_user = user_form.save(commit=False)
            obj_user.username = user_form.data.get('user-email')
            obj_user.first_name = user_form.data.get('user-name')

            user_form.save()
            employee_form.instance.user = user_form.instance
            employee_form.save()
            return HttpResponse(status=200)

        context['form_user'] = user_form
        context['form_employee'] = employee_form
        context['form_user_errors'] = user_form.errors
        context['form_employee_errors'] = employee_form.errors
        data_errors = {}
        data_errors.update(employee_form.errors)
        data_errors.update(user_form.errors)

        return HttpResponse(', '.join(data_errors.keys()), status=406)


class AlterEmployee(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Employee
    fields = ['user_type', 'cpf', 'image']
    template_name = './components/forms/establishment_employee_update_form.html'
    permission_required = "register.can_alter_employee"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = Employee.objects.get(id=self.kwargs['pk'])
        context['employee'] = employee
        context['form'] = EmployeeForm(instance=employee, user=self.request.user)
        return context

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        employee_est = Employee.objects.filter(id=self.kwargs['pk'],
                                               establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, employee_est.exists()):
            return True

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:employee_detail', kwargs={'pk': self.object.id})
        return reverse_lazy('register:employee_detail', args=(self.object.id,))


class ListEmployeeEstablishment(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Employee
    context_object_name = 'all_items'
    permission_required = "register.can_view_employee"
    template_name = 'employee_list.html'
    paginate_by = 10

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        employee_est = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, employee_est.exists()):
            return True

    def get_queryset(self):
        return Employee.objects.filter(establishment__id=self.kwargs['establishment_id']).order_by('user_type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = Establishment.objects.get(pk=self.kwargs['establishment_id'])
        return context


class ListSearchEmployeeEstablishment(ListEmployeeEstablishment):

    def get_queryset(self):
        result = super(ListSearchEmployeeEstablishment, self).get_queryset()

        query = self.request.GET.get('q')
        if query:
            return result.filter(Q(user__first_name__icontains=query) |
                                 Q(user__last_name__icontains=query))


class ListEmployeeAll(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    model = Employee
    context_object_name = 'all_items'
    permission_required = "register.can_view_employee"
    template_name = 'employee_list_all.html'
    paginate_by = 10

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True
        else:
            raise PermissionDenied

    def get_queryset(self):
        return Employee.objects.all().order_by('establishment')


class ListSearchEmployee(ListEmployeeAll):

    def get_queryset(self):
        result = super(ListSearchEmployee, self).get_queryset()

        query = self.request.GET.get('q')
        if query:
            return result.filter(Q(user__first_name__icontains=query) |
                                 Q(user__last_name__icontains=query))

        if not result:
            return Employee.objects.filter(establishment__id=self.kwargs['establishment_id']).order_by('user_type')
        return result


class DetailEmployee(LoginRequiredMixin, PermissionRequiredMixin, generic.DetailView):
    model = Employee
    context_object_name = 'item'
    permission_required = "register.can_view_employee"
    template_name = 'employee_detail.html'

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        employee_est = Employee.objects.filter(id=self.kwargs['pk'],
                                               establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, employee_est.exists()):
            return True


class DeleteEmployee(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_employee"
    model = Employee
    template_name = 'delete.html'

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        employee_est = Employee.objects.filter(id=self.kwargs['pk'],
                                               establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, employee_est.exists()):
            return True

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:employee_list_establishment', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:employee_list_establishment', args=(self.object.establishment.id,))


class ListUserLogged(LoginRequiredMixin, generic.ListView):
    model = User
    context_object_name = 'item'
    template_name = 'user_logged.html'

    def get_queryset(self):
        return User.objects.get(id=self.request.user.id)


class AlterUser(LoginRequiredMixin, generic.UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'email']
    template_name = './components/user/alter_user_form.html'
    success_url = reverse_lazy('register:user_logged_detail')


# Establishments
class DashboardEstablishment(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_view_dashboard_from_establishment"
    template_name = 'dashboard_establishment.html'
    context_object_name = 'all_items'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        month_filter = self.request.GET.get('month-filter')

        if month_filter:
            current_month = datetime.date(
                datetime.date.today().year,
                int(month_filter),
                datetime.date.today().day
            )
        else:
            current_month = datetime.date.today()

        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        data['establishment'] = establishment
        data['month_name'] = current_month.month
        data['filter_date'] = current_month

        type_filter = self.request.GET.get('type_filter')

        data['revenues'] = establishment_revenues(current_month, type_filter, establishment)
        data['variable_name_filter'] = get_variable_name_filter(type_filter)

        billing = BillPayment.objects.filter(
            date__month=current_month.month,
            date__year=current_month.year,
            establishment__id=self.kwargs['establishment_id'],
            status_payment__in=[
                BillPayment.STATUS_OFFLINE_APPROVED,
                BillPayment.STATUS_AUTHORIZED])

        data['billing'] = billing.aggregate(Sum('value')).get('value__sum')

        n_all_orders = Order.objects.filter(
            bill__establishment__id=self.kwargs['establishment_id'],
            created_at__year=current_month.year,
            created_at__month=current_month.month,
            canceled_at__isnull=True).count()
        data['n_all_orders'] = n_all_orders

        data['average_ticket'] = establishment.average_bills(current_month)

        data['more_requested'] = Order.objects.filter(
            bill__establishment_id=self.kwargs['establishment_id'],
            status__in=[
                Order.STATUS_PENDING, Order.STATUS_PREPARING,
                Order.STATUS_DONE]).values(
                    'item__name', 'item__photo').annotate(
                        pedidos=Sum('quantity')).order_by('-pedidos')[:5]

        data['report_offline_payment_value'] = establishment.report_offline_payment_with_month(current_month)

        return data

    def get_queryset(self):
        result = MenuItem.objects.filter(menu__establishment__id=self.kwargs['establishment_id'])
        category = self.request.GET.get('category')
        item_name = self.request.GET.get('item-name')

        if category:
            result = result.filter(Q(category__id=category))
        if item_name:
            result = result.filter(Q(name__icontains=item_name))

        return result

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        employee_est = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, employee_est.exists()):
            return True


class ListAllItemsMoreRequested(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_view_dashboard_from_establishment"
    template_name = 'items_more_requested.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(id=self.kwargs['establishment_id'])
        data['more_requested'] = Order.objects.filter(
            bill__establishment_id=self.kwargs['establishment_id'],
            status__in=[
                Order.STATUS_PENDING, Order.STATUS_PREPARING,
                Order.STATUS_DONE]).values(
                    'item__name', 'item__photo').annotate(
                        pedidos=Sum('quantity')).order_by('-pedidos')
        return data

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        employee_est = Employee.objects.filter(
            establishment__id=self.kwargs['establishment_id'],
            establishment=user.manager.establishment)

        if checker_permissions(user, self.permission_required, employee_est.exists()):
            return True


class DashboardAllEstablishments(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_view_dashboard_from_establishment"
    template_name = 'dashboard_all_establishments.html'
    context_object_name = 'all_items'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        month_filter = self.request.GET.get('month-filter')

        if month_filter:
            current_month = datetime.date(
                datetime.date.today().year,
                int(month_filter),
                datetime.date.today().day
            )
        else:
            current_month = datetime.date.today()

        data['month_name'] = current_month.month
        data['filter_date'] = current_month

        type_filter = self.request.GET.get('type_filter')
        data['revenues'] = all_establishments_revenues(current_month, type_filter)
        data['variable_name_filter'] = get_variable_name_filter(type_filter)

        users = User.objects.filter(employee__isnull=True)
        data['count_customers'] = users.count()
        data['customers_male'] = users.filter(profile__gender=Profile.GENDER_MALE).count()
        data['customers_female'] = users.filter(profile__gender=Profile.GENDER_FEMALE).count()
        data['customers_other'] = users.filter(profile__gender=Profile.GENDER_OTHER).count()

        all_billing = BillPayment.objects.filter(
            date__month=current_month.month,
            date__year=current_month.year).aggregate(Sum('value'))
        data['all_billing'] = all_billing.get('value__sum')

        all_bills = Bill.objects.filter(
            opening_date__month__gte=current_month.month,
            opening_date__year=current_month.year).count()
        data['all_bills'] = all_bills

        all_orders = Order.objects.filter(
            created_at__year=current_month.year,
            created_at__month=current_month.month,
            canceled_at__isnull=True).count()

        data['all_orders'] = all_orders
        data['all_compensations'] = Establishment.report_offline_all_establishments(current_month)

        data['customers_count'] = User.objects.filter(employee__isnull=True).count()
        data['all_establishments'] = establishments_performance()

        return data

    def has_permission(self):
        return self.request.user.is_superuser


class CreateEstablishment(LoginRequiredMixin,
                          PermissionRequiredMixin, TemplateView):
    template_name = './components/forms/establishment_create_establishment_form.html'
    permission_required = "register.can_create_establishment"
    success_url = reverse_lazy('register:establishment_list_view')
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = EstablishmentForm()
        return context

    def post(self, request, *args, **kwargs):
        form = EstablishmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(reverse('register:establishment_list_all'))
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)

    def has_permission(self):
        if self.request.user.is_superuser:
            return True
        else:
            raise PermissionDenied


class BaseEstablishment(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'establishment_base.html'
    permission_required = 'register.can_view_establishment'

    def get_context_data(self, **kwargs):
        context = super(BaseEstablishment, self).get_context_data(**kwargs)
        context['establishment'] = Establishment.objects.get(id=self.kwargs['id'])
        return context

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(
            establishment__id=self.kwargs['id'],
            establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class ConfigurationsEstablishment(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'establishment_configurations.html'
    permission_required = 'register.can_view_establishment'

    def get_context_data(self, **kwargs):
        context = super(ConfigurationsEstablishment, self).get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['id'])
        context['establishment'] = establishment
        context['photos'] = EstablishmentPhoto.objects.filter(
            establishment=establishment)
        context['amenities'] = establishment.amenities.all()
        context['operating_hours'] = EstablishmentOperatingHours.objects.filter(
            establishment=establishment)
        context['promocodes'] = EstablishmentPromotions.objects.filter(
            establishment=establishment)
        context['events'] = EstablishmentEvents.objects.filter(
            establishment=establishment)
        context['moip_account'] = MoipWirecardCustomer.objects.filter(
            establishment=establishment)
        context['establishment_payment_tax'] = "%.2f" % (establishment.payment_tax * 100)
        context['establishment_offline_percentage'] = "%.2f" % (establishment.offline_percentage * 100)
        return context

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['id'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateEstablismentLocation(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Establishment
    form_class = EstablishmentLocationForm
    template_name = 'establishment_form.html'
    permission_required = "register.can_update_location_establishment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['pk'])
        context['establishment'] = establishment
        context['title'] = 'Localização'
        context['form'] = EstablishmentLocationForm(instance=establishment)
        return context    

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['pk'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateEstablismentDescription(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Establishment
    form_class = EstablishmentDescriptionForm
    template_name = './components/forms/establishment_description_update_form.html'
    permission_required = "register.can_update_description_establishment"

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['pk'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateEstablismentAmenities(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Establishment
    form_class = EstablishmentAmenitiesForm
    template_name = './components/forms/establishment_amenities_update_form.html'
    permission_required = "register.can_update_amenities_establishment"

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['pk'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateGPSRestrictionEstablishment(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_update_functions_establishment"

    def get(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['pk'])
        establishment.gps_restriction = not establishment.gps_restriction
        establishment.save()
        return JsonResponse({'gps_restriction': establishment.gps_restriction,
                             'message': 'Status Altered'}, status=200)

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['pk'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateFeaturedEstablishment(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_update_functions_establishment"

    def get(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['pk'])
        establishment.featured = not establishment.featured
        establishment.save()
        return JsonResponse({'featured': establishment.featured,
                             'message': 'Status Altered'}, status=200)

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['pk'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateEstablismentTaxes(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Establishment
    form_class = EstablishmentTaxesForm
    template_name = 'establishment_form.html'
    permission_required = "register.can_update_taxes_establishment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['pk'])
        context['establishment'] = establishment
        context['title'] = 'Taxas'
        context['form'] = EstablishmentTaxesForm(instance=establishment)
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True


class UpdateEstablishmentPaysPaymentTax(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_update_functions_establishment"

    def get(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['pk'])
        establishment.pays_payment_tax = not establishment.pays_payment_tax
        establishment.save()
        return JsonResponse({'pays_payment_tax': establishment.pays_payment_tax,
                             'message': 'Status Altered'}, status=200)

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['pk'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateEstablismentCouvert(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Establishment
    form_class = EstablishmentTaxeCouvertForm
    template_name = './components/forms/establishment_couvert_update_form.html'
    permission_required = "register.can_update_couvert_taxe_establishment"

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['pk'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateEstablismentOfferRangeValue(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Establishment
    form_class = EstablishmentOfferRangeValueForm
    template_name = './components/forms/establishment_offer_range_update_form.html'
    permission_required = "register.can_update_offer_range_value"

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['pk'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateOpenOrCloseEstablishment(LoginRequiredMixin,
                                     PermissionRequiredMixin, View):
    permission_required = "register.can_update_opened"

    def get(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['pk'])
        establishment.opened = not establishment.opened
        establishment.save()
        return JsonResponse({'opened': establishment.opened,
                             'message': 'Status Altered'}, status=200)

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['pk'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class DeleteEstablishment(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_establishment"
    model = Establishment
    template_name = 'delete_establishment.html'
    success_url = reverse_lazy('register:home')

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True
        raise PermissionDenied


class DisableEstablishment(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['pk'])
        establishment.enabled = not establishment.enabled
        establishment.save()
        return JsonResponse({'enabled': establishment.enabled,
                             'message': 'Status Altered'}, status=200)

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True
        raise PermissionDenied


class CreateOperatingHours(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = './components/forms/establishment_operating_hours_form.html'
    permission_required = "register.can_create_operating_hour"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        context['establishment'] = establishment
        context['form'] = EstablishmentOperatingHoursForm(establishment)
        return context

    def post(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        form = EstablishmentOperatingHoursForm(establishment, request.POST)

        if form.is_valid():
            form.save()
            return redirect('register:establishment_configurations', **{'id': establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return HttpResponse(context, status=406)


class DeleteOperatingHour(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_operating_hour"
    model = EstablishmentOperatingHours
    template_name = './components/forms/establishment_operating_hours_delete_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        operating_hour = EstablishmentOperatingHours.objects.get(id=self.kwargs['pk'])
        context['operating_hour'] = operating_hour
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'id': self.object.establishment.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        operating_hours = EstablishmentOperatingHours.objects.filter(pk=self.kwargs['pk'],
                                                                     establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, operating_hours.exists()):
            return True


class CreatePromoCode(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = './components/forms/promocode_form.html'
    permission_required = "register.can_create_promocode"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        context['establishment'] = establishment
        context['form'] = EstablishmentPromocodeForm()
        return context

    def post(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        form = EstablishmentPromocodeForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.establishment = establishment
            form.save()
            return redirect('register:establishment_configurations', **{'id': obj.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class UpdatePromoCodes(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_create_promocode"

    def get(self, request, *args, **kwargs):
        promocode = EstablishmentPromotions.objects.get(id=self.kwargs['pk'])
        promocode.enabled = not promocode.enabled
        promocode.save()
        return JsonResponse({'enabled': promocode.enabled,
                             'message': 'Status Altered'}, status=200)

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        promocode = EstablishmentPromotions.objects.filter(id=self.kwargs['pk'],
                                                           establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, promocode.exists()):
            return True



class DeletePromocodes(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_promotions"
    model = EstablishmentPromotions
    template_name = './components/forms/establishment_promocode_delete_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        promocode = EstablishmentPromotions.objects.get(id=self.kwargs['pk'])
        context['promocode'] = promocode
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        promocode = EstablishmentPromotions.objects.filter(id=self.kwargs['pk'],
                                                           establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, promocode.exists()):
            return True


class CreateEvents(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = './components/forms/establishment_events_form.html'
    permission_required = "register.can_create_events"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = Establishment.objects.get(id=self.kwargs['establishment_id'])
        context['form'] = EstablishmentEventsForm()
        return context

    def post(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        form = EstablishmentEventsForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.establishment = establishment
            form.save()
            return redirect('register:establishment_configurations', **{'id': obj.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class UpdateEvents(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = EstablishmentEvents
    fields = ['description', 'date']
    template_name = './components/forms/establishment_event_update_form.html'
    permission_required = "register.can_create_promocode"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment_event = EstablishmentEvents.objects.get(id=self.kwargs['pk'])
        context['form'] = EstablishmentEventsForm(instance=establishment_event)
        context['establishment_event'] = establishment_event
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        event = EstablishmentEvents.objects.filter(id=self.kwargs['pk'],
                                                   establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, event.exists()):
            return True

class DeleteEvents(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_events"
    model = EstablishmentEvents
    template_name = './components/forms/establishment_event_delete_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment_event = EstablishmentEvents.objects.get(id=self.kwargs['pk'])
        context['establishment_event'] = establishment_event
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        event = EstablishmentEvents.objects.filter(id=self.kwargs['pk'],
                                                   establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, event.exists()):
            return True


class ListAllEstablishment(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view__all_establishments"
    template_name = 'establishment_all_list.html'
    context_object_name = 'all_items'
    paginate_by = 10

    def get_queryset(self):
        return Establishment.objects.all()


class ListSearchEstablishment(ListAllEstablishment):

    def get_queryset(self):
        return Establishment.objects.filter(name__icontains=self.request.GET.get('q'))


class AddPhotoOnEstablishment(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_add_photo_establishment"
    template_name = './components/forms/establishment_photo_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        context['establishment'] = establishment
        context['form'] = EstablishmentPhotoForm()
        return context

    def post(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        form = EstablishmentPhotoForm(request.POST, request.FILES)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.establishment = establishment
            form.save()
            return redirect('register:establishment_configurations', **{'id': obj.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)

class DeletePhotoFromEstablishment(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    model = EstablishmentPhoto
    permission_required = 'register.can_delete_photo_establishment'
    template_name = './components/forms/establishment_photo_delete_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photo = EstablishmentPhoto.objects.get(id=self.kwargs['pk'])
        context['photo'] = photo
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:establishment_configurations', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:establishment_configurations', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_photo = EstablishmentPhoto.objects.filter(id=self.kwargs['pk'],
                                                      establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_photo.exists()):
            return True



# RF 033(Menu and Items)
class CreateMenu(LoginRequiredMixin, PassRequestUserMixin, PermissionRequiredMixin, generic.CreateView):
    permission_required = "register.can_create_menu"
    model = Menu
    form_class = MenuForm
    template_name = 'generic_form.html'
    context_object_name = 'object_name'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_list_from_establishment', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:menu_list_from_establishment', args=(self.object.establishment.id,))


class UpdateMenu(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    permission_required = "register.can_update_menu"
    model = Menu
    fields = ['name']
    template_name = 'generic_form.html'
    context_object_name = 'object_name'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_list_from_establishment', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:menu_list_from_establishment', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        menu = Menu.objects.filter(id=self.kwargs['pk'],
                                   establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, menu.exists()):
            return True


class DeleteMenu(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_menu"
    model = Menu
    template_name = 'delete_item_on_menu_confirm.html'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_list_from_establishment', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:menu_list_from_establishment', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        menu = Menu.objects.filter(id=self.kwargs['pk'],
                                   establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, menu.exists()):
            return True


class ListMenuFromEstablishment(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_menu"
    template_name = 'menu_list.html'
    context_object_name = 'all_items'
    paginate_by = 10
    raise_exception = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment_id'] = self.kwargs['establishment_id']
        data['categories'] = ItemCategory.objects.filter(
            establishment__id=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        return Menu.objects.filter(establishment__id=self.kwargs['establishment_id'])

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class ListMenuSearchFromEstablishment(ListMenuFromEstablishment):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment_id'] = self.kwargs['establishment_id']
        return data

    def get_queryset(self):
        result = super(ListMenuSearchFromEstablishment, self).get_queryset()

        query = self.request.GET.get('q')
        if query:
            return result.filter(Q(name__icontains=query))


class CreateItemOnMenu(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_create_item_on_menu"
    template_name = 'menu_item_create_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        context['form'] = MenuItemForm(establishment)
        context['establishment_id'] = establishment.id
        return context

    def post(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        menu = Menu.objects.get(establishment=establishment)
        form = MenuItemForm(establishment, request.POST, request.FILES)

        if form.is_valid():
            obj = form.save(commit=False)
            form.save()
            return redirect('register:menu_item_list', **{'establishment_id': obj.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class UpdateItemOnMenu(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = MenuItem
    form_class = MenuItemForm
    context_object_name = 'menu_item'
    template_name = 'menu_item_update_form.html'
    permission_required = "register.can_change_item_on_menu"
    raise_exception = True

    def get_form_kwargs(self):
        kwargs = super(UpdateItemOnMenu, self).get_form_kwargs()
        kwargs['establishment'] = self.object.menu.establishment
        return kwargs

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_item_list', kwargs={'menu_id': self.object.menu.id})
        return reverse_lazy('register:menu_item_list', args=(self.object.menu.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        menu_item = MenuItem.objects.filter(id=self.kwargs['pk'],
                                            menu__establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, menu_item.exists()):
            return True


class DeleteItemOnMenu(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_item_on_menu"
    model = MenuItem
    template_name = 'delete_item_on_menu_confirm.html'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        menu_item = MenuItem.objects.get(id=self.kwargs['pk'])
        context['menu_item'] = menu_item

        return context


    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_item_list', kwargs={'menu_id': self.object.menu.id})
        return reverse_lazy('register:menu_item_list', args=(self.object.menu.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        menu_item = MenuItem.objects.filter(id=self.kwargs['pk'],
                                            menu__establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, menu_item.exists()):
            return True


class ListMenuItems(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_item_on_menu"
    template_name = 'menu_item_list.html'
    context_object_name = 'all_items'
    paginate_by = 10
    raise_exception = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.kwargs is None:
            raise PermissionDenied
        data['establishment'] = Establishment.objects.get(id=self.kwargs['establishment_id'])
        data['categories'] = ItemCategory.objects.filter(
            establishment__id=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        if self.kwargs is None:
            raise PermissionDenied
        return MenuItem.objects.filter(menu__establishment__id=self.kwargs['establishment_id']).order_by('id')

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class ListMenuItemsSearch(ListMenuItems):
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        return data

    def get_queryset(self):

        result = super(ListMenuItemsSearch, self).get_queryset()

        name = self.request.GET.get('item-name')
        category = self.request.GET.get('categories')

        if name:
            result = result.filter(Q(name__icontains=name))
        if category:
            result =  result.filter(Q(category__id=category))

        return result


class ListMenuOffers(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_menu_offer"
    template_name = 'menu_offer_list.html'
    context_object_name = 'all_items'
    paginate_by = 10
    raise_exception = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.kwargs is None:
            raise PermissionDenied
        data['establishment'] = Establishment.objects.get(id=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        if self.kwargs is None:
            raise PermissionDenied
        return MenuOffer.objects.filter(category__establishment__id=self.kwargs['establishment_id'])

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class CreateMenuOffer(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_create_menu_offer"
    template_name = 'menu_offer_create_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        context['establishment'] = establishment
        context['form'] = MenuOfferForm(establishment)
        return context

    def post(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        form = MenuOfferForm(establishment, request.POST)

        if form.is_valid():
            form.save()
            return redirect('register:menu_offer_list', **{'establishment_id': establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class DeleteMenuOffer(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_menu_offer"
    model = MenuOffer
    template_name = 'delete.html'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_offer_list', kwargs={'establishment_id': self.object.category.establishment.id})
        return reverse_lazy('register:menu_offer_list', args=(self.object.category.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        menu_offer = MenuOffer.objects.filter(id=self.kwargs['pk'],
                                              category__establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, menu_offer.exists()):
            return True


class UpdateMenuOffer(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = MenuOffer
    fields = ['name', 'category', 'discount']
    permission_required = "register.can_create_menu_offer"
    template_name = 'menu_offer_update_form.html'
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        menu_offer = MenuOffer.objects.get(id=self.kwargs['pk'])
        context['form'] = MenuOfferForm(menu_offer.category.establishment, instance=menu_offer)
        context['establishment'] = menu_offer.category.establishment
        context['menu_offer'] = menu_offer
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_offer_list', kwargs={'establishment_id': self.object.category.establishment.id})
        return reverse_lazy('register:menu_offer_list', args=(self.object.category.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        menu_offer = MenuOffer.objects.filter(id=self.kwargs['pk'],
                                              category__establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, menu_offer.exists()):
            return True


class CreateCategory(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_create_category"
    template_name = 'create_category_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ItemCategoryForm()
        return context

    def post(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        form = ItemCategoryForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.establishment = establishment
            form.save()
            return redirect('register:menu_item_list', **{'establishment_id': obj.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class UpdateCategory(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    login_url = reverse_lazy('register:home')
    model = ItemCategory
    permission_required = "register.can_update_category"
    fields = ['name']
    template_name = 'update_category_form.html'
    permission_required = "register.can_update_category"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = ItemCategory.objects.get(id=self.kwargs['pk'])
        context['category'] = category
        context['form'] = ItemCategoryForm(instance=category)
        context['establishment'] = category.establishment
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_item_list', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:menu_item_list', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        category = ItemCategory.objects.filter(id=self.kwargs['pk'],
                                               establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, category.exists()):
            return True


class DeleteCategory(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_category"
    model = ItemCategory
    template_name = 'delete.html'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_category_list', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:menu_category_list', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        category = ItemCategory.objects.filter(id=self.kwargs['pk'],
                                               establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, category.exists()):
            return True


class ListCategory(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_category"
    template_name = 'item_category_list.html'
    context_object_name = 'all_items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = Establishment.objects.get(id=self.kwargs['establishment_id'])
        return context

    def get_queryset(self):
        return ItemCategory.objects.filter(establishment__id=self.kwargs['establishment_id'])

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class CreateObservationItem(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_create_item_observation"
    template_name = 'create_menu_observation_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = Establishment.objects.get(id=self.kwargs['establishment_id'])
        context['form'] = ObservationItemForm()
        return context

    def post(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        form = ObservationItemForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.establishment = establishment
            form.save()
            return redirect('register:menu_item_list', **{'establishment_id': obj.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class UpdateObservationItem(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = ItemObservations
    fields = ['observation']
    template_name = 'update_observation_form.html'
    permission_required = "register.can_update_item_observation"
    raise_exception = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        observation = ItemObservations.objects.get(id=self.kwargs['pk'])
        context['observation'] = observation
        context['form'] = ObservationItemForm(instance=observation)
        context['establishment'] = observation.establishment
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_item_list', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:menu_item_list', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        observation = ItemObservations.objects.filter(id=self.kwargs['pk'],
                                                      establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, observation.exists()):
            return True


class DeleteObservationItem(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_item_observation"
    model = ItemObservations
    template_name = 'delete.html'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:menu_observation_list', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:menu_observation_list', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        observation = ItemObservations.objects.filter(id=self.kwargs['pk'],
                                                      establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, observation.exists()):
            return True


class ListObservationItem(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_item_observation"
    template_name = 'item_observation.html'
    context_object_name = 'all_items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = Establishment.objects.get(id=self.kwargs['establishment_id'])
        return context

    def get_queryset(self):
        return ItemObservations.objects.filter(establishment__id=self.kwargs['establishment_id'])

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


# Bill, Tables and Orders
class ListOrders(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_order"
    template_name = './components/kitchen/order_list.html'
    context_object_name = 'all_items'
    paginate_by = 10
    raise_exception = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(pk = self.kwargs['establishment_id'])
        data['tables'] = Table.objects.filter(establishment__id=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        return Order.objects.filter(bill__establishment__id=self.kwargs['establishment_id']).order_by('-created_at')

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_employee = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, est_employee.exists()):
            return True


class ListOrdersPendingKitchen(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_order"
    template_name = './components/kitchen/order_list_kitchen.html'
    context_object_name = 'orders'
    raise_exception = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(pk=self.kwargs['establishment_id'])
        data['categories'] = ItemCategory.objects.filter(establishment__id=self.kwargs['establishment_id'])
        data['tables'] = Table.objects.filter(establishment__id=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(bill__establishment__id=self.kwargs['establishment_id'],
                                    status=Order.STATUS_PENDING).order_by('-created_at')

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_employee = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, est_employee.exists()):
            return True


class ListOrdersPreparingKitchen(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_order"
    template_name = './components/kitchen/order_list_kitchen.html'
    context_object_name = 'orders'
    raise_exception = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(pk = self.kwargs['establishment_id'])
        data['tables'] = Table.objects.filter(establishment__id=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(bill__establishment__id=self.kwargs['establishment_id'],
                                    status=Order.STATUS_PREPARING).order_by('-created_at')

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_employee = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, est_employee.exists()):
            return True


class ListOrdersDoneKitchen(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_order"
    template_name = './components/kitchen/order_list_kitchen_done.html'
    context_object_name = 'orders'
    raise_exception = True
    paginate_by = 10

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(pk = self.kwargs['establishment_id'])
        data['tables'] = Table.objects.filter(establishment__id=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(bill__establishment__id=self.kwargs['establishment_id'],
            status=Order.STATUS_DONE).order_by('-created_at')

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_employee = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, est_employee.exists()):
            return True


class KitchenFilterOrdersByCategory(ListOrdersPendingKitchen):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(pk=self.kwargs['establishment_id'])
        data['categories'] = ItemCategory.objects.filter(establishment__id=self.kwargs['establishment_id'])
        data['tables'] = Table.objects.filter(establishment__id=self.kwargs['establishment_id'])
        data['categories_filter'] = ItemCategory.objects.filter(id__in=self.request.GET.getlist('category'))
        return data

    def get_queryset(self):
        result = super(KitchenFilterOrdersByCategory, self).get_queryset()

        categories = self.request.GET.getlist('category')

        if categories:
            return result.filter(item__category_id__in=map(int, categories))


class ListSearchDoneOrdersByUsers(ListOrdersDoneKitchen):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(pk = self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        result = super(ListSearchDoneOrdersByUsers, self).get_queryset()

        query = self.request.GET.get('q')
        if query:
            return result.filter(Q(user__first_name__icontains=query) |
                                 (Q(user__last_name__icontains=query) |
                                  (Q(user__username__icontains=query) |
                                   (Q(id__iexact=str(query))))))


class ListFilterOrdersByTableDone(ListOrdersDoneKitchen):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(pk = self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        result = super(ListFilterOrdersByTableDone, self).get_queryset()

        query = self.request.GET.get('table')
        if query:
            return result.filter(Q(bill__table__id=query))


class ListSearchOrders(ListOrders):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment_id'] = self.kwargs['establishment_id']
        return data

    def get_queryset(self):
        result = super(ListSearchOrders, self).get_queryset()

        query = self.request.GET.get('q')
        if query:
            return result.filter(Q(user__first_name__icontains=query) |
                                 (Q(user__last_name__icontains=query) |
                                  (Q(id__iexact=str(query)))))


class ListFilterOrdersByTable(ListOrders):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment_id'] = self.kwargs['establishment_id']
        return data

    def get_queryset(self):
        result = super(ListFilterOrdersByTable, self).get_queryset()

        table = self.request.GET.get('table')
        first_name = self.request.GET.get('first_name')

        if table:
            result = result.filter(Q(bill__table__id=table))

        if first_name:
            result = result.filter(
                (Q(bill__customers__first_name__icontains=first_name))
            )

        return result


class CreateOrder(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'order_form.html'
    permission_required = "register.can_create_order"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        context['menu_items'] = MenuItem.objects.filter(menu__establishment=establishment)
        context['bills'] = Bill.objects.filter(payment_date__isnull=True, establishment=establishment)
        context['form'] = OrderForm(establishment)
        return context

    def post(self, request, *args, **kwargs):
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        form = OrderForm(establishment, request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.save()
            form.save()
            return redirect('register:list_items_to_order', **{'establishment_id': obj.bill.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class LoadBillMembers(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_create_order"

    def get(self, request, *args, **kwargs):
        table_id = request.GET.get('table_id')
        users = User.objects.filter(id__in=BillMember.objects.filter(
            bill__id=table_id,
            joined_at__isnull=False,
            leave_at__isnull=True).values('customer'))
        return render(request, 'bill_dropdown_list_order.html', {'users': users})


class ListItemsToOrder(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = "register.can_view_item_on_menu"
    template_name = 'menu_item_list_to_order.html'
    context_object_name = 'items'
    raise_exception = True

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment_id'] = self.kwargs['establishment_id']
        data['categories'] = ItemCategory.objects.filter(
            establishment__id=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        result = MenuItem.objects.filter(menu__establishment__id=self.kwargs['establishment_id'])
        categories = ItemCategory.objects.filter(
            establishment__id=self.kwargs['establishment_id'])

        category = self.request.GET.get('category')
        item_name = self.request.GET.get('item-name')

        if category:
            category = (categories[int(category)-1])
            result = result.filter(Q(category__id=category.id))
        if item_name:
            result = result.filter(Q(name__icontains=item_name))

        return result

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_employee = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, est_employee.exists()):
            return True


class UpdateOrder(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Order
    template_name = 'generic_form.html'
    permission_required = "register.can_change_order"
    fields = ['item', 'quantity', 'observation']
    raise_exception = True

    def get_success_url(self, **kwargs):
        return reverse_lazy('register:table_list', args=(self.object.establishment.id, self.object.table_zone.id))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        order = Order.objects.filter(id=self.kwargs['pk'],
                                     bill__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, order.exists()):
            return True


class KitchenAcceptOrder(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_change_order_status"

    def get(self, request, *args, **kwargs):
        order = Order.objects.get(id=self.kwargs['order_id'])
        order.status = Order.STATUS_PREPARING
        order.kitchen_accepted_at = timezone.now()
        order.save()
        body_msg = "O restaurante " f'{order.bill.establishment.name}' " aceitou o seu pedido"
        order.send_fcm_push_notifications('Pedido Aceito', 'order_accepted', body_msg)
        return redirect('register:orders_list_kitchen_preparing', **{'establishment_id': order.bill.establishment.id})

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        order = Order.objects.filter(id=self.kwargs['order_id'],
                                     bill__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, order.exists()):
            return True


class KitchenDoneOrder(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_change_order_status"

    def get(self, request, *args, **kwargs):
        order = Order.objects.get(id=self.kwargs['order_id'])
        order.status = Order.STATUS_DONE
        order.kitchen_finished_at = timezone.now()
        body_msg = "O restaurante " f'{order.bill.establishment.name}' " finalizou o seu pedido"
        order.send_fcm_push_notifications('Pedido Pronto', 'order_ready', body_msg)
        order.save()
        return redirect('register:orders_list_kitchen_done', **{'establishment_id': order.bill.establishment.id})

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        order = Order.objects.filter(id=self.kwargs['order_id'],
                                     bill__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, order.exists()):
            return True


class KitchenCancelOrder(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_change_order_status"

    def get(self, request, *args, **kwargs):
        order = Order.objects.get(id=self.kwargs['order_id'])
        order.cancel_order()
        return redirect('register:orders_list_kitchen_pending', **{'establishment_id': order.bill.establishment.id})

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        order = Order.objects.filter(id=self.kwargs['order_id'],
                                     bill__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, order.exists()):
            return True


class CancelOrderOnListOrders(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_change_order_status"

    def get(self, request, *args, **kwargs):
        order = Order.objects.get(id=self.kwargs['order_id'])
        order.cancel_order()
        return redirect('register:orders_list', **{'establishment_id': order.bill.establishment.id})

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        order = Order.objects.filter(id=self.kwargs['order_id'],
                                     bill__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, order.exists()):
            return True


class CancelOrderOnListBill(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_change_order_status"

    def get(self, request, *args, **kwargs):
        order = Order.objects.get(id=self.kwargs['order_id'])
        order.cancel_order()
        return redirect('register:orders_from_bill', **{'bill_id': order.bill.id})

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        order = Order.objects.filter(id=self.kwargs['order_id'],
                                     bill__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, order.exists()):
            return True


class ListBillsOpened(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    template_name = 'bill_list.html'
    context_object_name = 'all_items'
    permission_required = 'register.can_view_bill'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(pk=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        return Bill.objects.filter(
            establishment__id=self.kwargs['establishment_id'],
            payment_date__isnull=True).order_by('-payment_date')

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_employee = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, est_employee.exists()):
            return True


class ListBillsClosed(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    template_name = 'bill_list_closed.html'
    context_object_name = 'bills_payment'
    permission_required = 'register.can_view_bill'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment'] = Establishment.objects.get(pk=self.kwargs['establishment_id'])
        return data

    def get_queryset(self):
        return BillPayment.objects.filter(
            establishment__id=self.kwargs['establishment_id'],
            status_payment__in=[
                BillPayment.STATUS_OFFLINE_APPROVED,
                BillPayment.STATUS_AUTHORIZED]).order_by('-bill')

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_employee = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, est_employee.exists()):
            return True


class ListBillMembersOnBill(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    template_name = 'bill_members_list.html'
    context_object_name = 'all_items'
    permission_required = 'register.can_view_bill'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        bill = Bill.objects.get(id=self.kwargs['bill_id'])
        context = super().get_context_data(**kwargs)
        context['establishment'] = bill.establishment
        context['bill'] = bill
        context['orders_total_couvert_service'] = bill.all_value_bill()
        context['still_have_to_pay'] = bill.still_have_to_pay()

        return context

    def get_queryset(self):
        return BillMember.objects.filter(bill__id=self.kwargs['bill_id'])


class ListOrdersFromBill(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    template_name = 'orders_from_bill.html'
    context_object_name = 'orders'
    permission_required = 'register.can_view_bill'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        bill = Bill.objects.get(id=self.kwargs['bill_id'])
        context = super().get_context_data(**kwargs)
        context['bill'] = bill
        context['establishment'] = bill.establishment
        context['still_have_to_pay'] = bill.still_have_to_pay()
        return context

    def get_queryset(self):
        return Order.objects.filter(bill__id=self.kwargs['bill_id'])


class ListSearchBills(ListBillsOpened):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment_id'] = self.kwargs['establishment_id']
        return data

    def get_queryset(self):
        result = super(ListSearchBills, self).get_queryset()

        query = self.request.GET.get('q')
        if query:
            return result.filter(Q(customers__first_name__icontains=query) |
                                 (Q(customers__last_name__icontains=query)))


class ListSearchBillsClosed(ListBillsClosed):

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['establishment_id'] = self.kwargs['establishment_id']
        return data

    def get_queryset(self):
        result = super(ListSearchBillsClosed, self).get_queryset()

        query = self.request.GET.get('month-filter')
        current_year = datetime.date.today()
        current_year = current_year.year
        if query:
            return result.filter(
                Q(date__month=query,
                  date__year=current_year))


class CreateTable(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'table_form.html'
    permission_required = "register.can_create_table"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        table_zone = TableZone.objects.get(id=self.kwargs['table_zone_id'])
        context['table_zone'] = table_zone
        context['establishment'] = table_zone.establishment
        context['form'] = TableForm(table_zone)
        return context

    def post(self, request, *args, **kwargs):
        table_zone = TableZone.objects.get(id=self.kwargs['table_zone_id'])
        form = TableForm(table_zone, request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.establishment = table_zone.establishment
            form.save()
            return redirect('register:table_zone_list', **{'establishment_id': obj.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class UpdateTableEnableOrDesable(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_update_table"

    def get(self, request, *args, **kwargs):
        table = Table.objects.get(id=self.kwargs['pk'])
        table.enabled = not table.enabled
        table.save()
        return JsonResponse({'enabled': table.enabled,
                             'message': 'Status Altered'}, status=200)


class UpdateTable(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = Table
    template_name = 'generic_form.html'
    permission_required = "register.can_update_table"
    fields = ['name']

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:table_zone_list', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:table_zone_list', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        table = Table.objects.filter(id=self.kwargs['pk'],
                                     establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, table.exists()):
            return True


class DeleteTable(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_table"
    model = Table
    template_name = 'delete.html'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:table_zone_list', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:table_zone_list', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        table = Table.objects.filter(id=self.kwargs['pk'],
                                     establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, table.exists()):
            return True


class CreateTableZone(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_create_table_zone"
    template_name = 'table_zone_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        context['establishment'] = establishment
        context['form'] = TableZoneForm()
        context['action'] = "Adicionar Table Zone"
        return context

    def post(self, request, *args, **kwargs):
        form = TableZoneForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
            obj.establishment = establishment
            form.save()
            return redirect('register:table_zone_list', **{'establishment_id': obj.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class ListTableZone(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    template_name = 'table_zone_list.html'
    context_object_name = 'all_items'
    permission_required = "register.can_view_table_zone"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = Establishment.objects.get(id=self.kwargs['establishment_id'])
        return context

    def get_queryset(self):
        return TableZone.objects.filter(establishment__id=self.kwargs['establishment_id'])

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class UpdateTableZone(LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView):
    model = TableZone
    template_name = './components/forms/establishment_update_tablezone.html'
    permission_required = "register.can_change_table_zone"
    fields = ['name', 'enabled']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instance = TableZone.objects.get(id=self.kwargs['pk'])
        context['establishment'] = instance.establishment
        context['table_zone'] = instance
        context['form'] = TableZoneForm(instance=instance)
        context['action'] = "Atualizar Table Zone"
        return context

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:table_zone_list', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:table_zone_list', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        table_zone = TableZone.objects.filter(id=self.kwargs['pk'],
                                              establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, table_zone.exists()):
            return True


class DesactiveTableZone(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "register.can_desactive_table_zone"

    def get(self, request, *args, **kwargs):
        table_zone = TableZone.objects.get(id=self.kwargs['pk'])
        table_zone.enabled = not table_zone.enabled
        table_zone.save()
        return JsonResponse({'enabled': table_zone.enabled,
                             'message': 'Status Altered'}, status=200)

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        table_zone = TableZone.objects.filter(id=self.kwargs['pk'],
                                              establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, table_zone.exists()):
            return True


class DeleteTableZone(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_table_zone"
    model = TableZone
    template_name = 'delete.html'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:table_zone_list', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:table_zone_list', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        table_zone = TableZone.objects.filter(id=self.kwargs['pk'],
                                              establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, table_zone.exists()):
            return True


class RequestWaiter(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    template_name = 'request_list.html'
    permission_required = "register.can_view_status_request"
    context_object_name = 'requests'
    raise_exception = True
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = Establishment.objects.get(id=self.kwargs['establishment_id'])
        return context

    def get_queryset(self):
        return Request.objects.filter(
            table__establishment__id=self.kwargs['establishment_id'],
            status=Request.STATUS_PENDING).order_by('-created_at')

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_employee = Employee.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                               establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, est_employee.exists()):
            return True


# Waiter update 'status' from request, after Answer Customer
class AcceptRequestWaiter(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_change_status_request"

    def get(self, request, *args, **kwargs):
        request_waiter = Request.objects.get(id=self.kwargs['pk'])
        request_waiter.status = request_waiter.STATUS_REQUESTED
        request_waiter.save()
        return redirect('register:request_list', **{'establishment_id': request_waiter.table.establishment.id})

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        request_answer = Request.objects.filter(id=self.kwargs['pk'],
                                                table__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, request_answer.exists()):
            return True


class AcceptAllRequestWaiter(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_change_status_request"

    def get(self, request, *args, **kwargs):
        employee = self.request.user.employee
        Request.objects.filter(
            table__establishment=employee.establishment,
            status=Request.STATUS_PENDING).update(status=Request.STATUS_REQUESTED)
        return redirect('register:request_list', **{'establishment_id': employee.establishment.id})

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        request_answer = Request.objects.filter(
            table__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, request_answer.exists()):
            return True


class ListEvaluation(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    template_name = 'evaluation_list.html'
    permission_required = "register.can_view_evaluation"
    context_object_name = 'all_evaluations_from_establishment'
    paginate_by = 10

    def get_queryset(self):
        return UserRating.objects.filter(bill__establishment__id=self.kwargs['establishment_id'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['establishment'] = Establishment.objects.get(pk=self.kwargs['establishment_id'])
        return context

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        est_manager = EstablishmentManager.objects.filter(establishment__id=self.kwargs['establishment_id'],
                                                          establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, est_manager.exists()):
            return True


class CreateAnswerToEvaluation(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'answer_form.html'
    permission_required = 'register.can_answer_evaluation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = AnswerToEvaluationForm()
        return context

    def post(self, request, *args, **kwargs):
        form = AnswerToEvaluationForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            evaluation = UserRating.objects.get(id=self.kwargs['evaluation_id'])
            obj.evaluation = evaluation
            obj.establishment = evaluation.bill.establishment
            form.save()
            return redirect('register:evaluation_list', **{'establishment_id': obj.establishment.id})
        else:
            context = self.get_context_data()
            context['form'] = form
            return render(request, self.template_name, context)


class DeleteAnswerEvaluation(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_answer_evaluation"
    model = AnswerEvaluation
    template_name = 'delete.html'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:evaluation_list', kwargs={'establishment_id': self.object.establishment.id})
        return reverse_lazy('register:evaluation_list', args=(self.object.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        evaluation = AnswerEvaluation.objects.filter(id=self.kwargs['pk'],
                                                     establishment=user.manager.establishment)
        if checker_permissions(user, self.permission_required, evaluation.exists()):
            return True


class DeleteEvaluation(LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView):
    permission_required = "register.can_delete_evaluation"
    model = UserRating
    template_name = 'delete.html'

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:evaluation_list', kwargs={'establishment_id': self.object.bill.establishment.id})
        return reverse_lazy('register:evaluation_list', args=(self.object.bill.establishment.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True
        raise PermissionDenied


class CreatePaymentOnBillMember(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'payment_create_bill_member_form.html'
    permission_required = "register.can_create_payment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bill_member'] = BillMember.objects.get(id=self.kwargs['bill_member_id'])
        return context

    def post(self, request, *args, **kwargs):
        value = self.request.POST.get('value')
        bill_member = BillMember.objects.get(id=self.kwargs['bill_member_id'])
        bill = bill_member.bill

        if not re.fullmatch(r'\d+([.,]\d{2})?', value):
            raise forms.ValidationError('Preço inválido')
        value = float(value.replace(',', '.'))

        if value < float(bill_member.value_consumed_without_tax_percentage()) or value > bill.all_value_bill():
            return HttpResponse(406)

        payment_uuid = str('Noruh_' + str(uuid.uuid4()))
        bill_payment = BillPayment.objects.create(
            payment_uuid=payment_uuid,
            establishment=bill.establishment,
            status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
            date=timezone.now(), bill=bill,
            bill_member=bill_member, value=value,
            status_updated=timezone.now())

        value_paid_and_value = value + float(bill.value_paid)
        if value_paid_and_value > bill.all_value_bill_without_taxe_service() and value_paid_and_value <= bill.all_value_bill():
            BillMember.objects.filter(bill=bill).update(leave_at=timezone.now())
            bill.payment_date = timezone.now()
            noruh_firestore = NoruhFireStore()
            data_notification = {'ḱey': 'bill_closed', 'billId': bill.id}
            noruh_firestore.add_data_on_collection(data_notification)

        bill.value_paid = value_paid_and_value
        bill.save()
        bill_member.leave_at = timezone.now()
        bill_member.save()

        noruh_firestore = NoruhFireStore()
        data_notification = bill_payment.notification_payload(key='payment_accepted')
        noruh_firestore.add_data_on_collection(data_notification)
        return HttpResponse(200)


class ApproveOrRejectPayment(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_accept_payment"
    template_name = 'payment_confirm_bill_member_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bill_payment = BillPayment.objects.get(id=self.kwargs['bill_payment_id'])
        context['bill_payment'] = bill_payment
        context['bill_member'] = bill_payment.bill_member
        return context

    def post(self, request, *args, **kwargs):
        bill_payment = BillPayment.objects.get(id=self.kwargs['bill_payment_id'])
        bill_payment.approve_offline_payment()
        return redirect('register:bill_member_on_bill_list', **{'bill_id': bill_payment.bill.id})

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:bill_member_on_bill_list', kwargs={'bill_id': self.object.bill.id})
        return reverse_lazy('register:bill_member_on_bill_list', args=(self.object.bill.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        bill_payment = BillPayment.objects.filter(
            id=self.kwargs['bill_payment_id'],
            bill__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, bill_payment.exists()):
            return True


class RejectPayment(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "register.can_accept_payment"
    template_name = 'payment_confirm_bill_member_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bill_payment = BillPayment.objects.get(id=self.kwargs['bill_payment_id'])
        context['bill_payment'] = bill_payment
        context['bill_member'] = BillMember.objects.get(
            bill=bill_payment.bill,
            customer=bill_payment.user)
        return context

    def post(self, request, *args, **kwargs):
        bill_payment = BillPayment.objects.get(id=self.kwargs['bill_payment_id'])
        bill_payment.reject_offline_payment()
        return redirect('register:bill_member_on_bill_list', **{'bill_id': bill_payment.bill.id})

    def get_success_url(self, **kwargs):
        if kwargs:
            return reverse_lazy('register:bill_member_on_bill_list', kwargs={'bill_id': self.object.bill.id})
        return reverse_lazy('register:bill_member_on_bill_list', args=(self.object.bill.id,))

    def has_permission(self):
        user = self.request.user
        if user.is_superuser:
            return True

        bill_payment = BillPayment.objects.filter(
            id=self.kwargs['bill_payment_id'],
            bill__establishment=user.employee.establishment)
        if checker_permissions(user, self.permission_required, bill_payment.exists()):
            return True


class CreatePaymentAllBill(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'payment_create_all_bill_form.html'
    permission_required = "register.can_create_payment"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bill = Bill.objects.get(id=self.kwargs['bill_id'])
        context['bill'] = bill
        context['form'] = PaymentOfflineForm(bill.id)
        return context

    def post(self, request, *args, **kwargs):
        bill = Bill.objects.get(id=self.kwargs['bill_id'])
        form = PaymentOfflineForm(bill.id, request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.payment_uuid = str('Noruh_' + str(uuid.uuid4()))
            obj.establishment = bill.establishment
            obj.bill = bill
            obj.status_payment = BillPayment.STATUS_OFFLINE_APPROVED
            obj.status_updated = timezone.now()

            bill.payment_date = timezone.now()
            bill.value_paid = bill.value_paid + form.clean_value()
            BillMember.objects.filter(bill=bill).update(leave_at=timezone.now())

            noruh_firestore = NoruhFireStore()
            data_notification = {
                'action': 'bill_closed',
                'billId': bill.id,
                'createdAt': timezone.now().isoformat()
            }
            noruh_firestore.add_data_on_collection(data_notification)

            devices = FCMDevice.objects.filter(
                user__in=BillMember.objects.filter(
                    bill=self.bill, leave_at__isnull=True).values('customer'))

            bill.save()
            form.save()
            return redirect('register:bill_member_on_bill_list', **{'bill_id': bill.id})
        else:
            context = self.get_context_data()
            context['must_pay_min_value'] = 'Você deve pagar o valor minimo de {}'.format(
                bill.all_value_bill_without_taxe_service())
            context['form'] = form
            return render(request, self.template_name, context)


class ListCompensations(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'list_compensations.html'

    def get(self, request, *args, **kwargs):
        establishments = Establishment.objects.all()
        establishment_id = self.request.GET.get('establishment-filter')

        if not establishment_id:
            establishment = establishments.first()
        else:
            establishment = Establishment.objects.get(id=establishment_id)
        return render(request, self.template_name, {
            'all_establishments': establishments,
            'establishment': establishment,
            'payments': establishment.report_offline_payment()
        })

    def has_permission(self):
        user = self.request.user
        if not user.is_superuser:
            raise PermissionDenied
        return True


class CreateCompensation(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'list_compensations.html'

    def get(self, request, *args, **kwargs):
        establishments = Establishment.objects.all()
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        reports = establishment.report_offline_payment()

        for report in reports:
            if report.get('m') == self.kwargs['month'] and report.get('y') == self.kwargs['year']:
                OfflineCompensations.objects.create(
                    establishment=establishment,
                    value=report.get('compensation_value'),
                    month=self.kwargs['month'],
                    year=self.kwargs['year'])

        return redirect('register:offline_compensations')

    def has_permission(self):
        user = self.request.user
        if not user.is_superuser:
            raise PermissionDenied
        return True


class GenerateCSVReport(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'list_compensations.html'

    def get(self, request, *args, **kwargs):
        month_year = '{}/{}'.format(self.kwargs['month'], self.kwargs['year'])
        establishment = Establishment.objects.get(id=self.kwargs['establishment_id'])
        payments = BillPayment.objects.filter(
            establishment=establishment,
            status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
            status_updated__month=self.kwargs['month'],
            status_updated__year=self.kwargs['year'])

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}-{}-compensation_details.csv"'.format(establishment.name, month_year)
        writer = csv.writer(response)

        writer.writerow([establishment.name, month_year])
        writer.writerow([''])
        writer.writerow(['Conta', 'Mesa', 'Membros', 'Data Pagamento', 'Valor', 'Repasse'])
        for payment in payments:
            bill_id = '#{}'.format(payment.id)
            date_time = '{}:{}'.format(payment.status_updated.hour, payment.status_updated.minute)
            date_payment = '{} {}'.format(payment.status_updated.date(), date_time)
            value_compensation = payment.value * establishment.offline_percentage
            writer.writerow([
                bill_id, payment.bill.table.name,
                payment.bill.customers.count(), date_payment,
                payment.value, "%.2f" % value_compensation])

        reports = establishment.report_offline_payment()
        for report in reports:
            if report.get('m') == self.kwargs['month'] and report.get('y') == self.kwargs['year']:
                compensation_value = "%.2f" % report.get('compensation_value')
                writer.writerow(['TOTAL', '', '', '', report.get('total'), compensation_value])

        return response

    def has_permission(self):
        user = self.request.user
        if not user.is_superuser:
            raise PermissionDenied
        return True
