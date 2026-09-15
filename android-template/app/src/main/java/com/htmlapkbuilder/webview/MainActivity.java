package com.htmlapkbuilder.webview;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.KeyEvent;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Toast;

/**
 * Main Activity - hosts the WebView that loads the bundled index.html
 */
public class MainActivity extends Activity {
    
    private WebView webView;
    private CustomWebChromeClient webChromeClient;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        // Create WebView programmatically
        webView = new WebView(this);
        setContentView(webView);
        
        // Configure WebView settings
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setDatabaseEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowContentAccess(true);
        webSettings.setGeolocationEnabled(false);
        webSettings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        
        // Cache settings for better performance
        webSettings.setCacheMode(WebSettings.LOAD_DEFAULT);
        webSettings.setAppCacheEnabled(true);
        
        // Set WebViewClient to handle page navigation within the app
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                // Handle external URLs differently if needed
                // For now, load all URLs in the WebView
                if (url.startsWith("http://") || url.startsWith("https://") || 
                    url.startsWith("file://") || url.startsWith("data:")) {
                    view.loadUrl(url);
                    return true;
                }
                // Let Android handle other URL schemes
                return false;
            }
        });
        
        // Set up WebChromeClient for file uploads and permissions
        webChromeClient = new CustomWebChromeClient(this, webView);
        webView.setWebChromeClient(webChromeClient);
        
        // Add JavaScript bridge
        AndroidBridge androidBridge = new AndroidBridge(this, webView);
        webView.addJavascriptInterface(androidBridge, "Android");
        
        // Load the bundled index.html from assets
        webView.loadUrl("file:///android_asset/index.html");
    }
    
    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        webChromeClient.handleFileActivityResult(requestCode, resultCode, data);
    }
    
    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        // Handle permission results if needed
    }
    
    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        // Handle back button navigation
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.onResume();
        }
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        if (webView != null) {
            webView.onPause();
        }
    }
    
    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.destroy();
        }
        super.onDestroy();
    }
}
