from django.db import models
from django.contrib.auth import get_user_model


# model Seminar
class Seminar(models.Model):
    name = models.CharField(max_length=150, blank=True)
    capacity = models.IntegerField()
    count = models.IntegerField()
    time = models.TimeField()
    online = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# User-Seminar mapping table
class UserSeminar(models.Model):
    User = get_user_model()
    user = models.ForeignKey(User, related_name='user_seminar_table', null=True, default=None, on_delete=models.CASCADE)
    seminar = models.ForeignKey(Seminar, related_name='user_seminar_table', null=True, default=None, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dropped_at = models.DateTimeField(null=True, default=None)
    is_active = models.BooleanField(default=True)