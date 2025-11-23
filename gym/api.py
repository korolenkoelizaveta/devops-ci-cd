from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, BasePermission, SAFE_METHODS

from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.contrib.auth import authenticate, login
import pyotp

from gym.models import User, MembershipType, Membership, WorkoutSession
from gym.serializers import (
    UserSerializer,
    MembershipTypeSerializer,
    MembershipSerializer,
    WorkoutSessionSerializer,
)

class UserProfileViewSet(GenericViewSet):
    """
    ViewSet для проверки логина и работы с двойной аутентификацией (OTP).
    """
    permission_classes = [IsAuthenticated]

    # ---- Сериализатор для OTP-кода ----
    class OTPSerializer(serializers.Serializer):
        key = serializers.CharField()

    # ---- Пермиссия: доступ только при пройденном OTP ----
    class OTPRequired(BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            cache_key = f"otp_good:{request.user.id}"
            return bool(cache.get(cache_key, False))

    # ---- Пермиссия: OTP нужен только для редактирования ----
    class OTPForEdit(BasePermission):
        """
        GET/HEAD/OPTIONS разрешены.
        Для PUT/PATCH/DELETE требуется пройденный OTP.
        POST по желанию можно пускать без OTP — сейчас так и сделано.
        """
        def has_permission(self, request, view):
            # безопасные методы — без OTP
            if request.method in SAFE_METHODS:
                return True

            # создание (POST) сейчас тоже без OTP
            if request.method == "POST":
                return True

            if not request.user or not request.user.is_authenticated:
                return False

            cache_key = f"otp_good:{request.user.id}"
            return bool(cache.get(cache_key, False))

    # ---- просто проверка: залогинен ли юзер ----
    @action(detail=False, url_path="check-login", methods=["GET"], permission_classes=[])
    def get_check_login(self, request, *args, **kwargs):
        return Response({
            "is_authenticated": self.request.user.is_authenticated
        })

    
    @action(detail=False, url_path="login", methods=["GET"], permission_classes=[])
    def use_login(self, request, *args, **kwargs):
        user = authenticate(username="username", password="pass")
        if user:
            login(request, user)
        return Response({
            "is_authenticated": bool(user)
        })

    # ---- Ввод OTP-кода ----
    @action(detail=False, url_path="otp-login", methods=["POST"], serializer_class=OTPSerializer)
    def otp_login(self, *args, **kwargs):
        totp = totp = pyotp.TOTP("JBSWY3DPEHPK3PXP")

        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)

        success = False
        if totp.now() == serializer.validated_data["key"]:
            cache_key = f"otp_good:{self.request.user.id}"
            # время жизни 5 мин
            cache.set(cache_key, True, timeout=300)
            success = True

        return Response({
            "success": success
        })

    # ---- Статус: пройдена ли сейчас 2FA ----
    @action(detail=False, url_path="otp-status")
    def get_otp_status(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            otp_good = False
        else:
            cache_key = f"otp_good:{self.request.user.id}"
            otp_good = cache.get(cache_key, False)

        return Response({
            "otp_good": otp_good
        })

    @action(detail=False, url_path="otp-required", permission_classes=[OTPRequired])
    def page_with_otp_required(self, *args, **kwargs):
        return Response({
            "success": True
        })

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
    permission_classes = [IsAuthenticated, UserProfileViewSet.OTPForEdit]
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
    
        # ---------- СТАТИСТИКА ----------
    class StatsSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        clients = serializers.IntegerField()
        trainers = serializers.IntegerField()
        min_id = serializers.IntegerField(allow_null=True)
        max_id = serializers.IntegerField(allow_null=True)
        avg_id = serializers.FloatField(allow_null=True)

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        stats = User.objects.aggregate(
            count=Count("*"),
            clients=Count("id", filter=Q(role="client")),
            trainers=Count("id", filter=Q(role="trainer")),
            min_id=Min("id"),
            max_id=Max("id"),
            avg_id=Avg("id"),
        )
        serializer = self.StatsSerializer(instance=stats)
        return Response(serializer.data)


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

    # ----- СТАТИСТИКА -----
    class StatsSerializer(serializers.Serializer):
        count = serializers.IntegerField()

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        stats = MembershipType.objects.aggregate(
            count=Count("*"),
        )
        serializer = self.StatsSerializer(instance=stats)
        return Response(serializer.data)


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
    permission_classes = [IsAuthenticated, UserProfileViewSet.OTPForEdit]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if user.is_superuser:
            # суперюзер видит всех, но может фильтровать по owner ?owner=<id>
            owner_id = self.request.query_params.get("owner")
            if owner_id:
                qs = qs.filter(owner_id=owner_id)
        else:
            # обычный юзер видит только свои абонементы
            qs = qs.filter(owner=user)

        return qs
    
     # ----- СТАТИСТИКА -----
    class StatsSerializer(serializers.Serializer):
        count = serializers.IntegerField()
        active = serializers.IntegerField()
        inactive = serializers.IntegerField()

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        stats = Membership.objects.aggregate(
            count=Count("*"),
            active=Count("id", filter=Q(is_active=True)),
            inactive=Count("id", filter=Q(is_active=False)),
        )
        serializer = self.StatsSerializer(instance=stats)
        return Response(serializer.data)


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
    permission_classes = [IsAuthenticated, UserProfileViewSet.OTPForEdit]

     # ----- СТАТИСТИКА -----
    class StatsSerializer(serializers.Serializer):
        total = serializers.IntegerField()
        last_7_days = serializers.IntegerField()
        upcoming = serializers.IntegerField()
        avg_per_client = serializers.FloatField()
        top_trainer_name = serializers.CharField(allow_null=True)
        top_trainer_sessions = serializers.IntegerField(allow_null=True)
        top_client_name = serializers.CharField(allow_null=True)
        top_client_sessions = serializers.IntegerField(allow_null=True)

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        qs = WorkoutSession.objects.all()
        now = timezone.now() 
        week_ago = now - timedelta(days=7)

        base = qs.aggregate(
            total=Count("*"),
            last_7_days=Count(
                "id",
                filter=Q(session_date__gte=week_ago, session_date__lte=now),
            ),
            upcoming=Count(
                "id",
                filter=Q(session_date__gt=now),
            ),
            distinct_clients=Count("client", distinct=True),
        )

        total = base["total"] or 0
        distinct_clients = base["distinct_clients"] or 0
        avg_per_client = float(total) / distinct_clients if distinct_clients > 0 else 0.0

        # самый загруженный тренер
        top_trainer = (
            qs.values("trainer", "trainer__name")
              .annotate(cnt=Count("id"))
              .order_by("-cnt")
              .first()
        )
        # самый активный клиент
        top_client = (
            qs.values("client", "client__name")
              .annotate(cnt=Count("id"))
              .order_by("-cnt")
              .first()
        )

        stats = {
            "total": total,
            "last_7_days": base["last_7_days"] or 0,
            "upcoming": base["upcoming"] or 0,
            "avg_per_client": avg_per_client,
            "top_trainer_name": top_trainer["trainer__name"] if top_trainer else None,
            "top_trainer_sessions": top_trainer["cnt"] if top_trainer else None,
            "top_client_name": top_client["client__name"] if top_client else None,
            "top_client_sessions": top_client["cnt"] if top_client else None,
        }

        serializer = self.StatsSerializer(instance=stats)
        return Response(serializer.data)
    


    #получить ключ
    #python
    #import pyotp
    #print(pyotp.TOTP("JBSWY3DPEHPK3PXP").now())
    #http://localhost:8000/api/user-profile/otp-status/
