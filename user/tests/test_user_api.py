from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse("user:token")
ME_URL = reverse('user:me')


def crate_user(**params):
    return get_user_model().objects.create_user(**params)


class publicUserApiTests(TestCase):
    """test the user api public"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        paylod = {
            'email': 'reza@gmail.com',
            'password': 'fajshdlfk',
            'name': 'some name',
        }

        response = self.client.post(CREATE_USER_URL, paylod)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**response.data)
        self.assertTrue(user.check_password(paylod['password']))
        self.assertNotIn('password', response.data)

    def test_user_exits(self):
        payload = {'email': 'reza@gmail.com', 'password': 'l;kajsdf'}
        crate_user(**payload)
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {'email': 'reza@gmail.com', 'password': 'lfa'}
        response = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user_exits = get_user_model().objects.filter(email=payload['email'])

    def test_create_token_for_user(self):
        payload = {'email': 'reza@gmail.com', 'password': 'lfa'}
        crate_user(**payload)
        response = self.client.post(TOKEN_URL, payload)
        self.assertIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        crate_user(email='reza@gamil.com', password='somthing')
        payload = {'email': 'reza@gmail.com', 'password': 'l;kajsdf'}
        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """create no token if user does not exist"""
        payload = {'email': 'reza@gmail.com', 'password': 'l;kajsdf'}
        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_feild(self):
        """test that email and password are required"""
        payload = {'email': 'reza@gmail.com', 'password': ''}
        response = self.client.post(TOKEN_URL, payload)
        self.assertNotIn('token', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    """requests that need authentication"""

    def setUp(self):
        self.user = crate_user(
            email='somthing@gmail.com',
            password='faskldjf',
            name='name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrive_profile_success(self):
        """retrieving profile for logged user"""
        response = self.client.get(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_not_allowed(self):
        """test that post is not allowed"""
        response = self.client.post(ME_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {'name': 'new name', 'password': 'f;ahdfjkhajkhdsflalks'}
        response = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
