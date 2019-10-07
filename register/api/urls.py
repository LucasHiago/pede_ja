from django.urls import path, include
from .views import (
    EstablishmentListAPIView,
    EstablishmentDetailAPIView,
    VerifyIfPromocodeIsEnabledView,
)
from .views import CuisineTypeListAPIView, MenuListAPIView
from .views import (
    BillAPIPost,
    BillHistoryAPIList,
    BillMemberAPIView,
    BillMemberAPICreate,
    BillMemberAPIConfirm,
    BillMemberAPIJoinCancel,
    BillMemberAPIConfirmAll,
    BillMemberAPIExitWithouPayment,
    OrderAPIUpdate,
    OrderAPIPost,
    OrderAPIDiscountPost,
    RequestAPIView,
    EvaluationAPIPost,
    EvaluationAPIView,
    EvaluationStatus,
)
from .views import (
    RegistrationUser,
    ForgotMyPasswordView,
    ResetPasswordUser,
    ProfileAPIUpdate,
    UserLoggedAPIList,
    UserAPIDetail,
    LogoutView,
)
from .views import (
    FacebookLogin,
    GoogleLogin,
)
from rest_auth.registration.views import (
    SocialAccountListView,
    SocialAccountDisconnectView
)


urlpatterns = [

    # Endpoints for Login, User and Registration
    path('user/registration/', RegistrationUser.as_view(), name='registration'),
    path('user/logout/', LogoutView.as_view(), name='logout'),
    path('user/forgot_password/', ForgotMyPasswordView.as_view(), name='forgot_password'),
    path('user/reset_password/', ResetPasswordUser.as_view(), name='reset_password'),

    path('rest-auth/facebook/', FacebookLogin.as_view(), name='fb_connect'),
    path('rest-auth/google/', GoogleLogin.as_view(), name='gl_connect'),
    path('rest-auth/socialaccounts/', SocialAccountListView.as_view(),
         name='social_account_list'),
    path('rest-auth/socialaccounts/<int:pk>/disconnect/',
         SocialAccountDisconnectView.as_view(),
         name='social_account_disconnect'),
    path('user/', UserLoggedAPIList.as_view(), name='api_user_list'),
    path('user/profile/update/', ProfileAPIUpdate.as_view(),
         name='api_profile_update'),

    # Endpoints for Cuisine Types, Establishment, Menu, Bill, Evaluations and Requests
    path('cuisine/list/', CuisineTypeListAPIView.as_view(),
         name='api_cuisine_type_list'),

    # List establishments for location and other search(promocode, opened, cuisine_type, featured, and name)
    path('establishment/list/', EstablishmentListAPIView.as_view(),
         name='api_establishment_list'),
    path('establishment/detail/<int:pk>/', EstablishmentDetailAPIView.as_view(),
         name='api_establishment_list_detail'),

    # List all items from menu use the `establishment_id` to path
    path('menu/list/<int:establishment_id>', MenuListAPIView.as_view(),
         name='api_menu_list'),

    # All endpoints for Bill and BillMemebers
    path('bill/history/', BillHistoryAPIList.as_view(),
         name='api_bill_history_list'),
    path('bill/active/', UserAPIDetail.as_view(),
         name='api_user_detail'),
    path('bill/create/', BillAPIPost.as_view(), name='api_bill_create'),
    path('bill/join/', BillMemberAPICreate.as_view(),
         name='api_bill_member_join'),
    path('bill/join/confirm/', BillMemberAPIConfirm.as_view(),
         name='api_bill_member_confirm'),
    path('bill/join/confirm/all/', BillMemberAPIConfirmAll.as_view(),
         name='api_bill_member_confirm_all'),
    path('bill/join/cancel/', BillMemberAPIJoinCancel.as_view(),
         name='api_bill_member_join_cancel'),
    path('bill/exit_without_payment/', BillMemberAPIExitWithouPayment.as_view(),
         name='api_bill_member_exit_bill'),
    path('bill/rating_status/', EvaluationStatus.as_view(),
         name='api_rating_status'),
    path('billmember/list/', BillMemberAPIView.as_view(),
         name='api_bill_member_list'),

    # Endpoints for create orders and update status from specific order
    path('order/post/', OrderAPIPost.as_view(), name='api_order_post'),
    path('order/offer/post/', OrderAPIDiscountPost.as_view(),
         name='api_order_post_offer'),
    path('order/update/<int:pk>/', OrderAPIUpdate.as_view(),
         name='api_order_update'),

    # Ednpoint for create a request attendance to Waiter
    path('request/post/', RequestAPIView.as_view(), name='api_request_post'),

    # Endpoints for create evaluation and list evaluations from establishment
    path('evaluation/post/', EvaluationAPIPost.as_view(),
         name='api_evaluation_post'),
    path('evaluation/list/<int:id_establishment>', EvaluationAPIView.as_view(),
         name='api_evaluation_list'),

    # Endpoint to verify if promocde is Enable or Disable
    path('promocode/status/', VerifyIfPromocodeIsEnabledView.as_view(),
         name='api_establishment_promocode_enabled'),

]
