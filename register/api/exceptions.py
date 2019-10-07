from rest_framework.exceptions import APIException


class TableDoesNotExistsAPIException(APIException):
    status_code = 400
    default_detail = 'This Table does Not Exist'
    default_code = 'table_does_not_exist'


class HaventEnoughRequestsMakeOrderAPIException(APIException):
    status_code = 401
    default_detail = 'You do not have enough requests to make an order'
    default_code = 'you_do_not_have_enough_requests_to_make_an_order'


class LimitDiscountAmoutIsOverAPIException(APIException):
    status_code = 405
    default_detail = 'Your discount amount is Over'
    default_code = 'your_discount_amount_is_over'


class ItemDoesntBelongToCategoryOffer(APIException):
    status_code = 404
    default_detail = 'This Item doesnt belong to Category from MenuOffer'
    default_code = 'this_item_doesnt_belong_to_category_from_menu_offer'


class EstablishmentDoesNotAvaibleAPIException(APIException):
    status_code = 401
    default_detail = 'This Establishment is Desactived'
    default_code = 'this_establishment_is_desactived'


class BillDoestNotAvaibleForJoinAPIException(APIException):
    status_code = 475
    default_detail = 'This Bill is not Avaible for Join'
    default_code = 'bill_dont_avaible_for_join'


class TableDoesntAvaibleAPIException(APIException):
    status_code = 406
    default_detail = 'This table is not Avaible'
    default_code = 'this_table_is_not_avaible'


class NotPartOfThisBillException(APIException):
    status_code = 406
    default_detail = 'You arent part of this Bill'
    default_code = 'you_arent_part_of_this_bill'


class BillAlreadyBeenPaidException(APIException):
    status_code = 412
    default_detail = 'This Bill Already Been Paid'
    default_code = 'this_bill_already_been_paid'


class YouHadBeenOnThisBillApiException(APIException):
    status_code = 471
    default_detail = 'You had been on this Bill'
    default_code = 'you_had_been_on_this_bill'


class OpenBillAPIException(APIException):
    status_code = 409
    default_detail = 'You already have an Open Bill'
    default_code = 'have_an_open_bill'
