import datetime
from django.db.models import Sum, Avg
from .models import Bill, Establishment, Order, UserRating, BillPayment


def all_establishments_revenues(current_month, type_filter):
    current_month = current_month.replace(day=1)
    values = []

    if type_filter == 'all_bills':
        for iteration in range(6, 0, -1):
            value_query = Bill.objects.filter(
                opening_date__year=current_month.year,
                opening_date__month=current_month.month).count()
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            month_dict['value'] = value_query
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'all_orders':
        for iteration in range(6, 0, -1):
            value_query = Order.objects.filter(
                created_at__year=current_month.year,
                created_at__month=current_month.month,
                canceled_at__isnull=True).count()

            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            month_dict['value'] = value_query
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'payment_online':
        for iteration in range(6, 0, -1):
            value_query = BillPayment.objects.filter(
                date__year=current_month.year,
                date__month=current_month.month,
                status_payment=BillPayment.STATUS_AUTHORIZED).aggregate(
                    Sum('value'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('value__sum'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('value__sum')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'payment_offline':
        for iteration in range(6, 0, -1):
            value_query = BillPayment.objects.filter(
                date__year=current_month.year,
                date__month=current_month.month,
                status_payment=BillPayment.STATUS_OFFLINE_APPROVED).aggregate(
                    Sum('value'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('value__sum'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('value__sum')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'evaluation_average':
        for iteration in range(6, 0, -1):
            value_query = UserRating.objects.filter(
                bill__payment_date__year=current_month.year,
                bill__payment_date__month=current_month.month).aggregate(
                    Avg('average'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('average__avg'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('average__avg')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'moip_taxe':
        for iteration in range(6, 0, -1):
            value_query = BillPayment.objects.filter(
                date__year=current_month.year,
                date__month=current_month.month).aggregate(
                    Sum('moip_fee'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('moip_fee__sum'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('moip_fee__sum')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    else:
        for iteration in range(6, 0, -1):
            value_query = BillPayment.objects.filter(
                date__month=current_month.month,
                date__year=current_month.year).aggregate(
                    Sum('value'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('value__sum'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('value__sum')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)
    return reversed(values)


def establishment_revenues(current_month, type_filter, establishment):
    current_month = current_month.replace(day=1)
    values = []

    if type_filter == 'all_bills':
        for iteration in range(6, 0, -1):
            value_query = Bill.objects.filter(
                establishment=establishment,
                opening_date__year=current_month.year,
                opening_date__month=current_month.month).count()
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            month_dict['value'] = value_query
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'all_orders':
        for iteration in range(6, 0, -1):
            value_query = Order.objects.filter(
                bill__establishment=establishment,
                created_at__year=current_month.year,
                created_at__month=current_month.month,
                canceled_at__isnull=True).count()

            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            month_dict['value'] = value_query
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'payment_online':
        for iteration in range(6, 0, -1):
            value_query = BillPayment.objects.filter(
                establishment=establishment,
                date__year=current_month.year,
                date__month=current_month.month,
                status_payment=BillPayment.STATUS_AUTHORIZED).aggregate(
                    Sum('value'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('value__sum'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('value__sum')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'payment_offline':
        for iteration in range(6, 0, -1):
            value_query = BillPayment.objects.filter(
                establishment=establishment,
                date__year=current_month.year,
                date__month=current_month.month,
                status_payment=BillPayment.STATUS_OFFLINE_APPROVED).aggregate(
                    Sum('value'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('value__sum'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('value__sum')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'evaluation_average':
        for iteration in range(6, 0, -1):
            value_query = UserRating.objects.filter(
                bill__establishment=establishment,
                bill__payment_date__year=current_month.year,
                bill__payment_date__month=current_month.month).aggregate(
                    Avg('average'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('average__avg'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('average__avg')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    elif type_filter == 'moip_taxe':
        for iteration in range(6, 0, -1):
            value_query = BillPayment.objects.filter(
                establishment=establishment,
                date__year=current_month.year,
                date__month=current_month.month).aggregate(
                    Sum('moip_fee'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('moip_fee__sum'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('moip_fee__sum')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    else:
        for iteration in range(6, 0, -1):
            value_query = BillPayment.objects.filter(
                date__month=current_month.month,
                date__year=current_month.year,
                establishment=establishment,
                status_payment__in=[
                    BillPayment.STATUS_OFFLINE_APPROVED,
                    BillPayment.STATUS_AUTHORIZED]).aggregate(
                        Sum('value'))
            month_dict = {}
            number_month = str(current_month.month)
            month_dict['month'] = number_month
            if not value_query.get('value__sum'):
                month_dict['value'] = 0
            else:
                month_dict['value'] = value_query.get('value__sum')
            values.append(month_dict)
            current_month = current_month - datetime.timedelta(weeks=4)

    return reversed(values)


def get_variable_name_filter(type_filter):
    if type_filter == 'all_bills':
        return 'Total de Contas'

    elif type_filter == 'all_orders':
        return 'Total de Pedidos'

    elif type_filter == 'payment_online':
        return 'Pagamento Online'

    elif type_filter == 'payment_offline':
        return 'Pagamento Offline'

    elif type_filter == 'evaluation_average':
        return 'Média das Avaliações'

    elif type_filter == 'moip_taxe':
        return 'Taxa Moip'

    else:
        return 'Faturamento Total'


def establishments_performance():
    establishments = Establishment.objects.all()
    list_establishments = []

    for establishment in establishments:
        payment_online = BillPayment.objects.filter(
            establishment=establishment,
            status_payment=BillPayment.STATUS_AUTHORIZED).aggregate(
                Sum('value')).get('value__sum')
        if not payment_online:
            payment_online = 0.0

        payment_offline = BillPayment.objects.filter(
            establishment=establishment,
            status_payment=BillPayment.STATUS_OFFLINE_APPROVED).aggregate(
                Sum('value')).get('value__sum')
        if not payment_offline:
            payment_offline = 0.0

        evaluation_average = UserRating.objects.filter(
            bill__establishment=establishment).aggregate(Avg('average')).get('average__avg')
        if not evaluation_average:
            evaluation_average = 0.0

        moip_taxe = BillPayment.objects.filter(establishment=establishment).aggregate(
            Sum('moip_fee')).get('moip_fee__sum')
        if not moip_taxe:
            moip_taxe = 0.0

        all_billing = Bill.objects.filter(establishment=establishment).aggregate(
            Sum('value_paid')).get('value_paid__sum')
        if not all_billing:
            all_billing = 0.0

        dict_establishment = {
            'name': establishment.name,
            'average_bills': establishment.average_bills(),
            'noruh_tax_to_super_admin': establishment.noruh_tax_to_super_admin(),
            'all_bills': Bill.objects.filter(establishment=establishment).count(),
            'all_orders':  Order.objects.filter(bill__establishment=establishment).count(),
            'payment_online': payment_online,
            'payment_offline': payment_offline,
            'evaluation_average': evaluation_average,
            'moip_taxe': moip_taxe,
            'all_billing': all_billing
        }
        list_establishments.append(dict_establishment)

    return list_establishments
