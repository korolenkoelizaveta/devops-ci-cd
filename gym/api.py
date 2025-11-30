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
        
    @action(detail=False, url_path="info", methods=["GET"])
    def info(self, request, *args, **kwargs):
        auth_user = request.user

        # базовая инфа из auth.User
        data = {
            "is_authenticated": auth_user.is_authenticated,
            "is_superuser": auth_user.is_superuser,
            "username": auth_user.username,
        }

        # пробуем найти "доменного" пользователя (gym.User), связанного через account
        try:
            domain_user = User.objects.get(account=auth_user)
            role = domain_user.role
        except User.DoesNotExist:
            domain_user = None
            role = None

        is_admin_role = role == User.Role.ADMIN
        is_admin = auth_user.is_superuser or is_admin_role

        data.update({
            "role": role,
            "is_admin": is_admin,
        })

        return Response(data)

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
        totp = pyotp.TOTP("JBSWY3DPEHPK3PXP")

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
        request_user = self.request.user

        # пытаемся найти "доменного" юзера (для роли admin тоже)
        current = None
        try:
            current = User.objects.get(account=request_user)
        except User.DoesNotExist:
            current = None

        # флаг: считаем ли этого юзера администратором системы
        is_admin_role = current and current.role == User.Role.ADMIN
        is_admin = request_user.is_superuser or is_admin_role

        # 🔹 1. Админ (любой) видит всех клиентов и тренеров, но не админов
        if is_admin:
            qs = qs.exclude(role=User.Role.ADMIN)
            role_param = self.request.query_params.get("role")
            if role_param in ("client", "trainer"):
                qs = qs.filter(role=role_param)
            return qs

        # 🔹 2. Обычный пользователь: client / trainer

        if current is None:
            return User.objects.none()

        # КЛИЕНТ: видит себя и всех тренеров
        if current.role == User.Role.CLIENT:
            return qs.exclude(role=User.Role.ADMIN).filter(
                Q(id=current.id) | Q(role=User.Role.TRAINER)
            )

        # ТРЕНЕР: видит себя и своих клиентов
        if current.role == User.Role.TRAINER:
            client_ids = (
                WorkoutSession.objects
                .filter(trainer=current)
                .values_list("client_id", flat=True)
                .distinct()
            )
            return qs.exclude(role=User.Role.ADMIN).filter(
                Q(id=current.id) | Q(id__in=client_ids)
            )

        return User.objects.none()

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
        request_user = request.user

        # пробуем найти доменного юзера
        current = None
        try:
            current = User.objects.get(account=request_user)
        except User.DoesNotExist:
            current = None

        is_admin_role = current and current.role == User.Role.ADMIN
        is_admin = request_user.is_superuser or is_admin_role

        # 🔹 1. АДМИН — старая глобальная статистика
        if is_admin:
            stats = User.objects.aggregate(
                count=Count("*"),
                clients=Count("id", filter=Q(role=User.Role.CLIENT)),
                trainers=Count("id", filter=Q(role=User.Role.TRAINER)),
                min_id=Min("id"),
                max_id=Max("id"),
                avg_id=Avg("id"),
            )
            serializer = self.StatsSerializer(instance=stats)
            return Response(serializer.data)

        # если доменного пользователя не нашли — пусто
        if current is None:
            stats = {
                "count": 0,
                "clients": 0,
                "trainers": 0,
                "min_id": None,
                "max_id": None,
                "avg_id": None,
            }
            return Response(self.StatsSerializer(instance=stats).data)

        # 🔹 2. КЛИЕНТ: считаем количество тренеров
        if current.role == User.Role.CLIENT:
            # можно брать из get_queryset, чтобы совпадало с тем, что он видит
            qs = self.get_queryset()
            trainers_cnt = qs.filter(role=User.Role.TRAINER).count()
            stats = {
                "count": trainers_cnt,   # всего "интересных" записей
                "clients": 0,
                "trainers": trainers_cnt,
                "min_id": None,
                "max_id": None,
                "avg_id": None,
            }
            return Response(self.StatsSerializer(instance=stats).data)

        # 🔹 3. ТРЕНЕР: считаем количество его клиентов
        if current.role == User.Role.TRAINER:
            client_ids = (
                WorkoutSession.objects
                .filter(trainer=current)
                .values_list("client_id", flat=True)
                .distinct()
            )
            clients_cnt = len(list(client_ids))
            stats = {
                "count": clients_cnt,
                "clients": clients_cnt,
                "trainers": 0,
                "min_id": None,
                "max_id": None,
                "avg_id": None,
            }
            return Response(self.StatsSerializer(instance=stats).data)

        # на всякий случай
        stats = {
            "count": 0,
            "clients": 0,
            "trainers": 0,
            "min_id": None,
            "max_id": None,
            "avg_id": None,
        }
        return Response(self.StatsSerializer(instance=stats).data)


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
        id = serializers.IntegerField()
        type = serializers.CharField()
        users_count = serializers.IntegerField()

    @action(detail=False, methods=["GET"], url_path="stats")
    def get_stats(self, request, *args, **kwargs):
        # для каждого типа считаем количество уникальных клиентов
        qs = (
            MembershipType.objects
            .annotate(users_count=Count("membership__client", distinct=True))
            .values("id", "type", "users_count")
        )
        serializer = self.StatsSerializer(instance=qs, many=True)
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
        request_user = self.request.user

        # пробуем найти доменного юзера
        current = None
        try:
            current = User.objects.get(account=request_user)
        except User.DoesNotExist:
            current = None

        is_admin_role = current and current.role == User.Role.ADMIN
        is_admin = request_user.is_superuser or is_admin_role

        # 🔹 админ — видит все абонементы
        if is_admin:
            owner_id = self.request.query_params.get("owner")
            if owner_id:
                qs = qs.filter(owner_id=owner_id)
            return qs

        if current is None:
            return Membership.objects.none()

        if current.role == User.Role.CLIENT:
            # клиент — только свои абонементы
            return qs.filter(client=current)

        if current.role == User.Role.TRAINER:
            # тренер — абонементы своих клиентов
            client_ids = (
                WorkoutSession.objects
                .filter(trainer=current)
                .values_list("client_id", flat=True)
                .distinct()
            )
            return qs.filter(client_id__in=client_ids)

        return Membership.objects.none()
    
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

    def get_queryset(self):
        qs = super().get_queryset()
        request_user = self.request.user

        current = None
        try:
            current = User.objects.get(account=request_user)
        except User.DoesNotExist:
            current = None

        is_admin_role = current and current.role == User.Role.ADMIN
        is_admin = request_user.is_superuser or is_admin_role

        # 🔹 админ видит все тренировки
        if is_admin:
            return qs

        if current is None:
            return WorkoutSession.objects.none()

        if current.role == User.Role.CLIENT:
            return qs.filter(client=current)

        if current.role == User.Role.TRAINER:
            return qs.filter(trainer=current)

        return WorkoutSession.objects.none()

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
        request_user = request.user

        # пробуем найти доменного gym.User
        current = None
        try:
            current = User.objects.get(account=request_user)
        except User.DoesNotExist:
            current = None

        is_admin_role = current and current.role == User.Role.ADMIN
        is_admin = request_user.is_superuser or is_admin_role

        now = timezone.now()
        week_ago = now - timedelta(days=7)

        # 🔹 1. АДМИН — старая глобальная статистика
        if is_admin:
            qs = WorkoutSession.objects.all()
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

            top_trainer = (
                qs.values("trainer", "trainer__name")
                  .annotate(cnt=Count("id"))
                  .order_by("-cnt")
                  .first()
            )
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
            return Response(self.StatsSerializer(instance=stats).data)

        # если доменного пользователя нет — всё нули
        if current is None:
            stats = {
                "total": 0,
                "last_7_days": 0,
                "upcoming": 0,
                "avg_per_client": 0.0,
                "top_trainer_name": None,
                "top_trainer_sessions": None,
                "top_client_name": None,
                "top_client_sessions": None,
            }
            return Response(self.StatsSerializer(instance=stats).data)

        # 🔹 2. КЛИЕНТ: считаем его тренировки и самого частого тренера
        if current.role == User.Role.CLIENT:
            qs = WorkoutSession.objects.filter(client=current)

            base = qs.aggregate(
                total=Count("*"),
                last_7_days=Count(
                    "id",
                    filter=Q(session_date__gte=week_ago, session_date__lte=now),
                ),
                upcoming=Count("id", filter=Q(session_date__gt=now)),
            )

            total = base["total"] or 0

            # тренер, с которым чаще всего занимается
            top_trainer = (
                qs.values("trainer", "trainer__name")
                  .annotate(cnt=Count("id"))
                  .order_by("-cnt")
                  .first()
            )

            stats = {
                "total": total,                       # всего его тренировок
                "last_7_days": base["last_7_days"] or 0,
                "upcoming": base["upcoming"] or 0,
                "avg_per_client": 0.0,               # для клиента не имеет смысла
                "top_trainer_name": top_trainer["trainer__name"] if top_trainer else None,
                "top_trainer_sessions": top_trainer["cnt"] if top_trainer else None,
                "top_client_name": None,
                "top_client_sessions": None,
            }
            return Response(self.StatsSerializer(instance=stats).data)

        # 🔹 3. ТРЕНЕР: считаем его тренировки и самого активного клиента
        if current.role == User.Role.TRAINER:
            qs = WorkoutSession.objects.filter(trainer=current)

            base = qs.aggregate(
                total=Count("*"),
                last_7_days=Count(
                    "id",
                    filter=Q(session_date__gte=week_ago, session_date__lte=now),
                ),
                upcoming=Count("id", filter=Q(session_date__gt=now)),
                distinct_clients=Count("client", distinct=True),
            )

            total = base["total"] or 0
            distinct_clients = base["distinct_clients"] or 0
            avg_per_client = float(total) / distinct_clients if distinct_clients > 0 else 0.0

            # самый активный клиент
            top_client = (
                qs.values("client", "client__name")
                  .annotate(cnt=Count("id"))
                  .order_by("-cnt")
                  .first()
            )

            stats = {
                "total": total,                      # всего проведённых тренировок
                "last_7_days": base["last_7_days"] or 0,
                "upcoming": base["upcoming"] or 0,
                "avg_per_client": avg_per_client,
                "top_trainer_name": None,
                "top_trainer_sessions": None,
                "top_client_name": top_client["client__name"] if top_client else None,
                "top_client_sessions": top_client["cnt"] if top_client else None,
            }
            return Response(self.StatsSerializer(instance=stats).data)

        # на всякий случай — нули
        stats = {
            "total": 0,
            "last_7_days": 0,
            "upcoming": 0,
            "avg_per_client": 0.0,
            "top_trainer_name": None,
            "top_trainer_sessions": None,
            "top_client_name": None,
            "top_client_sessions": None,
        }
        return Response(self.StatsSerializer(instance=stats).data)
    


    #получить ключ
    #python
    #import pyotp
    #print(pyotp.TOTP("JBSWY3DPEHPK3PXP").now())
    #http://localhost:8000/api/user-profile/otp-status/
