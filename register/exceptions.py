class OpenBillException(Exception):
    '''
    User try to ingress in a new Bill, but have an opened Bill.
    '''


class CannotLeaveBillException(Exception):
    '''
    The last member cannot leave the bill.
    '''


class CannotCancelOrderException(Exception):
    '''
    Orders accepted by kitchen cannot be canceled.
    '''
