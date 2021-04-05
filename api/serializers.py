from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from rest_framework import serializers
from api.models import Message, Dialog
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    id = serializers.ModelField(model_field=User._meta.get_field('id'))

    class Meta:
        model = User
        fields = ('id', 'username',)
        extra_kwargs = {'username': {'required': False}}


class MessageSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    dialog = 'DialogForMessageSerializer'

    class Meta:
        model = Message
        fields = ('id', 'owner', 'dialog', 'text', 'date_create')

    def create(self, validated_data):
        text = validated_data.get('text', None)
        dialog = validated_data.get('dialog', None)

        if text is None or text == '':
            raise serializers.ValidationError('Отсутствуют необходимые параметры!')

        if self.user not in dialog.owners.all():
            raise PermissionDenied

        message = Message()
        message.owner = self.user
        message.dialog = dialog
        message.text = text
        message.save()

        dialog.last_message = message
        dialog.save()

        return message

    def __init__(self, instance=None, data=serializers.empty, user=None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.user = user


class LastMessageSerializer(serializers.ModelSerializer):
    owner = UserSerializer()

    class Meta:
        model = Message
        fields = ('id', 'owner', 'text', 'date_create')


class DialogSerializer(serializers.ModelSerializer):
    owners = UserSerializer(many=True)
    last_message = LastMessageSerializer(read_only=True)
    # last_message = serializers.SerializerMethodField()

    class Meta:
        model = Dialog
        fields = ('id', 'owners', 'last_message')

    def create(self, validated_data):
        owners = validated_data.get('owners', None)

        if owners is None:
            raise serializers.ValidationError('Вы не задали владельцев диалога!')

        if len(owners) != 2:
            raise serializers.ValidationError('Участников диалога должно быть два!')

        try:
            user1 = User.objects.get(id=owners[0]['id'])
            user2 = User.objects.get(id=owners[1]['id'])
        except ObjectDoesNotExist:
            raise serializers.ValidationError('Указанных пользователя(-ей) не существует!')

        if user1 != self.user and user2 != self.user:
            raise serializers.ValidationError('Вы не можете создать не свой диалог!')

        if Dialog.objects.filter(owners=user1).filter(owners=user2).exists():
            raise serializers.ValidationError('Такой диалог уже существует!')

        dialog = Dialog()
        dialog.save()
        dialog.owners.add(user1)
        dialog.owners.add(user2)
        dialog.save()

        return dialog

    # @staticmethod
    # def get_last_message(obj):
    #     messages = obj.messages.order_by('-id').first()
    #     if messages is None:
    #         return None
    #     return LastMessageSerializer(messages).data

    def __init__(self, instance=None, data=serializers.empty, user=None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.user = user


class DialogForMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dialog
        fields = ('id',)
