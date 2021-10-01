from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db import IntegrityError, transaction

from rest_framework import status, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from user.serializers import UserParticipantSerializer, UserSerializer, UserLoginSerializer, UserCreateSerializer

User = get_user_model()


# POST /api/v1/signup/ -> 회원가입
class UserSignUpView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request, *args, **kwargs):

        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                user, jwt_token = serializer.save()
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT, data='이미 존재하는 유저 이메일입니다.')

        return Response({'user': user.email, 'token': jwt_token}, status=status.HTTP_201_CREATED)


# POST /api/v1/login/ -> 로그인
class UserLoginView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):

        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']

        return Response({'success': True, 'token': token}, status=status.HTTP_200_OK)


class UserViewSet(viewsets.GenericViewSet):

    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = UserSerializer
    queryset = User.objects.all()

    # PUT /api/v1/user/me/ -> 유저 정보 수정
    def update(self, request, pk=None):

        if pk != 'me':
            return Response(status=status.HTTP_403_FORBIDDEN, data='다른 유저 정보를 수정할 수 없습니다.')

        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
    
        try:
            with transaction.atomic():
                serializer.save()
        except ValidationError:
            return Response(status=status.HTTP_409_CONFLICT, data='이미 존재하는 유저 이메일입니다.')

        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)

    # GET /api/v1/user/{pk}/
    def retrieve(self, request, pk=None):
        user = request.user if pk == 'me' else self.get_object()
        return Response(self.get_serializer(user).data)

    # POST /api/v1/user/participant/ -> 참여자로 등록
    @action(methods=['POST'], detail=False)
    def participant(self, request):

        if request.user.is_participant:
            return Response(status=status.HTTP_400_BAD_REQUEST, data='이미 참여자로 등록되어 있습니다.')
        
        serializer = UserParticipantSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_201_CREATED, data=UserSerializer(request.user).data)