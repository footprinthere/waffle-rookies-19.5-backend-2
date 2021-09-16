from django.core.exceptions import ValidationError
from rest_framework import serializers
from .models import Seminar, UserSeminar

class ParticipantSeminarSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    joined_at = serializers.SerializerMethodField()

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'name',
            'joined_at',
            'is_active',
            'dropped_at'
        )
    
    def get_id(self, table):
        return table.seminar.id
    
    def get_name(self, table):
        return table.seminar.name

    def get_joined_at(self, table):
        return table.created_at


class InstructorChargeSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    joined_at = serializers.SerializerMethodField()

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'name',
            'joined_at'
        )

    def get_id(self, table):
        return table.seminar.id
    
    def get_name(self, table):
        return table.seminar.name

    def get_joined_at(self, table):
        return table.created_at


# Seminar의 serializer response에 포함되는 instructors 부분
class SeminarInstructorSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    joined_at = serializers.SerializerMethodField()

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'joined_at',
        )

    def get_id(self, table):
        return table.user.id
    def get_username(self, table):
        return table.user.username
    def get_email(self, table):
        return table.user.email
    def get_first_name(self, table):
        return table.user.first_name
    def get_last_name(self, table):
        return table.user.last_name
    def get_joined_at(self, table):
        return table.created_at


# Seminar의 serializer response에 포함되는 participants 부분
class SeminarParticipantSerializer(serializers.ModelSerializer):

    id = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    joined_at = serializers.SerializerMethodField()

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'joined_at',
            'is_active',
            'dropped_at',
        )

    def get_id(self, table):
        return table.user.id
    def get_username(self, table):
        return table.user.username
    def get_email(self, table):
        return table.user.email
    def get_first_name(self, table):
        return table.user.first_name
    def get_last_name(self, table):
        return table.user.last_name
    def get_joined_at(self, table):
        return table.created_at


class SeminarSerializer(serializers.ModelSerializer):

    time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M"])
    instructors = serializers.SerializerMethodField(read_only=True)
    participants = serializers.SerializerMethodField(read_only=True)
    online = serializers.BooleanField(default=True)

    class Meta:
        model = Seminar
        fields = (
            'id', 
            'name',
            'capacity',
            'count',
            'time',
            'online',

            'instructors',
            'participants',
        )


    def validate(self, data):
        name = data.get('name')
        capacity = data.get('capacity')
        count = data.get('count')
        time = data.get('count')

        if self.context.get('action') == 'create':
            for field in (name, capacity, count, time):
                if field is None:
                    raise ValidationError('입력되지 않은 정보가 있습니다.')
            if not name:
                raise ValidationError('세미나 이름은 빈칸일 수 없습니다.')
            if capacity < 0:
                raise ValidationError('세미나 정원은 양의 정수여야 합니다.')
            if count < 0:
                raise ValidationError('세미나 횟수는 양의 정수여야 합니다.')
        elif self.context.get('action') == 'update':
            if capacity is not None and capacity < 0:
                raise ValidationError('세미나 정원은 양의 정수여야 합니다.')
            if count is not None and count < 0:
                raise ValidationError('세미나 횟수는 양의 정수여야 합니다.')
        
        return data

    def get_instructors(self, seminar):
        result = []
        tables = seminar.user_seminar_table.all()
        for table in tables:
            if table.user.is_instructor:
                result.append(SeminarInstructorSerializer(table).data)
        return result

    def get_participants(self, seminar):
        result = []
        tables = seminar.user_seminar_table.all()
        for table in tables:
            if table.user.is_participant:
                result.append(SeminarParticipantSerializer(table).data)
        return result


class SeminarListSerializer(serializers.ModelSerializer):

    instructors = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Seminar
        fields = (
            'id',
            'name',
            'instructors',
            'participant_count',
        )

    def get_instructors(self, seminar):
        result = []
        tables = seminar.user_seminar_table.all()
        for table in tables:
            if table.user.is_instructor:
                result.append(SeminarInstructorSerializer(table).data)
        return result

    def get_participant_count(self, seminar):
        count = 0
        for table in seminar.user_seminar_table.all():
            user = table.user
            if user.is_participant and user.is_active:
                count += 1
        return count
