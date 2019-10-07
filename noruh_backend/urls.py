"""noruh_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.utils.translation import gettext as _
from django.contrib import admin
from django.urls import path, re_path, include

from rest_framework.documentation import include_docs_urls
from rest_auth.registration.views import VerifyEmailView

urlpatterns = [
    path('', include(('register.urls', 'register'), namespace='register')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),

    path('api/auth/', include('rest_framework_social_oauth2.urls')),

    path('api/', include(('register.api.urls', 'register-api'), namespace='register-api')),
    path('api/docs/', include_docs_urls(title='Noruh API Documentation')),
    path('api/payment/', include(('register.payment.urls', 'register-api-payment'), namespace='register-api-payment')),
    path('api/rest-auth/', include('rest_auth.urls')),
    path('api/rest-auth/accounts/', include('allauth.urls'), name='socialaccount_signup'),
    path('api/rest-auth/registration/', include('rest_auth.registration.urls')),
    re_path('account-confirm-email/', VerifyEmailView.as_view(), name='account_email_verification_sent'),
    re_path('account-confirm-email/<key>/', VerifyEmailView.as_view(), name='account_confirm_email'),

]

admin.site.site_header = _('Noruh')
admin.site.site_title = _('Noruh')
