from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from .models import Bot, Scenario, Step, UserBotState, ChatHistory

class BotConstructorTestCase(APITestCase):

    def setUp(self):
        # 1. Создаем тестового бота в БД
        self.bot = Bot.objects.create(
            name="Тестовый ИИ Бот",
            tg_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            gpt_model="gpt-4o-mini",
            system_prompt="Ты сердитый робот."
        )
        
        # 2. Создаем сценарий по умолчанию
        self.scenario = Scenario.objects.create(
            bot=self.bot,
            name="Приветственный сценарий",
            is_default=True
        )
        
        # 3. Создаем первый шаг с JSON-настройками генерации
        self.step = Step.objects.create(
            scenario=self.scenario,
            order=1,
            trigger_keyword="/start",
            payload={
                "bot_action": "gpt_generation",
                "custom_prompt": "Инструкция: Поприветствуй пользователя как космонавт."
            }
        )
        
        # URL нашего вебхука
        self.webhook_url = reverse('bot-webhook', kwargs={'bot_id': self.bot.id})

    @patch('api.views.get_gpt_response')  # Изолируем вызов GPT API
    @patch('telebot.TeleBot.send_message') # Изолируем отправку в Telegram
    def test_webhook_trigger_scenario_and_gpt(self, mock_send_message, mock_gpt_response):
        """Тест проверяет, что при отправке /start бот инициирует сценарий и запрашивает ответ ИИ."""
        
        # Настраиваем фейковый ответ от нашей GPT-функции
        mock_gpt_response.return_value = "Привет, Землянин! Я на орбите."
        
        # Имитируем входящий пакет от Telegram
        payload = {
            "update_id": 12345,
            "message": {
                "message_id": 55,
                "chat": {"id": "999999", "type": "private"},
                "text": "/start",
                "date": 1700000000  # Перемещено внутрь объекта message
            }
        }
        
        # Отправляем POST запрос на наш API
        response = self.client.post(self.webhook_url, payload, format='json')
        
        # Проверяем, что эндпоинт успешно ответил Telegram-серверу
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "success"})
        
        # Проверяем, что пользователю создался стейт (состояние) в БД
        user_state = UserBotState.objects.get(tg_chat_id="999999", bot=self.bot)
        self.assertEqual(user_state.current_step, self.step)
        
        # Проверяем, что функция генерации текста ИИ была вызвана
        mock_gpt_response.assert_called_once()
        
        # Проверяем, что была попытка отправить сообщение обратно в чат 999999
        mock_send_message.assert_called_with("999999", "Привет, Землянин! Я на орбите.")

