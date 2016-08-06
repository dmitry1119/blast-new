from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


# TODO: add tests
class UsernameCaseInsensitiveBackend(ModelBackend):
    """
    Backend for username case insensitive authenticating.
    """
    def authenticate(self, username=None, password=None, **kwargs):
        UserModel = get_user_model()

        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        try:
            user = UserModel.objects.get(username__iexact=username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password):
                return user