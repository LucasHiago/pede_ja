from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import *

urlpatterns = [

     # Urls for authentication on noruh web

     path('change_password/', RecoverPasswordByApi.as_view(), name='change_password'),
     path('reset_passowrd/complete/', RecoverPasswordByApiComplete.as_view(), name='reset_password_complete'),

     path('login/', Login.as_view(), name='login'),
     path('user/logged/', ListUserLogged.as_view(), name='user_logged_detail'),
     path('user/logged/alter/<int:pk>/', AlterUser.as_view(), name='user_logged_alter'),

     path('', Home.as_view(), name='home'),
     path('terms_and_conditions/', TermsAndContions.as_view(), name='terms_and_conditions'),

     # Url's for Establishments and configurations
     path('establishment/create/', CreateEstablishment.as_view(),
          name='establishment_create'),
     path('establishment/list/all/', ListAllEstablishment.as_view(),
          name='establishment_list_all'),
     path('establishment/search/list/', ListSearchEstablishment.as_view(),
          name='establishment_search_list'),
     path('establishment/configurations/<int:id>/', ConfigurationsEstablishment.as_view(),
          name='establishment_configurations'),
     path('establishment/base/<int:id>/', BaseEstablishment.as_view(),
          name='establishment_base'),
     path('establishment/update/location/<int:pk>/', UpdateEstablismentLocation.as_view(),
          name='establishment_update_location'),
     path('establishment/update/description/<int:pk>/', UpdateEstablismentDescription.as_view(),
          name='establishment_update_description'),
     path('establishment/update/amenities/<int:pk>/', UpdateEstablismentAmenities.as_view(),
          name='establishment_update_amenities'),
     path('establishment/update/gps_restriction/<int:pk>/', UpdateGPSRestrictionEstablishment.as_view(),
          name='establishment_update_gps_restriction'),
     path('establishment/update/featured/<int:pk>/', UpdateFeaturedEstablishment.as_view(),
          name='establishment_update_featured'),
     path('establishment/update/enable/<int:pk>/', DisableEstablishment.as_view(),
         name='establishment_update_enable'),
     path('establishment/update/taxes/<int:pk>/', UpdateEstablismentTaxes.as_view(),
          name='establishment_update_taxes'),
     path('establishment/update/pays_payment_tax/<int:pk>/', UpdateEstablishmentPaysPaymentTax.as_view(),
          name='establishment_update_pays_payment_tax'),
     path('establishment/update/couvert/<int:pk>/', UpdateEstablismentCouvert.as_view(),
          name='establishment_update_couvert'),
     path('establishment/update/offer_range_value/<int:pk>/', UpdateEstablismentOfferRangeValue.as_view(),
          name='establishment_update_offer_range_value'),
     path('establishment/update/open_close/<int:pk>/', UpdateOpenOrCloseEstablishment.as_view(),
          name='establishment_update_open_close'),
     path('establishment/delete/<int:pk>/', DeleteEstablishment.as_view(),
          name='establishment_delete'),
     path('establishment/create/photo/<int:establishment_id>/', AddPhotoOnEstablishment.as_view(),
          name='establishment_add_photo'),
     path('establishment/photo/delete/<int:pk>/', DeletePhotoFromEstablishment.as_view(),
          name='establishment_delete_photo'),
     path('dashboard/', DashboardAllEstablishments.as_view(), name='dashboard_all_establishments'),
     path('establishment/dashboard/<int:establishment_id>/', DashboardEstablishment.as_view(),
          name='establishment_dashboard'),
     path('establishment/dashboard/items_more_requested/<int:establishment_id>/', ListAllItemsMoreRequested.as_view(),
          name='establishment_items_more_requested'),

     # Url's for when Request a Waiter
     path('establishment/requests/list/<int:establishment_id>/',
          RequestWaiter.as_view(), name='request_list'),
     path('establishment/requests/accept/<int:pk>/',
          AcceptRequestWaiter.as_view(), name='accept_request'),
     path('establishment/requests/accept/all/<int:establishment_id>/',
          AcceptAllRequestWaiter.as_view(), name='accept_all_requests'),

     # Url's for Establishment Evaluations
     path('establishment/evaluation/list/<int:establishment_id>/',
          ListEvaluation.as_view(), name='evaluation_list'),
     path('establishment/evaluation/answer/<int:evaluation_id>/',
          CreateAnswerToEvaluation.as_view(), name='answer_evaluation'),
     path('establishment/evaluation/delete/<int:pk>/',
          DeleteEvaluation.as_view(), name='evaluation_delete'),
     path('establishment/evaluation/answer/delete/<int:pk>/',
          DeleteAnswerEvaluation.as_view(), name='evaluation_answer_delete'),

     # Url's for Employees
     path('establishment/employee/create/', CreateEmployee.as_view(),
          name='employee_create'),
     path('establishment/employee/list/<int:establishment_id>/',
          ListEmployeeEstablishment.as_view(), name='employee_list_establishment'),
     path('establishment/employee/list/<int:establishment_id>/search/',
          ListSearchEmployeeEstablishment.as_view(), name='employee_list_search_establishment'),
     path('establishment/employee/list/', ListEmployeeAll.as_view(),
          name='employee_list_all'),
     path('establishment/employee/list/search/', ListSearchEmployee.as_view(),
          name='employee_search_list'),
     path('establishment/employee/detail/<int:pk>/',
          DetailEmployee.as_view(), name='employee_detail'),
     path('establishment/employee/alter/<int:pk>/',
          AlterEmployee.as_view(), name='employee_alter'),
     path('establishment/employee/delete/<int:pk>/',
          DeleteEmployee.as_view(), name='employee_delete'),

     # Url's for Menu, MenuItem, ItemCategory, Observation
     path('menu/list/<int:establishment_id>/', ListMenuFromEstablishment.as_view(),
          name='menu_list_from_establishment'),
     path('menu/list/<int:establishment_id>/search/', ListMenuSearchFromEstablishment.as_view(),
          name='menu_list_search_from_establishment'),

     # Items from Menu
     path('menu/add/item/<int:establishment_id>/',
          CreateItemOnMenu.as_view(), name='menu_create_item'),
     path('menu/list/item/<int:establishment_id>/',
          ListMenuItems.as_view(), name='menu_item_list'),
     path('menu/list/item/<int:establishment_id>/search/',
          ListMenuItemsSearch.as_view(), name='menu_item_list_search'),
     path('menu/list/item/update/<int:pk>/',
          UpdateItemOnMenu.as_view(), name='menu_item_update'),
     path('menu/list/item/delete/<int:pk>/',
          DeleteItemOnMenu.as_view(), name='menu_item_delete'),

     # Category from Menu
     path('menu/category/create/<int:establishment_id>/',
          CreateCategory.as_view(), name='menu_category_create'),
     path('menu/category/list/<int:establishment_id>/',
          ListCategory.as_view(), name='menu_category_list'),
     path('menu/category/update/<int:pk>/',
          UpdateCategory.as_view(), name='menu_category_update'),
     path('menu/category/delete<int:pk>/',
          DeleteCategory.as_view(), name='menu_category_delete'),

     # Observations from Menu
     path('menu/observation/create/<int:establishment_id>',
          CreateObservationItem.as_view(), name='menu_observation_item_create'),
     path('menu/observation/list/<int:establishment_id>/',
          ListObservationItem.as_view(), name='menu_observation_list'),
     path('menu/observation/update/<int:pk>/',
          UpdateObservationItem.as_view(), name='menu_observation_update'),
     path('menu/observation/delete/<int:pk>/',
          DeleteObservationItem.as_view(), name='menu_observation_delete'),

     # Menu Offers
     path('menu/offer/create/<int:establishment_id>',
          CreateMenuOffer.as_view(), name='menu_offer_create'),
     path('menu/offer/list/<int:establishment_id>/',
          ListMenuOffers.as_view(), name='menu_offer_list'),
     path('menu/offer/delete/<int:pk>/',
          DeleteMenuOffer.as_view(), name='menu_offer_delete'),
     path('menu/offer/update/<int:pk>/',
          UpdateMenuOffer.as_view(), name='menu_offer_update'),

     # Url's for Orders, Bills and Tables
     path('orders/list/<int:establishment_id>/',
          ListOrders.as_view(), name='orders_list'),
     path('orders/list/kitchen/pending/<int:establishment_id>/',
          ListOrdersPendingKitchen.as_view(), name='orders_list_kitchen_pending'),
     path('orders/list/kitchen/preparing/<int:establishment_id>/',
          ListOrdersPreparingKitchen.as_view(), name='orders_list_kitchen_preparing'),
     path('orders/list/kitchen/done/<int:establishment_id>/',
          ListOrdersDoneKitchen.as_view(), name='orders_list_kitchen_done'),

     # Cancel Orders Button
     path('order/cancel_from_list_orders/<int:order_id>/',
          CancelOrderOnListOrders.as_view(), name='order_cancel_button_on_list_orders'),
     path('order/cancel_from_bill/<int:order_id>/',
          CancelOrderOnListBill.as_view(), name='order_cancel_button_on_list_bills'),

     # Url's for Views for Kitchen List Orders
     path('orders/list/kitchen/done/<int:establishment_id>/search/user/',
          ListSearchDoneOrdersByUsers.as_view(), name='orders_kitchen_done_search_user'),
     path('orders/list/kitchen/done/<int:establishment_id>/search/table/',
          ListFilterOrdersByTableDone.as_view(), name='orders_kitchen_done_search_table'),
     path('orders/list/<int:establishment_id>/search/',
          ListSearchOrders.as_view(), name='orders_search_list'),
     path('orders/list/filter/category/<int:establishment_id>/search/',
          KitchenFilterOrdersByCategory.as_view(), name='orders_kitchen_category_filter'),
     path('orders/list/<int:establishment_id>/filter_by_table/',
          ListFilterOrdersByTable.as_view(), name='orders_filter_by_table'),
     path('orders/list/items/to/order/<int:establishment_id>/',
          ListItemsToOrder.as_view(), name='list_items_to_order'),
     path('orders/create/<int:establishment_id>/',
          CreateOrder.as_view(), name='order_create'),
     path('orders/update/<int:pk>/',
          UpdateOrder.as_view(), name='orders_update'),
     path('orders/kitchen_accepted_at/<int:order_id>/',
          KitchenAcceptOrder.as_view(), name='order_kitchen_accepted_at'),
     path('orders/kitchen_done_order/<int:order_id>/',
          KitchenDoneOrder.as_view(), name='order_kitchen_done'),
     path('orders/kitchen_cancel_order/<int:order_id>/',
          KitchenCancelOrder.as_view(), name='order_kitchen_cancel'),

     # Url's for Bills and BillPayment
     path('bill/list/<int:establishment_id>/',
          ListBillsOpened.as_view(), name='bill_list'),
     path('bill/list/closed/<int:establishment_id>/',
          ListBillsClosed.as_view(), name='bill_list_closed'),
     path('bill/list/<int:establishment_id>/search/',
          ListSearchBills.as_view(), name='bill_search_list'),
     path('bill/list/search/closed/<int:establishment_id>/search/',
          ListSearchBillsClosed.as_view(), name='bill_search_list_closed'),
     path('bill/payment/create/<int:bill_id>/',
          CreatePaymentAllBill.as_view(), name='bill_payment_create'),
     path('bill/payment/create/bill_member/<int:bill_member_id>/',
          CreatePaymentOnBillMember.as_view(), name='bill_member_payment_create'),
     path('bill/payment/aprove_or_reject/<int:bill_payment_id>/',
          ApproveOrRejectPayment.as_view(), name='bill_payment_aprove_or_reject'),
     path('bill/payment/reject/<int:bill_payment_id>/',
          RejectPayment.as_view(), name='bill_payment_reject'),
     path('bill/bill_members/list/<int:bill_id>/',
          ListBillMembersOnBill.as_view(), name='bill_member_on_bill_list'),
     path('ajax/load_bill_members/', 
          LoadBillMembers.as_view(), name='ajax_load_bill_members'),          
     path('bill/orders/list/<int:bill_id>/',
          ListOrdersFromBill.as_view(), name='orders_from_bill'),

     # Url's for Tables and TableZone
     path('table_zone/create/<int:establishment_id>/',
          CreateTableZone.as_view(), name='table_zone_create'),
     path('table_zone/list/<int:establishment_id>/',
          ListTableZone.as_view(), name='table_zone_list'),
     path('table_zone/update/<int:pk>/',
          UpdateTableZone.as_view(), name='table_zone_update'),
     path('table_zone/delete/<int:pk>/',
          DeleteTableZone.as_view(), name='table_zone_delete'),
     path('table_zone/update/active_or_desactive/<int:pk>/',
          DesactiveTableZone.as_view(), name='table_zone_active_or_desactive'),
     path('table/create/<int:table_zone_id>/<int:establishment_id>/',
          CreateTable.as_view(), name='table_create'),
     path('table/update/<int:pk>/', UpdateTable.as_view(), name='table_update'),
     path('table/update/enabled/<int:pk>/',
          UpdateTableEnableOrDesable.as_view(), name='table_update_enabled'),
     path('table/delete/<int:pk>/', DeleteTable.as_view(), name='table_delete'),

     # Url's for Operating Hours
     path('operating_hours/create/<int:establishment_id>/',
          CreateOperatingHours.as_view(), name='operating_hour_create'),
     path('operating_hours/delete/<int:pk>/',
          DeleteOperatingHour.as_view(), name='operating_hour_delete'),

     # Url's for Promocodes
     path('promocode/create/<int:establishment_id>/',
          CreatePromoCode.as_view(), name='promocode_create'),
     path('promocode/update/<int:pk>/',
          UpdatePromoCodes.as_view(), name='promocode_update'),
     path('promocode/delete/<int:pk>/',
          DeletePromocodes.as_view(), name='promocode_delete'),

     # Url's for Events
     path('events/create/<int:establishment_id>/',
          CreateEvents.as_view(), name='events_create'),
     path('events/update/<int:pk>/',
          UpdateEvents.as_view(), name='events_update'),
     path('events/delete/<int:pk>/',
          DeleteEvents.as_view(), name='events_delete'),

     # Url's for Wirecard Payment
     path('wirecard/create/<int:establishment_id>/',
          CreateWirecard.as_view(), name='wirecard_create'),
     path('wirecard/company/create/<int:establishment_id>/',
          CreateCompanyWirecard.as_view(), name='wirecard_company_create'),          
     path('wirecard/detail/<int:pk>/',
          DetailWirecard.as_view(), name='wirecard_detail'),

     # Url's for offline Compensations
     path('offline/compensations/', ListCompensations.as_view(),
          name='offline_compensations'),
     path('offline/compensations/check_month/<int:month>/<int:year>/<int:establishment_id>/',
          CreateCompensation.as_view(), name='offline_compensations_check_month'),    
     path('offline/compensations/generate_report/<int:month>/<int:year>/<int:establishment_id>/', GenerateCSVReport.as_view(),
          name='offline_compensations_generate_report'),
           
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
