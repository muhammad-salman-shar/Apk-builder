#!/usr/bin/env python3
"""
Flask API for HTML to APK Builder

Provides REST endpoints for the web frontend.
"""

import os
import json
import shutil
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from pathlib import Path

from builder import (
    HtmlToApkBuilder,
    AppConfiguration,
    BuildError,
    validate_package_name,
    validate_app_name,
    validate_html_content
)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = Path(os.environ.get('UPLOAD_FOLDER', '/tmp/html_apk_uploads'))
OUTPUT_FOLDER = Path(os.environ.get('OUTPUT_FOLDER', '/tmp/html_apk_output'))
TEMPLATE_DIR = Path(os.environ.get('TEMPLATE_DIR', '../../android-template'))

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB max


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


@app.route('/api/validate/package-name', methods=['POST'])
def api_validate_package_name():
    """Validate package name"""
    data = request.get_json() or {}
    package_name = data.get('package_name', '')
    
    is_valid, error_msg = validate_package_name(package_name)
    
    return jsonify({
        'valid': is_valid,
        'message': error_msg if not is_valid else 'Valid package name'
    })


@app.route('/api/validate/app-name', methods=['POST'])
def api_validate_app_name():
    """Validate app name"""
    data = request.get_json() or {}
    app_name = data.get('app_name', '')
    
    is_valid, error_msg = validate_app_name(app_name)
    
    return jsonify({
        'valid': is_valid,
        'message': error_msg if not is_valid else 'Valid app name'
    })


@app.route('/api/validate/html', methods=['POST'])
def api_validate_html():
    """Validate HTML content"""
    data = request.get_json() or {}
    html_content = data.get('html_content', '')
    
    is_valid, error_msg = validate_html_content(html_content)
    
    return jsonify({
        'valid': is_valid,
        'message': error_msg if not is_valid else 'Valid HTML content'
    })


@app.route('/api/permissions', methods=['GET'])
def get_permissions():
    """Get available permissions list"""
    return jsonify({
        'permissions': AppConfiguration.AVAILABLE_PERMISSIONS
    })


@app.route('/api/build', methods=['POST'])
def build_apk():
    """
    Build APK from HTML and configuration
    
    Expects:
    - html_file: The index.html file
    - config: JSON string with app configuration
    """
    try:
        # Get HTML file
        if 'html_file' not in request.files:
            return jsonify({'error': 'No HTML file provided'}), 400
        
        html_file = request.files['html_file']
        
        if html_file.filename == '':
            return jsonify({'error': 'No HTML file selected'}), 400
        
        # Read HTML content
        html_content = html_file.read().decode('utf-8')
        
        # Validate HTML
        is_valid, error_msg = validate_html_content(html_content)
        if not is_valid:
            return jsonify({'error': f'Invalid HTML: {error_msg}'}), 400
        
        # Get configuration
        config_json = request.form.get('config', '{}')
        config_dict = json.loads(config_json)
        
        # Create configuration object
        config = AppConfiguration(config_dict)
        
        # Validate configuration
        is_valid, error_msg = config.validate()
        if not is_valid:
            return jsonify({'error': f'Invalid configuration: {error_msg}'}), 400
        
        # Build the project
        builder = HtmlToApkBuilder(
            template_dir=str(TEMPLATE_DIR),
            output_dir=str(OUTPUT_FOLDER)
        )
        
        project_dir = builder.build(html_content, config)
        
        # Return project directory path (for manual build)
        # Or compile APK if requested
        compile_apk = request.form.get('compile', 'false').lower() == 'true'
        
        if compile_apk:
            try:
                apk_path = builder.compile_apk(project_dir, debug=True)
                return send_file(apk_path, as_attachment=True)
            except BuildError as e:
                return jsonify({'error': str(e)}), 500
        
        return jsonify({
            'success': True,
            'project_dir': project_dir,
            'message': 'Project generated successfully. Run Gradle build to create APK.'
        })
        
    except json.JSONDecodeError as e:
        return jsonify({'error': f'Invalid JSON configuration: {str(e)}'}), 400
    except BuildError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'Build failed: {str(e)}'}), 500


@app.route('/api/build-project', methods=['POST'])
def build_project_only():
    """
    Generate Android project without compiling APK
    
    This is faster and allows external build systems to compile later.
    """
    try:
        # Get HTML file
        if 'html_file' not in request.files:
            return jsonify({'error': 'No HTML file provided'}), 400
        
        html_file = request.files['html_file']
        html_content = html_file.read().decode('utf-8')
        
        # Get configuration
        config_json = request.form.get('config', '{}')
        config_dict = json.loads(config_json)
        config = AppConfiguration(config_dict)
        
        # Validate
        is_valid, error_msg = validate_html_content(html_content)
        if not is_valid:
            return jsonify({'error': f'Invalid HTML: {error_msg}'}), 400
        
        is_valid, error_msg = config.validate()
        if not is_valid:
            return jsonify({'error': f'Invalid config: {error_msg}'}), 400
        
        # Build
        builder = HtmlToApkBuilder(
            template_dir=str(TEMPLATE_DIR),
            output_dir=str(OUTPUT_FOLDER)
        )
        
        project_dir = builder.build(html_content, config)
        
        return jsonify({
            'success': True,
            'project_dir': project_dir,
            'build_command': f'cd {project_dir}/android-project && ./gradlew assembleDebug'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
