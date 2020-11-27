from rest_framework import routers
from .views import TransactionViewSet

router = routers.DefaultRouter()
router.register('api', TransactionViewSet, 'transaction')

urlpatterns = router.urls