package com.htmlapkbuilder.webview;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Environment;
import android.webkit.ConsoleMessage;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.core.content.FileProvider;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * Custom WebChromeClient for handling file uploads, permissions, and console messages
 */
public class CustomWebChromeClient extends WebChromeClient {
    
    private static final int FILE_CHOOSER_REQUEST = 1;
    private static final int CAMERA_PERMISSION_REQUEST = 2;
    
    private Activity activity;
    private WebView webView;
    private ValueCallback<Uri[]> fileUploadCallback;
    
    public CustomWebChromeClient(Activity activity, WebView webView) {
        this.activity = activity;
        this.webView = webView;
    }
    
    @Override
    public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback,
                                     FileChooserParams fileChooserParams) {
        if (fileUploadCallback != null) {
            fileUploadCallback.onReceiveValue(null);
        }
        
        fileUploadCallback = filePathCallback;
        
        Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        
        activity.startActivityForResult(
            Intent.createChooser(intent, "Select File"),
            FILE_CHOOSER_REQUEST
        );
        
        return true;
    }
    
    @Override
    public void onPermissionRequest(PermissionRequest request) {
        List<String> grantedResources = new ArrayList<>();
        List<String> deniedResources = new ArrayList<>();
        
        for (String resource : request.getResources()) {
            boolean permissionGranted = false;
            
            switch (resource) {
                case PermissionRequest.RESOURCE_VIDEO_CAPTURE:
                    permissionGranted = checkCameraPermission();
                    if (!permissionGranted) {
                        requestCameraPermission();
                    }
                    break;
                    
                case PermissionRequest.RESOURCE_AUDIO_CAPTURE:
                    permissionGranted = checkMicrophonePermission();
                    if (!permissionGranted) {
                        requestMicrophonePermission();
                    }
                    break;
                    
                case PermissionRequest.RESOURCE_PROTECTED_MEDIA_ID:
                case PermissionRequest.RESOURCE_MIDI_SYSEX:
                    // Not supported
                    break;
            }
            
            if (permissionGranted) {
                grantedResources.add(resource);
            } else {
                deniedResources.add(resource);
            }
        }
        
        if (!grantedResources.isEmpty()) {
            request.grant(grantedResources.toArray(new String[0]));
        }
        if (!deniedResources.isEmpty()) {
            request.deny();
        }
    }
    
    private boolean checkCameraPermission() {
        return ContextCompat.checkSelfPermission(activity, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED;
    }
    
    private boolean checkMicrophonePermission() {
        return ContextCompat.checkSelfPermission(activity, Manifest.permission.RECORD_AUDIO)
                == PackageManager.PERMISSION_GRANTED;
    }
    
    private void requestCameraPermission() {
        ActivityCompat.requestPermissions(activity,
                new String[]{Manifest.permission.CAMERA},
                CAMERA_PERMISSION_REQUEST);
    }
    
    private void requestMicrophonePermission() {
        ActivityCompat.requestPermissions(activity,
                new String[]{Manifest.permission.RECORD_AUDIO},
                CAMERA_PERMISSION_REQUEST);
    }
    
    @Override
    public boolean onConsoleMessage(ConsoleMessage consoleMessage) {
        // Log console messages
        android.util.Log.d("WebView", consoleMessage.message() + " -- From line "
                + consoleMessage.lineNumber() + " of "
                + consoleMessage.sourceId());
        return true;
    }
    
    public void handleFileActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILE_CHOOSER_REQUEST) {
            if (fileUploadCallback == null) return;
            
            Uri[] results = null;
            
            if (resultCode == Activity.RESULT_OK && data != null) {
                String dataString = data.getDataString();
                if (dataString != null) {
                    results = new Uri[]{Uri.parse(dataString)};
                }
            }
            
            fileUploadCallback.onReceiveValue(results);
            fileUploadCallback = null;
        }
    }
}
