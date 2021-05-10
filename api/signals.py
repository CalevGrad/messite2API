from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Message, Dialog
from .serializers import MessageSerializer, DialogSerializer
from django.db.models import signals
from django.dispatch import receiver


@receiver(signals.post_save, sender=Message)
def notify_new_message(sender, **kwargs):
    channel_layer = get_channel_layer()
    message = kwargs['instance']
    data = MessageSerializer(message).data
    owners = message.dialog.owners.all()

    for user in owners:
        async_to_sync(channel_layer.group_send)('user_{}'.format(user.id), {'type': 'new_message', 'data': data})


@receiver(signals.post_save, sender=Dialog)
def notify_new_dialog(sender, **kwargs):
    channel_layer = get_channel_layer()
    dialog = kwargs['instance']
    data = DialogSerializer(dialog).data
    owners = dialog.owners.all()

    for user in owners:
        async_to_sync(channel_layer.group_send)('user_{}'.format(user.id), {'type': 'new_dialog', 'data': data})
