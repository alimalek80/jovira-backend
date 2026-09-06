from rest_framework import serializers
from .models import CustomUser

class AdminCustomUserSerializer(serializers.ModelSerializer):
    # Admin can set an initial password for the user
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = CustomUser
        fields = (
            "id", "email", "first_name", "last_name", "phone_number",
            "role", "department", "agency", "is_active", "is_staff", "is_superuser", "password"
        )
        read_only_fields = ("id",)
        extra_kwargs = {
            'role': {'required': True, 'allow_null': False} # Role is mandatory when created by admin
        }

    def validate(self, attrs):
        role = attrs.get('role')
        agency = attrs.get('agency')

        # Rule 1: If role is AGENCY, the agency field cannot be empty
        if role == CustomUser.RoleChoices.AGENCY and not agency:
            raise serializers.ValidationError({"agency": "For an AGENCY role, selecting an agency is required."})
        
        # Rule 2: If role is not AGENCY, clear the agency field to prevent dirty data
        if role != CustomUser.RoleChoices.AGENCY and agency is not None:
            attrs['agency'] = None

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = super().create(validated_data)
        
        # Hash the password if provided by admin
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        return user


class ClientCustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "email", "first_name", "last_name", "phone_number", "role", "department", "agency", "is_active")
        # Client users must not be able to update their role or agency
        read_only_fields = ("id", "role", "department", "agency", "is_active")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ("id", "email", "first_name", "last_name", "phone_number", "password", "password2")
        read_only_fields = ("id",)

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        
        # Security: Default role for public registration is always NORMAL
        validated_data["role"] = CustomUser.RoleChoices.NORMAL
        validated_data["agency"] = None
        
        return CustomUser.objects.create_user(password=password, **validated_data)