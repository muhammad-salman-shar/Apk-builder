# Add project specific ProGuard rules here.
# By default, the flags in this file are appended to flags specified
# in /sdk/tools/proguard/proguard-android.txt

# Keep JavaScript interface classes
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep WebView-related classes
-keepclassmembers class * extends android.webkit.WebViewClient {
    public void *(...);
}

-keepclassmembers class * extends android.webkit.WebViewClient {
    public boolean *(...);
}

# Keep bridge class
-keep class com.htmlapkbuilder.webview.AndroidBridge { *; }
