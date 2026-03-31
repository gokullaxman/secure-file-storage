import os
import io
import unittest
from cryptography.fernet import Fernet
from app import create_app
from app.extensions import db
from app.models import User, File

class SecureVaultTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['ENCRYPTION_KEY'] = Fernet.generate_key().decode('utf-8')
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        self.app.config['WTF_CSRF_ENABLED'] = False
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        self.test_upload_folder = self.app.config['UPLOAD_FOLDER']
        os.makedirs(self.test_upload_folder, exist_ok=True)
        
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        # Cleanup test uploads
        if os.path.exists(self.test_upload_folder):
            for f in os.listdir(self.test_upload_folder):
                os.remove(os.path.join(self.test_upload_folder, f))
            os.rmdir(self.test_upload_folder)

    def register(self, username, password):
        # With WTF_CSRF_ENABLED = False, we don't need CSRF token for tests
        return self.client.post('/login', data=dict(
            action='register',
            username=username,
            password=password
        ), follow_redirects=True)

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            action='login',
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.client.get('/logout', follow_redirects=True)

    def test_auth_flow(self):
        # Test registration
        rv = self.register('testuser', 'testpass123')
        self.assertIn(b'Secure Vault', rv.data) # Should redirect to dashboard
        self.logout()

        # Test login
        rv = self.login('testuser', 'testpass123')
        self.assertIn(b'Secure Vault', rv.data)
        
    def test_file_upload_and_download(self):
        self.register('testuser', 'testpass123')
        
        # Upload a file
        data = {
            'file': (io.BytesIO(b"super secret file content"), 'secret.txt')
        }
        rv = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertIn(b'File successfully uploaded and encrypted.', rv.data)
        self.assertIn(b'secret.txt', rv.data)
        
        # Verify file is stored
        file_record = File.query.first()
        self.assertIsNotNone(file_record)
        self.assertEqual(file_record.original_filename, 'secret.txt')
        
        # Verify file is actually encrypted on disk
        filepath = os.path.join(self.app.config['UPLOAD_FOLDER'], file_record.stored_filename)
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'rb') as f:
            encrypted_data = f.read()
        self.assertNotEqual(encrypted_data, b"super secret file content") # Should not be plaintext
            
        # Test download
        rv = self.client.get(f'/download/{file_record.id}')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, b"super secret file content") # Should be decrypted

if __name__ == '__main__':
    unittest.main()
