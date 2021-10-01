from factory.django import DjangoModelFactory
from faker import Faker

from django.test import TestCase
from rest_framework import status

from user.models import User
from user.models import InstructorProfile, ParticipantProfile
from user.serializers import jwt_token_of


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = 'test@test.com'

    @classmethod
    def create(cls, **kwargs):
        is_instructor, is_participant = kwargs.pop('is_instructor', False), kwargs.pop('is_participant', False)
        user = User.objects.create(**kwargs)
        user.set_password(kwargs.get('password', ''))
        if is_instructor:
            instructor = InstructorProfile.objects.create()
            user.instructor = instructor
        if is_participant:
            participant = ParticipantProfile.objects.create()
            user.participant = participant
        user.save()
        return user


# POST /api/v1/signup/ -> 회원가입
class PostUserTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        # 수강생 프로필을 가진 유저 만들기
        # 위 코드의 팩토리 구현을 참고해주세요.
        # UserFactory() 따위로 instance를 만들면,
        # 자동적으로 내부의 classmethod 'create'가 실행됩니다.
        # is_instructor, is_participant 옵션은 제가 임의로 추가한 편의기능입니다.

        cls.user = UserFactory(
            email='waffle@test.com',
            username='steve',
            first_name='지혁',
            last_name='강',
            password='password',
            is_participant=True
        )
        cls.user.participant.university = '서울대학교'
        cls.user.participant.save()

        # 클래스 전반에 걸쳐 기본적으로 사용할 데이터라면, 여기서 선언해줄 수 있습니다.
        # 이러한 개념을 FIXTURE 라고 합니다.
        cls.post_data = {
            'email': 'waffle@test.com',
            'username': 'steve',
            'password': 'password',
            'role': 'participant'
        }

    def test_post_user_중복(self):
        data = self.post_data
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)    # 중복 회원가입 시도 시 409

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)     # 생성되지 않음

    def test_post_user_잘못된_request들(self):
        data = self.post_data.copy()
        data.update({'role': 'wrong_role'})     # role 정보 잘못 입력
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = self.post_data.copy()
        data.pop('role')                        # role 정보 누락
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = self.post_data.copy()
        data['role'] = 'intructor'
        data['year'] = -1                       # year 정보 잘못 입력
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user_count = User.objects.count()
        self.assertEqual(user_count, 1)

    def test_post_user_participant(self):
        # participant인 유저 생성
        data = {
            "username": "participant",
            "password": "password",
            "first_name": "Davin",
            "last_name": "Byeon",
            "email": "bdv111@snu.ac.kr",
            "role": "participant",
            "university": "서울대학교"
        }
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data["user"], "bdv111@snu.ac.kr")
        self.assertIn("token", data)

        user_count = User.objects.count()
        self.assertEqual(user_count, 2)
        participant_count = ParticipantProfile.objects.count()
        self.assertEqual(participant_count, 2)
        instructor_count = InstructorProfile.objects.count()
        self.assertEqual(instructor_count, 0)

    def test_post_user_instructor(self):
        # instructor인 유저 생성
        faker = Faker()
        fake_email = faker.email()
        data = {
            "username": faker.user_name(),
            "password": "password",
            "first_name": faker.first_name(),
            "last_name": faker.last_name(),
            "email": fake_email,
            "role": "instructor",
            "university": "서울대학교",
            "company": "waffle studio",
        }
        response = self.client.post('/api/v1/signup/', data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertEqual(data['user'], fake_email)
        self.assertIn("token", data)

        user_count = User.objects.count()
        self.assertEqual(user_count, 2)
        participant_count = ParticipantProfile.objects.count()
        self.assertEqual(participant_count, 1)
        instructor_count = InstructorProfile.objects.count()
        self.assertEqual(instructor_count, 1)


# PUT /api/v1/user/me/ -> 유저 정보 수정
class PutUserMeTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        # participant인 유저 생성
        cls.participant = UserFactory(
            username='part',
            password='password',
            first_name='Davin',
            last_name='Byeon',
            email='bdv111@snu.ac.kr',
            is_participant=True
        )
        cls.participant.participant.university = '서울대학교'
        cls.participant.participant.save()
        cls.participant_token = 'JWT ' + jwt_token_of(User.objects.get(email='bdv111@snu.ac.kr'))

        # instructor인 유저 생성
        cls.instructor = UserFactory(
            username='inst',
            password='password',
            first_name='Davin',
            last_name='Byeon',
            email='bdv123@snu.ac.kr',
            is_instructor=True
        )
        cls.instructor.instructor.year = 1
        cls.instructor.instructor.save()
        cls.instructor_token = 'JWT ' + jwt_token_of(User.objects.get(email='bdv123@snu.ac.kr'))
    
    def test_put_user_incomplete_request(self):
        # No Token
        response = self.client.put('/api/v1/user/me/',
                                   data={"first_name": "Dabin"}, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # only first name
        response = self.client.put('/api/v1/user/me/',
                                   data={"first_name": "Dabin"},
                                   content_type='application/json',
                                   HTTP_AUTHORIZATION=self.participant_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        participant_user = User.objects.get(username='part')
        self.assertEqual(participant_user.first_name, 'Davin')

        # wrong year value
        wrong_year_data = {
            "username": "inst123",
            "company": "매스프레소",
            "year": -1
        }
        response = self.client.put('/api/v1/user/me/',
                                   data=wrong_year_data,
                                   content_type='application/json',
                                   HTTP_AUTHORIZATION=self.instructor_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        instructor_user = User.objects.get(username='inst')
        self.assertEqual(instructor_user.email, 'bdv123@snu.ac.kr')

        # email that already exists
        existing_email = {
            "username": "newname",
            "email": "bdv123@snu.ac.kr",
        }
        response = self.client.put(
            '/api/v1/user/me/', data=existing_email,
            content_type='application/json', HTTP_AUTHORIZATION=self.participant_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        participant_user = User.objects.get(username='part')
        self.assertEqual(participant_user.email, 'bdv111@snu.ac.kr')

        # wrong name
        wrong_username = {
            'first_name': 'Hi123',
            'last_name': '123Hi',
            'email': 'new@mail.com',
        }
        response = self.client.put(
            '/api/v1/user/me/', data=wrong_username,
            content_type='application/json', HTTP_AUTHORIZATION=self.participant_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        participant_user = User.objects.get(username='part')
        self.assertEqual(participant_user.email, 'bdv111@snu.ac.kr')

        # wrong lookup in URL
        response = self.client.put(
            '/api/v1/user/lookup/', data={'username':'newname'},
            content_type='application/json', HTTP_AUTHORIZATION=self.participant_token
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        participant_user = User.objects.get(username='part')
        self.assertEqual(participant_user.email, 'bdv111@snu.ac.kr')


    def test_put_user_me_participant(self):

        data = {
            "username": "part123",
            "email": "bdv111@naver.com",
            "university": "경북대학교"
        }
        response = self.client.put(
            '/api/v1/user/me/',
            data=data,
            content_type='application/json',
            HTTP_AUTHORIZATION=self.participant_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["username"], "part123")
        self.assertEqual(data["email"], "bdv111@naver.com")
        self.assertEqual(data["first_name"], "Davin")
        self.assertEqual(data["last_name"], "Byeon")
        self.assertIn("last_login", data)
        self.assertIn("date_joined", data)
        self.assertNotIn("token", data)

        participant = data["participant"]
        self.assertIsNotNone(participant)
        self.assertIn("id", participant)
        self.assertEqual(participant["university"], "경북대학교")
        self.assertTrue(participant["accepted"])
        self.assertEqual(len(participant["seminars"]), 0)

        self.assertIsNone(data["instructor"])
        participant_user = User.objects.get(username='part123')
        self.assertEqual(participant_user.email, 'bdv111@naver.com')

    def test_put_user_me_instructor(self):
        response = self.client.put(
            '/api/v1/user/me/',
            data = {
                "username": "inst123",
                "email": "bdv111@naver.com",
                "first_name": "Dabin",
                "last_name": "Byeon",
                "university": "서울대학교",  # this should be ignored
                "company": "매스프레소",
                "year": 2
            },
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["username"], "inst123")
        self.assertEqual(data["email"], "bdv111@naver.com")
        self.assertEqual(data["first_name"], "Dabin")
        self.assertEqual(data["last_name"], "Byeon")
        self.assertIn("last_login", data)
        self.assertIn("date_joined", data)
        self.assertNotIn("token", data)

        self.assertIsNone(data["participant"])

        instructor = data["instructor"]
        self.assertIsNotNone(instructor)
        self.assertIn("id", instructor)
        self.assertEqual(instructor["company"], "매스프레소")
        self.assertEqual(instructor["year"], 2)
        self.assertIsNone(instructor["charge"])

        instructor_user = User.objects.get(username='inst123')
        self.assertEqual(instructor_user.email, 'bdv111@naver.com')


################################################################


# POST /api/v1/login/ -> 유저 로그인
class PostUserLoginTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        faker = Faker()
        fake_email = faker.email()
        fake_password = faker.password()

        cls.user = UserFactory(
            email=fake_email,
            username=faker.user_name(),
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            password=fake_password,
        )

        cls.post_data = {
            'email': fake_email,
            'password': fake_password,
        }

    def test_post_user_login(self):
        response = self.client.post('/api/v1/login/', data=self.post_data)
        data = response.json()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('token', data)


# GET /api/v1/user/{id}/ -> 유저 정보 가져오기
class GetUserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.participant = UserFactory(
            username='part',
            password='password',
            email='part@mail.com',
            first_name='Seongtae',
            last_name='Jeong',
            is_participant=True
        )
        cls.participant.participant.university = 'SNU'
        cls.participant.participant.save()
        cls.participant_token = 'JWT ' + jwt_token_of(User.objects.get(username='part'))
        
        cls.instructor = UserFactory(
            username='inst',
            password='password',
            email='inst@mail.com',
            first_name='Seongtae',
            last_name='Jeong',
            is_instructor=True
        )
        cls.instructor.instructor.year = 3
        cls.instructor.instructor.company = 'waffle'
        cls.instructor.instructor.save()

    def test_user_created_well(self):
        participant = User.objects.get(username='part')
        instructor = User.objects.get(username='inst')
        self.assertTrue(participant.is_participant)
        self.assertTrue(instructor.is_instructor)
        self.assertEqual(participant.participant.university, 'SNU')
        self.assertEqual(instructor.instructor.company, 'waffle')
        self.assertEqual(instructor.instructor.year, 3)

    def test_get_user_me(self):
        response = self.client.get(
            '/api/v1/user/me/', content_type='application/json',
            HTTP_AUTHORIZATION=self.participant_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["username"], "part")
        self.assertEqual(data['email'], 'part@mail.com')
        self.assertEqual(data["first_name"], "Seongtae")
        self.assertEqual(data['last_name'], 'Jeong')
        self.assertIn('last_login', data)
        self.assertIn('date_joined', data)
        self.assertNotIn('token', data)
        self.assertIsNotNone(data['participant'])
        self.assertIsNone(data['instructor'])

        participant = data['participant']
        self.assertIn('id', participant)
        self.assertEqual(participant['university'], 'SNU')
        self.assertTrue(participant['accepted'])
        self.assertEqual(len(participant['seminars']), 0)

    def test_get_user_pk(self):
        pk = User.objects.get(username='inst').id

        response = self.client.get(
            '/api/v1/user/{}/'.format(pk), content_type='application/json',
            HTTP_AUTHORIZATION=self.participant_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["username"], "inst")
        self.assertEqual(data['email'], 'inst@mail.com')
        self.assertEqual(data["first_name"], "Seongtae")
        self.assertEqual(data['last_name'], 'Jeong')
        self.assertIn('last_login', data)
        self.assertIn('date_joined', data)
        self.assertNotIn('token', data)
        self.assertIsNone(data['participant'])
        self.assertIsNotNone(data['instructor'])

        instructor = data['instructor']
        self.assertIn('id', instructor)
        self.assertEqual(instructor['company'], 'waffle')
        self.assertEqual(instructor['year'], 3)
        self.assertIsNone(instructor['charge'])


# POSt /api/v1/user/participant/ -> 참여자로 등록
class PostUserParticipantTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.participant = UserFactory(
            username='part',
            password='password',
            email='part@mail.com',
            is_participant=True
        )
        cls.participant_token = 'JWT ' + jwt_token_of(User.objects.get(username='part'))

        cls.instructor = UserFactory(
            username='inst',
            password='password',
            email='inst@mail.com',
            first_name='Seongtae',
            last_name='Jeong',
            is_instructor=True
        )
        cls.instructor.instructor.company = 'waffle'
        cls.instructor.instructor.year = 3
        cls.instructor.instructor.save()
        cls.instructor_token = 'JWT ' + jwt_token_of(User.objects.get(username='inst'))

    def test_post_participant_bad_request(self):
        # 이미 participant인 유저
        response = self.client.post(
            '/api/v1/user/participant/', content_type='application/json',
            HTTP_AUTHORIZATION=self.participant_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_participant_no_body(self):
        # response body data가 입력되지 않았을 때
        response = self.client.post(
            '/api/v1/user/participant/',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIsNotNone(data['participant'])
        
        participant = data['participant']
        self.assertEqual(participant['university'], "")
        self.assertTrue(participant['accepted'])

    def test_post_participant(self):
        post_data = {'university': 'SNU', 'accepted': 'False'}
        response = self.client.post(
            '/api/v1/user/participant/', data=post_data,
            content_type='application/json',
            HTTP_AUTHORIZATION=self.instructor_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["username"], "inst")
        self.assertEqual(data['email'], 'inst@mail.com')
        self.assertEqual(data["first_name"], "Seongtae")
        self.assertEqual(data['last_name'], 'Jeong')
        self.assertIn('last_login', data)
        self.assertIn('date_joined', data)
        self.assertNotIn('token', data)
        self.assertIsNotNone(data['participant'])
        self.assertIsNotNone(data['instructor'])

        participant = data['participant']
        self.assertIn('id', participant)
        self.assertEqual(participant['university'], 'SNU')
        self.assertFalse(participant['accepted'])
        self.assertEqual(len(participant['seminars']), 0)

        instructor = data['instructor']
        self.assertIn('id', instructor)
        self.assertEqual(instructor['company'], 'waffle')
        self.assertEqual(instructor['year'], 3)
        self.assertIsNone(instructor['charge'])

