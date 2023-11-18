from django.urls import path, include

urlpatterns = [
    path('v1/users/', include('apps.users.api.v1.urls', namespace='apps.users.api.v1')),
    path('v1/ledgers/', include('apps.ledgers.api.v1.urls', namespace='apps.ledgers.api.v1')),
]
