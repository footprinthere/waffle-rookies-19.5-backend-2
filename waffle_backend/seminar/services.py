from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework import status
from django.utils import timezone
from django.db import transaction

from .models import Seminar, UserSeminar
from .serializers import SeminarListSerializer, SeminarSerializer

class SeminarUpdateService:
    def __init__(self, request, pk):
        self.request = request
        self.pk = pk
        self.queryset = Seminar.objects.all()

    def validate_user(self, user, seminar):
        if not user.is_instructor:
            return status.HTTP_403_FORBIDDEN, "해당 세미나의 진행자만 정보를 수정할 수 있습니다."
        for table in user.user_seminar_table.all():
            if seminar == table.seminar:
                break
        else:
            return status.HTTP_403_FORBIDDEN, "해당 세미나의 진행자만 정보를 수정할 수 있습니다."

    def get_participant_count(self, seminar):
            count = 0
            for table in seminar.user_seminar_table.filter(user__is_active=True):
                if table.user.is_participant:
                    count += 1
            return count
    
    def execute(self):
        try:
            seminar = Seminar.objects.get(id=self.pk)
        except Seminar.DoesNotExist:
            return status.HTTP_404_NOT_FOUND, '입력된 id에 해당하는 세미나가 존재하지 않습니다.'

        user_validation = self.validate_user(self.request.user, seminar)
        if user_validation:
            return user_validation

        participant_count = self.get_participant_count(seminar)
        try:
            capacity = int(self.request.data.get('capacity'))
        except ValueError:
            return status.HTTP_400_BAD_REQUEST, "정원 입력이 잘못되었습니다."
        except TypeError:   # None
            pass
        else:
            if capacity < participant_count:
                return status.HTTP_400_BAD_REQUEST, "정원은 현재 참여자 수보다 적을 수 없습니다."

        serializer = SeminarSerializer(seminar, self.request.data, partial=True, context={'action' : 'update'})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return status.HTTP_200_OK, serializer.data


class SeminarListService:
    def __init__(self, request):
        self.query_params = request.query_params
        self.queryset = Seminar.objects.all()

    def execute(self):
        name = self.query_params.get('name')
        order = self.query_params.get('order')

        if name is None:
            objects = self.queryset
        else:
            objects = self.queryset.filter(name=name)

        if order == 'earliest':
            objects = objects.order_by('created_at')
        else:
            objects = objects.order_by('-created_at')

        result = []
        for seminar in objects:
            result.append(SeminarListSerializer(seminar).data)
        return status.HTTP_200_OK, result


class SeminarRegisterService(serializers.Serializer):

    role = serializers.CharField(required=True)

    def _get_participant_count(self, seminar : Seminar):
            count = 0
            for table in seminar.user_seminar_table.filter(user__is_active=True):
                if table.user.is_participant:
                    count += 1
            return count

    def validate_role(self, value):
        if value not in ('participant', 'instructor'):
            raise ValidationError
        return value
    
    def execute(self):
        # check role validity
        try:
            with transaction.atomic():
                self.is_valid(raise_exception=True)
        except:
            return status.HTTP_400_BAD_REQUEST, '역할 정보가 잘못되었습니다.'

        # get seminar object
        try:
            seminar = Seminar.objects.get(id=self.context.get('pk'))
        except Seminar.DoesNotExist:
            return status.HTTP_404_NOT_FOUND, '입력된 id에 해당하는 세미나가 존재하지 않습니다.'

        # check user validity
        request = self.context.get('request')
        role = self.validated_data.get('role')
        user = request.user

        if role == 'instructor':
            if not user.is_instructor:
                return status.HTTP_403_FORBIDDEN, '진행자인 유저만 세미나의 진행자로 등록할 수 있습니다.'
            for table in user.user_seminar_table.all():
                if table.seminar:
                    return status.HTTP_400_BAD_REQUEST, '이미 담당하고 있는 세미나가 있습니다.'

        if role == 'participant':
            if not user.is_participant:
                return status.HTTP_403_FORBIDDEN, '참여자인 유저만 세미나의 참여자로 등록할 수 있습니다.'
            if not user.participant.accepted:
                return status.HTTP_403_FORBIDDEN, '세미나 참여 자격이 없습니다.'
            for table in user.user_seminar_table.all():
                if seminar == table.seminar:
                    if table.is_active:
                        return status.HTTP_400_BAD_REQUEST, '이미 참여하고 있는 세미나입니다.'
                    else:
                        return status.HTTP_400_BAD_REQUEST, '포기한 세미나에는 다시 참여할 수 없습니다.'
            participant_count = self._get_participant_count(seminar)
            if participant_count >= seminar.capacity:
                return status.HTTP_400_BAD_REQUEST, '세미나 정원이 초과되어 등록할 수 없습니다.'

        # connect user to seminar
        UserSeminar.objects.create(user=user, seminar=seminar)

        return status.HTTP_201_CREATED, SeminarSerializer(seminar).data


class SeminarUnregisterService:
    def __init__(self, request, pk):
        self.request = request
        self.pk = pk
        self.queryset = Seminar.objects.all()

    def execute(self):
        # get seminar object
        try:
            seminar = self.queryset.get(id=self.pk)
        except Seminar.DoesNotExist:
            return status.HTTP_404_NOT_FOUND, '입력된 id에 해당하는 세미나가 존재하지 않습니다.'

        # get user-seminar table
        user = self.request.user
        if not user.is_participant:
            return status.HTTP_403_FORBIDDEN, '세미나의 참여자만 참여를 포기할 수 있습니다.'
        try:
            table = UserSeminar.objects.get(user=user, seminar=seminar)
        except UserSeminar.DoesNotExist:    # not registered
            return status.HTTP_200_OK, SeminarSerializer(seminar).data

        # deactivate table
        table.is_active = False
        table.dropped_at = timezone.now()
        table.save()
        return status.HTTP_200_OK, SeminarSerializer(seminar).data
