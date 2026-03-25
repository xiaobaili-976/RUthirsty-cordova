# Add project specific ProGuard rules here.
-keep class com.zhizhi.music.** { *; }
-keep class org.tensorflow.** { *; }
-keep class com.itextpdf.** { *; }
-keepattributes *Annotation*
-keepclassmembers class * {
    @org.greenrobot.eventbus.Subscribe <methods>;
}
-dontwarn org.tensorflow.**
-dontwarn com.itextpdf.**
