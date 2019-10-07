from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination

class EstablishmentSetPagination(PageNumberPagination):
    page_size = 4
