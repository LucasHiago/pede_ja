from django.urls import path

from .views import *

# Endpoints for Payments
urlpatterns = [
    path('create/app/', CreateAppAPIPost.as_view(), name='api_create_app'),
    path('create/wirecard_noruh/', CreateWirecardNoruhAPIPost.as_view(), name='api_create_wirecard_noruh'),

    path('list/customer/', ListCustomerAPIGet.as_view(), name='api_create_customer_post'),

    path('create/credit_card/', CreateCreditCardPost.as_view(), name='api_create_credit_card'),
    path('list/credit_card/', ListCreditCards.as_view(), name='api_list_credit_card'),
    path('delete/credit_card/<int:pk>', DeleteCreditCard.as_view(), name='api_delete_credit_card'),

    path('create/online/', CreatePaymentPostOnline.as_view(), name='api_create_payment_online'),
    path('create/offline/', CreatePaymentPostOffline.as_view(), name='api_create_payment_offline'),
    path('status/bill/<int:bill_id>', StatusBillPaymentApiView.as_view(), name='api_status_payment'),
    path('status/user/<int:user_id>', StatusUserPaymentApiView.as_view(), name='api_status_payment'),

]
