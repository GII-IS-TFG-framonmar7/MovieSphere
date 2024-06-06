from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# --------------------------------------------------- Registro --------------------------------------------------- #
class UserSignupTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')
        self.user.save()

    def test_signup_get(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')

    def test_signup_post_success(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'first_name': 'new',
            'last_name': 'user',
            'email': 'user@user.com',
            'password1': 'abc123xyz!',
            'password2': 'abc123xyz!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_signup_post_failure(self):
        response = self.client.post(reverse('signup'), {
            'username': 'testuser',  # username already exists
            'password1': 'abc123xyz!',
            'password2': 'abc123xyz!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signup.html')
        self.assertContains(response, 'Ya existe un usuario con este nombre')

# --------------------------------------------------- Inicio de sesión --------------------------------------------------- #
class UserSigninTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')
        self.user.save()

    def test_signin_get(self):
        response = self.client.get(reverse('signin'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signin.html')

    def test_signin_post_success(self):
        response = self.client.post(reverse('signin'), {
            'username': 'testuser',
            'password': '12345'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_signin_post_failure(self):
        response = self.client.post(reverse('signin'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'signin.html')
        self.assertContains(response, 'El nombre de usuario o la contraseña son incorrectas')

# --------------------------------------------------- Cierre de sesión --------------------------------------------------- #
class UserSignoutTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')
        self.user.save()

    def test_signout(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

# --------------------------------------------------- Edición de perfil --------------------------------------------------- #
class UserProfileTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')
        self.user.save()

    def test_edit_profile_get(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_profile.html')

    def test_edit_profile_post_success(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('edit_profile'), {
            'username': 'updateduser',
            'first_name': 'updated',
            'last_name': 'user',
            'email': 'user@user.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_edit_profile_post_failure(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('edit_profile'), {
            'username': '',
            'first_name': '',
            'last_name': '',
            'email': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_profile.html')
        self.assertContains(response, 'Este campo es obligatorio.')

# --------------------------------------------------- Cambio de contraseña --------------------------------------------------- #
class UserPasswordChangeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', password='12345')
        self.user.save()

    def test_change_password(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('password_change_done'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('signin'))

    def test_change_password_old_password_incorrect(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('password_change'), {
            'old_password': 'wrongpassword',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_change_form.html')
        self.assertContains(response, 'Su contraseña antigua es incorrecta')

    def test_change_password_new_passwords_do_not_match(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('password_change'), {
            'old_password': '12345',
            'new_password1': 'newpassword123',
            'new_password2': 'differentnewpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_change_form.html')
        self.assertContains(response, 'Los dos campos de contraseña no coinciden')

# --------------------------------------------------- Sobre nosotros --------------------------------------------------- #
class AboutUsPageTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_about_us(self):
        response = self.client.get(reverse('about_us'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about_us.html')

