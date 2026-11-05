"""Entrada das rotas do acesso. Só formato; as regras de negócio ficam no service."""

from rest_framework import serializers


class EntrarSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=254)
    senha = serializers.CharField(max_length=128, trim_whitespace=False)


class PerfilSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=60, required=False)
    cor = serializers.CharField(max_length=7, required=False)


class SenhaSerializer(serializers.Serializer):
    senha_atual = serializers.CharField(max_length=128, trim_whitespace=False)
    senha_nova = serializers.CharField(max_length=128, trim_whitespace=False)


class AceitarConviteSerializer(serializers.Serializer):
    # `codigo` aceita vazio e longo para virar a resposta única de convite inválido, não um 422 que diferencie.
    codigo = serializers.CharField(max_length=500, allow_blank=True)
    nome = serializers.CharField(max_length=60)
    email = serializers.CharField(max_length=254)
    senha = serializers.CharField(max_length=128, trim_whitespace=False)
    cor = serializers.CharField(max_length=7)
