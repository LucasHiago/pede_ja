from noruh_backend.settings import (
    PUSHER_APP_ID,
    PUSHER_KEY,
    PUSHER_SECRET,
    PUSHER_CLUSTER,
    PUSHER_SSL
)
import pusher


class PusherNotification():
    pusher_client = pusher.Pusher(
        app_id=PUSHER_APP_ID,
        key=PUSHER_KEY,
        secret=PUSHER_SECRET,
        cluster=PUSHER_CLUSTER,
        ssl=PUSHER_SSL,
    )

    @classmethod
    def send_notifications(self, ids, channel, event, data):
        for id in ids:
            self.pusher_client.trigger(f'{channel}-{id}', event, data)
