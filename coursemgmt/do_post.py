from django.test import Client
c = Client()
print('login:', c.login(username='crudtester', password='TestPass123'))
resp = c.post('/programs/courses/create/', {'course_name':'Web Test Course 2','duration_hours':'8','fees':'50.00','level':'Beginner','status':'Active'}, follow=True)
print('status_code:', resp.status_code)
print('redirect_chain:', getattr(resp,'redirect_chain',None))
