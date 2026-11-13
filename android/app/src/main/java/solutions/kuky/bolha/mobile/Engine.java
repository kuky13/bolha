// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.PowerManager;
import android.os.SystemClock;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import org.json.JSONObject;
import java.io.*;
import java.util.LinkedHashSet;
import java.util.Set;

final class Engine {
    interface Listener { void frame(JSONObject state, String error); }
    interface MediaListener { void loaded(byte[] data); }
    private static Engine instance;
    static Engine get(Context context) {
        if (instance == null) instance = new Engine(context.getApplicationContext());
        return instance;
    }

    private final Context context;
    private final Handler worker;
    private final Handler main = new Handler(android.os.Looper.getMainLooper());
    private final Set<Listener> listeners = new LinkedHashSet<>();
    private final PhoneMotion phoneMotion;
    private final UsageContext usageContext;
    private final Object moveLock = new Object();
    private Action pendingMove;
    private PyObject python;
    private boolean running, screenAwake = true, screenReceiverRegistered;
    private long previous, lastContext;
    private volatile long lastInteraction = SystemClock.uptimeMillis();
    private volatile JSONObject state = new JSONObject();

    private Engine(Context context) {
        this.context = context;
        HandlerThread thread = new HandlerThread("Bolha physics");
        thread.start();
        worker = new Handler(thread.getLooper());
        phoneMotion = new PhoneMotion(context,this);
        usageContext = new UsageContext(context);
    }

    void listen(Listener listener) {
        if (!listeners.add(listener)) return;
        if (!screenReceiverRegistered) {
            screenAwake = context.getSystemService(PowerManager.class).isInteractive();
            IntentFilter filter = new IntentFilter(Intent.ACTION_SCREEN_ON);
            filter.addAction(Intent.ACTION_SCREEN_OFF);
            if (Build.VERSION.SDK_INT >= 33) context.registerReceiver(screenReceiver,filter,Context.RECEIVER_NOT_EXPORTED);
            else context.registerReceiver(screenReceiver,filter);
            screenReceiverRegistered = true;
        }
        updateRunning();
    }

    void remove(Listener listener) {
        listeners.remove(listener);
        if (listeners.isEmpty() && screenReceiverRegistered) {
            context.unregisterReceiver(screenReceiver);
            screenReceiverRegistered = false;
        }
        updateRunning();
    }

    private final BroadcastReceiver screenReceiver = new BroadcastReceiver() {
        @Override public void onReceive(Context context, Intent intent) {
            screenAwake = Intent.ACTION_SCREEN_ON.equals(intent.getAction());
            updateRunning();
        }
    };

    private void updateRunning() {
        boolean active = !listeners.isEmpty() && screenAwake;
        JSONObject preferences = state.optJSONObject("preferences");
        phoneMotion.update(active,preferences == null ? new JSONObject() : preferences);
        worker.post(() -> {
            if (active && !running) {
                running=true;
                previous=SystemClock.uptimeMillis();
                step.run();
            } else if (!active && running) {
                running=false;
                worker.removeCallbacks(step);
                worker.removeCallbacks(sendMove);
                synchronized (moveLock) { pendingMove=null; }
                if (python != null) {
                    try {
                        python.callAttr("control","{\"type\":\"suspend\"}");
                        python.callAttr("save");
                    }
                    catch (RuntimeException error) { report(null,error); }
                }
            }
        });
    }

    JSONObject state() { return state; }
    float density() { return context.getResources().getDisplayMetrics().density; }

    void resize(float width, float height) { invoke("resize",width,height,density()); }
    void control(JSONObject command) { invoke("control",command.toString()); }
    void configure(JSONObject preferences) {
        lastInteraction=SystemClock.uptimeMillis();
        if (preferences.has("hapticsEnabled")) context.getSharedPreferences("options",0).edit()
                .putBoolean("haptics",preferences.optBoolean("hapticsEnabled",true)).apply();
        invoke("configure",preferences.toString());
    }
    void motion(float ax, float ay, boolean shake) { invoke("motion",ax,ay,shake); }

    void loadMedia(String id, MediaListener callback) {
        worker.post(() -> {
            byte[] bytes=null;
            try { start(); bytes=python.callAttr("media",id).toJava(byte[].class); }
            catch (RuntimeException | IOException error) { android.util.Log.w("Bolha","Imagem indisponível",error); }
            byte[] result=bytes;
            main.post(() -> callback.loaded(result));
        });
    }

    private void invoke(String method, Object... arguments) {
        worker.post(() -> {
            try { start(); python.callAttr(method,arguments); }
            catch (Exception error) { report(null,error); }
        });
    }

    void action(String kind, String target, float x, float y, float vx, float vy) {
        lastInteraction=SystemClock.uptimeMillis();
        Action action=new Action(kind,target,x,y,vx,vy);
        if (kind.equals("drag")) {
            synchronized (moveLock) { pendingMove=action; }
            worker.removeCallbacks(sendMove);
            worker.post(sendMove);
            return;
        }
        Action lastMove;
        synchronized (moveLock) { lastMove=pendingMove; pendingMove=null; }
        worker.removeCallbacks(sendMove);
        worker.post(() -> {
            try {
                start();
                if (lastMove != null) send(lastMove);
                send(action);
            } catch (Exception error) { report(null,error); }
        });
    }

    private final Runnable sendMove = () -> {
        Action action;
        synchronized (moveLock) { action=pendingMove; pendingMove=null; }
        if (action == null) return;
        try { start(); send(action); }
        catch (Exception error) { report(null,error); }
    };

    private void send(Action action) {
        python.callAttr("action",action.kind,action.target,action.x,action.y,action.vx,action.vy);
    }

    private static final class Action {
        final String kind,target;
        final float x,y,vx,vy;
        Action(String kind,String target,float x,float y,float vx,float vy) {
            this.kind=kind;this.target=target;this.x=x;this.y=y;this.vx=vx;this.vy=vy;
        }
    }

    private void start() throws IOException {
        if (python != null) return;
        File content = new File(context.getFilesDir(), "content");
        extract("content", content);
        if (!Python.isStarted()) Python.start(new AndroidPlatform(context));
        PyObject module = Python.getInstance().getModule("mobile");
        File memory=new File(context.getFilesDir(),"memory");
        boolean hasPreferences=new File(memory,"config.json").isFile();
        module.callAttr("start",memory.getPath(),content.getPath());
        android.content.SharedPreferences oldOptions=context.getSharedPreferences("options",0);
        if (!hasPreferences && oldOptions.contains("haptics"))
            module.callAttr("configure","{\"hapticsEnabled\":"+oldOptions.getBoolean("haptics",true)+"}");
        python = module;
    }

    private void extract(String path, File output) throws IOException {
        String[] children = context.getAssets().list(path);
        if (children != null && children.length > 0) {
            if (!output.isDirectory() && !output.mkdirs()) throw new IOException(path);
            for (String child : children) extract(path + "/" + child, new File(output, child));
        } else {
            try (InputStream in = context.getAssets().open(path);
                 OutputStream out = new FileOutputStream(output)) {
                byte[] buffer = new byte[8192];
                for (int n; (n = in.read(buffer)) >= 0;) out.write(buffer, 0, n);
            }
        }
    }

    private final Runnable step = new Runnable() {
        public void run() {
            if (!running) return;
            long now = SystemClock.uptimeMillis();
            try {
                start();
                JSONObject preferences=state.optJSONObject("preferences");
                if (now-lastContext>=500) {
                    lastContext=now;
                    boolean readApp=preferences!=null && preferences.optBoolean("senseApp",false);
                    boolean readIdle=preferences!=null && preferences.optBoolean("senseIdle",false);
                    python.callAttr("context",readApp?usageContext.activePackage():"",
                            readIdle?(now-lastInteraction)/1000.:-1.);
                }
                state = new JSONObject(python.callAttr("tick", Math.min(.05, (now-previous)/1000.)).toString());
                state.put("motionAvailable",phoneMotion.available());
                state.put("usageAccess",UsageContext.permitted(context));
                previous = now;
                report(state, null);
                int interval=state.optJSONObject("preferences") == null ? 16
                        : 1000/Math.max(30,Math.min(60,state.optJSONObject("preferences").optInt("frameRate",60)));
                worker.postDelayed(this, Math.max(1, interval - (SystemClock.uptimeMillis()-now)));
            } catch (Exception error) {
                running=false;
                report(null, error);
            }
        }
    };

    private void report(JSONObject value, Exception error) {
        if (error != null) android.util.Log.e("Bolha", "Motor", error);
        main.post(() -> {
            JSONObject preferences=state.optJSONObject("preferences");
            phoneMotion.update(error == null && !listeners.isEmpty() && screenAwake,
                    preferences == null ? new JSONObject() : preferences);
            for (Listener listener : new LinkedHashSet<>(listeners))
                listener.frame(value == null ? state : value, error == null ? null : "A Bolha não conseguiu atualizar a sessão.");
        });
    }
}
