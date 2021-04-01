from rest_framework import generics, permissions, status
from .serializers import *
from rest_framework.response import Response


class DialogListView(generics.ListAPIView):
    queryset = Dialog.objects.all()
    serializer_class = DialogSerializer
    permission_classes = [permissions.IsAuthenticated]


class DialogRetrieveView(generics.RetrieveAPIView):
    queryset = Dialog.objects.all()
    serializer_class = DialogSerializer
    permission_classes = [permissions.IsAuthenticated]


class DialogCreateView(generics.CreateAPIView):
    queryset = Dialog.objects.all()
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
        queryset = Message.objects.all()

        params = self.request.query_params

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
