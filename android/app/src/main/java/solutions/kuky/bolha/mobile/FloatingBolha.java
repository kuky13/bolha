// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.app.*;
import android.content.*;
import android.content.res.Configuration;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.os.Build;
import android.os.IBinder;
import android.provider.Settings;
import android.view.*;
import org.json.JSONObject;

public final class FloatingBolha extends Service implements Engine.Listener {
    static boolean active;
    private Engine engine;
    private WindowManager windows;
    private Stage pet, toy, message;
    private WindowManager.LayoutParams petParams, toyParams, messageParams;
    private final Rect area = new Rect();
    private boolean petAdded, toyAdded, messageAdded;

    @Override public int onStartCommand(Intent intent, int flags, int id) {
        if (intent != null && "stop".equals(intent.getAction())) {
            stopSelf();
            return START_NOT_STICKY;
        }
        if (active) return START_NOT_STICKY;
        if (!Settings.canDrawOverlays(this)) { stopSelf(); return START_NOT_STICKY; }
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (Build.VERSION.SDK_INT >= 26)
            manager.createNotificationChannel(new NotificationChannel("bolha", "Bolha flutuante", NotificationManager.IMPORTANCE_LOW));
        int immutable = PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE;
        PendingIntent open = PendingIntent.getActivity(this,1,new Intent(this,MainActivity.class),immutable);
        PendingIntent stop = PendingIntent.getService(this,2,new Intent(this,FloatingBolha.class).setAction("stop"),immutable);
        Notification.Builder notification = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this,"bolha") : new Notification.Builder(this);
        notification.setSmallIcon(R.drawable.ic_bolha).setContentTitle("Bolha flutuante")
                .setContentText("Toque para abrir os controles").setContentIntent(open).setOngoing(true)
                .addAction(android.R.drawable.ic_menu_close_clear_cancel,"Parar",stop);
        startForeground(14,notification.build());
        windows = getSystemService(WindowManager.class);
        engine = Engine.get(this);
        pet = new Stage(this,engine,"pet");
        toy = new Stage(this,engine,"toy");
        message = new Stage(this,engine,"message");
        petParams = params("BolhaMascote");
        toyParams = params("BolhaBrinquedo");
        messageParams = params("BolhaMensagem");
        messageParams.flags |= WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE;
        if (Build.VERSION.SDK_INT >= 31) {
            android.hardware.input.InputManager input = getSystemService(android.hardware.input.InputManager.class);
            messageParams.alpha = input.getMaximumObscuringOpacityForTouch();
        }
        active = true;
        updateArea();
        engine.listen(this);
        return START_NOT_STICKY;
    }

    @SuppressWarnings("deprecation")
    private WindowManager.LayoutParams params(String title) {
        int type = Build.VERSION.SDK_INT >= 26 ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                : WindowManager.LayoutParams.TYPE_PHONE;
        WindowManager.LayoutParams value = new WindowManager.LayoutParams(1,1,type,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE | WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT);
        value.gravity = Gravity.TOP | Gravity.LEFT;
        value.setTitle(title);
        return value;
    }

    @SuppressWarnings("deprecation")
    private void updateArea() {
        if (Build.VERSION.SDK_INT >= 30) {
            WindowMetrics metrics = windows.getCurrentWindowMetrics();
            area.set(metrics.getBounds());
            android.graphics.Insets insets = metrics.getWindowInsets().getInsetsIgnoringVisibility(
                    WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
            area.set(0,0,area.width()-insets.left-insets.right,area.height()-insets.top-insets.bottom);
        } else {
            android.util.DisplayMetrics metrics = new android.util.DisplayMetrics();
            windows.getDefaultDisplay().getMetrics(metrics);
            area.set(0,0,metrics.widthPixels,metrics.heightPixels);
        }
        engine.resize(area.width(),area.height());
    }

    @Override public void onConfigurationChanged(Configuration configuration) {
        super.onConfigurationChanged(configuration);
        if (active) updateArea();
    }

    @Override public void frame(JSONObject s,String error) {
        if (!active) return;
        if (error != null || !Settings.canDrawOverlays(this)) { stopSelf(); return; }
        Haptics.frame(this,s);
        try {
            layout(pet,petParams,s,"x","y","radius",petAdded);
            petAdded = true;
            if (s.optBoolean("toyVisible")) {
                layout(toy,toyParams,s,"toyX","toyY","toyRadius",toyAdded);
                toyAdded = true;
            } else if (toyAdded) { windows.removeView(toy); toyAdded=false; }
            if (!s.optString("text").isEmpty()) {
                int radius = (int)s.optDouble("radius",32);
                int width = Math.min(area.width(), Math.max(195,radius*5));
                int x = Math.max(0,Math.min(area.width()-width,(int)s.optDouble("x")-width/2));
                int y = (int)s.optDouble("y")-radius-43;
                if (y < 0) y = (int)s.optDouble("y")+radius+6;
                y = Math.max(0,Math.min(area.height()-35,y));
                place(message,messageParams,x,y,width,35,messageAdded);
                messageAdded=true;
            } else if (messageAdded) { windows.removeView(message); messageAdded=false; }
        } catch (SecurityException | WindowManager.BadTokenException failure) {
            android.util.Log.e("Bolha","Janela flutuante",failure);
            stopSelf();
        }
    }

    private void layout(Stage view, WindowManager.LayoutParams params, JSONObject s,
                        String xKey,String yKey,String radiusKey,boolean added) {
        int side = Math.round((float)s.optDouble(radiusKey,32)*2.2f);
        int x = (int)Math.round(s.optDouble(xKey,0)-side/2f);
        int y = (int)Math.round(s.optDouble(yKey,0)-side/2f);
        place(view,params,x,y,side,side,added);
    }

    private void place(Stage view, WindowManager.LayoutParams params, int x, int y, int width, int height, boolean added) {
        view.origin(x,y);
        boolean changed = params.x!=x || params.y!=y || params.width!=width || params.height!=height;
        params.x=x; params.y=y; params.width=width; params.height=height;
        if (!added) windows.addView(view,params);
        else if (changed) windows.updateViewLayout(view,params);
        view.invalidate();
    }

    @Override public void onDestroy() {
        active=false;
        if (engine!=null) engine.remove(this);
        if (petAdded) windows.removeView(pet);
        if (toyAdded) windows.removeView(toy);
        if (messageAdded) windows.removeView(message);
        stopForeground(STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
