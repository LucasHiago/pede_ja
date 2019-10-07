import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from decouple import config


class NoruhFireStore():
    # Use the application default credentials
    cred = credentials.Certificate(
        config('FIRE_STORE_CREDENTIALS_PATH', default=''))
    firebase_admin.initialize_app(cred)

    db = firestore.client()

    def add_data_on_collection(self, data):
        self.db.collection(u'notifications').add(data)
