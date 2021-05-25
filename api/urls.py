from django.urls import path, include
from .views import *

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('dialogs/', DialogListView.as_view()),
    path('dialogs/<int:pk>/', DialogRetrieveView.as_view()),
    path('dialogs/new', DialogCreateView.as_view()),
    path('dialogs/exist', DialogExistRetrieveView.as_view()),
    path('messages/', MessageListView.as_view()),
    path('messages/<int:pk>/', MessageRetrieveView.as_view()),
    path('messages/new', MessageCreateView.as_view()),
    path('current-user/', CurrentUserRetrieveView.as_view()),
    path('search-user/', SearchUserListView.as_view()),
    path('users/', UserListView.as_view()),
    path('users/<int:pk>/', UserRetrieveView.as_view()),
]
