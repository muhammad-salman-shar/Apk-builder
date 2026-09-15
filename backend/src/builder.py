#!/usr/bin/env python3
"""
HTML to APK Builder Backend

This module handles the core logic for building Android APKs from user-provided HTML files.
"""

import os
import re
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


class BuildError(Exception):
    """Custom exception for build errors"""
    pass


class ConfigValidator:
    """Validates app configuration values"""
    
    # Package name pattern (Java package naming convention)
    PACKAGE_PATTERN = re.compile(r'^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$')
    
    # Version name pattern (semantic versioning)
    VERSION_NAME_PATTERN = re.compile(r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$')
    
    # App name allowed characters
    APP_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_\.]+$')
    
    @classmethod
    def validate_package_name(cls, package_name: str) -> Tuple[bool, str]:
        """Validate Android package/application ID"""
        if not package_name:
            return False, "Package name is required"
        
        if len(package_name) < 3:
            return False, "Package name must be at least 3 characters"
        
        if len(package_name) > 255:
            return False, "Package name must be less than 255 characters"
        
        if not cls.PACKAGE_PATTERN.match(package_name):
            return False, "Invalid package name format. Use reverse domain notation (e.g., com.example.app)"
        
        return True, ""
    
    @classmethod
    def validate_app_name(cls, app_name: str) -> Tuple[bool, str]:
        """Validate application name"""
        if not app_name:
            return False, "App name is required"
        
        if len(app_name) < 1:
            return False, "App name must be at least 1 character"
        
        if len(app_name) > 50:
            return False, "App name must be less than 50 characters"
        
        if not cls.APP_NAME_PATTERN.match(app_name):
            return False, "App name contains invalid characters"
        
        return True, ""
    
    @classmethod
    def validate_version_name(cls, version_name: str) -> Tuple[bool, str]:
        """Validate version name"""
        if not version_name:
            return False, "Version name is required"
        
        if not cls.VERSION_NAME_PATTERN.match(version_name):
            return False, "Version name must follow semantic versioning (e.g., 1.0.0)"
        
        return True, ""
    
    @classmethod
    def validate_version_code(cls, version_code: int) -> Tuple[bool, str]:
        """Validate version code"""
        if not isinstance(version_code, int):
            try:
                version_code = int(version_code)
            except (ValueError, TypeError):
                return False, "Version code must be an integer"
        
        if version_code < 1 or version_code > 2147483647:
            return False, "Version code must be between 1 and 2147483647"
        
        return True, ""
    
    @classmethod
    def validate_html_content(cls, html_content: str) -> Tuple[bool, str]:
        """Validate HTML content"""
        if not html_content:
            return False, "HTML content is empty"
        
        if len(html_content) < 10:
            return False, "HTML content too short"
        
        # Basic HTML structure check
        if '<html' not in html_content.lower() and '<!doctype' not in html_content.lower():
            return False, "Content doesn't appear to be valid HTML"
        
        return True, ""


class AppConfiguration:
    """Represents the app configuration"""
    
    DEFAULT_CONFIG = {
        'app_name': 'HTML App',
        'package_name': 'com.htmlapkbuilder.app',
        'version_name': '1.0.0',
        'version_code': 1,
        'min_sdk': 24,
        'target_sdk': 34,
        'permissions': [],
        'theme': 'default'
    }
    
    AVAILABLE_PERMISSIONS = [
        {'id': 'camera', 'permission': 'android.permission.CAMERA', 'label': 'Camera'},
        {'id': 'microphone', 'permission': 'android.permission.RECORD_AUDIO', 'label': 'Microphone'},
        {'id': 'storage_read', 'permission': 'android.permission.READ_EXTERNAL_STORAGE', 'label': 'Read Storage'},
        {'id': 'storage_write', 'permission': 'android.permission.WRITE_EXTERNAL_STORAGE', 'label': 'Write Storage'},
        {'id': 'vibrate', 'permission': 'android.permission.VIBRATE', 'label': 'Vibration'},
        {'id': 'notifications', 'permission': 'android.permission.POST_NOTIFICATIONS', 'label': 'Notifications'},
        {'id': 'location', 'permission': 'android.permission.ACCESS_FINE_LOCATION', 'label': 'Location'},
        {'id': 'internet', 'permission': 'android.permission.INTERNET', 'label': 'Internet'},
    ]
    
    def __init__(self, config_dict: Optional[Dict] = None):
        self.config = {**self.DEFAULT_CONFIG}
        if config_dict:
            self.config.update(config_dict)
    
    def validate(self) -> Tuple[bool, str]:
        """Validate all configuration values"""
        validators = [
            (ConfigValidator.validate_app_name, self.config.get('app_name', '')),
            (ConfigValidator.validate_package_name, self.config.get('package_name', '')),
            (ConfigValidator.validate_version_name, self.config.get('version_name', '')),
            (ConfigValidator.validate_version_code, self.config.get('version_code', 1)),
        ]
        
        for validator, value in validators:
            is_valid, error_msg = validator(value)
            if not is_valid:
                return False, error_msg
        
        # Validate permissions
        requested_permissions = self.config.get('permissions', [])
        available_ids = [p['id'] for p in self.AVAILABLE_PERMISSIONS]
        
        for perm_id in requested_permissions:
            if perm_id not in available_ids:
                return False, f"Unknown permission: {perm_id}"
        
        return True, ""
    
    def get_permission_list(self) -> list:
        """Get list of Android permissions based on selection"""
        selected_ids = self.config.get('permissions', [])
        permissions = []
        
        for perm in self.AVAILABLE_PERMISSIONS:
            if perm['id'] in selected_ids:
                permissions.append(perm['permission'])
        
        return permissions
    
    def to_dict(self) -> Dict:
        """Return configuration as dictionary"""
        return self.config.copy()


class HtmlToApkBuilder:
    """Main builder class for converting HTML to APK"""
    
    def __init__(self, template_dir: str, output_dir: str):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = None
    
    def build(self, html_content: str, config: AppConfiguration) -> str:
        """
        Build APK from HTML content and configuration
        
        Args:
            html_content: The user's HTML file content
            config: App configuration object
            
        Returns:
            Path to the generated project directory
        """
        # Validate inputs
        is_valid, error_msg = ConfigValidator.validate_html_content(html_content)
        if not is_valid:
            raise BuildError(f"Invalid HTML: {error_msg}")
        
        is_valid, error_msg = config.validate()
        if not is_valid:
            raise BuildError(f"Invalid configuration: {error_msg}")
        
        # Create temporary project directory
        self.temp_dir = tempfile.mkdtemp(prefix='html_apk_')
        project_dir = Path(self.temp_dir)
        
        try:
            # Copy template
            self._copy_template(project_dir)
            
            # Inject HTML
            self._inject_html(project_dir, html_content)
            
            # Apply configuration
            self._apply_config(project_dir, config)
            
            return str(project_dir)
            
        except Exception as e:
            # Cleanup on failure
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            raise BuildError(f"Build failed: {str(e)}")
    
    def _copy_template(self, dest_dir: Path):
        """Copy Android template to destination"""
        template_path = self.template_dir
        
        if not template_path.exists():
            raise BuildError(f"Template directory not found: {template_path}")
        
        # Copy entire template
        shutil.copytree(
            template_path,
            dest_dir / 'android-project',
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns('*.gradle.kts', 'local.properties', '.gradle', 'build', '*.iml')
        )
    
    def _inject_html(self, project_dir: Path, html_content: str):
        """Replace the bundled index.html with user's HTML"""
        assets_dir = project_dir / 'android-project' / 'app' / 'src' / 'main' / 'assets'
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        html_path = assets_dir / 'index.html'
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _apply_config(self, project_dir: Path, config: AppConfiguration):
        """Apply configuration to the Android project"""
        project_path = project_dir / 'android-project'
        cfg = config.to_dict()
        
        # Update strings.xml with app name
        strings_xml = project_path / 'app' / 'src' / 'main' / 'res' / 'values' / 'strings.xml'
        if strings_xml.exists():
            content = strings_xml.read_text(encoding='utf-8')
            content = re.sub(
                r'<string name="app_name">[^<]*</string>',
                f'<string name="app_name">{cfg["app_name"]}</string>',
                content
            )
            strings_xml.write_text(content, encoding='utf-8')
        
        # Update build.gradle with package name and version info
        build_gradle = project_path / 'app' / 'build.gradle'
        if build_gradle.exists():
            content = build_gradle.read_text(encoding='utf-8')
            
            # Replace applicationId
            content = re.sub(
                r'applicationId "[^"]*"',
                f'applicationId "{cfg["package_name"]}"',
                content
            )
            
            # Replace versionName
            content = re.sub(
                r'versionName "[^"]*"',
                f'versionName "{cfg["version_name"]}"',
                content
            )
            
            # Replace versionCode
            content = re.sub(
                r'versionCode \d+',
                f'versionCode {cfg["version_code"]}',
                content
            )
            
            build_gradle.write_text(content, encoding='utf-8')
        
        # Update AndroidManifest.xml with permissions
        manifest = project_path / 'app' / 'src' / 'main' / 'AndroidManifest.xml'
        if manifest.exists():
            content = manifest.read_text(encoding='utf-8')
            
            # Add requested permissions
            permissions = config.get_permission_list()
            existing_perms = re.findall(r'<uses-permission android:name="([^"]+)"', content)
            
            for perm in permissions:
                if perm not in existing_perms:
                    # Insert before <application> tag
                    perm_line = f'    <uses-permission android:name="{perm}" />\n'
                    content = content.replace('<application>', perm_line + '\n<application>')
            
            manifest.write_text(content, encoding='utf-8')
        
        # Update settings.gradle with project name
        settings_gradle = project_path / 'settings.gradle'
        if settings_gradle.exists():
            content = settings_gradle.read_text(encoding='utf-8')
            safe_name = re.sub(r'[^a-zA-Z0-9]', '', cfg['app_name'])
            content = re.sub(
                r'rootProject\.name = "[^"]*"',
                f'rootProject.name = "{safe_name}"',
                content
            )
            settings_gradle.write_text(content, encoding='utf-8')
    
    def compile_apk(self, project_dir: str, debug: bool = True) -> str:
        """
        Compile the Android project to APK
        
        Args:
            project_dir: Path to the Android project directory
            debug: Whether to build debug APK
            
        Returns:
            Path to the generated APK
        """
        project_path = Path(project_dir) / 'android-project'
        
        if not project_path.exists():
            raise BuildError(f"Project directory not found: {project_path}")
        
        # Run Gradle build
        gradle_cmd = './gradlew' if os.name != 'nt' else 'gradlew.bat'
        build_type = 'assembleDebug' if debug else 'assembleRelease'
        
        try:
            result = subprocess.run(
                [gradle_cmd, build_type],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise BuildError(f"Gradle build failed:\n{result.stderr}")
            
            # Find APK
            apk_dir = project_path / 'app' / 'build' / 'outputs' / 'apk'
            apk_type = 'debug' if debug else 'release'
            
            for apk_file in apk_dir.rglob(f'*-{apk_type}.apk'):
                return str(apk_file)
            
            raise BuildError("APK file not found after build")
            
        except subprocess.TimeoutExpired:
            raise BuildError("Build timed out after 5 minutes")
        except FileNotFoundError:
            raise BuildError("Gradle not found. Please install Android SDK and set up Gradle.")


def validate_package_name(package_name: str) -> Tuple[bool, str]:
    """Standalone function to validate package name"""
    return ConfigValidator.validate_package_name(package_name)


def validate_app_name(app_name: str) -> Tuple[bool, str]:
    """Standalone function to validate app name"""
    return ConfigValidator.validate_app_name(app_name)


def validate_html_content(html_content: str) -> Tuple[bool, str]:
    """Standalone function to validate HTML content"""
    return ConfigValidator.validate_html_content(html_content)
