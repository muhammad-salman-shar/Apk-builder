package com.htmlapkbuilder.webview;

import android.Manifest;
import android.app.Activity;
import android.app.DownloadManager;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import android.widget.Toast;

import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.core.content.ContextCompat;

import org.json.JSONObject;

/**
 * JavaScript Bridge for Android Native Functionality
 * 
 * This class exposes native Android APIs to JavaScript running in the WebView.
 * All methods are annotated with @JavascriptInterface and must be called from JavaScript.
 * 
 * SECURITY: Only expose safe, narrowly-scoped methods. Validate all inputs.
 */
public class AndroidBridge {
    
    private static final String NOTIFICATION_CHANNEL_ID = "html_apk_notifications";
    private static final int PERMISSION_REQUEST_CODE = 1001;
    
    private Activity activity;
    private WebView webView;
    private Handler mainHandler;
    
    public AndroidBridge(Activity activity, WebView webView) {
        this.activity = activity;
        this.webView = webView;
        this.mainHandler = new Handler(Looper.getMainLooper());
    }
    
    /**
     * Show a toast message
     * @param message The message to display
     * @param duration "short" or "long"
     */
    @JavascriptInterface
    public void toast(String message, String duration) {
        mainHandler.post(() -> {
            int toastDuration = "long".equals(duration) ? Toast.LENGTH_LONG : Toast.LENGTH_SHORT;
            Toast.makeText(activity.getApplicationContext(), message, toastDuration).show();
        });
    }
    
    /**
     * Vibrate the device
     * @param durationMs Duration in milliseconds
     */
    @JavascriptInterface
    public void vibrate(long durationMs) {
        mainHandler.post(() -> {
            Vibrator vibrator = (Vibrator) activity.getSystemService(Context.VIBRATOR_SERVICE);
            if (vibrator != null && vibrator.hasVibrator()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    vibrator.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE));
                } else {
                    vibrator.vibrate(durationMs);
                }
            }
        });
    }
    
    /**
     * Show a notification
     * @param json JSON string with title, body, and optional id
     * Example: {"title": "Hello", "body": "World", "id": 1}
     */
    @JavascriptInterface
    public void notify(String json) {
        mainHandler.post(() -> {
            try {
                JSONObject data = new JSONObject(json);
                String title = data.optString("title", "Notification");
                String body = data.optString("body", "");
                int notificationId = data.optInt("id", (int) System.currentTimeMillis());
                
                // Create notification channel for Android O+
                createNotificationChannel();
                
                // Check notification permission for Android 13+
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    if (ContextCompat.checkSelfPermission(activity, Manifest.permission.POST_NOTIFICATIONS)
                            != PackageManager.PERMISSION_GRANTED) {
                        // Request permission via callback
                        notifyPermissionRequired();
                        return;
                    }
                }
                
                android.app.Notification notification = new NotificationCompat.Builder(activity, NOTIFICATION_CHANNEL_ID)
                        .setSmallIcon(android.R.drawable.ic_dialog_info)
                        .setContentTitle(title)
                        .setContentText(body)
                        .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                        .setAutoCancel(true)
                        .build();
                
                NotificationManagerCompat notificationManager = NotificationManagerCompat.from(activity);
                notificationManager.notify(notificationId, notification);
                
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }
    
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    NOTIFICATION_CHANNEL_ID,
                    "App Notifications",
                    NotificationManager.IMPORTANCE_DEFAULT
            );
            channel.setDescription("Notifications from HTML app");
            
            NotificationManager notificationManager = activity.getSystemService(NotificationManager.class);
            if (notificationManager != null) {
                notificationManager.createNotificationChannel(channel);
            }
        }
    }
    
    private void notifyPermissionRequired() {
        mainHandler.post(() -> {
            Toast.makeText(activity, "Notification permission required", Toast.LENGTH_LONG).show();
        });
    }
    
    /**
     * Download a file
     * @param json JSON with url and filename
     * Example: {"url": "https://example.com/file.pdf", "filename": "file.pdf"}
     */
    @JavascriptInterface
    public void download(String json) {
        mainHandler.post(() -> {
            try {
                JSONObject data = new JSONObject(json);
                String url = data.getString("url");
                String filename = data.optString("filename", "downloaded_file");
                
                DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url));
                request.setTitle(filename);
                request.setDescription("Downloading...");
                request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                request.setAllowedOverMetered(true);
                request.setAllowedOverRoaming(true);
                request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, filename);
                
                DownloadManager downloadManager = (DownloadManager) activity.getSystemService(Context.DOWNLOAD_SERVICE);
                if (downloadManager != null) {
                    downloadManager.enqueue(request);
                    Toast.makeText(activity, "Download started", Toast.LENGTH_SHORT).show();
                }
            } catch (Exception e) {
                e.printStackTrace();
                Toast.makeText(activity, "Download failed: " + e.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    /**
     * Share text content
     * @param json JSON with text and optional title
     * Example: {"text": "Check this out!", "title": "Share"}
     */
    @JavascriptInterface
    public void share(String json) {
        mainHandler.post(() -> {
            try {
                JSONObject data = new JSONObject(json);
                String text = data.getString("text");
                String title = data.optString("title", "Share");
                
                Intent shareIntent = new Intent(Intent.ACTION_SEND);
                shareIntent.setType("text/plain");
                shareIntent.putExtra(Intent.EXTRA_TEXT, text);
                shareIntent.putExtra(Intent.EXTRA_SUBJECT, title);
                
                activity.startActivity(Intent.createChooser(shareIntent, "Share via"));
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }
    
    /**
     * Copy text to clipboard
     * @param text The text to copy
     */
    @JavascriptInterface
    public void copyToClipboard(String text) {
        mainHandler.post(() -> {
            ClipboardManager clipboard = (ClipboardManager) activity.getSystemService(Context.CLIPBOARD_SERVICE);
            if (clipboard != null) {
                ClipData clip = ClipData.newPlainText("label", text);
                clipboard.setPrimaryClip(clip);
                Toast.makeText(activity, "Copied to clipboard", Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    /**
     * Open an external URL in browser
     * @param url The URL to open
     */
    @JavascriptInterface
    public void openUrl(String url) {
        mainHandler.post(() -> {
            try {
                Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                activity.startActivity(intent);
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }
    
    /**
     * Request runtime permissions
     * @param permissions Array of permission strings
     */
    @JavascriptInterface
    public void requestPermissions(String permissionsJson) {
        mainHandler.post(() -> {
            try {
                JSONObject data = new JSONObject(permissionsJson);
                String[] permissions = new String[data.length()];
                int i = 0;
                for (String key : data.keySet()) {
                    permissions[i++] = data.getString(key);
                }
                
                ActivityCompat.requestPermissions(activity, permissions, PERMISSION_REQUEST_CODE);
            } catch (Exception e) {
                e.printStackTrace();
            }
        });
    }
    
    /**
     * Get Android version info
     * @return JSON string with SDK version
     */
    @JavascriptInterface
    public String getAndroidVersion() {
        try {
            JSONObject result = new JSONObject();
            result.put("sdkInt", Build.VERSION.SDK_INT);
            result.put("release", Build.VERSION.RELEASE);
            return result.toString();
        } catch (Exception e) {
            return "{}";
        }
    }
    
    /**
     * Check if a permission is granted
     * @param permission The permission to check
     * @return "granted", "denied", or "not_requested"
     */
    @JavascriptInterface
    public String checkPermission(String permission) {
        int result = ContextCompat.checkSelfPermission(activity, permission);
        if (result == PackageManager.PERMISSION_GRANTED) {
            return "granted";
        } else if (ActivityCompat.shouldShowRequestPermissionRationale(activity, permission)) {
            return "denied";
        } else {
            return "not_requested";
        }
    }
}
