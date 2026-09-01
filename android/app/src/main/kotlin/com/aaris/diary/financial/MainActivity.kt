package com.aaris.diary.financial

import android.os.Build
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity

class MainActivity : FlutterActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Android 15+ can raise display refresh rate while the user is
        // actively touching this window. The system owns the policy,
        // so supported 90/120Hz devices get lower touch latency without
        // pinning a high refresh rate while the UI is idle.
        if (Build.VERSION.SDK_INT >= 35) {
            window.setFrameRateBoostOnTouchEnabled(true)
        }
    }
}
