from rest_framework import serializers
from .models import Bot, Scenario, Step

class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Step
        fields = ['id', 'scenario', 'order', 'trigger_keyword', 'payload']
        read_only_fields = ['scenario']


class ScenarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scenario
        fields = ['id', 'bot', 'name', 'description', 'is_default']


class BotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bot
        fields = ['id', 'name', 'tg_token', 'owner', 'is_active', 'gpt_model', 'system_prompt', 'max_tokens_per_req']
        read_only_fields = ['owner']
