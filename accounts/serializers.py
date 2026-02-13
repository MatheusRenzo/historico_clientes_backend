from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import UserClienteMembership, UserClienteRole

User = get_user_model()


class MembershipInputSerializer(serializers.Serializer):
    cliente = serializers.IntegerField()
    role = serializers.ChoiceField(choices=UserClienteRole.choices)


class CreateUserWithMembershipsSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    nome = serializers.CharField(max_length=150, required=False, allow_blank=True)
    sobrenome = serializers.CharField(max_length=150, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)

    memberships = MembershipInputSerializer(many=True)

    def validate_username(self, value):
        v = value.strip()
        if User.objects.filter(username__iexact=v).exists():
            raise serializers.ValidationError("Username já existe.")
        return v

    def validate_email(self, value):
        v = value.strip().lower()
        if User.objects.filter(email__iexact=v).exists():
            raise serializers.ValidationError("Email já existe.")
        return v

    def create(self, validated_data):
        memberships = validated_data.pop("memberships")
        password = validated_data.pop("password")

        nome = validated_data.pop("nome", "")
        sobrenome = validated_data.pop("sobrenome", "")

        user = User.objects.create(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=nome,
            last_name=sobrenome,
            is_active=True,
        )
        user.set_password(password)
        user.save()

        UserClienteMembership.objects.bulk_create([
            UserClienteMembership(
                user=user,
                cliente_id=m["cliente"],
                role=m["role"],
                ativo=True,
            )
            for m in memberships
        ])

        return user
