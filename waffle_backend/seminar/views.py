from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from django.utils import timezone

from .models import Seminar, UserSeminar
from .serializers import SeminarSerializer, SeminarListSerializer
from seminar.services import SeminarListService, SeminarRegisterService, SeminarUnregisterService, SeminarUpdateService


class SeminarViewSet(GenericViewSet):

    serializer_class = SeminarSerializer
    queryset = Seminar.objects.all()

    # POST /api/v1/seminar/ -> 세미나 생성
    def create(self, request):
        
        serializer = SeminarSerializer(data=request.data, context={'request' : request, 'action' : 'create'})
        status_code, response_data = serializer.execute_create()
        return Response(status=status_code, data=response_data)

    # PUT /api/v1/seminar/{id}/ -> 세미나 정보 수정
    def update(self, request, pk=None):
        service = SeminarUpdateService(request, pk)
        status_code, response_data = service.execute()
        return Response(status=status_code, data=response_data)

    # GET /api/v1/seminar/{id}/ -> 세미나 정보 가져오기
    def retrieve(self, request, pk=None):
        try:
            seminar = Seminar.objects.get(id=pk)
        except Seminar.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data='입력된 id에 해당하는 세미나가 존재하지 않습니다.')
        serializer = self.get_serializer(seminar)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # GET /api/v1/seminar/ -> 세미나 정보 리스트 가져오기
    def list(self, request):
        service = SeminarListService(request)
        status_code, response_data = service.execute()
        return Response(status=status_code, data=response_data)
        
    # POST /api/v1/seminar/{id}/user/ -> 세미나에 유저 등록하기
    def register_user(self, request, pk=None):
        service = SeminarRegisterService(data=request.data, context={'request': request, 'pk': pk})
        status_code, response_body = service.execute()
        return Response(status=status_code, data=response_body)

    # DELETE /api/v1/seminar/{id}/user/ -> 세미나 유저 등록 해제하기
    def unregister_user(self, request, pk=None):
        service = SeminarUnregisterService(request, pk)
        status_code, response_body = service.execute()
        return Response(status=status_code, data=response_body)

    # 세미나 등록/해제 동작 url mapping
    @action(methods=['POST', 'DELETE'], detail=True)
    def user(self, request, pk=None):
        if request.method == 'POST':
            return self.register_user(request, pk)
        elif request.method == 'DELETE':
            return self.unregister_user(request, pk)