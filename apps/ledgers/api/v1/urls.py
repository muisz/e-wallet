from rest_framework.routers import DefaultRouter

from apps.ledgers.api.v1 import views

app_name = 'apps.ledgers.api.v1'
urlpatterns = []

router = DefaultRouter()
router.register(r'(?P<ledger_id>\d+)/transactions', views.transaction_view, basename='transaction')
router.register('callbacks', views.callback_view, basename='callback')
router.register('', views.ledger_view, basename='ledger')

urlpatterns += router.urls
