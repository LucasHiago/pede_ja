from django.core.management import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):

    help = "Add permissions to Groups"

    def handle(self, *args, **options):

        def create_groups_and_permissions(group, permissions):
            for permission in permissions:
                print (permission)
                perm = Permission.objects.get(codename=permission)
                print (perm)
                group.permissions.add(perm)
                print ("Added")

        '''
        Adminsitrador Estabelecimento
        '''
        print ("Ready to Create Groups")
        establishment_manager = Group.objects.create(id=1, name='Administrador estabelecimento')
        print ("Group for Manager Created")
        manager_permisions = ['can_view_bill', 'can_view_payment', 'can_change_status_payment',
                              'can_accept_payment', 'can_create_payment', 'can_update_payment',
                              'can_delete_payment', 'can_list_operating_hour', 'can_view_status_request',
                              'can_change_status_request', 'can_change_order_status', 'can_view_order',
                              'can_change_order', 'can_create_order', 'can_create_employee',
                              'can_view_employee', 'can_alter_employee', 'can_delete_employee',
                              'can_view_establishment', 'can_update_description_establishment',
                              'can_update_amenities_establishment', 'can_update_couvert_taxe_establishment',
                              'can_update_functions_establishment', 'can_update_location_establishment',
                              'can_update_opened', 'can_create_wirecard', 'can_view_wirecard',
                              'can_add_photo_establishment', 'can_delete_photo_establishment',
                              'can_view_photo_establishment', 'can_create_operating_hour',
                              'can_update_operating_hour', 'can_create_events',
                              'can_delete_operating_hour', 'can_view_events',
                              'can_delete_events', 'can_create_promocode', 'can_view_promotions',
                              'can_delete_promotions', 'can_create_menu', 'can_view_menu',
                              'can_update_menu', 'can_delete_menu', 'can_create_category',
                              'can_view_category', 'can_update_category', 'can_delete_category',
                              'can_create_item_observation', 'can_view_item_observation',
                              'can_update_item_observation', 'can_delete_item_observation',
                              'can_create_item_on_menu', 'can_view_item_on_menu',
                              'can_change_item_on_menu', 'can_delete_item_on_menu',
                              'can_create_table_zone', 'can_view_table_zone',
                              'can_view_table_zone', 'can_change_table_zone',
                              'can_desactive_table_zone', 'can_delete_table_zone',
                              'can_create_table', 'can_view_table', 'can_update_table',
                              'can_delete_table', 'can_view_evaluation', 'can_delete_evaluation',
                              'can_view_dashboard_from_establishment', 'can_answer_evaluation',
                              'can_create_menu_offer', 'can_view_menu_offer', 'can_update_menu_offer',
                              'can_delete_menu_offer', 'can_update_offer_range_value']
        create_groups_and_permissions(establishment_manager, manager_permisions)

        '''
        Kitchen
        '''
        kitchen = Group.objects.create(id=2, name='Cozinha')
        print ("Group for Kitchen Created")
        kitchen_permissions = ['can_view_order', 'can_change_order_status']
        create_groups_and_permissions(kitchen, kitchen_permissions)

        '''
        Waiter
        '''
        waiter = Group.objects.create(id=3, name='Garçom')
        print ("Group for Waiter Created")
        waiter_permissions = ['can_view_bill', 'can_view_payment', 'can_change_status_payment',
                              'can_create_payment', 'can_accept_payment', 'can_delete_payment',
                              'can_view_establishment', 'can_list_operating_hour',
                              'can_view_item_on_menu', 'can_change_order', 'can_create_order',
                              'can_change_order_status', 'can_view_order', 'can_view_status_request',
                              'can_change_status_request']
        create_groups_and_permissions(waiter, waiter_permissions)

        '''
        Door Man
        '''
        door_man = Group.objects.create(id=4, name='Porteiro')
        print ("Group for Door Man Created")
        door_man_permissions = ['can_view_bill', 'can_view_payment']
        create_groups_and_permissions(waiter, waiter_permissions)
