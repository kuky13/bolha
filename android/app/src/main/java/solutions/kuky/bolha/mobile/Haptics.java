// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.content.Context;
import android.os.Build;
import android.os.SystemClock;
import android.os.VibrationEffect;
import android.os.Vibrator;
import org.json.JSONObject;

final class Haptics {
    private static final HapticCadence cadence = new HapticCadence();

    static boolean enabled(Context context) {
        return context.getSharedPreferences("options",0).getBoolean("haptics",true);
    }

    static void frame(Context context, JSONObject state) {
        switch (cadence.frame(state.optString("emotion").equals("bravo"),
                state.optDouble("impact",0),SystemClock.uptimeMillis())) {
            case ANGER: pulse(context,36,52); break;
            case IMPACT: pulse(context,17,36); break;
            default: break;
        }
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
