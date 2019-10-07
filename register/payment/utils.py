import json
import uuid

from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework import status

from register.models import (
    UserCreditCard,
    UserPayment
)


def int_max_length(length):
    def wrapper(value):
        if len(str(value)) > length:
            raise serializers.ValidationError('The value is too long')
    return wrapper


def int_min_length(length):
    def wrapper(value):
        if len(str(value)) < length:
            raise serializers.ValidationError('The value is too short')
    return wrapper


def create_app(data):
    return {
       'name': data.get('name'),
       'description': data.get('description'),
       'site': data.get('site'),
       'redirectUri': data.get('redirect_uri')}


def create_wirecard_personal_establishment(cleaned_data):
    return {
        'email': {
            'address': cleaned_data.get('email'),
        },
        'person': {
            'name': cleaned_data.get('name'),
            'lastName': cleaned_data.get('last_name'),
            'taxDocument': {
                'type': 'CPF',
                'number': cleaned_data.get('number_cpf'),
            },
            'identityDocument': {
                'type': 'RG',
                'number': cleaned_data.get('number_rg'),
                'issuer': cleaned_data.get('issuer'),
                'issueDate': cleaned_data.get('issue_date')
            },
            'birthDate': cleaned_data.get('birth_date'),
            'phone': {
                'countryCode': cleaned_data.get('country_code'),
                'areaCode': cleaned_data.get('area_code'),
                'number': cleaned_data.get('phone_number'),
            },
            'address': {
                'street': cleaned_data.get('street'),
                'streetNumber': cleaned_data.get('street_number'),
                'district': cleaned_data.get('district'),
                'zipCode': cleaned_data.get('zip_code'),
                'city': cleaned_data.get('city'),
                'state': cleaned_data.get('state'),
                'country': 'BRA',
            }
        },
        'type': 'MERCHANT'
    }


def create_wirecard_company_establishment(cleaned_data):
    return {
        'email': {
            'address': cleaned_data.get('email'),
        },
        'person': {
            'name': cleaned_data.get('name_person'),
            'taxDocument': {
                'type': 'CPF',
                'number': cleaned_data.get('number_cpf'),
            },
            'birthDate': cleaned_data.get('birth_date'),
            'phone': {
                'countryCode': cleaned_data.get('country_code_personal'),
                'areaCode': cleaned_data.get('area_code_personal'),
                'number': cleaned_data.get('phone_number_personal'),
            },
            'address': {
                'street': cleaned_data.get('street_personal'),
                'streetNumber': cleaned_data.get('street_number_personal'),
                'district': cleaned_data.get('district_personal'),
                'zipCode': cleaned_data.get('zip_code_personal'),
                'city': cleaned_data.get('city_personal'),
                'state': cleaned_data.get('state_personal'),
                'country': 'BRA',
            }
        },
        'company': {
            'name': cleaned_data.get('name_company'),
            'businessName': cleaned_data.get('business_name'),
            'openingDate': cleaned_data.get('opening_date'),
            'taxDocument': {
                'type': 'CNPJ',
                'number': cleaned_data.get('number_cnpj'),
            },
            'mainActivity': {
                'cnae': cleaned_data.get('cnae'),
                'description': cleaned_data.get('description'),
            },
            'phone': {
                'countryCode': cleaned_data.get('country_code_company'),
                'areaCode': cleaned_data.get('area_code_company'),
                'number': cleaned_data.get('phone_number_company'),
            },
            'address': {
                'street': cleaned_data.get('street_company'),
                'streetNumber': cleaned_data.get('street_number_company'),
                'district': cleaned_data.get('district_company'),
                'zipCode': cleaned_data.get('zip_code_company'),
                'city': cleaned_data.get('city_company'),
                'state': cleaned_data.get('state_company'),
                'country': 'BRA',
            }
        },
        'businessSegment': {
            'id': 20
        },
        'site': 'https://www.noruh.com/',
        'type': 'MERCHANT',
        'tosAcceptance': {
            'acceptedAt': timezone.now().isoformat(),
            'ip': cleaned_data.get('remote_addr'),
            'userAgent': cleaned_data.get('user_agent'),
        }
    }


def create_wirecard_noruh(data):
    return {
        'email': {
            'address': data.get('email'),
        },
        'person': {
            'name': data.get('name'),
            'lastName': data.get('last_name'),
            'taxDocument': {
                'type': 'CPF',
                'number': data.get('number_cpf'),
            },
            'identityDocument': {
                'type': 'RG',
                'number': data.get('number_rg'),
                'issuer': data.get('issuer'),
                'issueDate': data.get('issue_date')
            },
            'birthDate': data.get('birth_date'),
            'phone': {
                'countryCode': data.get('country_code'),
                'areaCode': data.get('area_code'),
                'number': data.get('phone_number'),
            },
            'address': {
                'street': data.get('street'),
                'streetNumber': data.get('street_number'),
                'district': data.get('district'),
                'zipCode': data.get('zip_code'),
                'city': data.get('city'),
                'state': data.get('state'),
                'country': 'BRA',
            }
        },
        'type': 'MERCHANT'}


def create_customer_parse_moip(data):
    return {
        'ownId': data.get('own_id'),
        'fullname': data.get('full_name'),
        'email': data.get('email'),
        'birthDate': data.get('birth_date'),
        'taxDocument': {
            'type': data.get('type'),
            'number': data.get('number_document'),
        },
        'phone': {
            'countryCode': data.get('country_code'),
            'areaCode': data.get('area_code'),
            'number': data.get('phone_number'),
        },
        'shippingAddress': {
            'city': data.get('city'),
            'district': data.get('district'),
            'street': data.get('street'),
            'streetNumber': data.get('street_number'),
            'zipCode': data.get('zip_code'),
            'state': data.get('state'),
            'country': data.get('country'),
        }
    }


def create_credit_card_parse_moip(data):
    return {
        'method': 'CREDIT_CARD',
        'creditCard': {
            'expirationMonth': data.get('expiration_month'),
            'expirationYear': data.get('expiration_year'),
            'number': data.get('number_card'),
            'cvc': data.get('cvc'),
            'holder': {
                'fullname': data.get('full_name'),
                'birthdate': data.get('birth_date'),
                'taxDocument': {
                    'type': data.get('type'),
                    'number': data.get('number_document')
                },
                'phone': {
                    'countryCode': data.get('country_code'),
                    'areaCode': data.get('area_code'),
                    'number': data.get('phone_number'),
                }
            }
        }
    }


def create_order_parse_moip(data):
    return {
        'ownId': data.get('payment_uuid'),
        'amount': {
            'currency': "BRL",
        },
        'items': [
            {
                'product': "Noruh Service",
                'category': "FOOD_SERVICE",
                'quantity': 1,
                'detail': 'Nouruh - Payment by Smartphone',
                'price': data.get('value'),
            }
        ],
        'customer': {
            'id': data.get('customer_moip')
        },
        'receivers': [
            {
                'type': "PRIMARY",
                'feePayor': data.get('fee_payor_est'),
                'moipAccount': {
                    'id': data.get('id_moip_wirecard_establishment')
                },
                'amount': {
                    'fixed': data.get('value_establishment')
                }
            },
            {
                'type': "SECONDARY",
                'feePayor': data.get('fee_payor_noruh'),
                'moipAccount': {
                    'id': data.get('id_moip_wirecard_noruh')
                },
                'amount': {
                    'fixed': data.get('value_noruh_fee')
                }
            }
        ]
    }


def create_order_establishment_parse_moip(data):
    return {
        'ownId': data.get('payment_uuid'),
        'amount': {
            'currency': "BRL",
        },
        'items': [
            {
                'product': "Noruh Service",
                'category': "FOOD_SERVICE",
                'quantity': 1,
                'detail': 'Nouruh - Payment by Smartphone',
                'price': data.get('value'),
            }
        ],
        'customer': {
            'id': data.get('customer_moip')
        },
        'receivers': [
            {
                'type': "SECONDARY",
                'feePayor': True,
                'moipAccount': {
                    'id': data.get('id_moip_wirecard_establishment')
                },
                'amount': {
                    'fixed': data.get('value_establishment')
                }
            },
        ]
    }


def create_payment_parse_moip(data):
    return {
            'installmentCount': 1,
            'statementDescriptor': 'Noruh',
            'fundingInstrument': {
                'method': 'CREDIT_CARD',
                'creditCard': {
                    'id': data.get('credit_card_id'),
                    'cvc': '123',
                    'store': 'true',
                    'holder': {
                        'fullname': data.get('full_name'),
                        'birthdate': data.get('birth_date'),
                        'taxDocument': {
                            'type': data.get('type_doc'),
                            'number': data.get('number_document')},
                        'phone': {
                            'countryCode': data.get('country_code'),
                            'areaCode': data.get('area_code'),
                            'number': data.get('phone_number')}
                    }
                }
            },
            'device': {
                'ip': '',
                'geolocation': {
                    'latitude': data.get('lat'),
                    'longitude': data.get('lng')},
                'userAgent': '',
                'fingerprint': ''
            }
    }


def create_customer_on_moip(moip, data, user):
    own_id = str('Noruh_' + str(uuid.uuid4()))
    country_code = int(str(user.profile.phone_number)[:2])
    area_code = int(str(user.profile.phone_number)[2:4])
    phone_number = int(str(user.profile.phone_number)[4:13])

    data_customer = {"own_id": own_id, "full_name": data.get('full_name'),
                     "email": user.email, "type": data.get('type_document'),
                     "birth_date": data.get('birth_date'),
                     "city": data.get('city'),
                     "number_document": data.get('number_document'),
                     "country_code": country_code,
                     "area_code": area_code,
                     "phone_number": phone_number,
                     "district": data.get('district'),
                     "street": data.get('street'),
                     "street_number": data.get('street_number'),
                     "zip_code": data.get('zip_code'),
                     "state": data.get('state'),
                     "country": data.get('country')}

    parameters_customer = create_customer_parse_moip(data_customer)

    customer = moip.post_customer(parameters_customer)
    customer = json.loads(customer)

    if 'errors' in customer:
        return {'status': 400, 'response': customer}

    moip_user_id = customer['id']
    user_moip_token = customer['_links'][
        'hostedAccount']['redirectHref']
    link, token = str(user_moip_token).split("token=")
    user_moip_token = token

    user_payment = UserPayment.objects.create(
        user=user, moip_user_id=moip_user_id,
        moip_user_token=user_moip_token)
    return {'status': 200, 'user_payment': user_payment}


def create_credit_card_on_moip(moip, data, user, user_payment):
    country_code = int(str(user.profile.phone_number)[:2])
    area_code = int(str(user.profile.phone_number)[2:4])
    phone_number = int(str(user.profile.phone_number)[4:13])

    data_credit_card = {"expiration_month": data.get('expiration_month'),
                        "expiration_year": data.get('expiration_year'),
                        "number_card": data.get('number_card'),
                        "cvc": data.get('cvc'),
                        "full_name": data.get('full_name'),
                        "birth_date": data.get('birth_date'),
                        "type": data.get('type_document'),
                        "number_document": data.get('number_document'),
                        "country_code": country_code,
                        "area_code": area_code,
                        "phone_number": phone_number}

    moip_user_id = user_payment.moip_user_id
    parameters_credit_card = create_credit_card_parse_moip(data_credit_card)
    credit_card = moip.post_credit_card(moip_user_id, parameters_credit_card)
    credit_card = json.loads(credit_card)

    if 'errors' in credit_card:
        return {'status': 400, 'response': credit_card}

    last_four_digits = credit_card['creditCard']['last4']
    brand = credit_card['creditCard']['brand']
    id_card_moip = credit_card['creditCard']['id']

    UserCreditCard.objects.create(
        last_four_digits=last_four_digits, brand_card=brand,
        id_moip_card=id_card_moip, user_payment=user_payment,
        full_name=data.get('full_name'), birth_date=data.get('birth_date'),
        type_doc=data.get('type_document'),
        number_doc=data.get('number_document'))

    return {'status': 200, 'credit_card': credit_card}