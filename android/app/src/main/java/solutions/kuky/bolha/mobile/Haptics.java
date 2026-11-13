// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.content.Context;
import android.os.Build;
import android.os.SystemClock;
import android.os.VibrationEffect;
import android.os.Vibrator;
import org.json.JSONObject;

final class Haptics {
    private static boolean angry;
    private static long lastAnger = -6000, lastTap;
    private static double lastImpact;

    static boolean enabled(Context context) {
        return context.getSharedPreferences("options",0).getBoolean("haptics",true);
    }

    static void frame(Context context, JSONObject state) {
        boolean nextAngry = state.optString("emotion").equals("bravo");
        long now = SystemClock.uptimeMillis();
        if (nextAngry && !angry && now-lastAnger >= 6000) {
            lastAnger = now;
            pulse(context, 36, 52);
        }
        angry = nextAngry;
        double impact = state.optDouble("impact",0);
        if (impact > 0 && impact != lastImpact && now-lastTap >= 160) {
            lastTap = now;
            pulse(context, 17, 36);
        }
        lastImpact = impact;
    }

    @SuppressWarnings("deprecation")
    private static void pulse(Context context, int millis, int amplitude) {
        if (!enabled(context)) return;
        Vibrator vibrator = (Vibrator)context.getSystemService(Context.VIBRATOR_SERVICE);
        if (vibrator == null || !vibrator.hasVibrator()) return;
        if (Build.VERSION.SDK_INT >= 26)
            vibrator.vibrate(VibrationEffect.createOneShot(millis, vibrator.hasAmplitudeControl()
                    ? amplitude : VibrationEffect.DEFAULT_AMPLITUDE));
        else vibrator.vibrate(millis);
    }
}
