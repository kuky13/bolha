// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.content.Context;
import android.os.Handler;
import android.os.HandlerThread;
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
    private static Engine instance;
    static Engine get(Context context) {
        if (instance == null) instance = new Engine(context.getApplicationContext());
        return instance;
    }

    private final Context context;
    private final Handler worker;
    private final Handler main = new Handler(android.os.Looper.getMainLooper());
    private final Set<Listener> listeners = new LinkedHashSet<>();
    private PyObject python;
    private boolean running;
    private long previous;
    private volatile JSONObject state = new JSONObject();

    private Engine(Context context) {
        this.context = context;
        HandlerThread thread = new HandlerThread("Bolha physics");
        thread.start();
        worker = new Handler(thread.getLooper());
    }

    void listen(Listener listener) {
        listeners.add(listener);
        if (listeners.size() == 1) worker.post(() -> {
            running = true;
            previous = SystemClock.uptimeMillis();
            worker.removeCallbacks(step);
            step.run();
        });
    }

    void remove(Listener listener) {
        listeners.remove(listener);
        if (listeners.isEmpty()) worker.post(() -> {
            running = false;
            worker.removeCallbacks(step);
            if (python != null) {
                try { python.callAttr("save"); }
                catch (RuntimeException error) { android.util.Log.e("Bolha", "Salvar", error); }
            }
        });
    }

    JSONObject state() { return state; }

    void resize(float width, float height) {
        worker.post(() -> {
            try { start(); python.callAttr("resize", width, height); }
            catch (Exception error) { report(null, error); }
        });
    }

    void action(String kind, String target, float x, float y, float vx, float vy) {
        worker.post(() -> {
            try { start(); python.callAttr("action", kind, target, x, y, vx, vy); }
            catch (Exception error) { report(null, error); }
        });
    }

    private void start() throws IOException {
        if (python != null) return;
        File content = new File(context.getFilesDir(), "content");
        extract("content", content);
        if (!Python.isStarted()) Python.start(new AndroidPlatform(context));
        PyObject module = Python.getInstance().getModule("mobile");
        module.callAttr("start", new File(context.getFilesDir(), "memory").getPath(), content.getPath());
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
                state = new JSONObject(python.callAttr("tick", Math.min(.05, (now-previous)/1000.)).toString());
                previous = now;
                report(state, null);
                worker.postDelayed(this, Math.max(1, 33 - (SystemClock.uptimeMillis()-now)));
            } catch (Exception error) {
                report(null, error);
            }
        }
    };

    private void report(JSONObject value, Exception error) {
        if (error != null) android.util.Log.e("Bolha", "Motor", error);
        main.post(() -> {
            for (Listener listener : new LinkedHashSet<>(listeners))
                listener.frame(value, error == null ? null : "A Bolha não conseguiu abrir a sessão.");
        });
    }
}
