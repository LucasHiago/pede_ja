from rest_framework.exceptions import APIException


class UserHasBeenPaymentException(APIException):
    status_code = 451
    default_detail = 'This User has been Payment'
    default_code = 'this_user_has_been_payment'


class TheSameUUIDPaymentException(APIException):
    status_code = 423
    default_detail = 'The Same uuid Payment Exception'
    default_code = 'the_same_uuid_payment_exception'


class NotPartOfThisBillForPaymentException(APIException):
    status_code = 406
    default_detail = 'You arent part of this Bill'
    default_code = 'you_arent_part_of_this_bill'


class MustPayTheValueFromAllBillPaymentException(APIException):
    status_code = 455
    default_detail = 'You must pay the value from All Bill'
    default_code = 'You_must_pay_the_value_from_all_bill'


class LimitsForPayNoruhFee(APIException):
    status_code = 460
    default_detail = 'The Numbers of noruh fee has been paid'
    default_code = 'the_numbers_of_noruh_fee_has_been_paid'


class YouCanOnlyPayWhatsMissingFromTheBill(APIException):
    status_code = 464
    default_detail = 'You can only pay whats missing from the Bill'
    default_code = 'you_can_only_pay_whats_missing_from_the_bill'


class PaymentError(Exception):
    pass
