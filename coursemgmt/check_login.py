from django.test import Client
c = Client()
print('login attempt:', c.login(username='crudtester', password='TestPass123'))
