# HTML to APK Builder

A web application that converts a single self-contained HTML file into an Android APK. Users provide one HTML file (with inline CSS and JavaScript), configure app settings, and receive a complete Android application.

## 🚀 Features

- **Single HTML File Input**: Accepts one self-contained `index.html` with inline CSS (`<style>`) and JavaScript (`<script>`)
- **No File Splitting**: Your HTML remains as a single file - never split into separate `.css` or `.js` files
- **Android WebView Runtime**: Built on a robust Android WebView template
- **Native Bridge API**: JavaScript can access native Android functionality through a secure bridge
- **Configurable App Settings**: App name, package ID, version, permissions
- **Modern Android Support**: Targets Android 14 (API 34) with backwards compatibility to API 24
- **Secure by Design**: Validated inputs, narrowly-scoped native APIs, no arbitrary code execution

## 📁 Repository Structure

```
/workspace
├── android-template/          # Reusable Android WebView template
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/htmlapkbuilder/webview/
│   │   │   │   ├── MainActivity.java         # Main activity with WebView
│   │   │   │   ├── AndroidBridge.java        # JavaScript ↔ Native bridge
│   │   │   │   └── CustomWebChromeClient.java # File uploads, permissions
│   │   │   ├── assets/
│   │   │   │   └── index.html                # Template HTML (replaced during build)
│   │   │   ├── res/                          # Android resources
│   │   │   └── AndroidManifest.xml           # App manifest
│   │   ├── build.gradle                      # App-level Gradle config
│   │   └── proguard-rules.pro
│   ├── build.gradle                          # Project-level Gradle config
│   ├── settings.gradle
│   └── gradle.properties
│
├── backend/                                   # Python backend
│   ├── src/
│   │   ├── builder.py                        # Core build logic
│   │   └── api.py                            # Flask REST API
│   ├── uploads/                              # Temporary upload storage
│   └── output/                               # Build output directory
│
├── web-builder/                              # Web frontend
│   └── public/
│       └── index.html                        # Builder UI
│
├── tests/
│   └── unit/
│       └── test_builder.py                   # Unit tests
│
├── docs/                                     # Documentation
├── examples/                                 # Example HTML apps
└── scripts/                                  # Utility scripts
```

## 🏗️ Architecture

```
┌─────────────┐
│   USER      │
│ index.html  │
│ (ONE FILE)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   WEB UI    │  ← Upload HTML + Configure
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  BACKEND    │  ← Validate + Process
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  ANDROID    │  ← Copy template + Inject HTML
│  TEMPLATE   │     Apply configuration
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   GRADLE    │  ← Build APK
│    BUILD    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    APK      │
└─────────────┘
```

## 🔧 How It Works

### 1. HTML Injection

The builder takes the user's `index.html` and places it into the Android project's `app/src/main/assets/` directory. The Android app loads this file via:

```java
webView.loadUrl("file:///android_asset/index.html");
```

### 2. Configuration Application

The builder modifies these files based on user configuration:

- **`strings.xml`**: App name
- **`build.gradle`**: Package name, version name, version code
- **`AndroidManifest.xml`**: Permissions
- **`settings.gradle`**: Project name

### 3. Building

After project generation, run Gradle to compile the APK:

```bash
cd android-project
./gradlew assembleDebug
```

## 🔌 JavaScript Bridge API

The Android template exposes native functionality to JavaScript through the `Android` object.

### Available Methods

#### `Android.toast(message, duration)`
Show a toast notification.

```javascript
Android.toast('Hello!', 'short');  // or 'long'
```

#### `Android.vibrate(durationMs)`
Vibrate the device.

```javascript
Android.vibrate(200);  // Vibrate for 200ms
```

#### `Android.notify(json)`
Show a system notification.

```javascript
Android.notify(JSON.stringify({
    title: 'Hello',
    body: 'World',
    id: 123  // Optional notification ID
}));
```

#### `Android.download(json)`
Download a file using Android's Download Manager.

```javascript
Android.download(JSON.stringify({
    url: 'https://example.com/file.pdf',
    filename: 'myfile.pdf'
}));
```

#### `Android.share(json)`
Share text content.

```javascript
Android.share(JSON.stringify({
    text: 'Check this out!',
    title: 'Share'
}));
```

#### `Android.copyToClipboard(text)`
Copy text to clipboard.

```javascript
Android.copyToClipboard('Text to copy');
```

#### `Android.openUrl(url)`
Open URL in external browser.

```javascript
Android.openUrl('https://example.com');
```

#### `Android.getAndroidVersion()`
Get Android version information.

```javascript
const info = JSON.parse(Android.getAndroidVersion());
console.log('SDK:', info.sdkInt);
```

#### `Android.checkPermission(permission)`
Check if a permission is granted.

```javascript
const status = Android.checkPermission('android.permission.CAMERA');
// Returns: "granted", "denied", or "not_requested"
```

#### `Android.requestPermissions(json)`
Request runtime permissions.

```javascript
Android.requestPermissions(JSON.stringify({
    0: 'android.permission.CAMERA',
    1: 'android.permission.RECORD_AUDIO'
}));
```

### File Input Support

Standard HTML file inputs work automatically:

```html
<input type="file" accept="image/*">
```

The `CustomWebChromeClient` handles the file chooser dialog.

## ⚙️ App Configuration

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `app_name` | Display name of the app | `My HTML App` |
| `package_name` | Android application ID | `com.example.myapp` |
| `version_name` | Semantic version | `1.0.0` |
| `version_code` | Integer version | `1` |

### Optional Permissions

| ID | Permission | Description |
|----|------------|-------------|
| `camera` | `CAMERA` | Camera access |
| `microphone` | `RECORD_AUDIO` | Microphone access |
| `storage_read` | `READ_EXTERNAL_STORAGE` | Read files |
| `storage_write` | `WRITE_EXTERNAL_STORAGE` | Write files |
| `vibrate` | `VIBRATE` | Vibration |
| `notifications` | `POST_NOTIFICATIONS` | Show notifications (Android 13+) |
| `location` | `ACCESS_FINE_LOCATION` | GPS location |
| `internet` | `INTERNET` | Network access (included by default) |

## 🛠️ Local Development

### Prerequisites

- Python 3.8+
- Node.js (optional, for serving frontend)
- Android SDK with Gradle (for building APKs)

### Backend Setup

```bash
cd /workspace/backend
pip install flask werkzeug

# Run the API server
python src/api.py
```

### Frontend Setup

The frontend is static HTML/JS/CSS. Serve it with any static server:

```bash
# Using Python
cd /workspace/web-builder/public
python -m http.server 8080

# Or using Node.js
npx serve ../public
```

### Running Tests

```bash
cd /workspace
python -m pytest tests/unit/test_builder.py -v

# Or using unittest
python -m unittest tests.unit.test_builder
```

## 📦 Building an APK

### Via Web Interface

1. Open the web builder UI
2. Upload your `index.html`
3. Configure app settings
4. Select required permissions
5. Click "Build Android Project"
6. Run the provided Gradle command

### Via API

```bash
curl -X POST http://localhost:5000/api/build-project \
  -F "html_file=@index.html" \
  -F 'config={
    "app_name": "My App",
    "package_name": "com.example.myapp",
    "version_name": "1.0.0",
    "version_code": 1,
    "permissions": ["internet"]
  }'
```

### Manual Gradle Build

```bash
cd /path/to/generated/android-project
./gradlew assembleDebug

# APK will be at:
# app/build/outputs/apk/debug/app-debug.apk
```

## 🔒 Security Considerations

### Input Validation

- All configuration values are validated before use
- Package names must follow Java naming conventions
- HTML content is validated to ensure it's actual HTML
- File uploads are size-limited (10MB max)

### Path Traversal Prevention

- Uploaded files are stored in isolated temporary directories
- File names are sanitized
- No direct filesystem access from HTML

### JavaScript Bridge Security

- Only narrowly-scoped methods are exposed
- No arbitrary Java method invocation
- Dangerous APIs require explicit permission selection
- All bridge methods validate their inputs

### Server-Side Protection

- HTML files are treated as untrusted content
- No server-side execution of uploaded HTML
- Build process runs in isolated temporary directories
- Temporary files are cleaned up after build

## 📝 Known Limitations

1. **Single HTML File**: External CSS/JS files must be inlined. The builder does not support multi-file projects.

2. **Large Assets**: Base64-encoded assets increase file size. Consider the 10MB upload limit.

3. **WebView Limitations**: Some modern browser APIs may not be available in Android WebView.

4. **Native Features**: Only the documented bridge APIs are available. Custom native code requires modifying the template.

5. **iOS**: This tool only builds Android APKs. iOS builds would require a separate Xcode template.

## 🧪 Testing

### Unit Tests

Run the test suite:

```bash
python -m unittest discover -s tests/unit
```

### Manual Testing

1. Use the example HTML in `/examples/`
2. Build an APK
3. Install on Android device/emulator
4. Test all bridge API methods

## 📄 License

This project is provided as-is for educational and practical use.

## 🤝 Contributing

When contributing:

1. Keep the single-HTML-file requirement intact
2. Don't add GitHub Actions workflows (handled separately)
3. Test all changes with real HTML files
4. Document any new bridge APIs
5. Maintain backward compatibility where possible

## 🆘 Troubleshooting

### Build Fails with "Gradle not found"

Ensure Android SDK is installed and `ANDROID_HOME` is set:

```bash
export ANDROID_HOME=/path/to/android/sdk
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools
```

### "Invalid package name" Error

Package names must:
- Start with a lowercase letter
- Use only lowercase letters, numbers, and underscores
- Have at least two segments separated by dots
- Example: `com.example.app` ✓, `Com.Example.App` ✗

### HTML Validation Fails

Ensure your HTML has proper structure:

```html
<!DOCTYPE html>
<html>
<head>
    <title>My App</title>
    <style>/* CSS here */</style>
</head>
<body>
    <!-- Content here -->
    <script>/* JS here */</script>
</body>
</html>
```

### Bridge Methods Not Working

- Ensure you're running in the Android app, not a browser
- Check that required permissions are granted
- Verify JSON formatting for methods that require it
