from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('dialogs/all', DialogListView.as_view()),
    path('dialogs/<int:pk>', DialogRetrieveView.as_view()),
    path('dialogs/new', DialogCreateView.as_view()),
    path('messages/new', MessageCreateView.as_view())
]