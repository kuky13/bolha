// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.view.Surface;
import android.view.WindowManager;
import org.json.JSONObject;

final class PhoneMotion implements SensorEventListener {
    private final Context context;
    private final Engine engine;
    private final SensorManager manager;
    private final Sensor sensor;
    private final ShakeMotion detector = new ShakeMotion();
    private final float[] gravity = new float[3];
    private boolean listening, initialized;
    private float sensitivity = 1;

    PhoneMotion(Context context, Engine engine) {
        this.context = context;
        this.engine = engine;
        manager = context.getSystemService(SensorManager.class);
        Sensor selected = manager == null ? null : manager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION);
        sensor = selected != null || manager == null ? selected : manager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
    }

    void update(boolean active, JSONObject preferences) {
        sensitivity = (float)preferences.optDouble("shakeSensitivity", 1);
        boolean wanted = active && sensor != null && preferences.optBoolean("shakeEnabled", false);
        if (wanted == listening) return;
        listening = wanted;
        detector.reset();
        initialized = false;
        if (wanted) manager.registerListener(this, sensor, SensorManager.SENSOR_DELAY_GAME);
        else if (manager != null) manager.unregisterListener(this);
    }

    boolean available() { return sensor != null; }

    @Override public void onSensorChanged(SensorEvent event) {
        if (!listening) return;
        float x=event.values[0], y=event.values[1], z=event.values[2];
        if (event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
            if (!initialized) {
                System.arraycopy(event.values,0,gravity,0,3);
                initialized = true;
            }
            for (int index=0; index<3; index++) gravity[index]=.9f*gravity[index]+.1f*event.values[index];
            x-=gravity[0]; y-=gravity[1]; z-=gravity[2];
        }
        if (!detector.sample(x,y,z,event.timestamp/1000000L,sensitivity)) return;
        float screenX=x, screenY=-y;
        int rotation=context.getSystemService(WindowManager.class).getDefaultDisplay().getRotation();
        if (rotation==Surface.ROTATION_90) { screenX=y; screenY=x; }
        else if (rotation==Surface.ROTATION_180) { screenX=-x; screenY=y; }
        else if (rotation==Surface.ROTATION_270) { screenX=-y; screenY=-x; }
        engine.motion(Math.max(-24,Math.min(24,screenX)), Math.max(-24,Math.min(24,screenY)),true);
    }

    @Override public void onAccuracyChanged(Sensor sensor, int accuracy) { }
}
