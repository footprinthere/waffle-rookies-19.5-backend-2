from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from django.utils import timezone

from .models import Seminar, UserSeminar
from .serializers import SeminarSerializer, SeminarListSerializer


class SeminarViewSet(GenericViewSet):

    # POST /api/v1/seminar/ -> 세미나 생성
    def create(self, request):
        
        serializer = SeminarSerializer(data=request.data, context={'action' : 'create'})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # PUT /api/v1/seminar/{id}/ -> 세미나 정보 수정
    def update(self, request, pk=None):
        try:
            seminar = Seminar.objects.get(id=pk)
        except Seminar.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data='입력된 id에 해당하는 세미나가 존재하지 않습니다.')

        user = request.user
        if user.is_anonymous:
            return Response(status=status.HTTP_403_FORBIDDEN, data="먼저 로그인 하세요.")
        if not user.is_instructor:
            return Response(status=status.HTTP_403_FORBIDDEN, data="해당 세미나의 진행자만 정보를 수정할 수 있습니다.")
        for table in user.user_seminar_table.all():
            if seminar == table.seminar:
                break
        else:
            return Response(status=status.HTTP_403_FORBIDDEN, data="해당 세미나의 진행자만 정보를 수정할 수 있습니다.")

        num_active_participants = 0
        for table in seminar.user_seminar_table.all():
            user = table.user
            if user.is_participant and user.is_active:
                num_active_participants += 1
        try:
            capacity = int(request.data.get('capacity'))
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST, data="정원 입력이 잘못되었습니다.")
        except TypeError:   # None
            pass
        else:
            if capacity < num_active_participants:
                return Response(status=status.HTTP_400_BAD_REQUEST, data="정원은 현재 참여자 수보다 적을 수 없습니다.")

        serializer = SeminarSerializer(seminar, request.data, partial=True, context={'action' : 'update'})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /api/v1/seminar/{id}/ -> 세미나 정보 가져오기
    def retrieve(self, request, pk=None):
        try:
            seminar = Seminar.objects.get(id=pk)
        except Seminar.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data='입력된 id에 해당하는 세미나가 존재하지 않습니다.')
        serializer = SeminarSerializer(seminar)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /api/v1/seminar/ -> 세미나 정보 리스트 가져오기
    def list(self, request):
        name = request.query_params.get('name')
        order = request.query_params.get('order')
        if name is None:
            objects = Seminar.objects.all()
        else:
            objects = Seminar.objects.filter(name=name)
        if order == 'earliest':
            objects = objects.order_by('created_at')
        else:
            objects = objects.order_by('-created_at')

        result = []
        for seminar in objects:
            result.append(SeminarListSerializer(seminar).data)
        return Response(result, status=status.HTTP_200_OK)

    # POST /api/v1/seminar/{id}/user/ -> 세미나에 유저 등록하기
    def register_user(self, request, pk=None):

        def _get_participant_count(seminar):
            count = 0
            for table in seminar.user_seminar_table.all():
                user = table.user
                if user.is_participant and user.is_active:
                    count += 1
            return count

        # get seminar object
        try:
            seminar = Seminar.objects.get(id=pk)
        except Seminar.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data='입력된 id에 해당하는 세미나가 존재하지 않습니다.')

        role = request.data.get('role')
        if role not in ('instructor', 'participant'):
            return Response(status=status.HTTP_400_BAD_REQUEST, data='역할 정보가 잘못되었습니다.')

        # check user validity
        user = request.user
        if role == 'instructor':
            if not user.is_instructor:
                return Response(status=status.HTTP_403_FORBIDDEN, data='진행자인 유저만 세미나의 진행자로 등록할 수 있습니다.')
            for table in user.user_seminar_table.all():
                if table.seminar:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data='이미 담당하고 있는 세미나가 있습니다.')

        if role == 'participant':
            if not user.is_participant:
                return Response(status=status.HTTP_403_FORBIDDEN, data='참여자인 유저만 세미나의 참여자로 등록할 수 있습니다.')
            if not user.participant.accepted:
                return Response(status=status.HTTP_403_FORBIDDEN, data='세미나 참여 자격이 없습니다.')
            for table in user.user_seminar_table.all():
                if seminar == table.seminar:
                    if table.is_active:
                        return Response(status=status.HTTP_400_BAD_REQUEST, data='이미 참여하고 있는 세미나입니다.')
                    else:
                        return Response(status=status.HTTP_400_BAD_REQUEST, data='포기한 세미나에는 다시 참여할 수 없습니다.')
            participant_count = _get_participant_count(seminar)
            if participant_count >= seminar.capacity:
                return Response(status=status.HTTP_400_BAD_REQUEST, data='세미나 정원이 초과되어 등록할 수 없습니다.')

        # connect user to seminar
        table = UserSeminar(user=user, seminar=seminar)
        table.save()

        return Response(SeminarSerializer(seminar).data, status=status.HTTP_201_CREATED)

    # DELETE /api/v1/seminar/{id}/user/ -> 세미나 유저 등록 해제하기
    def unregister_user(self, request, pk=None):

        # get seminar object
        try:
            seminar = Seminar.objects.get(id=pk)
        except Seminar.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data='입력된 id에 해당하는 세미나가 존재하지 않습니다.')

        print("after getting an object")
        
        # get user-seminar table
        user = request.user
        if not user.is_participant:
            return Response(status=status.HTTP_403_FORBIDDEN, data='세미나의 참여자만 참여를 포기할 수 있습니다.')
        try:
            table = UserSeminar.objects.get(user=user, seminar=seminar)
        except UserSeminar.DoesNotExist:    # not registered
            return Response(SeminarSerializer(seminar).data, status=status.HTTP_200_OK)

        # deactivate table
        table.is_active = False
        table.dropped_at = timezone.now()
        table.save()
        return Response(SeminarSerializer(seminar).data, status=status.HTTP_200_OK)

    # 세미나 등록/해제 동작 url mapping
    @action(methods=['POST', 'DELETE'], detail=True)
    def user(self, request, pk=None):
        if request.method == 'POST':
            return self.register_user(request, pk)
        elif request.method == 'DELETE':
            return self.unregister_user(request, pk)