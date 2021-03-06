import bleach

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Count
from rest_framework import serializers
from api.models import Message, Dialog, Event
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    # id = serializers.ModelField(model_field=User._meta.get_field('id'))

    class Meta:
        model = User
        fields = ('id', 'username',)
        extra_kwargs = {'username': {'required': False}}


class MessageSerializer(serializers.ModelSerializer):
    # owner = UserSerializer(read_only=True)
    # dialog = 'DialogForMessageSerializer'

    class Meta:
        model = Message
        fields = ('id', 'owner', 'dialog', 'text', 'date_create')
        extra_kwargs = {'owner': {'read_only': True}}

    def create(self, validated_data):
        text = validated_data.get('text', None)
        dialog = validated_data.get('dialog', None)

        if text is None or text == '':
            raise serializers.ValidationError('Отсутствуют необходимые параметры!')

        owners = dialog.owners.all()

        if self.user not in owners:
            raise PermissionDenied

        message = Message()
        message.owner = self.user
        message.dialog = dialog
        message.text = text
        message.save()

        dialog.last_message = message
        dialog.save()

        send_event('new_message', owners, MessageSerializer(message).data)

        return message

    def __init__(self, instance=None, data=serializers.empty, user=None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.user = user


# class LastMessageSerializer(serializers.ModelSerializer):
#     # owner = UserSerializer()
#
#     class Meta:
#         model = Message
#         fields = ('id', 'owner', 'text', 'date_create')


class DialogSerializer(serializers.ModelSerializer):
    # owners = UserSerializer(many=True)
    last_message = MessageSerializer(read_only=True)

    # last_message = serializers.SerializerMethodField()

    class Meta:
        model = Dialog
        fields = ('id', 'owners', 'last_message')
        extra_kwargs = {'owners': {'many': True}}

    def create(self, validated_data):
        owners = validated_data.get('owners', None)

        if owners is None:
            raise serializers.ValidationError('Вы не задали владельцев диалога!')

        if len(owners) != 2:
            raise serializers.ValidationError('Участников диалога должно быть два!')

        user1 = owners[0]
        user2 = owners[1]

        if user1 != self.user and user2 != self.user:
            raise serializers.ValidationError('Вы не можете создать не свой диалог!')

        if user1 == user2:
            if Dialog.objects.annotate(owners_count=Count('owners')).filter(owners_count=1, owners=user1).exists():
                raise serializers.ValidationError('Такой диалог уже существует!')
        elif Dialog.objects.filter(owners=user1).filter(owners=user2).exists():
            raise serializers.ValidationError('Такой диалог уже существует!')

        dialog = Dialog()
        dialog.save()
        dialog.owners.add(user1)

        if user1 != user2:
            dialog.owners.add(user2)

        message = Message(text=self.message, owner=self.user, dialog=dialog)
        message.save()
        dialog.last_message = message

        dialog.save()

        send_event('new_dialog', owners, DialogSerializer(dialog).data)

        return dialog

    # @staticmethod
    # def get_last_message(obj):
    #     messages = obj.messages.order_by('-id').first()
    #     if messages is None:
    #         return None
    #     return LastMessageSerializer(messages).data

    def __init__(self, instance=None, data=serializers.empty, user=None, message=None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.user = user
        self.message = message


# class DialogForMessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Dialog
#         fields = ('id',)


# class CurrentUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('id', 'username')


class EventSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ('id', 'type', 'data')

    def get_data(self, obj):
        if obj.type == 'new_dialog':
            return DialogSerializer(Dialog.objects.get(id=obj.object_id)).data
        if obj.type == 'new_message':
            return MessageSerializer(Message.objects.get(id=obj.object_id)).data


def create_event(type, owners, object_id):
    """
    Создаёт событие
    """
    event = Event()
    event.type = type
    event.object_id = object_id
    event.save()
    for owner in owners:
        event.owners.add(owner)
    event.save()
    return event


def send_event(type, owners, data):
    """
    Отсылает событие каналам
    """
    event = create_event(type, owners, data['id'])
    channel_layer = get_channel_layer()
    for user in owners:
        async_to_sync(channel_layer.group_send)('user_{}'.format(user.id),
                                                {
                                                    'type': type,
                                                    'event': event.id,
                                                    'data': data
                                                })
