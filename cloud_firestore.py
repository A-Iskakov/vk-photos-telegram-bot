from google.cloud import firestore

from settings import TELEGRAM_BOT_USE_WEBHOOK


class FirestoreData:
    def __init__(self):

        if not TELEGRAM_BOT_USE_WEBHOOK:
            # debug
            self.db = firestore.Client.from_service_account_json('isb-2007-bot.json')
        else:
            # production
            self.db = firestore.Client()

        self.coll_ref = self.db.collection('vk_users_data')

    def get_data_from_firestore(self, telegram_user_id):

        docs = self.coll_ref.where('telegram_user_id', u'==', telegram_user_id).get()
        # print(docs)
        for doc in docs:
            return doc.to_dict()

        return False

    def add_data_from_firestore(self, telegram_user_id, vk_token, first_name=None, last_name=None,
                                telegram_username=None):

        self.coll_ref.add({'telegram_user_id': telegram_user_id,
                           'vk_token': vk_token,
                           'first_name': first_name,
                           'last_name': last_name,
                           'telegram_username': telegram_username})
