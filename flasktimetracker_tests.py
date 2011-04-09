import unittest
import flasktimetracker
from flasktimetracker import Interval, User
from datetime import datetime, timedelta
from flask import Flask
from werkzeug import generate_password_hash, check_password_hash

class FlaskTimeTrackerTestCase(unittest.TestCase):
    
    def setUp(self):
        self.appClient = flasktimetracker.app.test_client()

    def assert200(self, status_code):
        self.assertEqual(status_code, 200)
        
    def assert_site_available(self, site):
        response = self.appClient.get(site)
        self.assert200(response.status_code)
        
    def login(self, username, password):
        return self.appClient.post('/checkLogin', data=dict(username=username, password=password), follow_redirects=True)

    def logout(self):
        return self.appClient.get('/logout', follow_redirects=True)

    def flush_db(self):
#        Interval.drop_collection()assert
        User.drop_collection()
    
    def set_initial_data(self):
        admin = User(username="admin", overtime=0, worktime=28800)
        admin.set_pw_hash("geheim")
        
        interval1 = Interval()
        interval1.start = datetime(2011, 4, 4, 19, 56, 23, 709000)
        interval1.stop = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=1)

        interval2 = Interval()
        interval2.start = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=2)
        interval2.stop = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=5)
                
        admin.intervals.append(interval1)
        admin.intervals.append(interval2)
        admin.save()
        
    def test_initial_data(self):
        self.flush_db()
        self.set_initial_data()
        
        user = User.objects().first()
        self.assertEqual(user.username, "admin")
        self.assertTrue(check_password_hash(user.pw_hash, "geheim"))
        self.assertEqual(user.overtime, 0)
        self.assertEqual(user.worktime, 28800)
        self.assertEqual(len(user.intervals), 2)
        
        interval = user.intervals.pop()
        self.assertEqual(interval.start, datetime(2011, 4, 4, 19, 56, 23, 709000)+ timedelta(hours=2))
        self.assertEqual(interval.stop, datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=5))
        
        interval = user.intervals.pop()
        self.assertEqual(interval.start, datetime(2011, 4, 4, 19, 56, 23, 709000))
        self.assertEqual(interval.stop, datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=1))
       
    def test_login_available(self):
        self.assert_site_available("/login")
        
    def test_login_valid_user_pw(self):
        response = self.login("admin","geheim")
        self.assertTrue('logged in successfully.' in response.data, response.data)
        
    def test_login_invalid_user(self):       
        response = self.login("admin" + 'x',"geheim")
        self.assertTrue('user/pw invalid.' in response.data, response.data)

    def test_login_invalid_pw(self):       
        response = self.login("admin", "geheim" + 'x')
        self.assertTrue('user/pw invalid.' in response.data, response.data)

    def test_login_empty_user(self):       
        response = self.login("", "geheim")
        self.assertTrue('This field is required.' in response.data, response.data)
        
    def test_login_empty_pw(self):       
        response = self.login("admin", "")
        self.assertTrue('This field is required.' in response.data, response.data)
        
if __name__ == '__main__':
    unittest.main()
