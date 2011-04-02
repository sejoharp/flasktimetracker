import unittest
import flasktimetracker

class FlaskTimeTrackerTestCase(unittest.TestCase):
    
    def setUp(self):
        self.app = flasktimetracker.app.test_client()

    def login(self, username, password):
        return self.app.post('/checkLogin', data=dict(username=username, password=password), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_login_valid_user_pw(self):
        response = self.login("admin","geheim")
        assert 'logged in successfully.' in response.data
        
    def test_login_invalid_user(self):       
        response = self.login("admin" + 'x',"geheim")
        assert 'user/pw invalid.' in response.data

    def test_login_invalid_pw(self):       
        response = self.login("admin", "geheim" + 'x')
        assert 'user/pw invalid.' in response.data

    def test_login_empty_user(self):       
        response = self.login("", "geheim")
        print response.data
        assert 'This field is required.' in response.data
        
    def test_login_empty_pw(self):       
        response = self.login("admin", "")
        assert 'This field is required.' in response.data
        
if __name__ == '__main__':
    unittest.main()
