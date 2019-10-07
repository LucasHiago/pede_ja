import uuid
import datetime

from django.core.management import BaseCommand
from django.contrib.auth.models import User

from register.models import (
    Establishment,
    Bill,
    BillMember,
    BillPayment,
    MenuItem,
    Order,
    UserRating,
    TableZone,
    Table
)


class Command(BaseCommand):

    help = "Create more bills, orders and Payment"
    '''
    This code, has a function of popular still more the bank and test
    views in the front end with past dates
    '''

    def handle(self, *args, **options):
        '''
        Get some important objects to create another objects
        '''
        establishment = Establishment.objects.get(id=1)
        table_zone = TableZone.objects.get(name='Zona 01')
        item_soda = MenuItem.objects.get(name='Guarana Antartica Lata')

        '''
        The flow for a customer.
        - Create a new table from establishment(because, not to conflict with
        accounts already created and open with tables)
        - Create customer
        - Create a bill with this customer
        - Create a bill BillMember with this customer and associate to a bill
        - Create a order with this customer
        - Create a Payment
        - Create a Evaluation
        '''

        ''' The first Flow with first Customer '''
        print('creating a first month')
        current_month = datetime.date.today()
        table_04 = Table.objects.create(name='Mesa 04',
                                        establishment=establishment,
                                        table_zone=table_zone,
                                        enabled=True)
        customer_04 = User.objects.create(username='customer_04',
                                          password='noruh_123',
                                          email='customer_04@noruh.com')
        bill_04 = Bill(establishment=establishment, table=table_04)
        bill_04.save()
        bill_member_04 = BillMember(customer=customer_04,
                                    bill_owner=True,
                                    joined_at=current_month,
                                    couvert_value=establishment.taxe_couvert)
        bill_member_04.bill = bill_04
        bill_member_04.save()
        Order.objects.create(user=customer_04,
                             bill=bill_04,
                             item=item_soda,
                             quantity=3,
                             kitchen_accepted_at=current_month,
                             kitchen_finished_at=current_month,
                             status=Order.STATUS_DONE)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=current_month,
                                   status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
                                   bill=bill_04,
                                   value=17.60,
                                   user=customer_04)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=current_month,
                                   status_payment=BillPayment.STATUS_AUTHORIZED,
                                   bill=bill_04,
                                   value=20.00,
                                   user=customer_04)
        bill_04.payment_date = current_month
        bill_04.save()
        UserRating.objects.create(bill=bill_04,
                                  user=bill_member_04,
                                  environment=9,
                                  food=8,
                                  service=10,
                                  observation='ótima comida com bom ambiente')
        print('first month, ok')

        ''' The second Flow with second Customer '''
        print('creating a second month')
        a_month_ago = current_month - datetime.timedelta(30)
        table_05 = Table.objects.create(name='Mesa 05',
                                        establishment=establishment,
                                        table_zone=table_zone,
                                        enabled=True)
        customer_05 = User.objects.create(username='customer_05',
                                          password='noruh_123',
                                          email='customer_05@noruh.com')
        bill_05 = Bill(establishment=establishment, table=table_05)
        bill_05.save()
        bill_member_05 = BillMember(customer=customer_05,
                                    bill_owner=True,
                                    joined_at=current_month,
                                    couvert_value=establishment.taxe_couvert)
        bill_member_05.bill = bill_05
        bill_member_05.save()
        Order.objects.create(user=customer_05,
                             bill=bill_05,
                             item=item_soda,
                             quantity=3,
                             kitchen_accepted_at=a_month_ago,
                             kitchen_finished_at=a_month_ago,
                             status=Order.STATUS_DONE)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=a_month_ago,
                                   status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
                                   bill=bill_05,
                                   value=17.60,
                                   user=customer_05)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=a_month_ago,
                                   status_payment=BillPayment.STATUS_AUTHORIZED,
                                   bill=bill_05,
                                   value=20.00,
                                   user=customer_05)
        bill_05.payment_date = a_month_ago
        bill_05.save()
        UserRating.objects.create(bill=bill_05,
                                  user=bill_member_05,
                                  environment=7,
                                  food=5,
                                  service=8,
                                  observation='comida não muito boa')
        print('second month, ok')

        ''' The third Flow with third Customer '''
        print('creating a third month')
        two_months_ago = current_month - datetime.timedelta(60)
        customer_06 = User.objects.create(username='customer_06',
                                          password='noruh_123',
                                          email='customer_06@noruh.com')
        table_06 = Table.objects.create(name='Mesa 06',
                                        establishment=establishment,
                                        table_zone=table_zone,
                                        enabled=True)
        bill_06 = Bill(establishment=establishment, table=table_06)
        bill_06.save()
        bill_member_06 = BillMember(customer=customer_06,
                                    bill_owner=True,
                                    joined_at=two_months_ago,
                                    couvert_value=establishment.taxe_couvert)
        bill_member_06.bill = bill_06
        bill_member_06.save()
        Order.objects.create(user=customer_06,
                             bill=bill_06,
                             item=item_soda,
                             quantity=3,
                             kitchen_accepted_at=two_months_ago,
                             kitchen_finished_at=two_months_ago,
                             status=Order.STATUS_DONE)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=two_months_ago,
                                   status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
                                   bill=bill_06,
                                   value=17.60,
                                   user=customer_06)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=two_months_ago,
                                   status_payment=BillPayment.STATUS_AUTHORIZED,
                                   bill=bill_06,
                                   value=20.00,
                                   user=customer_06)
        bill_06.payment_date = two_months_ago
        bill_06.save()
        UserRating.objects.create(bill=bill_06,
                                  user=bill_member_06,
                                  environment=10,
                                  food=10,
                                  service=10,
                                  observation='serviço e atendimento excelentes')
        print('third month, ok')

        ''' The fourth Flow with fourth Customer '''
        print('creating a fourth month')
        three_months_ago = current_month - datetime.timedelta(90)
        customer_07 = User.objects.create(username='customer_07',
                                          password='noruh_123',
                                          email='customer_07@noruh.com')
        table_07 = Table.objects.create(name='Mesa 07',
                                        establishment=establishment,
                                        table_zone=table_zone,
                                        enabled=True)
        bill_07 = Bill(establishment=establishment, table=table_07)
        bill_07.save()
        bill_member_07 = BillMember(customer=customer_07,
                                    bill_owner=True,
                                    joined_at=three_months_ago,
                                    couvert_value=establishment.taxe_couvert)
        bill_member_07.bill = bill_07
        bill_member_07.save()
        Order.objects.create(user=customer_07,
                             bill=bill_07,
                             item=item_soda,
                             quantity=3,
                             kitchen_accepted_at=three_months_ago,
                             kitchen_finished_at=three_months_ago,
                             status=Order.STATUS_DONE)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=three_months_ago,
                                   status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
                                   bill=bill_07,
                                   value=17.60,
                                   user=customer_07)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=three_months_ago,
                                   status_payment=BillPayment.STATUS_AUTHORIZED,
                                   bill=bill_07,
                                   value=20.00,
                                   user=customer_07)
        bill_07.payment_date = three_months_ago
        bill_07.save()
        UserRating.objects.create(bill=bill_07,
                                  user=bill_member_07,
                                  environment=9,
                                  food=8,
                                  service=9,
                                  observation='boa experiencia')
        print('Fourth month, ok')

        ''' The fifth Flow with fifth Customer '''
        print('creating a fifth month')
        four_months_ago = current_month - datetime.timedelta(120)
        customer_08 = User.objects.create(username='customer_08',
                                          password='noruh_123',
                                          email='customer_08@noruh.com')
        table_08 = Table.objects.create(name='Mesa 08',
                                        establishment=establishment,
                                        table_zone=table_zone,
                                        enabled=True)
        bill_08 = Bill(establishment=establishment, table=table_08)
        bill_08.save()
        bill_member_08 = BillMember(customer=customer_08,
                                    bill_owner=True,
                                    joined_at=four_months_ago,
                                    couvert_value=establishment.taxe_couvert)
        bill_member_08.bill = bill_08
        bill_member_08.save()
        Order.objects.create(user=customer_08,
                             bill=bill_08,
                             item=item_soda,
                             quantity=3,
                             kitchen_accepted_at=four_months_ago,
                             kitchen_finished_at=four_months_ago,
                             status=Order.STATUS_DONE)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=four_months_ago,
                                   status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
                                   bill=bill_08,
                                   value=17.60,
                                   user=customer_08)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=four_months_ago,
                                   status_payment=BillPayment.STATUS_AUTHORIZED,
                                   bill=bill_08,
                                   value=20.00,
                                   user=customer_08)
        bill_08.payment_date = four_months_ago
        bill_08.save()
        UserRating.objects.create(bill=bill_08,
                                  user=bill_member_08,
                                  environment=9,
                                  food=8,
                                  service=9,
                                  observation='boa experiência')

        print('fifth month, ok')

        ''' The sixth Flow with sixth Customer '''
        print('creating a sixth month')
        five_months_ago = current_month - datetime.timedelta(150)
        customer_09 = User.objects.create(username='customer_09',
                                          password='noruh_123',
                                          email='customer_09@noruh.com')
        table_09 = Table.objects.create(name='Mesa 09',
                                        establishment=establishment,
                                        table_zone=table_zone,
                                        enabled=True)
        bill_09 = Bill(establishment=establishment, table=table_09)
        bill_09.save()
        bill_member_09 = BillMember(customer=customer_09,
                                    bill_owner=True,
                                    joined_at=five_months_ago,
                                    couvert_value=establishment.taxe_couvert)
        bill_member_09.bill = bill_09
        bill_member_09.save()
        Order.objects.create(user=customer_09,
                             bill=bill_09,
                             item=item_soda,
                             quantity=3,
                             kitchen_accepted_at=five_months_ago,
                             kitchen_finished_at=five_months_ago,
                             status=Order.STATUS_DONE)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=five_months_ago,
                                   status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
                                   bill=bill_09,
                                   value=17.60,
                                   user=customer_09)
        BillPayment.objects.create(payment_uuid=str('Noruh_' + str(uuid.uuid4())),
                                   establishment=establishment,
                                   status_updated=five_months_ago,
                                   status_payment=BillPayment.STATUS_AUTHORIZED,
                                   bill=bill_09,
                                   value=20.00,
                                   user=customer_09)
        bill_09.payment_date = five_months_ago
        bill_09.save()
        UserRating.objects.create(bill=bill_09,
                                  user=bill_member_09,
                                  environment=9,
                                  food=8,
                                  service=9,
                                  observation='boa experiência')
