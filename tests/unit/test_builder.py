#!/usr/bin/env python3
"""
Unit tests for HTML to APK Builder backend
"""

import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'src'))

from builder import (
    ConfigValidator,
    AppConfiguration,
    validate_package_name,
    validate_app_name,
    validate_html_content
)


class TestConfigValidator(unittest.TestCase):
    """Test configuration validation"""
    
    def test_valid_package_name(self):
        """Test valid package names"""
        valid_names = [
            'com.example.app',
            'com.mycompany.myapp',
            'org.test.application',
            'com.app_v2.prod'
        ]
        
        for name in valid_names:
            is_valid, msg = ConfigValidator.validate_package_name(name)
            self.assertTrue(is_valid, f"{name} should be valid: {msg}")
    
    def test_invalid_package_name(self):
        """Test invalid package names"""
        invalid_names = [
            '',
            'com',
            'Com.example.app',  # Capital letter
            '123.com.app',  # Starts with number
            'com..example',  # Double dot
            'com/example/app',  # Wrong separator
        ]
        
        for name in invalid_names:
            is_valid, msg = ConfigValidator.validate_package_name(name)
            self.assertFalse(is_valid, f"{name} should be invalid")
    
    def test_valid_app_name(self):
        """Test valid app names"""
        valid_names = [
            'My App',
            'Test-App',
            'App_1.0',
            'My.App.Name'
        ]
        
        for name in valid_names:
            is_valid, msg = ConfigValidator.validate_app_name(name)
            self.assertTrue(is_valid, f"{name} should be valid: {msg}")
    
    def test_invalid_app_name(self):
        """Test invalid app names"""
        invalid_names = [
            '',
            'a' * 51,  # Too long
            'App@Name!',  # Invalid chars
        ]
        
        for name in invalid_names:
            is_valid, msg = ConfigValidator.validate_app_name(name)
            self.assertFalse(is_valid, f"{name} should be invalid")
    
    def test_valid_version_name(self):
        """Test valid version names"""
        valid_versions = [
            '1.0.0',
            '2.1.0',
            '1.2.3-beta',
            '10.20.30'
        ]
        
        for version in valid_versions:
            is_valid, msg = ConfigValidator.validate_version_name(version)
            self.assertTrue(is_valid, f"{version} should be valid: {msg}")
    
    def test_invalid_version_name(self):
        """Test invalid version names"""
        invalid_versions = [
            '',
            '1.0',  # Missing patch
            'v1.0.0',  # Leading v
            '1.0.0.0',  # Too many parts
        ]
        
        for version in invalid_versions:
            is_valid, msg = ConfigValidator.validate_version_name(version)
            self.assertFalse(is_valid, f"{version} should be invalid")
    
    def test_valid_version_code(self):
        """Test valid version codes"""
        valid_codes = [1, 100, 2147483647]
        
        for code in valid_codes:
            is_valid, msg = ConfigValidator.validate_version_code(code)
            self.assertTrue(is_valid, f"{code} should be valid: {msg}")
    
    def test_invalid_version_code(self):
        """Test invalid version codes"""
        invalid_codes = [0, -1, 2147483648]
        
        for code in invalid_codes:
            is_valid, msg = ConfigValidator.validate_version_code(code)
            self.assertFalse(is_valid, f"{code} should be invalid")
    
    def test_valid_html_content(self):
        """Test valid HTML content"""
        valid_html = [
            '<!DOCTYPE html><html><head></head><body></body></html>',
            '<html><body>Hello</body></html>',
            '<!doctype html><html lang="en"><body>Test</body></html>'
        ]
        
        for html in valid_html:
            is_valid, msg = ConfigValidator.validate_html_content(html)
            self.assertTrue(is_valid, f"HTML should be valid: {msg}")
    
    def test_invalid_html_content(self):
        """Test invalid HTML content"""
        invalid_html = [
            '',
            '   ',
            'Just text',
            '<div>Only a div</div>'
        ]
        
        for html in invalid_html:
            is_valid, msg = ConfigValidator.validate_html_content(html)
            self.assertFalse(is_valid, f"HTML should be invalid: {msg}")


class TestAppConfiguration(unittest.TestCase):
    """Test app configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = AppConfiguration()
        
        self.assertEqual(config.config['app_name'], 'HTML App')
        self.assertEqual(config.config['package_name'], 'com.htmlapkbuilder.app')
        self.assertEqual(config.config['version_name'], '1.0.0')
        self.assertEqual(config.config['version_code'], 1)
    
    def test_custom_config(self):
        """Test custom configuration"""
        custom = {
            'app_name': 'My Custom App',
            'package_name': 'com.example.custom',
            'version_name': '2.0.0',
            'version_code': 5
        }
        
        config = AppConfiguration(custom)
        
        self.assertEqual(config.config['app_name'], 'My Custom App')
        self.assertEqual(config.config['package_name'], 'com.example.custom')
        self.assertEqual(config.config['version_name'], '2.0.0')
        self.assertEqual(config.config['version_code'], 5)
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        config = AppConfiguration({
            'app_name': 'Valid App',
            'package_name': 'com.valid.app',
            'version_name': '1.0.0',
            'version_code': 1
        })
        
        is_valid, msg = config.validate()
        self.assertTrue(is_valid)
        
        # Invalid config
        config = AppConfiguration({
            'app_name': '',
            'package_name': 'invalid',
            'version_name': 'bad',
            'version_code': 0
        })
        
        is_valid, msg = config.validate()
        self.assertFalse(is_valid)
    
    def test_permissions(self):
        """Test permission handling"""
        config = AppConfiguration({
            'permissions': ['camera', 'internet']
        })
        
        perms = config.get_permission_list()
        
        self.assertIn('android.permission.CAMERA', perms)
        self.assertIn('android.permission.INTERNET', perms)


class TestStandaloneFunctions(unittest.TestCase):
    """Test standalone validation functions"""
    
    def test_validate_package_name_function(self):
        """Test standalone package name validation"""
        is_valid, msg = validate_package_name('com.test.app')
        self.assertTrue(is_valid)
        
        is_valid, msg = validate_package_name('invalid')
        self.assertFalse(is_valid)
    
    def test_validate_app_name_function(self):
        """Test standalone app name validation"""
        is_valid, msg = validate_app_name('Test App')
        self.assertTrue(is_valid)
        
        is_valid, msg = validate_app_name('')
        self.assertFalse(is_valid)
    
    def test_validate_html_content_function(self):
        """Test standalone HTML validation"""
        is_valid, msg = validate_html_content('<html><body>Test</body></html>')
        self.assertTrue(is_valid)
        
        is_valid, msg = validate_html_content('')
        self.assertFalse(is_valid)


if __name__ == '__main__':
    unittest.main()
