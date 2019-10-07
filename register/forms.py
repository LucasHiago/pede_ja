import re
from django import forms
from django.forms import (
    ModelForm,
    TextInput,
    Select,
    Textarea,
    NumberInput
)
from decimal import Decimal
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from localflavor.br.forms import BRCPFField, BRCNPJField

from .models import (
    AnswerEvaluation,
    Bill,
    BillMember,
    BillPayment,
    Employee,
    Establishment,
    EstablishmentEvents,
    EstablishmentOperatingHours,
    EstablishmentPromotions,
    EstablishmentPhoto,
    ItemCategory,
    ItemObservations,
    Menu,
    MenuItem,
    MenuOffer,
    Order,
    Table,
    TableZone,
    DAYS_OF_WEEK,
)
from leaflet.forms.widgets import LeafletWidget


class BillMemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.customer.first_name and obj.customer.last_name:
            return f'{obj.customer.first_name} {obj.customer.last_name}'
        else:
            return obj.customer.email


class UserEmployeeForm(UserCreationForm):
    name = forms.CharField(max_length=150, required=True, label='Nome completo',
                           help_text='Campo requerido. Informe o nome completo.')
    email = forms.EmailField(max_length=254, required=True, help_text='Campo requerido. Informe um email válido.')

    class Meta:
        model = User
        fields = ['name', 'email',
                  'password1', 'password2']
        help_texts = {
            'name': 'Campo requerido. Informe o nome completo.',
            'email': 'Campo requerido. Informe um email válido.',
        }

    def clean(self):
        email = self.data.get('user-email')
        if User.objects.filter(username=email, email=email).exists():
            raise forms.ValidationError({'email': 'Já existe um colaborador com esse email cadastrado'})


class UpdatePasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(
        label='Repita a Senha', widget=forms.PasswordInput())

    def __init__(self, user, *args, **kwargs):
        super(UpdatePasswordForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not password1:
            raise forms.ValidationError(_('Uma senha deve ser informada'))
        validate_password(password1, self.user.password)
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password2')
        if not password1:
            raise forms.ValidationError(_('Senha de confirmação deve ser informada'))
        return password1

    def clean(self):
        password1 = self.cleaned_data.get('password1', '')
        password2 = self.cleaned_data.get('password2', '')
        if password1 != password2:
            raise forms.ValidationError('As senhas não são iguais')
        return self.cleaned_data

    def save(self, commit=True):
        self.user.set_password(self.cleaned_data.get('password1'))
        if commit:
            self.user.save()
        return self.user


class EmployeeForm(ModelForm):
    cpf = BRCPFField(
        max_length=11,
        min_length=11,
        help_text="Somente números",
        label="CPF")

    class Meta:
        model = Employee
        fields = ['cpf', 'user_type',
                  'establishment', 'image']

    def __init__(self, establishment_id=None, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(EmployeeForm, self).__init__(*args, **kwargs)
        if establishment_id:
            self.fields.pop('establishment')
            self.establishment = Establishment.objects.get(id=establishment_id)

    def save(self, commit=True):
        instance = super(EmployeeForm, self).save(commit=False)
        if hasattr(self, 'establishment'):
            instance.establishment = self.establishment
        instance.save()
        return instance


class MoipWirecardCustomerForm(forms.Form):
    # personal informations
    email = forms.CharField()
    name = forms.CharField()
    last_name = forms.CharField()
    birth_date = forms.CharField(help_text='Padrão: aaaa-mm-dd')
    # cpf
    number_cpf = BRCPFField()
    # id_document
    number_rg = forms.CharField(help_text='Ex: Somente números')
    issuer = forms.CharField(help_text='Ex: Somente números')
    issue_date = forms.CharField()
    # phone informations
    country_code = forms.CharField(help_text='Código do País. Ex: 55')
    area_code = forms.CharField(help_text='Código do Estado. Ex: 11')
    phone_number = forms.CharField()
    # address informations
    street = forms.CharField()
    street_number = forms.CharField()
    district = forms.CharField()
    zip_code = forms.CharField(help_text='Ex: Somente números')
    city = forms.CharField()
    state = forms.CharField(help_text='Ex: Sigla do Estado.')

    def validate(self):
        if self.data.get('email') is None:
            raise forms.ValidationError('You cannot create a Wirecard without email')


class MoipWirecardCompanyForm(forms.Form):
    email = forms.CharField()
    name_person = forms.CharField(help_text='Nome do Representante')
    birth_date = forms.CharField(help_text='Padrão: aaaa-mm-dd')

    # cpf
    number_cpf = BRCPFField(help_text='Somente Números')

    # phone informations
    country_code_personal = forms.CharField(help_text='Código do País. Ex: 55')
    area_code_personal = forms.CharField(help_text='Código do Estado. Ex: 11')
    phone_number_personal = forms.CharField()

    # address informations
    street_personal = forms.CharField()
    street_number_personal = forms.CharField()
    district_personal = forms.CharField()
    zip_code_personal = forms.CharField(help_text='Ex: Somente números')
    city_personal = forms.CharField()
    state_personal = forms.CharField(help_text='Ex: Sigla do Estado.')

    # Company Informations
    name_company = forms.CharField(help_text='Nome Fantasia')
    business_name = forms.CharField(help_text='Razão social')
    opening_date = forms.CharField(help_text='Padrão: aaaa-mm-dd')

    # CNPJ
    number_cnpj = BRCNPJField()

    # CNAE Informations
    cnae = forms.CharField(help_text='Código CNAE de atividade. Exemplo 82.91-1/00')
    description = forms.CharField(
        help_text='Descrição da atividade. Exemplo: Atividades de cobranças e informações cadastrais')

    # Phone informations
    country_code_company = forms.CharField(help_text='Código do País. Ex: 55')
    area_code_company = forms.CharField(help_text='Código do Estado. Ex: 11')
    phone_number_company = forms.CharField()

    # Address informations
    street_company = forms.CharField()
    street_number_company = forms.IntegerField()
    district_company = forms.CharField()
    zip_code_company = forms.CharField(help_text='Ex: Somente números')
    city_company = forms.CharField()
    state_company = forms.CharField(help_text='Ex: Sigla do Estado.')

    def validate(self):
        if self.data.get('email') is None:
            raise forms.ValidationError('You cannot create a Wirecard without email')


class EstablishmentForm(ModelForm):

    class Meta:
        model = Establishment
        fields = ['name', 'description',
                  'address', 'geo_loc',
                  'amenities', 'cuisine_type',
                  'enabled', 'opened', 'noruh_fee',
                  'gps_restriction', 'logo_url',
                  'featured', 'pays_payment_tax',
                  'moip_fee', 'payment_tax', 'taxe_service',
                  'taxe_couvert']
        labels = {
            'name': 'Nome',
            'description': 'Descrição',
            'address': 'Endereço',
            'geo_loc': '',
            'amenities': 'Comodidades',
            'cuisine_type': 'Tipo de Cozinha',
            'enabled': 'Ativo',
            'opened': 'Aberto',
            'noruh_fee': 'Taxa Noruh',
            'gps_restriction': 'Pedidos a Distância',
            'logo_url': 'Logo da Empresa',
            'featured': 'Destaque',
            'pays_payment_tax': 'Taxa de pagamento',
            'moip_fee': 'Taxa Moip',
            'payment_tax': 'Taxa de Pagamento',
            'taxe_service': 'Taxa de serviço',
            'taxe_couvert': 'Taxa Couvert'
        }

        widgets = {
          'geo_loc': LeafletWidget(),
        }

    def __init__(self, *args, **kwargs):
        on_edit = kwargs.get('on_edit', False)
        if 'on_edit' in kwargs:
            kwargs.pop('on_edit')

        super(EstablishmentForm, self).__init__(*args, **kwargs)


class EstablishmentLocationForm(ModelForm):

    class Meta:
        model = Establishment
        fields = ['geo_loc', 'address']
        labels = {
            'geo_loc': 'Localização',
            'address': 'Endereço'
        }
        widgets = {'geo_loc': LeafletWidget()}


class EstablishmentDescriptionForm(ModelForm):

    class Meta:
        model = Establishment
        fields = ['name', 'description', 'cuisine_type', 'logo_url']
        labels = {
            'name': 'Nome do Estabelecimento',
            'description': 'Descrição',
            'cuisine_type': 'Tipo de Cozinha',
            'logo_url': 'Logo do Restaurante',
        }


class EstablishmentAmenitiesForm(ModelForm):

    class Meta:
        model = Establishment
        fields = ['amenities']
        labels = {
            'amenities': 'Selecionar comodidades',
        }


class EstablishmentTaxesForm(ModelForm):

    class Meta:
        model = Establishment
        fields = ['noruh_fee', 'pays_payment_tax',
                  'moip_fee', 'payment_tax',
                  'taxe_service', 'offline_percentage']
        labels = {
            'noruh_fee': 'Gorjeta Noruh',
            'pays_payment_tax': 'Estabelecimento irá pagar as taxas referentes ao uso do sistema Moip-Wirecard',
            'moip_fee': 'Taxa Moip',
            'payment_tax': 'Taxa de Pagamento',
            'taxe_service': 'Taxa de Serviço',
            'offline_percentage': 'Porcentagem Offline',
        }
        help_texts = {
            'noruh_fee': 'Gorjeta a ser aplicada para clientes deste estabelecimento e ser direcionada ao Noruh',
            'moip_fee': 'Valor fixo a ser repassado ao Moip-Wirecard para cada transição',
            'payment_tax': 'Porcentagem a ser cobrada deste estabelecimento para cada transição via Moip-Wirecard',
            'taxe_service': 'Taxa de Serviço(%) do estabelecimento',
            'offline_percentage': 'Porcentagem a cobrar de valores referentes a pagamentos offline',
        }


class EstablishmentTaxeCouvertForm(ModelForm):

    class Meta:
        model = Establishment
        fields = ['taxe_couvert']
        labels = {
            'taxe_couvert': 'Taxa Couvert',
        }


class EstablishmentOfferRangeValueForm(ModelForm):

    class Meta:
        model = Establishment
        fields = ['offer_range_value', 'offer_count_limit']
        labels = {
            'offer_range_value': 'Valor para o Intervalo de Ofertas',
            'offer_count_limit': 'Quantidade de ofertas para uma conta'
        }


class OrderForm(ModelForm):
    menu_item = forms.CharField(
        label='Produto',
        required=True,
        )
    bill = forms.CharField(
        label='Mesa',
        required=True,
        )

    class Meta:
        model = Order
        fields = ['menu_item', 'quantity', 'bill', 'user', 'observation']
        labels = {
            'quantity': 'Quantidade',
            'user': 'Usuário',
            'observation': 'Observações'
        }

    def __init__(self, establishment, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user_id = self.fields['user'].widget.value_from_datadict(
            self.data, self.files, self.add_prefix('user'))

        if user_id:
            self.fields['user'].queryset = User.objects.filter(id=user_id)
        else:
            self.fields['user'].queryset = User.objects.none()

        if 'bill' in self.data:
            try:
                bill_id = str(self.data.get('bill'))
                self.fields['user'].queryset = User.objects.filter(
                    id__in=BillMember.objects.filter(
                        bill__id=bill_id).values('customer'))
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['user'].queryset = User.objects.none()

    def clean_menu_item(self):
        menu_item_name = (self.data.get('menu_item'))
        menu_item = MenuItem.objects.get(name=menu_item_name)
        return menu_item

    def clean_bill(self):
        bill_id = (self.data.get('bill'))
        bill = Bill.objects.get(
            id=bill_id, payment_date__isnull=True)
        return bill

    def save(self, commit=True):
        instance = self.instance
        instance.item = self.clean_menu_item()
        instance.bill = self.clean_bill()
        instance.status = Order.STATUS_PENDING
        return super().save(commit)


class PaymentOfflineForm(ModelForm):
    value = forms.CharField(
        required=True,
        widget=TextInput(attrs={
            'class': 'input',
            'placeholder': 'Ex: 10,90'
            })
        )

    class Meta:
        model = BillPayment
        fields = ['bill_member']
        field_classes = {
            'bill_member': BillMemberChoiceField
        }
        exclude = ['establishment', 'bill',
                   'status_payment', 'status_updated',
                   'date']

    def __init__(self, bill_id, *args, **kwargs):
        self.bill_id = bill_id
        super(PaymentOfflineForm, self).__init__(*args, **kwargs)
        self.fields['bill_member'].queryset = BillMember.objects.filter(
            bill__id=bill_id, leave_at__isnull=True)

    def clean_value(self):
        value = (self.data.get('value'))
        bill = Bill.objects.get(id=self.bill_id)
        leftover = bill.all_value_bill_without_taxe_service() - bill.value_paid

        if not re.fullmatch(r'\d+([.,]\d{2})?', value):
            raise forms.ValidationError('Valor inválido')
        value = Decimal(value.replace(',', '.'))

        if float(value) < float(leftover) or float(value) > bill.all_value_bill():
            raise forms.ValidationError(
                'Você deve pagar o valor minimo de {}'.format(leftover))
        return value

    def save(self, commit=True):
        instance = self.instance
        instance.value = self.clean_value()
        return super().save(commit)


class EstablishmentOperatingHoursForm(ModelForm):
    opening_time = forms.CharField(
        required=True,
        max_length=5,
        label='Horário que abre')
    closing_time = forms.CharField(
        required=True,
        max_length=5,
        label='Horário que abre')

    class Meta:
        model = EstablishmentOperatingHours
        fields = ['dow']
        labels = {
            'dow': ('Dia'),
        }

    def __init__(self, establishment, *args, **kwargs):
        super(EstablishmentOperatingHoursForm, self).__init__(*args, **kwargs)
        self.establishment = establishment
        days_registered = EstablishmentOperatingHours.objects.filter(
            establishment=establishment).values_list('dow')
        days_not_registred = []

        for day in DAYS_OF_WEEK:
            if (day[0], ) not in days_registered:
                days_not_registred.append(day)
        self.fields['dow'].widget.choices = days_not_registred

    def clean_opening_time(self):
        opening_time = self.data.get('opening_time', '')
        time = re.fullmatch(r'(?P<hour>(?:2[0-3])|(?:[01]?\d))(?:\:(?P<min>[0-5]\d)(?:\:(?P<sec>[0-5]\d))?)?', opening_time)
        if time:
            return f'{time.group("hour")}:{time.group("min") or "00"}'

    def clean_closing_time(self):
        closing_time = self.data.get('closing_time', '')
        time = re.fullmatch(r'(?P<hour>(?:2[0-3])|(?:[01]?\d))(?:\:(?P<min>[0-5]\d)(?:\:(?P<sec>[0-5]\d))?)?', closing_time)
        if time:
            return f'{time.group("hour")}:{time.group("min") or "00"}'

    def clean(self):
        if EstablishmentOperatingHours.objects.filter(
                dow=self.data.get('dow'), establishment=self.establishment):
            raise forms.ValidationError('Já existe um horário para esse dia')
        return self.cleaned_data

    def save(self):
        instance = super(EstablishmentOperatingHoursForm, self).save(commit=False)
        instance.establishment = self.establishment
        instance.opening_time = self.cleaned_data.get('opening_time')
        instance.closing_time = self.cleaned_data.get('closing_time')
        instance.save()
        return instance


class EstablishmentPromocodeForm(ModelForm):

    class Meta:
        model = EstablishmentPromotions
        fields = ['promocode', 'value', 'description', 'enabled']
        labels = {
            'promocode': ('Promocode'),
            'value': ('Valor do Promocode'),
            'description': ('Descrição'),
            'enabled': ('Ativa'),
        }

    def __init__(self, *args, **kwargs):
        super(EstablishmentPromocodeForm, self).__init__(*args, **kwargs)


class EstablishmentEventsForm(ModelForm):

    class Meta:
        model = EstablishmentEvents
        fields = ['description', 'date']
        labels = {
            'description': ('Descrição do Evento'),
            'Data': ('Data'),
        }

    def __init__(self, *args, **kwargs):
        super(EstablishmentEventsForm, self).__init__(*args, **kwargs)


class EstablishmentPhotoForm(ModelForm):

    class Meta:
        model = EstablishmentPhoto
        fields = ['photo']
        labels = {
            'photo': ('Adicionar Foto'),
        }

    def __init__(self, *args, **kwargs):
        super(EstablishmentPhotoForm, self).__init__(*args, **kwargs)


class ItemCategoryForm(ModelForm):

    class Meta:
        model = ItemCategory
        fields = ['name']
        labels = {
            'name': ('Nome da Categoria'),
        }
        widgets = {
            'name': TextInput(attrs={
                'class': 'input',
                'placeholder': 'Ex: Cozinha Tailandesa'
            })
        }

    def __init__(self, *args, **kwargs):
        super(ItemCategoryForm, self).__init__(*args, **kwargs)


class ObservationItemForm(ModelForm):

    class Meta:
        model = ItemObservations
        fields = ['observation']
        labels = {
            'obsveration': ('Observação'),
        }
        widgets = {
            'observation': Textarea(attrs={
                'class': 'textarea',
                'placeholder': 'Inserir observacoes'
            })
        }

    def __init__(self, *args, **kwargs):
        super(ObservationItemForm, self).__init__(*args, **kwargs)


class MenuOfferForm(ModelForm):

    class Meta:
        model = MenuOffer
        fields = ['name', 'category', 'discount']
        labels = {
            'name': 'Nome da oferta',
            'category': 'Categoria',
            'discount': 'Desconto para Oferta'
        }

    def __init__(self, establishment, *args, **kwargs):
        super(MenuOfferForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = ItemCategory.objects.filter(establishment=establishment)

    def clean_discount(self):
        discount = self.data.get('discount')
        if not re.fullmatch(r'\d+([.,]\d{2})?', discount):
            raise forms.ValidationError('Desconto inválido')
        return float(discount.replace(',', '.'))


class MenuForm(ModelForm):

    class Meta:
        model = Menu
        fields = ['name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(MenuForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(MenuForm, self).save(commit=False)
        instance.establishment = self.user.manager.establishment
        instance.save()
        return instance


class MenuItemForm(ModelForm):
    preparation_time = forms.IntegerField(
        min_value=1,
        max_value=59,
        required=True,
        widget=NumberInput(attrs={
            'class': 'input',
            'placeholder': 'Ex: 40'
            })
        )
    price = forms.CharField(
        required=True,
        widget=TextInput(attrs={
            'class': 'input',
            'placeholder': 'Ex: R$ 45,90'
            })
        )

    class Meta:
        model = MenuItem
        fields = ['description', 'name', 'available',
                  'photo', 'category', 'serve_up',
                  'observations', 'offer']
        widgets = {
            'name': TextInput(attrs={
                'class': 'input',
                'placeholder': 'Ex: Macarronada Italiana '
                }),
            'description': Textarea(attrs={
                'class': 'textarea',
                'placeholder': 'Ex: Macarronada clássica feita com ingredientes italiano.'
            }),
            'serve_up': Select(choices=[(n, f'{n} pessoa'+'s'*(n>1)) for n in range(1, 11)])
        }

    def __init__(self, establishment, *args, **kwargs):
        super(MenuItemForm, self).__init__(*args, **kwargs)
        self.establishment = establishment
        self.fields['category'].queryset = ItemCategory.objects.filter(establishment=establishment)
        self.fields['observations'].queryset = ItemObservations.objects.filter(establishment=establishment)
        self.fields['offer'].queryset = MenuOffer.objects.filter(category__establishment=establishment)
        self.fields['preparation_time'].initial = getattr(self.instance.preparation_time, 'minute', 10)
        self.fields['price'].initial = self.instance.price

    def clean_preparation_time(self):
        preparation_time = self.cleaned_data.get('preparation_time', None)
        return f'00:{preparation_time}:00'

    def clean_price(self):
        price = self.data.get('price')
        if not re.fullmatch(r'\d+([.,]\d{2})?', price):
            raise forms.ValidationError('Preço inválido')
        return float(price.replace(',', '.'))

    def save(self, commit=True):
        instance = self.instance
        instance.establishment = self.establishment
        instance.menu = Menu.objects.get(establishment=self.establishment)
        instance.price = self.cleaned_data.get('price')
        instance.preparation_time = self.cleaned_data.get('preparation_time')
        return super().save(commit)


class TableZoneForm(ModelForm):

    class Meta:
        model = TableZone
        fields = ['name', 'enabled']
        labels = {
            'name': ('Nome da Zona de Mesas'),
            'enabled': ('Ativa'),
        }
        widgets = {
            'name': TextInput(attrs={
                'class': 'input',
                'placeholder': 'Ex: Área Externa'
            })
        }

    def __init__(self, *args, **kwargs):
        super(TableZoneForm, self).__init__(*args, **kwargs)


class TableForm(ModelForm):

    class Meta:
        model = Table
        fields = ['name', 'enabled', 'table_zone']
        labels = {
            'name': 'Nome da mesa',
            'enabled': 'Ativado?',
            'table_zone': 'Zona'
        }

    def __init__(self, table_zone, *args, **kwargs):
        super(TableForm, self).__init__(*args, **kwargs)
        self.fields['table_zone'].queryset = TableZone.objects.filter(
            id=table_zone.id)


class AnswerToEvaluationForm(ModelForm):

    class Meta:
        model = AnswerEvaluation
        fields = ['answer']
        labels = {
            'answer': '',
        }
        widgets = {
            'name': TextInput(attrs={
                'class': 'input',
                'placeholder': 'Escreva uma resposta'
            })
        }
