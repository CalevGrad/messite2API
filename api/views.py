from rest_framework import generics, permissions, status
from .serializers import *
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound


class DialogListView(generics.ListAPIView):
    queryset = Dialog.objects.all()
    serializer_class = DialogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = self.request.user.dialogs.all()
        queryset = queryset.order_by("-last_message_id")
        return queryset


class DialogRetrieveView(generics.RetrieveAPIView):
    queryset = Dialog.objects.all()
    serializer_class = DialogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if self.request.user not in instance.owners.all():
            raise PermissionDenied

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class DialogExistRetrieveView(generics.RetrieveAPIView):
    queryset = Dialog.objects.all()
    serializer_class = DialogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        params = self.request.query_params

        user_id = params.get('user_id', None)

        if user_id is None:
            raise ValidationError('Введите id пользователя!')

        try:
            user = User.objects.get(id=int(user_id))
        except ObjectDoesNotExist:
            raise ValidationError('Такого пользователя не существует!')

        if self.request.user == user:
            dialog = Dialog.objects.annotate(owners_count=Count('owners')).filter(owners_count=1, owners=user).first()
        else:
            dialog = Dialog.objects.filter(owners=self.request.user).filter(owners=user).first()

        if dialog is None:
            raise NotFound

        serializer = self.get_serializer(dialog)

        return Response(serializer.data)


class DialogCreateView(generics.CreateAPIView):
    serializer_class = DialogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        message = request.data.get('first_message', None)
        if message is None:
            raise ValidationError('Отсутствует first_message!')

        serializer = self.get_serializer(data=request.data, user=request.user, message=message)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        parameters: 'message_id', 'count_messages', 'dialog_id'
        """
        queryset = Message.objects.all()

        params = self.request.query_params

        dialog_id = params.get('dialog_id', None)
        message_id = params.get('message_id', None)
        count_messages = params.get('count_messages', None)

        if dialog_id is not None:
            if not self.request.user.dialogs.filter(id=int(dialog_id)).exists():
                raise PermissionDenied
            queryset = queryset.filter(dialog_id=int(dialog_id))
        else:
            queryset = queryset.filter(owner=self.request.user)

        if message_id is not None:
            queryset = queryset.filter(id__lte=int(message_id))

        if count_messages is not None:
            queryset = queryset[:int(count_messages)]

        return queryset


class MessageCreateView(generics.CreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, user=request.user)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CurrentUserRetrieveView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def retrieve(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.request.user)
        return Response(serializer.data)


class SearchUserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        params = self.request.query_params

        username = params.get('username', None)

        if username is None:
            raise ValidationError('Введите имя пользователя!')

        return User.objects.filter(username__icontains=username)


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        params = self.request.query_params

        user_id_list = params.getlist('user_id_list[]', None)

        if user_id_list is not None:
            user_id_list = list(map(int, user_id_list))
            queryset = queryset.filter(id__in=user_id_list)

        return queryset
