import telebot
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Bot, Scenario, Step, UserBotState
from .serializers import BotSerializer, ScenarioSerializer, StepSerializer
from .services.gpt_client import get_gpt_response

class BotViewSet(viewsets.ModelViewSet):
    queryset = Bot.objects.all()
    serializer_class = BotSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user if self.request.user.is_authenticated else None)


class ScenarioViewSet(viewsets.ModelViewSet):
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer

    @action(detail=True, methods=['get'])
    def steps(self, request, pk=None):
        """Обеспечивает доступ GET /scenarios/{id}/steps"""
        scenario = self.get_object()
        steps = scenario.steps.all()
        serializer = StepSerializer(steps, many=True)
        return Response(serializer.data)


class StepViewSet(viewsets.ModelViewSet):
    queryset = Step.objects.all()
    serializer_class = StepSerializer

    def get_queryset(self):
        # Фильтруем шаги в зависимости от сценария в URL
        scenario_id = self.kwargs.get('scenario_id')
        if scenario_id:
            return Step.objects.filter(scenario_id=scenario_id)
        return super().get_queryset()

    def perform_create(self, serializer):
        scenario_id = self.kwargs.get('scenario_id')
        scenario = get_object_or_404(Scenario, id=scenario_id)
        serializer.save(scenario=scenario)


@method_decorator(csrf_exempt, name='dispatch')
class TelegramWebhookView(APIView):
    """Приемщик сообщений от Telegram-ботов."""
    permission_classes = []
    authentication_classes = []

    def post(self, request, bot_id, *args, **kwargs):
        bot_obj = get_object_or_404(Bot, id=bot_id, is_active=True)
        t_bot = telebot.TeleBot(bot_obj.tg_token, threaded=False)
        
        update = telebot.types.Update.de_json(request.data)
        if not update or not update.message or not update.message.text:
            return Response({"status": "ignored"}, status=status.HTTP_200_OK)
            
        message = update.message
        chat_id = str(message.chat.id)
        user_text = message.text

        # Инициализация или получение состояния (стейта) пользователя
        user_state, created = UserBotState.objects.get_or_create(bot=bot_obj, tg_chat_id=chat_id)

        # Обработка перезапуска команды /start
        if created or user_text == "/start" or not user_state.current_step:
            default_scenario = bot_obj.scenarios.filter(is_default=True).first() or bot_obj.scenarios.first()
            if default_scenario:
                user_state.current_step = default_scenario.steps.first()
                user_state.save()

        current_step = user_state.current_step
        
        if current_step:
            payload = current_step.payload
            action_type = payload.get("bot_action", "gpt_generation")
            
            if action_type == "gpt_generation":
                # Берем кастомный промпт шага или дефолтный системный промпт бота
                step_prompt = payload.get("custom_prompt", bot_obj.system_prompt)
                reply_text = get_gpt_response(bot_obj, chat_id, user_text, override_prompt=step_prompt)
            else:
                reply_text = payload.get("static_text", "Я вас не понял.")
                
            # Переключаем стейт на следующий шаг сценария (если он есть)
            next_order = current_step.order + 1
            next_step = Step.objects.filter(scenario=current_step.scenario, order=next_order).first()
            if next_step:
                user_state.current_step = next_step
                user_state.save()
        else:
            # Свободное общение с GPT, если шаги не заданы
            reply_text = get_gpt_response(bot_obj, chat_id, user_text)

        try:
            t_bot.send_message(chat_id, reply_text)
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")

        return Response({"status": "success"}, status=status.HTTP_200_OK)
