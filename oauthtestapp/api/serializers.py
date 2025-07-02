from django.contrib.auth.models import User
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'full_name', 'date_joined']
        extra_kwargs = {
            'password': {'write_only': True},
            'date_joined': {'read_only': True},
        }

    def get_full_name(self, obj):
        """Return the user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for returning user profile data to frontend."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'username']
        read_only_fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'username']
    
    def get_full_name(self, obj):
        """Return the user's full name."""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username