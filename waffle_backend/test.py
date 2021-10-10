from seminar.models import UserSeminar, Seminar
from user.models import User, InstructorProfile, ParticipantProfile
from user.serializers import UserCreateSerializer

table = UserSeminar()
table.save()

seminar = Seminar(user_seminar_table=table, name='backend')
seminar.save()
inst = InstructorProfile(company='waffle', year=3)
inst.save()
part = ParticipantProfile(university='SNU', accepted=True)
part.save()

data = {'email' : 'user_inst@mail.com', 'username' : 'user_inst', 'password' : 'pswd!user', 'role' : 'instructor', 'company' : 'waffle', 'year' : 3, 'university' : 'SNU'}
serializer = UserCreateSerializer(data=data)
print("serializer.is_valid()")
serializer.is_valid(raise_exception=True)