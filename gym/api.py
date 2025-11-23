from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, filters

from gym.models import User, MembershipType, Membership, WorkoutSession
from gym.serializers import (
    UserSerializer,
    MembershipTypeSerializer,
    MembershipSerializer,
    WorkoutSessionSerializer,
)


class UsersViewset(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "phone", "specialization", "role"]
    ordering_fields = ["name", "role"]
    ordering = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        role = self.request.query_params.get("role")
        if role in ("client", "trainer"):
            qs = qs.filter(role=role)
        return qs


class MembershipTypesViewset(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = MembershipType.objects.all()
    serializer_class = MembershipTypeSerializer


class MembershipsViewset(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = (
        Membership.objects
        .select_related("client", "membership_type")
        .all()
    )
    serializer_class = MembershipSerializer


class WorkoutSessionsViewset(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = (
        WorkoutSession.objects
        .select_related("client", "trainer")
        .all()
    )
    serializer_class = WorkoutSessionSerializer
