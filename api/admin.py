from django.contrib import admin
from .models import Bot, Scenario, Step, ChatHistory, UserBotState

class StepInline(admin.TabularInline):
    model = Step
    extra = 1

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ('name', 'bot', 'is_default')
    inlines = [StepInline]

@admin.register(Bot)
class BotAdmin(admin.ModelAdmin):
    list_display = ('name', 'gpt_model', 'is_active', 'created_at')
    search_fields = ('name', 'tg_token')

admin.site.register(ChatHistory)
admin.site.register(UserBotState)
