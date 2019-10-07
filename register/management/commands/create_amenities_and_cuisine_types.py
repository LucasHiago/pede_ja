from django.core.management import BaseCommand
from register.models import CuisineType, Amenity


class Command(BaseCommand):

    help = "Populate Database with Amenities and Cuisines Types"

    def handle(self, *args, **options):

        # Create All Amenities
        print("Create Amenities")
        wifi, created = Amenity.objects.get_or_create(
            name='Wi-fi', description='Rede sem fio')
        if created:
            print("wifi created")
        else:
            print("wifi already exists")
        park, created = Amenity.objects.get_or_create(
            name='Estacionamento',
            description='Vagas para guardar seu veiculo')
        if created:
            print("park created")
        else:
            print("park already exists")

        tables, created = Amenity.objects.get_or_create(
            name='Mesas ao ar livre', description='Mesas em área externa')
        if created:
            print("tables created")
        else:
            print("tables already exists")

        air_conditioning, created = Amenity.objects.get_or_create(
            name='Ar Condicionado', description='Climatização')
        if created:
            print("air_conditioning created")
        else:
            print("air_conditioning already exists")

        shows, created = Amenity.objects.get_or_create(
            name='Shows', description='Shows')
        if created:
            print("shows created")
        else:
            print("shows already exists")

        wheelchair_accessible, created = Amenity.objects.get_or_create(
            name='Acessível', description='Acessibilidade para Cadeirantes')
        if created:
            print("wheelchair_accessible created")
        else:
            print("wheelchair_accessible already exists")

        valet_parking, created = Amenity.objects.get_or_create(
            name='Manobrista', description='Manobrista')
        if created:
            print("valet_parking created")
        else:
            print("valet_parking already exists")

        beverage_counter, created = Amenity.objects.get_or_create(
            name='Balcão de Bebidas', description='Balcão de Bebidas')
        if created:
            print("beverage_counter created")
        else:
            print("beverage_counter already exists")

        # Create all Cuisines Type
        print("Create Cuisines Type")
        contemporary, created = CuisineType.objects.get_or_create(
            name='Contemporânea')
        if created:
            print("contemporary cuisine created")
        else:
            print("contemporary cuisine already exists")

        italian, created = CuisineType.objects.get_or_create(
            name='Italiana')
        if created:
            print("italian cuisine created")
        else:
            print("italian cuisine already exists")

        brazilian, created = CuisineType.objects.get_or_create(
            name='Brasileira')
        if created:
            print("brazilian cuisine created")
        else:
            print("brazilian cuisine already exists")

        international, created = CuisineType.objects.get_or_create(
            name='Internacional')
        if created:
            print("international cuisine created")
        else:
            print("international cuisine already exists")

        american, created = CuisineType.objects.get_or_create(
            name='Americana')
        if created:
            print("american cuisine created")
        else:
            print("american cuisine already exists")

        snacks, created = CuisineType.objects.get_or_create(
            name='Petiscos')
        if created:
            print("snacks cuisine created")
        else:
            print("snacks cuisine already exists")

        varied, created = CuisineType.objects.get_or_create(
            name='Variada')
        if created:
            print("varied cuisine created")
        else:
            print("varied cuisine already exists")
