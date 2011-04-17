import unittest
import flasktimetracker
from flasktimetracker import Interval, User, login
from datetime import datetime, timedelta
from flask import Flask, session
from werkzeug import generate_password_hash, check_password_hash

class FlaskTimeTrackerTestCase(unittest.TestCase):
    
    def setUp(self):
        self.appClient = flasktimetracker.app.test_client()
        self.flush_db()
        self.set_initial_data()

    def get(self, url):
        return self.appClient.get(url, follow_redirects=True)
    
    def post(self, url, parameter):
        return self.appClient.post(url,data=parameter, follow_redirects=True)
    
    def assert200(self, status_code):
        self.assertEqual(status_code, 200)
        
    def assert_site_available(self, site):
        response = self.get(site)
        self.assert200(response.status_code)
        
    def login(self, username, password):
        return self.post('/login/check', dict(username=username, password=password))

    def login_admin(self):
        return self.login("admin","geheim")
        
    def logout(self):
        return self.get('/login/disable')

    def flush_db(self):
        Interval.drop_collection()
        User.drop_collection()
    
    def set_initial_data(self):
        admin = User(username="admin", overtime=0, worktime=28800)
        admin.set_pw_hash("geheim")
        admin.save()
        
        interval1 = Interval()
        interval1.start = datetime(2011, 4, 4, 19, 56, 23, 709000)
        interval1.stop = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=1)
        interval1.userid = admin.id
        interval1.save()

        interval2 = Interval()
        interval2.start = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=2)
        interval2.stop = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=5)
        interval2.userid = admin.id
        interval2.save()
                      
    def test_initial_data(self):
        user_count = User.objects().all().count()
        self.assertEqual(1, user_count, "1 != " + str(user_count))
        user = User.objects().first()
        self.assertEqual(user.username, "admin")
        self.assertTrue(check_password_hash(user.pw_hash, "geheim"))
        self.assertEqual(user.overtime, 0)
        self.assertEqual(user.worktime, 28800)
        
        intervals = Interval.objects(userid=user.id)
        self.assertEqual(len(intervals), 2)
        
        interval = intervals.next()
        self.assertEqual(interval.start, datetime(2011, 4, 4, 19, 56, 23, 709000))
        self.assertEqual(interval.stop, datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=1))
        
        interval = intervals.next()
        self.assertEqual(interval.start, datetime(2011, 4, 4, 19, 56, 23, 709000)+ timedelta(hours=2))
        self.assertEqual(interval.stop, datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=5))
       
    def test_login_available(self):
        """ tests availability of site login """
        self.assert_site_available("/login/show")
        
    def test_login0(self):
        """ tests login with valid user and pw """
        response = self.login("admin","geheim")
        self.assertTrue('logged in successfully.' in response.data, response.data)

    def test_login1(self):
        """ tests login and logout with valid data """
        response = self.login("admin","geheim")
        self.assertTrue('logged in successfully.' in response.data, response.data)
        response = self.logout()
        self.assertTrue('logged out successfully.' in response.data, response.data)
                       
    def test_login2(self):
        """ tests login with invalid user """       
        response = self.login("admin" + 'x',"geheim")
        self.assertTrue('user/pw invalid.' in response.data, response.data)

    def test_login3(self):   
        """ tests login with invalid pw """    
        response = self.login("admin", "geheim" + 'x')
        self.assertTrue('user/pw invalid.' in response.data, response.data)

    def test_login4(self):       
        """ tests login with empty user """
        response = self.login("", "geheim")
        self.assertTrue('This field is required.' in response.data, response.data)
        
    def test_login5(self):
        """ tests login with empty pw """       
        response = self.login("admin", "")
        self.assertTrue('This field is required.' in response.data, response.data)

    def test_interval1(self):
        """ test the duration calucation """
        interval1 = Interval()
        interval1.start = datetime(2011, 4, 4, 19, 56, 23, 709000)
        interval1.stop = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=1)
        self.assertEqual(interval1.duration(), timedelta(0, 3600))
        
    def test_interval2(self):
        """ tests duration calculation with empty stop-property """
        interval1 = Interval()
        interval1.start = datetime(2011, 4, 4, 19, 56, 23, 709000)
        
        pre = interval1.duration()
        result = interval1.duration()
        post = interval1.duration()
        
        self.assertTrue(pre < result < post, str(pre) + " < " + str(result) + " < " + str(post))
    
    def test_calc_durations(self):
        """ tests sum durations from several intervals """
        interval1 = Interval()
        interval1.start = datetime(2011, 4, 4, 19, 56, 23, 709000)
        interval1.stop = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=1)

        interval2 = Interval()
        interval2.start = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=2)
        interval2.stop = datetime(2011, 4, 4, 19, 56, 23, 709000) + timedelta(hours=5)
        
        result = flasktimetracker.calc_durations([interval1, interval2]);
        self.assertEqual(timedelta(hours=4), result, str(interval1.duration()) + " " + str(interval2.duration()))
        
        result = flasktimetracker.calc_durations([]);
        self.assertEqual(timedelta(hours=0), result, str(timedelta(hours=0)) + " " + str(result))

        result = flasktimetracker.calc_durations(None);
        self.assertEqual(timedelta(hours=0), result, str(timedelta(hours=0)) + " " + str(result))
        
    def test_interval_edit(self):
        """ tests the interval edit form """
        self.login_admin()
        response = self.get('/interval/edit/123')
        self.assertTrue('404' in response.data, response.data)
        
        interval = Interval.objects().first()
        response = self.get("/interval/edit/" + str(interval.id))
        self.assertTrue('404' not in response.data, response.data)
        
    def test_save_interval(self):
        """ tests saving intervals """
        self.assertTrue(False)
if __name__ == '__main__':
    unittest.main()
