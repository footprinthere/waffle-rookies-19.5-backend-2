from abc import ABC

from django.core.validators import validate_email
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework_jwt.settings import api_settings

from user.models import ParticipantProfile, InstructorProfile
from seminar.serializers import ParticipantSeminarSerializer, InstructorChargeSerializer

# 토큰 사용을 위한 기본 세팅
User = get_user_model()
JWT_PAYLOAD_HANDLER = api_settings.JWT_PAYLOAD_HANDLER
JWT_ENCODE_HANDLER = api_settings.JWT_ENCODE_HANDLER


# [ user -> jwt_token ] function
def jwt_token_of(user):
    payload = JWT_PAYLOAD_HANDLER(user)
    jwt_token = JWT_ENCODE_HANDLER(payload)
    return jwt_token


# signup 작업에 관여
class UserCreateSerializer(serializers.Serializer):

    email = serializers.EmailField(required=True)
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    role = serializers.CharField(required=True, write_only=True)
    university = serializers.CharField(required=False)
    accepted = serializers.BooleanField(required=False, default=True)
    company = serializers.CharField(required=False)
    year = serializers.IntegerField(required=False)


    def validate(self, data):
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        if bool(first_name) ^ bool(last_name):
            raise serializers.ValidationError("성과 이름 중에 하나만 입력할 수 없습니다.")
        if first_name and last_name and not (first_name.isalpha() and last_name.isalpha()):
            raise serializers.ValidationError("이름에 숫자가 들어갈 수 없습니다.")
        
        role = data.get('role')
        if role not in ('participant', 'instructor'):
            raise serializers.ValidationError("역할 정보가 잘못되었습니다.")

        return data

    def create(self, validated_data):
        # TODO (1. 유저 만들고 (ORM) , 2. 비밀번호 설정하기; 아래 코드를 수정해주세요.)

        # extract field values from input data
        password = validated_data.pop('password')
        role = validated_data.pop('role')
        university = validated_data.pop('university', "")
        accepted = validated_data.pop('accepted', True)
        company = validated_data.pop('company', "")
        year = validated_data.pop('year', None)

        user = User(**validated_data)
        user.set_password(password)

        if role == 'participant':
            participant = ParticipantProfile(university=university, accepted=accepted)
            participant.save()
            user.participant = participant
        else:
            instructor = InstructorProfile(company=company, year=year)
            instructor.save()
            user.instructor = instructor
        
        user.save()
        return user, jwt_token_of(user)


class UserLoginSerializer(serializers.Serializer):

    email = serializers.CharField(max_length=64, required=True)
    password = serializers.CharField(max_length=128, write_only=True)
    token = serializers.CharField(max_length=255, read_only=True)

    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)
        user = authenticate(email=email, password=password)

        if user is None:
            raise serializers.ValidationError("이메일 또는 비밀번호가 잘못되었습니다.")

        update_last_login(None, user)
        return {
            'email': user.email,
            'token': jwt_token_of(user)
        }


class ParticipantProfileSerializer(serializers.ModelSerializer):
    seminars = serializers.SerializerMethodField()

    class Meta:
        model = ParticipantProfile
        fields = (
            'id',
            'university',
            'accepted',
            'seminars'
        )
    
    def get_seminars(self, obj):
        tables = obj.user.user_seminar_table.all()
        result = []
        for table in tables:
            result.append(ParticipantSeminarSerializer(table, context=self.context).data)
        return result


class InstructorProfileSerializer(serializers.ModelSerializer):
    charge = serializers.SerializerMethodField()

    class Meta:
        model = InstructorProfile
        fields = (
            'id',
            'company',
            'year',
            'charge'
        )
    
    def get_charge(self, obj):
        tables = obj.user.user_seminar_table.all()
        if not tables:  # if empty
            return None
        return InstructorChargeSerializer(tables[0], context=self.context).data


class UserSerializer(serializers.ModelSerializer):
    participant = serializers.SerializerMethodField()
    instructor = serializers.SerializerMethodField()
    university = serializers.CharField(write_only=True)
    company = serializers.CharField(write_only=True)
    year = serializers.IntegerField(write_only=True)

    class Meta:
        model = User
        # Django 기본 User 모델에 존재하는 필드 중 일부
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'date_joined',
            'participant',
            'instructor',

            'university',
            'company',
            'year',
        )
        extra_kwargs = {'password' : {'write_only' : True}}

    def get_participant(self, user):
        if not user.is_participant:
            return None
        return ParticipantProfileSerializer(user.participant).data
    
    def get_instructor(self, user):
        if not user.is_instructor:
            return None
        return InstructorProfileSerializer(user.instructor).data


    def validate(self, data):
        print("before validation", data, self.initial_data)

        first_name = data.get('first_name')
        last_name = data.get('last_name')
        if bool(first_name) ^ bool(last_name):
            raise serializers.ValidationError("성과 이름 중에 하나만 입력할 수 없습니다.")
        if first_name and last_name and not (first_name.isalpha() and last_name.isalpha()):
            raise serializers.ValidationError("이름에 숫자가 들어갈 수 없습니다.")
        
        year = data.get('year')
        if year is not None and year < 0:
            raise serializers.ValidationError("경력은 음수가 될 수 없습니다.")
        
        return data

    def create(self, validated_data):
        user = super().create(validated_data)
        return user

    def update(self, user, validated_data):
        print("after validation", validated_data)
        university = validated_data.pop('university', None)
        company = validated_data.pop('company', None)
        year = validated_data.pop('year', None)

        if user.is_participant:
            if university:
                user.participant.university = university
                user.participant.save()
        else:
            if company:
                user.instructor.company = company
            if year:
                user.instructor.year = year
            user.instructor.save()
        
        super().update(user, validated_data)
        return user


# participant로 등록하는 작업에 관여
class UserParticipantSerializer(serializers.Serializer):
    university = serializers.CharField(required=False)
    accepted = serializers.BooleanField(required=False, default=True)

    def update(self, user: User, validated_data):
        university = validated_data.get('university')
        university = university if university else ""
        accepted = validated_data.get('accepted')
        accepted = accepted if accepted is not None else True

        profile = ParticipantProfile(university=university, accepted=accepted)
        profile.save()
        user.participant = profile
        user.save()

        return user