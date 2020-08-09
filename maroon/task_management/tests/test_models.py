from django.test import TestCase
from .. import models

class ProfileModelTests(TestCase):
    def create_profile(self, username="user_1", email="user_1@gmail.com"):
        user = models.User.objects.create(username=username, email=email)
        user.save()
        return models.Profile.objects.get(user=user)

        
    def test_profile_creation(self):
        """
        Test that on profile creation that the user is tied to the profile
        """
        profile = self.create_profile()
        self.assertEqual(profile.user.username, "user_1")
        self.assertEqual(profile.user.email, "user_1@gmail.com")

    def test_profile_token_creation(self):
        """
        Test that there is a token created for the user
        """
        profile = self.create_profile()
        self.assertTrue(models.Token.objects.filter(user=profile.user).exists())