from django.test import TestCase
from factory.django import DjangoModelFactory
from faker import Faker

from rest_framework import status

from user.models import User
from user.serializers import jwt_token_of
from user.tests import UserFactory

from .models import Seminar, UserSeminar

from datetime import datetime, timedelta


class SeminarFactory(DjangoModelFactory):
    class Meta:
        model = Seminar

    @classmethod
    def create(self, **kwargs):
        charger_name = kwargs.pop('charger_name', None)
        participant_name = kwargs.pop('participant_name', None)
        seminar = Seminar.objects.create(**kwargs)

        if charger_name:
            charger = User.objects.get(username=charger_name)
            UserSeminar.objects.create(user=charger, seminar=seminar)
        if participant_name:
            participant = User.objects.get(username=participant_name)
            UserSeminar.objects.create(user=participant, seminar=seminar)

        return seminar


class PostSeminarTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.part = UserFactory(
            username='part',
            email='part@mail.com',
            password='password',
            first_name='Seongtae',
            last_name='Jeong',
            is_participant=True
        )
        cls.part_token = 'JWT ' + jwt_token_of(User.objects.get(username='part'))

        cls.inst = UserFactory(
            username='inst',
            email='inst@mail.com',
            password='password',
            first_name='Seongtae',
            last_name='Jeong',
            is_instructor=True
        )
        cls.inst.instructor.company = 'waffle'
        cls.inst.instructor.year = 3
        cls.inst.instructor.save()
        cls.inst_token = 'JWT ' + jwt_token_of(User.objects.get(username='inst'))

        cls.post_data = {
            'name': 'Django',
            'capacity': 10,
            'count': 5,
            'time': '10:00',
            'online': False,
        }

    def post_request(self, data, username):
        token = getattr(self, username+'_token')
        return self.client.post(
            '/api/v1/seminar/', data=data,
            HTTP_AUTHORIZATION=token
        )

    def test_post_seminar_bad_requests(self):
        # field value omitted
        data = self.post_data.copy()
        data.pop('name')
        response = self.post_request(data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = self.post_data.copy()
        data.pop('capacity')
        response = self.post_request(data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = self.post_data.copy()
        data.pop('count')
        response = self.post_request(data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        data = self.post_data.copy()
        data.pop('time')
        response = self.post_request(data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # empty name
        data = self.post_data.copy()
        data.update({'name' : ""})
        response = self.post_request(data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # negative count
        data = self.post_data.copy()
        data.update({'count' : -1})
        response = self.post_request(data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # negative capacity
        data = self.post_data.copy()
        data.update({'capacity' : -1})
        response = self.post_request(data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # wrong time format
        data = self.post_data.copy()
        data.update({'time' : 12})
        response = self.post_request(data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # wrong online value
        data = self.post_data.copy()
        data.update({'online' : 'online'})
        response = self.post_request(data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_seminar_forbidden(self):
        # a participant user
        response = self.post_request(self.post_data, 'part')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_seminar(self):
        # online value omitted
        post_data = self.post_data.copy()
        post_data.pop('online')
        response = self.post_request(post_data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.json()
        self.assertEqual(data['online'], True)

        # normal request
        response = self.post_request(self.post_data, 'inst')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Django')
        self.assertEqual(data['capacity'], 10)
        self.assertEqual(data['count'], 5)
        self.assertEqual(data['time'], '10:00')
        self.assertEqual(data['online'], False)
        self.assertEqual(data['participants'], [])
        self.assertIn('instructors', data)

        instructor_list = data['instructors']
        self.assertEqual(len(instructor_list), 1)
        instructor = instructor_list[0]
        self.assertIn('id', instructor)
        self.assertEqual(instructor['username'], 'inst')
        self.assertEqual(instructor['email'], 'inst@mail.com')
        self.assertEqual(instructor['first_name'], 'Seongtae')
        self.assertEqual(instructor['last_name'], 'Jeong')
        self.assertIn('joined_at', instructor)


class PutSeminarTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.part = UserFactory(
            username='part',
            email='part@mail.com',
            password='password',
            first_name='Seongtae',
            last_name='Jeong',
            is_participant=True
        )
        cls.part_token = 'JWT ' + jwt_token_of(User.objects.get(username='part'))

        cls.inst = UserFactory(
            username='inst',
            email='inst@mail.com',
            password='password',
            first_name='Seongtae',
            last_name='Jeong',
            is_instructor=True
        )
        cls.inst_token = 'JWT ' + jwt_token_of(User.objects.get(username='inst'))

        cls.charger = UserFactory(
            username='charger',
            email='charger@mail.com',
            password='password',
            first_name='Seongtae',
            last_name='Jeong',
            is_instructor=True
        )
        cls.charger.instructor.company = 'waffle'
        cls.charger.instructor.year = 3
        cls.charger.instructor.save()
        cls.charger_token = 'JWT ' + jwt_token_of(User.objects.get(username='charger'))

        cls.seminar = SeminarFactory(
            name='Backend',
            capacity=5,
            count=3,
            time='10:00',
            online=True,
            charger_name='charger',
            participant_name='part'
        )

        cls.put_data = {
            'name': 'Django',
            'capacity': 10,
            'count': 5,
            'time': '12:00',
            'online': False,
        }

    def put_request(self, data, pk, username):
        token = getattr(self, username+'_token')
        return self.client.put(
            f'/api/v1/seminar/{pk}/', data=data,
            content_type='application/json', HTTP_AUTHORIZATION=token
        )

    def test_put_seminar_wrong_requests(self):
        id = Seminar.objects.get(name='Backend').id

        # not an instructor
        response = self.put_request(self.put_data, id, 'part')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.seminar.name, 'Backend')

        # not a charger
        response = self.put_request(self.put_data, id, 'inst')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.seminar.name, 'Backend')

        # wrong seminar id
        response = self.put_request(self.put_data, 100, 'charger')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # wrong capacity value
        data = self.put_data.copy()
        data.update({'capacity' : 0})
        response = self.put_request(data, id, 'charger')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.seminar.name, 'Backend')

    def test_put_seminar(self):
        id = Seminar.objects.get(name='Backend').id

        # empty body
        response = self.put_request({}, id, 'charger')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn('id', response_data)
        self.assertEqual(response_data['name'], 'Backend')
        self.assertEqual(response_data['capacity'], 5)
        self.assertEqual(response_data['count'], 3)
        self.assertEqual(response_data['time'], '10:00')
        self.assertEqual(response_data['online'], True)
        self.assertEqual(len(response_data['instructors']), 1)
        self.assertEqual(len(response_data['participants']), 1)

        # partial update
        response = self.put_request(self.put_data, id, 'charger')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn('id', response_data)
        self.assertEqual(response_data['name'], 'Django')
        self.assertEqual(response_data['capacity'], 10)
        self.assertEqual(response_data['count'], 5)
        self.assertEqual(response_data['time'], '12:00')
        self.assertEqual(response_data['online'], False)
        self.assertEqual(len(response_data['instructors']), 1)
        self.assertEqual(len(response_data['participants']), 1)

        instructor = response_data['instructors'][0]
        self.assertIn('id', instructor)
        self.assertEqual(instructor['username'], 'charger')
        self.assertEqual(instructor['email'], 'charger@mail.com')
        self.assertEqual(instructor['first_name'], 'Seongtae')
        self.assertEqual(instructor['last_name'], 'Jeong')
        self.assertIn('joined_at', instructor)

        participant = response_data['participants'][0]
        self.assertIn('id', participant)
        self.assertEqual(participant['username'], 'part')
        self.assertEqual(participant['email'], 'part@mail.com')
        self.assertEqual(participant['first_name'], 'Seongtae')
        self.assertEqual(participant['last_name'], 'Jeong')
        self.assertIn('joined_at', participant)
        self.assertEqual(participant['is_active'], True)
        self.assertIsNone(participant['dropped_at'])


class GetSeminarListTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.part1 = UserFactory(
            username='part1',
            email='part1@mail.com',
            password='password',
            is_participant=True
        )

        cls.part2 = UserFactory(
            username='part2',
            email='part2@mail.com',
            password='password',
            is_participant=True
        )

        cls.inst = UserFactory(
            username='inst',
            email='inst@mail.com',
            password='password',
            first_name='Seongtae',
            last_name='Jeong',
            is_instructor=True
        )
        cls.token = 'JWT ' + jwt_token_of(User.objects.get(username='inst'))

        cls.seminar1 = SeminarFactory(
            name='Seminar1',
            capacity=5,
            count=3,
            time='10:00',
            online=True,
            charger_name='inst',
            participant_name='part1'
        )
        cls.seminar1.created_at = datetime.now() + timedelta(days=2)
        cls.seminar1.save()

        cls.seminar2 = SeminarFactory(
            name='Seminar2',
            capacity=5,
            count=3,
            time='10:00',
            online=True,
            charger_name='inst',
            participant_name='part2'
        )
        cls.seminar2.created_at = datetime.now() + timedelta(days=1)
        cls.seminar2.save()

        cls.seminar3 = SeminarFactory(
            name='Seminar2',
            capacity=5,
            count=3,
            time='10:00',
            online=True,
            charger_name='inst',
            participant_name='part1'
        )
        UserSeminar.objects.create(user=cls.part2, seminar=cls.seminar3)

    def get_request(self, query_params=""):
        return self.client.get(
            f'/api/v1/seminar/{query_params}',
            content_type='application/json',
            HTTP_AUTHORIZATION=self.token
        )

    def test_get_seminar_list(self):
        response = self.get_request()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 3)

        seminar = data[0]
        self.assertIn('id', seminar)
        self.assertEqual(seminar['name'], 'Seminar1')
        self.assertEqual(len(seminar['instructors']), 1)
        instructor = seminar['instructors'][0]
        self.assertIn('id', instructor)
        self.assertEqual(instructor['username'], 'inst')
        self.assertEqual(instructor['email'], 'inst@mail.com')
        self.assertEqual(instructor['first_name'], 'Seongtae')
        self.assertEqual(instructor['last_name'], 'Jeong')
        self.assertIn('joined_at', instructor)
        self.assertEqual(seminar['participant_count'], 1)

        seminar = data[1]
        self.assertIn('id', seminar)
        self.assertEqual(seminar['name'], 'Seminar2')
        self.assertEqual(len(seminar['instructors']), 1)
        instructor = seminar['instructors'][0]
        self.assertIn('id', instructor)
        self.assertEqual(instructor['username'], 'inst')
        self.assertEqual(instructor['email'], 'inst@mail.com')
        self.assertEqual(instructor['first_name'], 'Seongtae')
        self.assertEqual(instructor['last_name'], 'Jeong')
        self.assertIn('joined_at', instructor)
        self.assertEqual(seminar['participant_count'], 1)

        seminar = data[2]
        self.assertIn('id', seminar)
        self.assertEqual(seminar['name'], 'Seminar2')
        self.assertEqual(len(seminar['instructors']), 1)
        instructor = seminar['instructors'][0]
        self.assertIn('id', instructor)
        self.assertEqual(instructor['username'], 'inst')
        self.assertEqual(instructor['email'], 'inst@mail.com')
        self.assertEqual(instructor['first_name'], 'Seongtae')
        self.assertEqual(instructor['last_name'], 'Jeong')
        self.assertIn('joined_at', instructor)
        self.assertEqual(seminar['participant_count'], 2)

    def test_get_seminar_list_query_params(self):
        # getting seminars with certain name
        response = self.get_request('?name=Seminar1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 1)
        seminar = data[0]
        self.assertIn('id', seminar)
        self.assertEqual(seminar['name'], 'Seminar1')
        self.assertEqual(len(seminar['instructors']), 1)
        instructor = seminar['instructors'][0]
        self.assertIn('id', instructor)
        self.assertEqual(instructor['username'], 'inst')
        self.assertEqual(instructor['email'], 'inst@mail.com')
        self.assertEqual(instructor['first_name'], 'Seongtae')
        self.assertEqual(instructor['last_name'], 'Jeong')
        self.assertIn('joined_at', instructor)
        self.assertEqual(seminar['participant_count'], 1)

        # getting earliest seminar first
        response = self.get_request('?order=earliest')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['name'], 'Seminar2')
        self.assertEqual(data[1]['name'], 'Seminar2')
        self.assertEqual(data[2]['name'], 'Seminar1')

        # getting seminars with certain name, earliest first
        response = self.get_request('?name=Seminar2&order=earliest')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 2)

        seminar = data[0]
        self.assertEqual(seminar['name'], 'Seminar2')
        self.assertEqual(seminar['participant_count'], 2)
        seminar = data[1]
        self.assertEqual(seminar['name'], 'Seminar2')
        self.assertEqual(seminar['participant_count'], 1)

        # invalid order value
        response = self.get_request('?order=hello')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]['name'], 'Seminar1')
        self.assertEqual(data[1]['name'], 'Seminar2')
        self.assertEqual(data[2]['name'], 'Seminar2')


class GetSeminarTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.part1 = UserFactory(
            username='part1',
            email='part1@mail.com',
            password='password',
            is_participant=True
        )

        cls.part2 = UserFactory(
            username='part2',
            email='part2@mail.com',
            password='password',
            is_participant=True
        )

        cls.inst = UserFactory(
            username='inst',
            email='inst@mail.com',
            password='password',
            first_name='Seongtae',
            last_name='Jeong',
            is_instructor=True
        )
        cls.token = 'JWT ' + jwt_token_of(User.objects.get(username='inst'))

        cls.seminar1 = SeminarFactory(
            name='Seminar1',
            capacity=5,
            count=3,
            time='10:00',
            online=True,
            charger_name='inst',
            participant_name='part1'
        )

        cls.seminar2 = SeminarFactory(
            name='Seminar2',
            capacity=5,
            count=3,
            time='10:00',
            online=True,
            charger_name='inst',
            participant_name='part1'    # part2 added later
        )
        UserSeminar.objects.create(user=cls.part2, seminar=cls.seminar2)

    def get_request(self, id):
        return self.client.get(
            f'/api/v1/seminar/{id}/', content_type='application/json',
            HTTP_AUTHORIZATION=self.token
        )

    def test_get_seminar_not_found(self):
        response = self.get_request(10)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_seminar(self):
        id = Seminar.objects.get(name='Seminar1').id
        response = self.get_request(id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Seminar1')
        self.assertEqual(data['capacity'], 5)
        self.assertEqual(data['count'], 3)
        self.assertEqual(data['time'], '10:00')
        self.assertEqual(data['online'], True)

        self.assertEqual(len(data['instructors']), 1)
        instructor = data['instructors'][0]
        self.assertIn('id', instructor)
        self.assertEqual(instructor['username'], 'inst')
        self.assertEqual(instructor['email'], 'inst@mail.com')
        self.assertEqual(instructor['first_name'], 'Seongtae')
        self.assertEqual(instructor['last_name'], 'Jeong')
        self.assertIn('joined_at', instructor)

        self.assertEqual(len(data['participants']), 1)
        participant = data['participants'][0]
        self.assertIn('id', participant)
        self.assertEqual(participant['username'], 'part1')
        self.assertEqual(participant['email'], 'part1@mail.com')
        self.assertEqual(participant['first_name'], "")
        self.assertEqual(participant['last_name'], "")
        self.assertIn('joined_at', participant)
        self.assertEqual(participant['is_active'], True)
        self.assertIsNone(participant['dropped_at'])

        id = Seminar.objects.get(name='Seminar2').id
        response = self.get_request(id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Seminar2')
        self.assertEqual(data['capacity'], 5)
        self.assertEqual(data['count'], 3)
        self.assertEqual(data['time'], '10:00')
        self.assertEqual(data['online'], True)

        self.assertEqual(len(data['instructors']), 1)
        instructor = data['instructors'][0]
        self.assertIn('id', instructor)
        self.assertEqual(instructor['username'], 'inst')
        self.assertEqual(instructor['email'], 'inst@mail.com')
        self.assertEqual(instructor['first_name'], 'Seongtae')
        self.assertEqual(instructor['last_name'], 'Jeong')
        self.assertIn('joined_at', instructor)

        self.assertEqual(len(data['participants']), 2)
        participant = data['participants'][0]
        self.assertIn('id', participant)
        self.assertEqual(participant['username'], 'part1')
        self.assertEqual(participant['email'], 'part1@mail.com')
        self.assertEqual(participant['first_name'], "")
        self.assertEqual(participant['last_name'], "")
        self.assertIn('joined_at', participant)
        self.assertEqual(participant['is_active'], True)
        self.assertIsNone(participant['dropped_at'])


class PostSeminarUserTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.part1 = UserFactory(
            username='part1',
            email='part1@mail.com',
            password='password',
            is_participant=True
        )
        cls.part1_token = 'jWT ' + jwt_token_of(User.objects.get(username='part1'))

        cls.part2 = UserFactory(
            username='part2',
            email='part2@mail.com',
            password='password',
            is_participant=True
        )
        cls.part2_token = 'JWT ' + jwt_token_of(User.objects.get(username='part2'))

        cls.inst = UserFactory(
            username='inst',
            email='inst@mail.com',
            password='password',
            is_instructor=True
        )
        cls.inst_token = 'JWT ' + jwt_token_of(User.objects.get(username='inst'))

        cls.seminar1 = SeminarFactory(
            name='Seminar1',
            capacity=1,
            count=5,
            time='10:00',
            online=True
        )

        cls.seminar2 = SeminarFactory(
            name='Seminar2',
            capacity=1,
            count=3,
            time='12:00',
            online=True
        )

    def post_request(self, id, data, username):
        token = getattr(self, f"{username}_token")
        return self.client.post(
            f'/api/v1/seminar/{id}/user/', data=data,
            content_type='application/json', HTTP_AUTHORIZATION=token
        )

    def test_seminar_register_user(self):
        # participant
        id = Seminar.objects.get(name='Seminar1').id
        response = self.post_request(id, {'role':'participant'}, 'part1')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Seminar1')
        self.assertEqual(data['capacity'], 1)
        self.assertEqual(data['count'], 5)
        self.assertEqual(data['time'], '10:00')
        self.assertEqual(data['online'], True)
        self.assertEqual(data['instructors'], [])
        self.assertEqual(len(data['participants']), 1)

        participant = data['participants'][0]
        self.assertIn('id', participant)
        self.assertEqual(participant['username'], 'part1')
        self.assertEqual(participant['email'], 'part1@mail.com')
        self.assertEqual(participant['first_name'], "")
        self.assertEqual(participant['last_name'], "")
        self.assertIn('joined_at', participant)
        self.assertEqual(participant['is_active'], True)
        self.assertIsNone(participant['dropped_at'])

        # instructor
        response = self.post_request(id, {'role':'instructor'}, 'inst')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Seminar1')
        self.assertEqual(data['capacity'], 1)
        self.assertEqual(data['count'], 5)
        self.assertEqual(data['time'], '10:00')
        self.assertEqual(data['online'], True)
        self.assertEqual(len(data['instructors']), 1)
        self.assertEqual(len(data['participants']), 1)

        instructor = data['instructors'][0]
        self.assertIn('id', instructor)
        self.assertEqual(instructor['username'], 'inst')
        self.assertEqual(instructor['email'], 'inst@mail.com')
        self.assertEqual(instructor['first_name'], '')
        self.assertEqual(instructor['last_name'], '')
        self.assertIn('joined_at', instructor)

    def test_seminar_register_user_wrong_requests(self):
        # seminar not found
        response = self.post_request(100, {'role':'instructor'}, 'inst')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        id = Seminar.objects.get(name='Seminar1').id

        # wrong role info
        response = self.post_request(id, {'role':'instructor'}, 'part1')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.seminar1.user_seminar_table.count(), 0)

        response = self.post_request(id, {'role':'participant'}, 'inst')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.seminar1.user_seminar_table.count(), 0)

        response = self.post_request(id, {'role':'Hello'}, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.seminar1.user_seminar_table.count(), 0)

        # capacity already full
        response = self.post_request(id, {'role':'participant'}, 'part1')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.post_request(id, {'role':'participant'}, 'part2')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.seminar1.user_seminar_table.count(), 1)

        # instructor who is already in charge of a seminar
        response = self.post_request(id, {'role':'instructor'}, 'inst')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        id2 = Seminar.objects.get(name='Seminar2').id
        response = self.post_request(id2, {'role':'instructor'}, 'inst')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.seminar2.user_seminar_table.count(), 0)

        # already registered
        self.seminar1.capacity = 2
        self.seminar1.save()
        response = self.post_request(id, {'role':'participant'}, 'part1')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.seminar1.user_seminar_table.count(), 2)


class DeleteSeminarUserTestCase(TestCase):
    
    @classmethod
    def setUpTestData(cls):
        cls.part = UserFactory(
            username='part',
            email='part@mail.com',
            password='password',
            is_participant=True
        )
        cls.part_token = 'jWT ' + jwt_token_of(User.objects.get(username='part'))

        cls.inst = UserFactory(
            username='inst',
            email='inst@mail.com',
            password='password',
            is_instructor=True
        )
        cls.inst_token = 'JWT ' + jwt_token_of(User.objects.get(username='inst'))

        cls.seminar = SeminarFactory(
            name='Seminar',
            capacity=1,
            count=5,
            time='10:00',
            online=True,
            charger_name='inst'
        )

    def delete_request(self, id, username):
        token = getattr(self, f"{username}_token")
        return self.client.delete(
            f'/api/v1/seminar/{id}/user/',
            content_type='application/json',
            HTTP_AUTHORIZATION=token
        )

    def test_seminar_unregister_user(self):
        # register first
        id = self.seminar.id
        response = self.client.post(
            f'/api/v1/seminar/{id}/user/', data={'role':'participant'},
            content_type='application/json',
            HTTP_AUTHORIZATION=self.part_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # unregister
        response = self.delete_request(id, 'part')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(self.seminar.user_seminar_table.count(), 2)
        table = self.seminar.user_seminar_table.get(user=self.part)
        self.assertEqual(table.is_active, False)
        self.assertIsNotNone(table.dropped_at)

        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'Seminar')
        self.assertEqual(data['capacity'], 1)
        self.assertEqual(data['count'], 5)
        self.assertEqual(data['time'], '10:00')
        self.assertEqual(data['online'], True)
        self.assertEqual(len(data['instructors']), 1)
        self.assertEqual(len(data['participants']), 1)

        participant = data['participants'][0]
        self.assertIn('id', participant)
        self.assertEqual(participant['username'], 'part')
        self.assertEqual(participant['email'], 'part@mail.com')
        self.assertEqual(participant['first_name'], "")
        self.assertEqual(participant['last_name'], "")
        self.assertIn('joined_at', participant)
        self.assertEqual(participant['is_active'], False)
        self.assertIsNotNone(participant['dropped_at'])

    def test_seminar_unregister_user_wrong_requests(self):
        id = self.seminar.id

        # not registered yet -> still 200
        response = self.delete_request(id, 'part')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.seminar.user_seminar_table.count(), 1)

        # register
        response = self.client.post(
            f'/api/v1/seminar/{id}/user/', data={'role':'participant'},
            HTTP_AUTHORIZATION=self.part_token
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # seminar not found
        response = self.delete_request(100, 'part')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        table = self.seminar.user_seminar_table.get(user=self.part)
        self.assertEqual(table.is_active, True)

        # instructor requesting to unregister
        response = self.delete_request(id, 'inst')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        table = self.seminar.user_seminar_table.get(user=self.part)
        self.assertEqual(table.is_active, True)

        # trying to register again after unregistered
        response = self.delete_request(id, 'part')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(
            f'/api/v1/seminar/{id}/user/', data={'role':'participant'},
            HTTP_AUTHORIZATION=self.part_token
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        table = self.seminar.user_seminar_table.get(user=self.part)
        self.assertEqual(table.is_active, False)
        