from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Conversion

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

class ConversionInputSerializer(serializers.Serializer):
    """Serializer for accepting meter input for conversion."""
    meters = serializers.DecimalField(
        max_digits=10, 
        decimal_places=6,
        min_value=0,
        help_text="Value in meters to convert to feet"
    )

class ConversionSerializer(serializers.ModelSerializer):
    """Serializer for conversion history."""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    conversion_formula = serializers.CharField(source='conversion_formula_used', read_only=True)
    
    class Meta:
        model = Conversion
        fields = [
            'id', 
            'meters_value', 
            'feet_value', 
            'timestamp', 
            'user_name',
            'user_full_name',
            'conversion_formula',
            'ip_address'
        ]
        read_only_fields = ['id', 'timestamp', 'user_name', 'user_full_name', 'conversion_formula']
    
    def get_user_full_name(self, obj):
        """Return the user's full name."""
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username

class ConversionResponseSerializer(serializers.Serializer):
    """Serializer for conversion API response."""
    meters = serializers.DecimalField(max_digits=10, decimal_places=6)
    feet = serializers.DecimalField(max_digits=10, decimal_places=6)
    conversion_id = serializers.IntegerField()
    timestamp = serializers.DateTimeField()
    formula_used = serializers.CharField()
    message = serializers.CharField()