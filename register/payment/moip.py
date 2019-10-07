
import requests

from rest_framework.renderers import JSONRenderer


class MoipAPP(object):
    def __init__(self, token, key):
        self.base_url = 'https://sandbox.moip.com.br'
        self.token = token
        self.key = key

    def get(self, url, parameters=None):
        response = requests.get(
            '{0}/{1}'.format(self.base_url, url),
            params=parameters,
            auth=(self.token, self.key)
        )
        return response.text

    def post(self, url, parameters=None):
        headers = {
            'Content-type': 'application/json; charset="UTF-8"',
        }

        response = requests.post(
            '{0}/{1}'.format(self.base_url, url),
            data=JSONRenderer().render(parameters),
            headers=headers,
            auth=(self.token, self.key)
        )
        return response.text

    def create_app(self, parameters):
        response = self.post('v2/channels', parameters=parameters)
        return response


class Moip(object):

    STATUS_IN_ANALYSIS = 'IN_ANALYSIS'
    STATUS_AUTHORIZED = 'AUTHORIZED'
    STATUS_CANCELLED = 'CANCELLED'

    def __init__(self, access_token):
        self.base_url = 'https://sandbox.moip.com.br'
        self.access_token = access_token

    def get(self, url, parameters=None):
        headers = {
            'Content-type': 'application/json; charset="UTF-8"',
            'Authorization': 'Bearer ' + self.access_token
        }

        response = requests.get('{0}/{1}'.format(self.base_url, url),
                                params=parameters, headers=headers)
        return response.text

    def post(self, url, parameters=None):
        headers = {
            'Content-type': 'application/json; charset="UTF-8"',
            'Authorization': 'Bearer ' + self.access_token
        }

        response = requests.post(
            '{0}/{1}'.format(self.base_url, url),
            data=JSONRenderer().render(parameters),
            headers=headers
        )
        return response.text

    def create_wirecard(self, parameters):
        response = self.post('v2/accounts', parameters=parameters)
        return response

    def post_customer(self, parameters):
        response = self.post('v2/customers', parameters=parameters)
        return response

    def get_customer(self, customer_id):
        response = self.get('v2/customers/{0}'.format(customer_id))
        return response

    def post_credit_card(self, customer_id, parameters):
        response = self.post(
            'v2/customers/{0}/fundinginstruments'.format(customer_id),
            parameters=parameters)
        return response

    def delete_creditcard(self, creditcard_id):
        headers = {
            'Content-type': 'application/json; charset="UTF-8"',
            'Authorization': 'Bearer ' + self.access_token
        }
        response = requests.delete(
            '{0}/v2/fundinginstruments/{1}'.format(self.base_url,
                creditcard_id), headers=headers)
        return response.status_code

    def post_order(self, parameters):
        response = self.post('v2/orders', parameters=parameters)
        return response

    def get_order(self, order_id):
        response = self.get('v2/orders/{0}'.format(order_id))
        return response

    def post_payment(self, order_id, parameters):
        response = self.post(
            'v2/orders/{0}/payments'.format(order_id), parameters)
        return response

    def get_payment(self, payment_id):
        response = self.get('v2/payments/{0}'.format(payment_id))
        return response

    def capture_payment(self, payment_id):
        response = self.post('v2/payments/{0}/capture'.format(payment_id))
        return response

    def cancel_pre_authorized_payment(self, payment_id):
        response = self.post('v2/payments/{0}/void'.format(payment_id))
        return response

    def verify_account(self, account_id):
        response = self.get('v2/accounts/{0}'.format(account_id))
        return response
