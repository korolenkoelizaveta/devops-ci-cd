from rest_framework import serializers
from gym.models import User, MembershipType, Membership, WorkoutSession

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        read_only_fields = ("owner",)
    
    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["owner"] = request.user
        return super().create(validated_data)

class MembershipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipType
        fields = "__all__"

class MembershipSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="client")
    )
    membership_type = serializers.PrimaryKeyRelatedField(
        queryset=MembershipType.objects.all()
    )

    read_only_fields = ("owner",)

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["owner"] = request.user
        return super().create(validated_data)

    class Meta:
        model = Membership
        fields = "__all__"


class WorkoutSessionSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="client")
    )
    trainer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="trainer")
    )
    read_only_fields = ("owner",)

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["owner"] = request.user
        return super().create(validated_data)

    class Meta:
        model = WorkoutSession
        fields = "__all__"
