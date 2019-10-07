import uuid

from django.core.management import BaseCommand
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone

from register.models import (
    Amenity,
    CuisineType,
    Establishment,
    Employee,
    Bill,
    BillMember,
    BillPayment,
    ItemCategory,
    ItemObservations,
    Menu,
    MenuItem,
    Order,
    UserRating,
    TableZone,
    Table
)


class Command(BaseCommand):

    help = "Populate Database with Examples Data"

    def handle(self, *args, **options):

        amenity_01 = Amenity.objects.create(name='Ar condicionado',
                                            description='Otima climatização')
        amenity_02 = Amenity.objects.create(name='Garçons Exclusivos',
                                            description='Otimo atendimento')

        cuisine_type = CuisineType.objects.create(name="Americana")

        establishment_one = Establishment(
            name='Establishment 01',
            description='Ótima comida',
            address='Rua 01',
            cuisine_type=cuisine_type,
            enabled=True,
            opened=True,
            gps_restriction=True,
            logo_url='example_database/establishment_logo.jpg',
            noruh_fee=4.0)

        establishment_one.geo_loc = GEOSGeometry('POINT(-35.782471 -9.589917)', srid=4326)
        establishment_one.save()
        establishment_one.amenities.add(amenity_01, amenity_02)
        establishment_one.save()

        establishment_two = Establishment(
            name='Establishment 02',
            description='Ótima comida',
            address='Rua 01',
            cuisine_type=cuisine_type,
            enabled=True,
            opened=True,
            gps_restriction=True,
            logo_url='example_database/images.jpg',
            noruh_fee=4.0)

        establishment_two.geo_loc = GEOSGeometry('POINT(-35.782471 -9.589917)', srid=4326)
        establishment_two.save()
        establishment_two.amenities.add(amenity_01, amenity_02)
        establishment_two.save()

        user_manager_est_01 = User.objects.create(
            username='manager_est_01',
            email='manager_est_01@noruh.com',
            password='noruh_123')
        Employee.objects.create(
            user=user_manager_est_01,
            user_type=Employee.USER_MANAGER,
            establishment=establishment_one,
            cpf="55245617072",
            image='example_database/manager_profile.png')

        user_waiter_est_01 = User.objects.create(
            username='waiter_est_01',
            email='waiter_est_01@noruh.com',
            password='noruh_123')
        Employee.objects.create(
            user=user_waiter_est_01,
            user_type=Employee.USER_WAITER,
            establishment=establishment_one,
            cpf="63238944088",
            image='example_database/waiter_profile.jpeg')

        user_kitchen_est_01 = User.objects.create(
            username='kitchen_est_01',
            email='kitchen_est_01@noruh.com',
            password='noruh_123')
        Employee.objects.create(
            user=user_kitchen_est_01,
            user_type=Employee.USER_KITCHEN,
            establishment=establishment_one,
            cpf="26663076035",
            image='example_database/kitchen_profile.png')

        user_door_man_est_01 = User.objects.create(
            username='door_man_est_01',
            email='door_man_est_01@noruh.com',
            password='noruh_123')
        Employee.objects.create(
            user=user_door_man_est_01,
            user_type=Employee.USER_KITCHEN,
            establishment=establishment_one,
            cpf="22763771009",
            image='example_database/door_man_profile.jpg')

        category_01 = ItemCategory.objects.create(
            name='Bebidas',
            establishment=establishment_one)
        category_02 = ItemCategory.objects.create(
            name='Comidas',
            establishment=establishment_one)

        observation_01 = ItemObservations.objects.create(
            observation='Gelada',
            establishment=establishment_one)
        ItemObservations.objects.create(
            observation='Com gelo e limão',
            establishment=establishment_one)
        observation_03 = ItemObservations.objects.create(
            observation='Com cebola',
            establishment=establishment_one)
        observation_04 = ItemObservations.objects.create(
            observation='Sem pimenta',
            establishment=establishment_one)

        menu_item_01 = MenuItem(
            menu=Menu.objects.get(establishment=establishment_one),
            name='Guarana Antartica Lata',
            description='Refrigerante Guarana',
            available=True,
            price=5.90,
            photo='example_database/guarana.JPG',
            category=category_01,
            serve_up=1,
            preparation_time="00:02:00")
        menu_item_01.save()
        menu_item_01.observations.add(observation_01)
        menu_item_01.save()

        menu_item_02 = MenuItem(
            menu=Menu.objects.get(establishment=establishment_one),
            name='Macaxeira com Charque',
            description='Macaxeira cozinhada com Charque assado',
            available=True,
            price=19.90,
            photo='example_database/macaxeia.jpg',
            category=category_02,
            serve_up=2,
            preparation_time="00:15:00")
        menu_item_02.save()
        menu_item_02.observations.add(observation_03, observation_04)
        menu_item_02.save()

        customer_01 = User.objects.create(
            username='customer_01',
            password='noruh_123',
            email='customer_01@noruh.com')
        customer_02 = User.objects.create(
            username='customer_02',
            password='noruh_123',
            email='customer_02@noruh.com')
        customer_03 = User.objects.create(
            username='customer_03',
            password='noruh_123',
            email='customer_03@noruh.com')

        table_zone_01 = TableZone.objects.create(
            name='Zona 01',
            establishment=establishment_one,
            enabled=True)
        table_zone_02 = TableZone.objects.create(
            name='Zona 02',
            establishment=establishment_one,
            enabled=True)

        table_01 = Table.objects.create(
            name='Mesa 01',
            establishment=establishment_one,
            table_zone=table_zone_01,
            enabled=True)
        Table.objects.create(
            name='Mesa 02',
            establishment=establishment_one,
            table_zone=table_zone_01,
            enabled=True)
        table_03 = Table.objects.create(
            name='Mesa 03',
            establishment=establishment_one,
            table_zone=table_zone_02,
            enabled=True)

        bill_01 = Bill(establishment=establishment_one, table=table_01)
        bill_01.save()
        bill_member_01 = BillMember(
            customer=customer_01,
            bill_owner=True,
            joined_at=timezone.now(),
            couvert_value=establishment_one.taxe_couvert)
        bill_member_01.bill = bill_01
        bill_member_01.save()

        bill_02 = Bill(establishment=establishment_one, table=table_03)
        bill_02.save()
        bill_member_02 = BillMember(
            customer=customer_02,
            bill_owner=True,
            joined_at=timezone.now(),
            couvert_value=establishment_one.taxe_couvert)
        bill_member_03 = BillMember(
            customer=customer_03,
            bill_owner=False,
            joined_at=timezone.now(),
            couvert_value=establishment_one.taxe_couvert)
        bill_member_02.bill = bill_02
        bill_member_02.save()
        bill_member_03.bill = bill_02
        bill_member_03.save()

        Order.objects.create(
            user=customer_01,
            bill=bill_01,
            item=menu_item_01,
            quantity=3,
            kitchen_accepted_at=timezone.now(),
            kitchen_finished_at=timezone.now(),
            status=Order.STATUS_DONE)
        Order.objects.create(
            user=customer_01,
            bill=bill_01,
            item=menu_item_02,
            quantity=1,
            kitchen_accepted_at=timezone.now(),
            status=Order.STATUS_PREPARING)
        Order.objects.create(
            user=customer_02,
            bill=bill_02,
            item=menu_item_02,
            quantity=2,
            status=Order.STATUS_PENDING)
        payment_uuid = str('Noruh_' + str(uuid.uuid4()))
        BillPayment.objects.create(
            payment_uuid=payment_uuid,
            establishment=establishment_one,
            status_payment=BillPayment.STATUS_OFFLINE_APPROVED,
            bill=bill_01,
            value=37.60,
            bill_member=bill_member_01)
        UserRating.objects.create(
            bill=bill_01,
            user=bill_member_01,
            environment=9,
            food=8,
            service=10,
            observation='ótima comida')
