// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.app.*;
import android.content.*;
import android.content.res.Configuration;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.graphics.RectF;
import android.os.Build;
import android.os.IBinder;
import android.provider.Settings;
import android.view.*;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONObject;

public final class FloatingBolha extends Service implements Engine.Listener {
    static boolean active;
    private Engine engine;
    private WindowManager windows;
    private final Rect area = new Rect();
    private final Map<String,Layer> layers = new HashMap<>();
    private float density;

    private final class Layer {
        final Stage view;
        final WindowManager.LayoutParams params;
        boolean added;
        Layer(String type,String title,boolean interactive) {
            view=new Stage(FloatingBolha.this,engine,type);
            params=windowParams(title,interactive);
        }
    }

    @Override public int onStartCommand(Intent intent,int flags,int id) {
        if (intent!=null && "stop".equals(intent.getAction())) {
            stopSelf();return START_NOT_STICKY;
        }
        if (active) return START_NOT_STICKY;
        if (!Settings.canDrawOverlays(this)) { stopSelf();return START_NOT_STICKY; }
        NotificationManager manager=getSystemService(NotificationManager.class);
        if (Build.VERSION.SDK_INT>=26)
            manager.createNotificationChannel(new NotificationChannel("bolha","Bolha flutuante",NotificationManager.IMPORTANCE_LOW));
        int immutable=PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE;
        PendingIntent open=PendingIntent.getActivity(this,1,new Intent(this,MainActivity.class),immutable);
        PendingIntent stop=PendingIntent.getService(this,2,new Intent(this,FloatingBolha.class).setAction("stop"),immutable);
        Notification.Builder notification=Build.VERSION.SDK_INT>=26
                ?new Notification.Builder(this,"bolha"):new Notification.Builder(this);
        notification.setSmallIcon(R.drawable.ic_bolha).setContentTitle("Bolha flutuante")
            .setContentText("Toque para abrir a Bolha e sua Central").setContentIntent(open).setOngoing(true)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel,"Parar",stop);
        startForeground(14,notification.build());
        windows=getSystemService(WindowManager.class);
        engine=Engine.get(this);
        density=getResources().getDisplayMetrics().density;
        active=true;
        updateArea();
        engine.listen(this);
        return START_NOT_STICKY;
    }

    @SuppressWarnings("deprecation")
    private WindowManager.LayoutParams windowParams(String title,boolean interactive) {
        int type=Build.VERSION.SDK_INT>=26?WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
                :WindowManager.LayoutParams.TYPE_PHONE;
        int flags=WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE
                |WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL
                |WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN;
        if (!interactive) flags|=WindowManager.LayoutParams.FLAG_NOT_TOUCHABLE|WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS;
        WindowManager.LayoutParams value=new WindowManager.LayoutParams(1,1,type,flags,PixelFormat.TRANSLUCENT);
        value.gravity=Gravity.TOP|Gravity.LEFT;
        value.setTitle(title);
        if (Build.VERSION.SDK_INT>=30) value.setFitInsetsTypes(0);
        if (!interactive && Build.VERSION.SDK_INT>=31) {
            android.hardware.input.InputManager input=getSystemService(android.hardware.input.InputManager.class);
            value.alpha=input.getMaximumObscuringOpacityForTouch();
        }
        return value;
    }

    @SuppressWarnings("deprecation")
    private void updateArea() {
        density=getResources().getDisplayMetrics().density;
        if (Build.VERSION.SDK_INT>=30) {
            WindowMetrics metrics=windows.getCurrentWindowMetrics();
            Rect bounds=metrics.getBounds();
            android.graphics.Insets insets=metrics.getWindowInsets().getInsetsIgnoringVisibility(
                    WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());
            area.set(bounds.left+insets.left,bounds.top+insets.top,
                    bounds.right-insets.right,bounds.bottom-insets.bottom);
        } else {
            android.util.DisplayMetrics metrics=new android.util.DisplayMetrics();
            windows.getDefaultDisplay().getRealMetrics(metrics);
            int status=systemDimension("status_bar_height"),navigation=systemDimension("navigation_bar_height");
            area.set(0,status,metrics.widthPixels,Math.max(status+100,metrics.heightPixels-navigation));
        }
        engine.resize(area.width()/density,area.height()/density);
    }

    private int systemDimension(String name) {
        int id=getResources().getIdentifier(name,"dimen","android");
        return id==0?0:getResources().getDimensionPixelSize(id);
    }

    @Override public void onConfigurationChanged(Configuration configuration) {
        super.onConfigurationChanged(configuration);
        detachAll();
        if (active) updateArea();
    }

    @Override public void frame(JSONObject state,String error) {
        if (!active) return;
        if (error!=null || !Settings.canDrawOverlays(this)) { stopSelf();return; }
        Haptics.frame(this,state);
        Set<String> wanted=new HashSet<>();
        try {
            float radius=(float)state.optDouble("radius",68);
            float x=(float)state.optDouble("x"),y=(float)state.optDouble("y");
            JSONArray objects=state.optJSONArray("objects");
            RectF visual=new RectF(x-radius*2.1f,y-radius*2.1f,x+radius*2.1f,y+radius*2.1f);
            if (!state.optString("text").isEmpty() && state.optDouble("speechAlpha",1)>0)
                visual.union(Stage.speechBounds(this,state));
            if (objects!=null) for (int index=0;index<objects.length();index++) {
                JSONObject object=objects.optJSONObject(index);
                if (object==null || !object.optString("kind").equals("fireworks")) continue;
                float ox=(float)object.optDouble("x"),oy=(float)object.optDouble("y");
                float halfWidth=(float)object.optDouble("width",300)/2,halfHeight=(float)object.optDouble("height",250)/2;
                visual.union(ox-halfWidth,oy-halfHeight,ox+halfWidth,oy+halfHeight);
            }
            if (state.optBoolean("visible",true)) {
                show("pet-visual","pet-visual","BolhaVisual",false,state,
                        visual.left,visual.top,visual.width(),visual.height(),wanted);
                JSONObject pose=state.optJSONObject("pose");
                if (state.optBoolean("interactive",true) && (pose==null || !pose.has("corner_peek"))) {
                    float inputSize=Math.max(48,radius*2);
                    show("pet","pet-input","BolhaMascote",true,state,
                            x-inputSize/2,y-inputSize/2,inputSize,inputSize,wanted);
                }
            }
            if (state.optBoolean("toyVisible")) {
                float size=Math.max(48,(float)state.optDouble("toyRadius",16)*2.4f);
                show("toy","toy","BolhaBrinquedo",true,state,
                        (float)state.optDouble("toyX")-size/2,(float)state.optDouble("toyY")-size/2,size,size,wanted);
            }
            if (objects!=null) for (int index=0;index<objects.length();index++) {
                JSONObject object=objects.optJSONObject(index);
                if (object==null) continue;
                String kind=object.optString("kind"),id=object.optString("id");
                if (id.isEmpty() || kind.equals("ball") || kind.equals("paper") || kind.equals("fireworks")) continue;
                if (kind.equals("meme") && !object.optBoolean("mediaReady")) continue;
                float width=(float)object.optDouble("width",120),height=(float)object.optDouble("height",90);
                show("object:"+id,"object:"+id,"BolhaObjeto-"+id,true,state,
                        (float)object.optDouble("x")-width/2,(float)object.optDouble("y")-height/2,width,height,wanted);
            }
            JSONObject match=state.optJSONObject("pingpong");
            if (match!=null) {
                float width=Math.min(76,area.width()/density*.22f);
                show("paddle","paddle","BolhaRaquete",true,state,
                        area.width()/density-width,0,width,area.height()/density,wanted);
            }
            for (String key:new HashSet<>(layers.keySet())) if (!wanted.contains(key)) remove(key);
        } catch (SecurityException|WindowManager.BadTokenException failure) {
            android.util.Log.e("Bolha","Janela flutuante",failure);stopSelf();
        }
    }

    private void show(String key,String type,String title,boolean interactive,JSONObject state,
                      float x,float y,float width,float height,Set<String> wanted) {
        wanted.add(key);
        Layer layer=layers.get(key);
        if (layer==null) { layer=new Layer(type,title,interactive);layers.put(key,layer); }
        layer.view.frame(state);
        layer.view.origin(x,y);
        WindowManager.LayoutParams params=layer.params;
        int px=area.left+Math.round(x*density),py=area.top+Math.round(y*density);
        int w=Math.max(1,Math.round(width*density)),h=Math.max(1,Math.round(height*density));
        boolean changed=params.x!=px || params.y!=py || params.width!=w || params.height!=h;
        params.x=px;params.y=py;params.width=w;params.height=h;
        if (!layer.added) { windows.addView(layer.view,params);layer.added=true; }
        else if (changed) windows.updateViewLayout(layer.view,params);
    }

    private void remove(String key) {
        Layer layer=layers.remove(key);
        if (layer!=null && layer.added) windows.removeView(layer.view);
    }

    private void detachAll() {
        for (String key:new HashSet<>(layers.keySet())) remove(key);
    }

    @Override public void onDestroy() {
        active=false;
        detachAll();
        if (engine!=null) engine.remove(this);
        stopForeground(STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }

    @Override public IBinder onBind(Intent intent) { return null; }
}
