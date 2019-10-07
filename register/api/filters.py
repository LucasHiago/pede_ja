from django_filters import rest_framework as filters
from register.models import (
    Establishment,
    BillMember
)


class EstablishmentFilter(filters.FilterSet):

    opened = filters.BooleanFilter('opened')
    featured = filters.BooleanFilter('featured')
    promotions = filters.BooleanFilter('promotions__enabled')
    establishment_name = filters.CharFilter('name', lookup_expr='icontains')
    cuisine_name = filters.CharFilter('cuisine_type__name', lookup_expr='exact')

    class Meta:
        model = Establishment
        fields = ['opened', 'featured', 'promotions',
                  'establishment_name', 'cuisine_name']


class BillMemberFilter(filters.FilterSet):

    bill_id = filters.NumberFilter('bill__id')
    only_pending = filters.BooleanFilter('joined_at', lookup_expr='isnull')

    class Meta:
        model = BillMember
        fields = ['bill_id', 'only_pending']
