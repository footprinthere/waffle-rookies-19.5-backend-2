from django.urls import path, include
from rest_framework.routers import SimpleRouter

from .views import SeminarViewSet

router = SimpleRouter()
router.register('seminar', SeminarViewSet, basename='seminar')

urlpatterns = [
    path("", include(router.urls), name='seminar')
]