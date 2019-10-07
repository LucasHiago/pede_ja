from django.test import TestCase
from model_mommy import mommy
from register.models import (
    Amenity,
    Establishment,
    Bill,
    BillMember,
    BillMember,
    Order
    )
from register.forms import EstablishmentForm
from register.exceptions import (
    OpenBillException,
    CannotLeaveBillException,
    CannotCancelOrderException,
)
from django.contrib.auth.models import User, Permission, Group
from django.utils import timezone
from django.urls import reverse

# Tests Models

class EstablishmentTestCase(TestCase):
    def setUp(self):
        amenity = Amenity.objects.create(
            name='amenity_test', description='teste')
        establishment = Establishment.objects.create(name='bar teste',
                                                     address='rua 16',
                                                     geo_loc='-687.65625, 26.74561',
                                                     amenities=1,
                                                     noruh_fee=0.03
                                                     )

    def test_name_establishment(self):
        establishment = Establishment.objects.get(id=1)
        field_label = establishment._meta.get_field('bar teste').verbose_name
        self.assertEquals(field_label, 'bar teste')


class BillMemberTestCase(TestCase):
    def test_open_bill_twice_with_differente_bills_is_not_permited(self):
        '''
        The same customer cannot open 2 different bills at same time.
        '''
        bill = mommy.make(Bill)
        customer = mommy.make(User)
        mommy.make(BillMember, bill=bill, customer=customer)

        with self.assertRaises(OpenBillException):
            mommy.make(BillMember, customer=customer)

    def test_open_bill_twice_on_the_same_bill_is_not_permited(self):
        '''
        The same customer cannot participate of the same bill at same time.
        '''
        bill = mommy.make(Bill)
        customer = mommy.make(User)
        mommy.make(BillMember, bill=bill, customer=customer)

        with self.assertRaises(OpenBillException):
            mommy.make(BillMember, bill=bill, customer=customer)

    def test_leave(self):
        bill = mommy.make(Bill)
        bm1 = mommy.make(BillMember, bill=bill)
        bm2 = mommy.make(BillMember, bill=bill)
        self.assertIsNotNone(bm1.joined_at)
        self.assertIsNone(bm1.leave_at)
        self.assertIsNotNone(bm2.joined_at)
        self.assertIsNone(bm2.leave_at)
        bm1.leave()
        self.assertIsNotNone(bm1.leave_at)
        self.assertIsNone(bm2.leave_at)

    def test_leave_without_extra_members(self):
        '''
        A bill always need to have at least 1 active customer.
        '''
        bm = mommy.make(BillMember)
        bm.save()

        with self.assertRaises(CannotLeaveBillException):
            bm.leave()

    def test_owner_with_single_customer(self):
        customer = mommy.make(User)
        bm = mommy.make(BillMember, customer=customer)
        self.assertEqual(bm.bill.owner, customer)

    def test_owner_with_many_customer(self):
        customer = mommy.make(User)
        bill = mommy.make(Bill)
        bm = mommy.make(BillMember, customer=customer, bill=bill)
        mommy.make(BillMember, bill=bill, _quantity=5)
        self.assertEqual(bill.owner, customer)
        self.assertEqual(bill.customers.count(), 6)

    def test_second_owner_after_first_owner_leaves(self):
        first_owner = mommy.make(User)
        second_owner = mommy.make(User)
        bill = mommy.make(Bill)
        bm = mommy.make(BillMember, customer=first_owner, bill=bill)
        mommy.make(BillMember, customer=second_owner, bill=bill)
        mommy.make(BillMember, bill=bill, _quantity=4)
        bm.leave()
        self.assertEqual(bill.owner, second_owner)
        self.assertEqual(bill.customers.count(), 6)


class OrderTestCase(TestCase):
    def test_cancel_order_set_canceled_at(self):
        order = mommy.make(Order)
        self.assertIsNone(order.canceled_at)
        order.cancel()
        self.assertIsNotNone(order.canceled_at)

    def test_cannot_cancel_order_accepted_by_kitchen(self):
        order = mommy.make(Order, kitchen_accepted_at=timezone.now())
        self.assertIsNone(order.canceled_at)
        with self.assertRaises(CannotCancelOrderException):
            order.cancel()

# Forms Tests


# Views Tests
class HomeTestCase(TestCase):

    def setUp(self):
        self.url = reverse('home')

    def test_response_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'home.html')


'''
class CreateEstablishmentTestCase(TestCase):

    def setUp(self):
        self.url = reverse('establishment_create')
        template_group = Group.objects.get(name=LOCAL_ADMIN_GROUP_TEMPLATE)
        user_test = mommy.make(User)
        self.c = Client()
        self.user_test.save()

    def test_cannot_create_establishment_without_login(self):
        response = self.c.get('establishment_create')
        self.assertEqual(response.status_code, 302)

    def test_can_acces_and_create_establishment_with_login(self):
        self.user.groups.add(self.my_group)
        self.user.save()
        self.c.login(username='test', password='test')
        response = self.c.get('establishment_create')
        self.assertEqual(response.status_code, 200)
'''
class LoginTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = mommy.prepare(User, username='matheus') 
        self.user.set_password('password')
        self.user.save()
        self.client.login(username='matheus', password='password')


    def test_secure_page(self):
        self.client.login(username='temporary', password='temporary')
        response = self.client.get('login', follow=True)
        user = User.objects.get(username='temporary')
        self.assertEqual(response.context['username'], 'temporary')
