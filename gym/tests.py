from django.test import TestCase
from rest_framework.test import APIClient
from gym.models import Client, Trainer, Membership, MembershipType, WorkoutSession
from model_bakery import baker

class ClientsViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_clients_list(self):
        client = baker.make("Client")
        r = self.client.get('/api/clients/')
        data = r.json()
        
        assert client.name == data[0]['name']
        assert client.id == data[0]['id']
        assert client.phone == data[0]['phone']
        assert len(data) == 1

    def test_create_client(self):
        r = self.client.post("/api/clients/", {
            "name": "Ярыгин Егор",
            "phone": "88005553536",
        })
        
        new_client_id = r.json()['id']
        clients = Client.objects.all()
        assert len(clients) == 1
        
        new_client = Client.objects.filter(id=new_client_id).first()
        assert new_client.name == "Ярыгин Егор"
        assert new_client.phone == "88005553536"

    def test_update_client(self):
        client = baker.make("Client")
        
        r = self.client.put(f'/api/clients/{client.id}/', {
            "name": "Попов Михаил",
            "phone": "88005553538"
        }, content_type='application/json')
        
        assert r.status_code == 200
        
        r = self.client.get(f'/api/clients/{client.id}/')
        data = r.json()
        assert data['name'] == "Попов Михаил"
        assert data['phone'] == "88005553538"

    def test_delete_client(self):
        clients = baker.make("Client", 10)
        r = self.client.get('/api/clients/')
        data = r.json()
        assert len(data) == 10
        
        client_id_to_delete = clients[2].id
        self.client.delete(f'/api/clients/{client_id_to_delete}/')
        
        r = self.client.get('/api/clients/')
        data = r.json()
        assert len(data) == 9
        assert client_id_to_delete not in [i['id'] for i in data]


class TrainersViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_trainers_list(self):
        trainer = baker.make("Trainer")
        r = self.client.get('/api/trainers/')
        data = r.json()
        
        assert trainer.name == data[0]['name']
        assert trainer.id == data[0]['id']
        assert trainer.specialization == data[0]['specialization']
        assert len(data) == 1

    def test_create_trainer(self):
        r = self.client.post("/api/trainers/", {
            "name": "Иванов Петр",
            "specialization": "Фитнес",
        })
        
        assert r.status_code == 201
        new_trainer_id = r.json()['id']
        trainers = Trainer.objects.all()
        assert len(trainers) == 1
        
        new_trainer = Trainer.objects.get(id=new_trainer_id)
        assert new_trainer.name == "Иванов Петр"
        assert new_trainer.specialization == "Фитнес"

    def test_update_trainer(self):
        trainer = baker.make("Trainer")
        
        r = self.client.put(f'/api/trainers/{trainer.id}/', {
            "name": "Сидоров Алексей",
            "specialization": "Йога"
        }, content_type='application/json')
        
        assert r.status_code == 200
        
        trainer.refresh_from_db()
        assert trainer.name == "Сидоров Алексей"
        assert trainer.specialization == "Йога"

    def test_delete_trainer(self):
        trainers = baker.make("Trainer", 5)
        initial_count = Trainer.objects.count()
        
        trainer_id_to_delete = trainers[1].id
        self.client.delete(f'/api/trainers/{trainer_id_to_delete}/')
        
        assert Trainer.objects.count() == initial_count - 1
        assert not Trainer.objects.filter(id=trainer_id_to_delete).exists()


class MembershipTypesViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_membershiptypes_list(self):
        membership_type = baker.make("MembershipType")
        r = self.client.get('/api/membershiptype/')
        data = r.json()
        
        assert membership_type.type == data[0]['type']
        assert membership_type.duration == data[0]['duration']
        assert len(data) == 1

    def test_create_membershiptype(self):
        r = self.client.post("/api/membershiptype/", {
            "type": "Премиум",
            "duration": "6 месяцев",
        })
        
        assert r.status_code == 201
        new_membershiptype_id = r.json()['id']
        membership_types = MembershipType.objects.all()
        assert len(membership_types) == 1
        
        new_membershiptype = MembershipType.objects.get(id=new_membershiptype_id)
        assert new_membershiptype.type == "Премиум"
        assert new_membershiptype.duration == "6 месяцев"

    def test_update_membershiptype(self):
        membership_type = baker.make("MembershipType")
        
        r = self.client.put(f'/api/membershiptype/{membership_type.id}/', {
            "type": "Стандарт",
            "duration": "3 месяца"
        }, content_type='application/json')
        
        assert r.status_code == 200
        
        membership_type.refresh_from_db()
        assert membership_type.type == "Стандарт"
        assert membership_type.duration == "3 месяца"

    def test_delete_membershiptype(self):
        membership_types = baker.make("MembershipType", 3)
        initial_count = MembershipType.objects.count()
        
        membership_type_id_to_delete = membership_types[0].id
        self.client.delete(f'/api/membershiptype/{membership_type_id_to_delete}/')
        
        assert MembershipType.objects.count() == initial_count - 1


class MembershipsViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_memberships_list(self):
        client = baker.make("Client")
        membership_type = baker.make("MembershipType")
        membership = baker.make("Membership", client=client, membership_type=membership_type)

        r = self.client.get('/api/membership/')
        data = r.json()
        print(data)

        assert membership.client.id == data[0]['id']
        assert membership.membership_type.id == data[0]['id']
        assert data[0]['is_active'] == True
        
        assert len(data) == 1

    def test_create_membership(self):
        client = baker.make("Client")
        membership_type = baker.make("MembershipType")

        
        r = self.client.post("/api/membership/", {
            "client": client.id,
            "membership_type": membership_type.id,
            "is_active": True
        })

        new_membership_id = r.json()['id']
        memberships = Membership.objects.all()
        assert len(memberships) == 1
        
        new_membership = Membership.objects.filter(id=new_membership_id).first()
        assert new_membership.client == client
        assert new_membership.membership_type == membership_type
        assert new_membership.is_active == True

    def test_update_membership(self):
        client = baker.make("Client")
        membership_type = baker.make("MembershipType")
        membership = baker.make("Membership", client=client, membership_type=membership_type)
        
        new_client = baker.make("Client")
        new_membership_type = baker.make("MembershipType")
        
        r = self.client.put(f'/api/membership/{membership.id}/', {
            "client": new_client.id,
            "membership_type": new_membership_type.id,
            "is_active": False
        })
        
        assert r.status_code == 200
        
        membership.refresh_from_db()
        assert membership.client == new_client
        assert membership.membership_type == new_membership_type
        assert membership.is_active == False

    def test_delete_membership(self):
        memberships = baker.make("Membership", 3)

        
        initial_count = Membership.objects.count()
        membership_id_to_delete = memberships[1].id
        self.client.delete(f'/api/membership/{membership_id_to_delete}/')
        
        assert Membership.objects.count() == initial_count - 1


class WorkoutSessionsViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_workoutsessions_list(self):
        client = baker.make("Client")
        trainer = baker.make("Trainer")
        workout_session = baker.make("WorkoutSession", client=client, trainer=trainer)
        
        r = self.client.get('/api/workoutsession/')
        data = r.json()
        
        assert len(data) == 1
        assert workout_session.client.id == data[0]['id']
        assert workout_session.trainer.id == data[0]['id']

    def test_create_workoutsession(self):
        client = baker.make("Client")
        trainer = baker.make("Trainer")
        
        r = self.client.post("/api/workoutsession/", {
            "client": client.id,
            "trainer": trainer.id,
            "session_date": "2024-01-15T10:00:00Z"
        })

        new_workout_session_id = r.json()['id']
        workout_sessions = WorkoutSession.objects.all()
        assert len(workout_sessions) == 1
        
        new_workout_session = WorkoutSession.objects.filter(id=new_workout_session_id).first()
        assert new_workout_session.client == client
        assert new_workout_session.trainer == trainer
        assert new_workout_session.session_date.isoformat() == "2024-01-15T10:00:00+00:00"

    def test_update_workoutsession(self):
        client = baker.make("Client")
        trainer = baker.make("Trainer")
        workout_session = baker.make("WorkoutSession", client=client, trainer=trainer)
        
        new_trainer = baker.make("Trainer")
        
        r = self.client.put(f'/api/workoutsession/{workout_session.id}/', {
            "client": client.id,
            "trainer": new_trainer.id,
            "session_date": "2024-01-20T15:00:00Z"
        }, content_type='application/json')
        
        assert r.status_code == 200
        
        workout_session.refresh_from_db()
        assert workout_session.trainer == new_trainer

    def test_delete_workoutsession(self):
        client = baker.make("Client")
        trainer = baker.make("Trainer")
        workout_sessions = baker.make("WorkoutSession", 4, client=client, trainer=trainer)
        
        initial_count = WorkoutSession.objects.count()
        workout_session_id_to_delete = workout_sessions[2].id
        self.client.delete(f'/api/workoutsession/{workout_session_id_to_delete}/')
        
        assert WorkoutSession.objects.count() == initial_count - 1
