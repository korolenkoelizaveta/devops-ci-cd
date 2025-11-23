from django.db import models
from django.conf import settings 


class User(models.Model):
    class Role(models.TextChoices):
        CLIENT = "client", "Клиент"
        TRAINER = "trainer", "Тренер"

    name = models.TextField("ФИО")
    role = models.CharField("Роль", max_length=16, choices=Role.choices)
    phone = models.TextField("Телефон", blank=True, null=True)          # для клиента
    specialization = models.TextField("Специализация", blank=True, null=True)  # для тренера
    picture = models.ImageField("Изображение", null=True, blank=True, upload_to="users")
    

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self) -> str: 
        return f"{self.name} ({self.get_role_display()})"


class MembershipType(models.Model):
    type = models.TextField("Тип абонемента")
    description = models.TextField("Описание", null=True)

    class Meta:
        verbose_name = "Тип абонемента"
        verbose_name_plural = "Типы абонементов"

    def str(self) -> str:
        return self.type


class Membership(models.Model):
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Клиент",
        limit_choices_to={"role": "client"},
        related_name="memberships",
    )
    membership_type = models.ForeignKey(
        MembershipType,
        on_delete=models.CASCADE,
        verbose_name="Тип абонемента",
    )
    is_active = models.BooleanField("Активен", default=True)

    # НОВОЕ ПОЛЕ: кто создал абонемент
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # это django.contrib.auth.models.User
        verbose_name="Пользователь (владелец записи)",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="memberships_created",
    )

    class Meta:
        verbose_name = "Абонемент"
        verbose_name_plural = "Абонементы"

    def str(self):
        return f"{self.client} – {self.membership_type}"


class WorkoutSession(models.Model):
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Клиент",
        limit_choices_to={"role": "client"},
        related_name="workout_sessions_as_client",
    )
    trainer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Тренер",
        limit_choices_to={"role": "trainer"},
        related_name="workout_sessions_as_trainer",
    )
    session_date = models.DateTimeField("Дата и время тренировки")

    class Meta:
        verbose_name = "Тренировка"
        verbose_name_plural = "Тренировки"
