import os
from openai import OpenAI
from ..models import Bot, ChatHistory

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_gpt_response(bot: Bot, tg_chat_id: str, user_message: str, override_prompt: str = None) -> str:
    """
    Отправляет запрос к ChatCompletions с сохранением истории сообщений в БД.
    """
    # Сохраняем сообщение пользователя
    ChatHistory.objects.create(bot=bot, tg_chat_id=tg_chat_id, role="user", content=user_message)
    
    # Базовый системный промпт
    system_prompt = override_prompt if override_prompt else bot.system_prompt
    messages = [{"role": "system", "content": system_prompt}]
    
    # Извлекаем последние 10 сообщений для экономии токенов и удержания контекста
    history_qs = ChatHistory.objects.filter(bot=bot, tg_chat_id=tg_chat_id).order_by('timestamp')[:10]
    for msg in history_qs:
        messages.append({"role": msg.role, "content": msg.content})
        
    try:
        response = client.chat.completions.create(
            model=bot.gpt_model,
            messages=messages,
            max_tokens=bot.max_tokens_per_req,
            temperature=0.7
        )
        
        gpt_text = response.choices[0].message.content
        
        # Сохраняем ответ ИИ
        ChatHistory.objects.create(bot=bot, tg_chat_id=tg_chat_id, role="assistant", content=gpt_text)
        return gpt_text

    except Exception as e:
        print(f"OpenAI Error: {e}")
        return "Извините, возникла ошибка ИИ при обработке вашего сообщения."
