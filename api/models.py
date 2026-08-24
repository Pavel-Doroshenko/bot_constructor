from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Bot(models.Model):
    """Конфигурация ИИ-бота."""
    name = models.CharField(max_length=255, verbose_name="Имя бота")
    tg_token = models.CharField(max_length=255, unique=True, verbose_name="Токен Telegram")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bots', verbose_name="Владелец", null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    # Дефолтные настройки GPT
    gpt_model = models.CharField(max_length=50, default="gpt-4o-mini", verbose_name="Модель GPT")
    system_prompt = models.TextField(default="Ты полезный ИИ-ассистент.", verbose_name="Системный промпт")
    max_tokens_per_req = models.PositiveIntegerField(default=500, verbose_name="Лимит токенов на ответ")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Scenario(models.Model):
    """Сценарий диалога."""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='scenarios', verbose_name="Бот")
    name = models.CharField(max_length=255, verbose_name="Название сценария")
    description = models.TextField(blank=True, verbose_name="Описание")
    is_default = models.BooleanField(default=False, verbose_name="По умолчанию")

    def __str__(self):
        return f"{self.name} ({self.bot.name})"


class Step(models.Model):
    """Шаг внутри сценария с JSON-логикой."""
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='steps', verbose_name="Сценарий")
    order = models.PositiveIntegerField(verbose_name="Порядок выполнения")
    trigger_keyword = models.CharField(max_length=255, blank=True, verbose_name="Ключевое слово (триггер)")
    payload = models.JSONField(verbose_name="Данные шага (JSON)", help_text="Пример: {'bot_action': 'gpt_generation', 'custom_prompt': '...'}")

    class Meta:
        ordering = ['order']
        unique_together = ('scenario', 'order')

    def __str__(self):
        return f"Шаг {self.order} -> {self.scenario.name}"


class ChatHistory(models.Model):
    """История реплик для сохранения контекста ИИ."""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE, related_name='chats')
    tg_chat_id = models.CharField(max_length=100, verbose_name="ID чата Telegram")
    role = models.CharField(max_length=20, verbose_name="Роль (system/user/assistant)")
    content = models.TextField(verbose_name="Текст")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']


class UserBotState(models.Model):
    """Текущее состояние (шаг сценария) конкретного пользователя в боте."""
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    tg_chat_id = models.CharField(max_length=100)
    current_step = models.ForeignKey(Step, on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('bot', 'tg_chat_id')
