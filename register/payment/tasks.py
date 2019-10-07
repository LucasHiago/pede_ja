import logging
import json

from django.contrib.auth.models import User
from django.utils import timezone
from django.shortcuts import get_object_or_404

from celery.decorators import task

from fcm_django.models import FCMDevice

from register.payment.moip import Moip
from register.convert_json import objects_to_json

from noruh_backend.pusher import PusherNotification
from noruh_backend.firestore_connect import NoruhFireStore

from register.models import (
    Employee,
    MoipWirecardCustomer,
    BillPayment,
    BillMember,
    Bill
)

logger = logging.getLogger(__name__)


@task(name="verify_payment")
def verify_payment(id_payment_moip, bill_id, value_paid, value, user_id):
    noruh_wirecard = get_object_or_404(MoipWirecardCustomer, observation='Noruh')
    access_token = noruh_wirecard.access_token
    moip = Moip(access_token)
    status_payment = moip.get_payment(id_payment_moip)
    status_payment = json.loads(status_payment)
    logger.info(status_payment.get('status'))
    noruh_firestore = NoruhFireStore()

    if status_payment.get('status') == Moip.STATUS_IN_ANALYSIS:
        return verify_payment.apply_async(
            (id_payment_moip, bill_id, value_paid, value, user_id),
            countdown=10)

    bill = get_object_or_404(Bill, id=bill_id)
    bill_payment = BillPayment.objects.get(id_payment_moip=id_payment_moip)
    bill_payment.status_payment = status_payment.get('status')
    bill_payment.status_updated = timezone.now()
    bill_payment.save()

    devices = FCMDevice.objects.filter(
            user__in=BillMember.objects.filter(
                bill=bill, leave_at__isnull=True).values('customer'))

    """
    If Wirecard/Moip return STATUS_AUTHORIZED,
    start the business rules and verifications
    """
    if status_payment.get('status') == Moip.STATUS_AUTHORIZED:
        bill.value_paid = float(bill.value_paid) + value
        bill.save()
        user_logged = User.objects.get(id=user_id)

        orders_and_couvert = bill.orders_total() + bill.establishment.taxe_couvert
        taxe_service = (bill.orders_total() * bill.establishment.taxe_service)
        couvert_for_all = bill.couvert_for_all()
        all_value_bill = bill.orders_total() + couvert_for_all + bill.establishment.noruh_fee + taxe_service

        if bill_payment.promocode is not None:
            all_value_bill = (all_value_bill - bill_payment.promocode.value)

        # Verify if value_paid for all bill has been completed, and then leave out all members
        if bill.value_paid >= orders_and_couvert and bill.value_paid <= all_value_bill:
            bill.payment_date = timezone.now()
            bill.save()
            BillMember.objects.filter(
                bill=bill_id, leave_at__isnull=True).update(
                    leave_at=timezone.now())
            data_notification = {
                'action': 'bill_closed',
                'billId': bill.id,
                'createdAt': timezone.now().isoformat()
            }
            noruh_firestore.add_data_on_collection(data_notification)

        # Leave out from bill, bill member that has been payed
        bill_member = BillMember.objects.get(
            bill=bill_id, customer=user_logged,
            leave_at__isnull=True)
        bill_member.leave_at = timezone.now()
        bill_member.save()

        # Send notification to customers, on devices
        body_msg = "O seu pagamento de R$:" f'{value}' " no restaurante " f'{bill.establishment.name}' " foi aprovado"
        data_payment = {
            "bill_id": bill.id,
            "status_payment": bill_payment.status_payment,
            "value": bill_payment.value
        }
        data_payment = json.dumps(data_payment, default=objects_to_json)
        data_dict = {"key": "payment_accepted", "data": data_payment}
        devices.send_message("Pagamento Aprovado", body_msg,
                             icon=bill.establishment.logo_url.url,
                             data=data_dict)

        data_notification = bill_payment.notification_payload(key='payment_accepted')
        noruh_firestore.add_data_on_collection(data_notification)

        # Send notification to door mans, on Noruh Web Admin
        door_mans = User.objects.filter(
            id__in=Employee.objects.filter(
                establishment=bill.establishment,
                user_type=Employee.USER_DOOR_MAN).values('user'))

        list_door_mans = [door_man.id for door_man in door_mans]
        data = {
            "bill_id": bill.id,
            "username": user_logged.first_name,
            "payment_status": Moip.STATUS_AUTHORIZED,
            "table": bill.table.name
        }
        PusherNotification.send_notifications(
            list_door_mans, 'door_man', 'payment_confirm', data)

    # If Payment Cancelled, only send a notification to customer
    if status_payment.get('status') == Moip.STATUS_CANCELLED:
        body_msg = "O seu pagamento de R$:" f'{value}' " no restaurante " f'{bill.establishment.name}' " foi recusado"
        data_payment = {
            "bill_id": bill.id,
            "status_payment": bill_payment.status_payment,
            "value": bill_payment.value
        }
        data_payment = json.dumps(data_payment, default=objects_to_json)
        data_dict = {"key": "payment_refused", "data": data_payment}
        devices.send_message("Pagamento Recusado", body_msg,
                             icon=bill.establishment.logo_url.url,
                             data=data_dict)

        data_notification = bill_payment.notification_payload(key='payment_refused')
        noruh_firestore.add_data_on_collection(data_notification)

    return True
