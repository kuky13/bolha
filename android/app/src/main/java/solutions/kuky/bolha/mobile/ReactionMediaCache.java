// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Movie;
import android.graphics.Paint;
import android.graphics.RectF;
import android.os.SystemClock;
import android.view.View;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import org.json.JSONArray;
import org.json.JSONObject;

/** Decodes the bounded Python payloads in memory and drops them with their objects. */
final class ReactionMediaCache {
    private static ReactionMediaCache instance;
    static ReactionMediaCache get(Engine engine) {
        if (instance == null) instance = new ReactionMediaCache(engine);
        return instance;
    }

    private final Engine engine;
    private final Map<String, Media> images = new HashMap<>();
    private final Set<String> requested = new HashSet<>();
    private final ThreadPoolExecutor decoder = new ThreadPoolExecutor(1,1,0,TimeUnit.MILLISECONDS,
        new ArrayBlockingQueue<>(4), runnable -> {
            Thread thread=new Thread(runnable,"Bolha image decoder");
            thread.setDaemon(true);
            return thread;
        });
    private Set<String> alive = new HashSet<>();

    private ReactionMediaCache(Engine engine) { this.engine = engine; }

    void retain(JSONArray objects) {
        Set<String> next = new HashSet<>();
        if (objects != null) for (int i = 0; i < objects.length(); i++) {
            JSONObject object = objects.optJSONObject(i);
            if (object != null && object.optString("kind").equals("meme")) next.add(object.optString("id"));
        }
        for (String id : new HashSet<>(images.keySet())) if (!next.contains(id)) {
            images.remove(id).close();
        }
        requested.retainAll(next);
        alive = next;
    }

    void draw(Canvas canvas, JSONObject object, RectF target, View view) {
        String id = object.optString("id");
        Media media = images.get(id);
        if (media == null && object.optBoolean("mediaReady") && requested.add(id)) {
            engine.loadMedia(id, bytes -> {
                if (!alive.contains(id)) return;
                if (bytes == null) { failed(id); return; }
                try {
                    decoder.execute(() -> {
                        Media decoded;
                        try { decoded=Media.decode(bytes); }
                        catch (RuntimeException error) { decoded=null; }
                        Media result=decoded;
                        view.post(() -> {
                            if (!alive.contains(id)) { if (result!=null) result.close(); return; }
                            if (result==null) failed(id);
                            else images.put(id,result);
                            view.invalidate();
                        });
                    });
                } catch (RejectedExecutionException error) { failed(id); }
            });
        }
        if (media != null) {
            media.draw(canvas, target);
            if (media.movie != null) view.postInvalidateOnAnimation();
        }
    }

    private void failed(String id) {
        try { engine.control(new JSONObject().put("type","reaction-failed").put("id",id)); }
        catch (org.json.JSONException error) { android.util.Log.w("Bolha","Reação indisponível",error); }
    }

    @SuppressWarnings("deprecation")
    private static final class Media {
        private static final int MAX_SIDE = 2048;
        final Bitmap bitmap;
        final Movie movie;
        final long started = SystemClock.uptimeMillis();
        final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);

        private Media(Bitmap bitmap, Movie movie) { this.bitmap = bitmap; this.movie = movie; }

        static Media decode(byte[] bytes) {
            if (bytes.length < 12 || bytes.length > 6 * 1024 * 1024) return null;
            boolean gif = bytes[0] == 'G' && bytes[1] == 'I' && bytes[2] == 'F';
            if (gif) {
                int width = (bytes[6] & 255) | ((bytes[7] & 255) << 8);
                int height = (bytes[8] & 255) | ((bytes[9] & 255) << 8);
                if (!dimensions(width, height)) return null;
                Movie movie = Movie.decodeByteArray(bytes, 0, bytes.length);
                return movie == null ? null : new Media(null, movie);
            }
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inJustDecodeBounds = true;
            BitmapFactory.decodeByteArray(bytes, 0, bytes.length, options);
            if (!dimensions(options.outWidth, options.outHeight)) return null;
            options.inJustDecodeBounds = false;
            options.inSampleSize = 1;
            while (Math.max(options.outWidth, options.outHeight) / options.inSampleSize > 640) options.inSampleSize *= 2;
            Bitmap bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.length, options);
            return bitmap == null ? null : new Media(bitmap, null);
        }

        private static boolean dimensions(int width, int height) {
            return width > 0 && height > 0 && width <= MAX_SIDE && height <= MAX_SIDE;
        }

        void draw(Canvas canvas, RectF target) {
            float width = movie != null ? movie.width() : bitmap.getWidth();
            float height = movie != null ? movie.height() : bitmap.getHeight();
            float scale = Math.min(target.width() / width, target.height() / height);
            float x = target.centerX() - width * scale / 2, y = target.centerY() - height * scale / 2;
            if (movie != null) {
                movie.setTime((int)((SystemClock.uptimeMillis() - started) % Math.max(1, movie.duration())));
                canvas.save(); canvas.translate(x, y); canvas.scale(scale, scale); movie.draw(canvas, 0, 0, paint); canvas.restore();
            } else {
                canvas.drawBitmap(bitmap, null, new RectF(x, y, x + width * scale, y + height * scale), paint);
            }
        }

        void close() { if (bitmap != null) bitmap.recycle(); }
    }
}
