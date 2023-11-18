from rest_framework.routers import DefaultRouter

from apps.users.api.v1 import views


app_name = 'apps.users.api.v1'
urlpatterns = []

router = DefaultRouter()
router.register('auth', views.auth_view, basename='auth')

urlpatterns += router.urls
