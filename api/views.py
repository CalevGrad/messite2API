from rest_framework import generics, permissions, status
from .serializers import *
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied


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


class DialogCreateView(generics.CreateAPIView):
    serializer_class = DialogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, user=request.user)
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
            if self.request.user.dialogs.filter(id=dialog_id).exists():
                raise PermissionDenied
            queryset = queryset.filter(dialog_id=dialog_id)
        else:
            queryset = queryset.filter(owner=self.request.user)

        if message_id is not None:
            queryset = queryset.filter(id__lte=message_id)

        if count_messages is not None:
            queryset = queryset[:count_messages]

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
