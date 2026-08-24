from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BotViewSet, ScenarioViewSet, StepViewSet, TelegramWebhookView

router = DefaultRouter()
router.register(r'bots', BotViewSet, basename='bot')
router.register(r'scenarios', ScenarioViewSet, basename='scenario')

urlpatterns = [
    
    # Вложенный CRUD для шагов сценариев
    path('scenarios/<int:scenario_id>/steps/', StepViewSet.as_view({'get': 'list', 'post': 'create'}), name='scenario-steps-list'),
    path('scenarios/<int:scenario_id>/steps/<int:pk>/', StepViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='scenario-steps-detail'),

    path('', include(router.urls)),
    
    # Приемщик вебхуков
    path('bots/<int:bot_id>/webhook/', TelegramWebhookView.as_view(), name='bot-webhook'),
]
