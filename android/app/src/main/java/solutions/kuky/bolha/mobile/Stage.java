// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.RectF;
import android.net.Uri;
import android.os.Build;
import android.text.Layout;
import android.text.StaticLayout;
import android.text.TextPaint;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewConfiguration;
import android.view.WindowManager;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/** A snapshot in logical dp owns drawing and hit testing for this native surface. */
final class Stage extends View {
    private final Engine engine;
    private final String layer;
    private final float density;
    private final BolhaRenderer character = new BolhaRenderer();
    private final ObjectRenderer objects;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final DragMotion drag;
    private JSONObject frame = new JSONObject();
    private double animationEpoch = Double.NaN;
    private float originX, originY;
    private String held;
    private int pointerId = -1;
    private boolean paddle;

    Stage(Context context, Engine engine, String layer) {
        super(context);
        this.engine = engine;
        this.layer = layer;
        density = getResources().getDisplayMetrics().density;
        objects = new ObjectRenderer(engine,getResources().getConfiguration().fontScale);
        drag = new DragMotion(ViewConfiguration.get(context).getScaledTouchSlop() / density);
        setLayerType(View.LAYER_TYPE_SOFTWARE, null);
        setContentDescription(layer.equals("toy") ? "Brinquedo da Bolha" : layer.equals("preview") ? "Prévia das expressões da Bolha" : "Bolha");
        setClickable(!layer.equals("preview") && !layer.equals("message"));
    }

    void origin(float x, float y) { originX = x; originY = y; }
    void frame(JSONObject state) {
        frame = state;
        ReactionMediaCache.get(engine).retain(state.optJSONArray("objects"));
        invalidate();
    }
    private static float n(JSONObject value, String key, float fallback) { return BolhaRenderer.number(value,key,fallback); }

    private float animationPhase(JSONObject state) {
        double now=state.optDouble("phase",0);
        if (!Double.isFinite(now)) return 0;
        // Keep millisecond precision even after the device has been up for weeks.
        if (Double.isNaN(animationEpoch) || now<animationEpoch) animationEpoch=now;
        return (float)(now-animationEpoch);
    }

    @Override protected void onSizeChanged(int w, int h, int oldW, int oldH) {
        if (layer.isEmpty()) engine.resize(w / density, h / density);
    }

    @Override protected void onDraw(Canvas canvas) {
        JSONObject state = frame;
        if (layer.isEmpty()) canvas.drawColor(Color.rgb(24,20,32));
        if (layer.equals("pet-input")) {
            canvas.drawColor(Color.argb(1,0,0,0));
            return;
        }
        canvas.save(); canvas.scale(density,density); canvas.translate(-originX,-originY);
        float phase = animationPhase(state);
        if (layer.equals("preview")) drawPreview(canvas,state);
        else if (layer.startsWith("object:")) {
            JSONObject item = findObject(layer.substring(7));
            if (item != null) objects.draw(canvas,item,phase,this);
        } else if (layer.equals("toy")) {
            if (state.optBoolean("toyVisible")) objects.toy(canvas,state);
        } else if (layer.equals("message")) speech(canvas,state);
        else if (layer.equals("paddle")) paddle(canvas,state);
        else {
            if (layer.isEmpty()) {
                JSONArray all = state.optJSONArray("objects");
                if (all != null) for (int index = 0; index < all.length(); index++) {
                    JSONObject item = all.optJSONObject(index);
                    if (item != null && !item.optString("kind").equals("ball") && !item.optString("kind").equals("paper")) objects.draw(canvas,item,phase,this);
                }
            }
            JSONObject pose = state.optJSONObject("pose");
            if (state.optBoolean("visible",true) || pose != null && pose.optString("effect").equals("pop")) character.draw(canvas,state);
            if (layer.equals("pet-visual")) {
                JSONArray all=state.optJSONArray("objects");
                if (all!=null) for (int index=0;index<all.length();index++) {
                    JSONObject item=all.optJSONObject(index);
                    if (item!=null && item.optString("kind").equals("fireworks")) objects.draw(canvas,item,phase,this);
                }
                speech(canvas,state);
            }
            if (layer.isEmpty()) {
                if (state.optBoolean("toyVisible")) objects.toy(canvas,state);
                speech(canvas,state);
                paddle(canvas,state);
            }
        }
        canvas.restore();
    }

    private void drawPreview(Canvas canvas, JSONObject state) {
        try {
            JSONObject preview = new JSONObject();
            for (String key : new String[]{"pose","poseMode","gaze","earGaze","phase","preferences","emotion"})
                if (state.has(key)) preview.put(key,state.get(key));
            preview.put("x",getWidth()/density/2);
            preview.put("y",getHeight()/density/2);
            preview.put("radius",Math.min(64,getHeight()/density*.27));
            preview.put("visible",true);
            preview.put("angle",0);
            character.draw(canvas,preview);
        } catch (JSONException error) { android.util.Log.w("Bolha","Prévia indisponível",error); }
    }

    static RectF speechBounds(Context context, JSONObject state) {
        String text = state.optString("text");
        JSONArray area = state.optJSONArray("bounds");
        float left = area == null ? 0 : (float)area.optDouble(0);
        float top = area == null ? 0 : (float)area.optDouble(1);
        float right = area == null ? 360 : (float)area.optDouble(2,360);
        float bottom = area == null ? 720 : (float)area.optDouble(3,720);
        float width = Math.min(230,Math.max(60,right-left-16));
        TextPaint paint = new TextPaint(Paint.ANTI_ALIAS_FLAG);
        paint.setTextSize(12 * context.getResources().getConfiguration().fontScale);
        float measured = paint.measureText(text) + 22;
        width = Math.min(width,Math.max(60,measured));
        StaticLayout layout = StaticLayout.Builder.obtain(text,0,text.length(),paint,Math.max(1,(int)width-22)).setIncludePad(false).build();
        float height = layout.getHeight() + 28;
        float x = Math.max(left+8,Math.min(right-width-8,n(state,"x",left+width/2)-width/2));
        float y = n(state,"y",top)-n(state,"radius",68)-height-8;
        if (y < top+8) y = n(state,"y",top)+n(state,"radius",68)+8;
        y = Math.max(top+8,Math.min(bottom-height-8,y));
        return new RectF(x,y,x+width,y+height);
    }

    private void speech(Canvas canvas, JSONObject state) {
        if (state.optString("text").isEmpty()) return;
        int saved = canvas.saveLayerAlpha(null,Math.round(Math.max(0,Math.min(1,n(state,"speechAlpha",1)))*255));
        RectF rect=speechBounds(getContext(),state);
        objects.bubble(canvas,rect,state.optString("text"),state.optBoolean("thought"),rect.top>n(state,"y",0),n(state,"x",rect.centerX()));
        canvas.restoreToCount(saved);
    }

    private void paddle(Canvas canvas, JSONObject state) {
        JSONObject match = state.optJSONObject("pingpong");
        if (match == null) return;
        JSONArray cursor = state.optJSONArray("cursor");
        if (cursor == null) cursor = match.optJSONArray("cursor");
        float x = cursor == null ? 320 : (float)cursor.optDouble(0), y = cursor == null ? 300 : (float)cursor.optDouble(1);
        paint.setStyle(Paint.Style.FILL); paint.setColor(Color.rgb(199,169,244));
        canvas.drawRoundRect(x-7,y-26,x+7,y+26,7,7,paint);
        paint.setColor(Color.rgb(255,211,100)); canvas.drawRoundRect(x-3,y+20,x+3,y+45,3,3,paint);
        if (layer.isEmpty()) {
            paint.setColor(Color.rgb(236,231,245)); paint.setTextAlign(Paint.Align.CENTER); paint.setTextSize(15);
            canvas.drawText("Você " + match.optInt("playerScore") + "  ·  Bolha " + match.optInt("petScore"),getWidth()/density/2,28,paint);
        }
    }

    private JSONObject findObject(String id) {
        JSONArray all = frame.optJSONArray("objects");
        if (all != null) for (int index = 0; index < all.length(); index++) {
            JSONObject item = all.optJSONObject(index);
            if (item != null && item.optString("id").equals(id)) return item;
        }
        return null;
    }
    private float rawX(MotionEvent event,int index) { return (event.getRawX()+event.getX(index)-event.getX())/density; }
    private float rawY(MotionEvent event,int index) { return (event.getRawY()+event.getY(index)-event.getY())/density; }

    private void updateTouchCursor(MotionEvent event,int index) {
        JSONObject preferences=frame.optJSONObject("preferences");
        if (preferences != null && !preferences.optBoolean("senseCursor",true)) return;
        engine.action("cursor","",event.getX(index)/density+originX,
                event.getY(index)/density+originY,0,0);
    }

    private final Runnable showMenu = this::showObjectMenu;

    private void showObjectMenu() {
        if (held == null || drag.moved()) return;
        JSONObject item = findObject(held);
        if (item == null) return;
        String id = held;
        release(true);
        objectMenu(item,id);
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        if (layer.equals("message") || layer.equals("preview")) return false;
        int action = event.getActionMasked();
        int cursorIndex=action==MotionEvent.ACTION_DOWN?0:event.findPointerIndex(pointerId);
        if (cursorIndex>=0 && (action==MotionEvent.ACTION_DOWN || action==MotionEvent.ACTION_MOVE
                || action==MotionEvent.ACTION_UP)) updateTouchCursor(event,cursorIndex);
        if (action == MotionEvent.ACTION_DOWN) {
            pointerId = event.getPointerId(0);
            float x = event.getX()/density+originX, y = event.getY()/density+originY;
            if (frame.optJSONObject("pingpong") != null) { paddle = true; return true; }
            float cx, cy;
            if (layer.startsWith("object:")) {
                JSONObject item = findObject(layer.substring(7));
                if (item == null || item.optString("kind").equals("fireworks")) return false;
                held = item.optString("id"); cx = n(item,"x",x); cy = n(item,"y",y);
            } else if (layer.equals("toy") || layer.isEmpty() && frame.optBoolean("toyVisible") && Math.hypot(n(frame,"toyX",0)-x,n(frame,"toyY",0)-y) <= Math.max(24,n(frame,"toyRadius",18)+8)) {
                held = "toy"; cx = n(frame,"toyX",x); cy = n(frame,"toyY",y);
            } else if (layer.equals("pet") || layer.equals("pet-input") || layer.isEmpty() && Math.hypot(n(frame,"x",0)-x,n(frame,"y",0)-y) <= n(frame,"radius",68)+7) {
                held = "pet"; cx = n(frame,"x",x); cy = n(frame,"y",y);
            } else {
                JSONObject item = hitObject(x,y);
                if (item == null) return false;
                held = item.optString("id"); cx = n(item,"x",x); cy = n(item,"y",y);
            }
            drag.start(cx,cy,rawX(event,0),rawY(event,0),event.getEventTime());
            if (getParent() != null) getParent().requestDisallowInterceptTouchEvent(true);
            engine.action("drag-start",held,cx,cy,0,0);
            postDelayed(showMenu,ViewConfiguration.getLongPressTimeout());
            return true;
        }
        int index = event.findPointerIndex(pointerId);
        if (action == MotionEvent.ACTION_CANCEL || index < 0 || action == MotionEvent.ACTION_POINTER_UP && event.getPointerId(event.getActionIndex()) == pointerId) {
            release(true); paddle = false; pointerId = -1; return true;
        }
        if (action == MotionEvent.ACTION_POINTER_DOWN || action == MotionEvent.ACTION_POINTER_UP) return held != null || paddle;
        if (paddle) {
            if (action == MotionEvent.ACTION_UP) { paddle = false; pointerId = -1; }
            return true;
        }
        if (held == null) return false;
        drag.sample(rawX(event,index),rawY(event,index),event.getEventTime());
        if (action == MotionEvent.ACTION_MOVE) {
            if (drag.moved()) removeCallbacks(showMenu);
            engine.action("drag",held,drag.x(),drag.y(),0,0);
            return true;
        }
        if (action == MotionEvent.ACTION_UP) {
            String target = held; boolean moved = drag.moved();
            release(false);
            if (!moved) {
                if (target.equals("pet")) engine.action("caress","",0,0,0,0);
                else if (target.equals("toy")) engine.action("lift","",0,0,0,0);
                if (Haptics.enabled(getContext())) performHapticFeedback(android.view.HapticFeedbackConstants.VIRTUAL_KEY);
                performClick();
            }
            return true;
        }
        return true;
    }

    private JSONObject hitObject(float x,float y) {
        JSONArray all = frame.optJSONArray("objects");
        if (all != null) for (int i = all.length()-1; i >= 0; i--) {
            JSONObject item = all.optJSONObject(i);
            if (item != null && !item.optString("kind").equals("fireworks") && !item.optString("kind").equals("ball") && Math.abs(n(item,"x",0)-x) <= n(item,"width",0)/2 && Math.abs(n(item,"y",0)-y) <= n(item,"height",0)/2) return item;
        }
        return null;
    }

    private void release(boolean cancelled) {
        removeCallbacks(showMenu);
        if (held != null) {
            engine.action("drag-end",cancelled ? "cancel-"+held : held,drag.x(),drag.y(),cancelled ? 0 : drag.vx(),cancelled ? 0 : drag.vy());
            held = null;
        }
        pointerId = -1;
        if (getParent() != null) getParent().requestDisallowInterceptTouchEvent(false);
    }

    private void objectMenu(JSONObject item,String id) {
        String source = item.optString("sourceUrl");
        String[] choices = source.isEmpty() ? new String[]{"Dispensar"} : new String[]{"Informações e origem","Abrir origem","Dispensar"};
        AlertDialog dialog = new AlertDialog.Builder(getContext()).setTitle(item.optString("kind").equals("meme") ? "Reação da Bolha" : "Objeto da Bolha").setItems(choices,(window,selected) -> {
            if (selected == choices.length-1) {
                String kind = item.optString("kind");
                engine.action(kind.equals("notebook") ? "notebook" : kind.equals("corner") ? "corner" : "dismiss",id,0,0,0,0);
            } else if (selected == 0) {
                showDialog(new AlertDialog.Builder(getContext()).setTitle("Origem da reação").setMessage(item.optString("provider")+"\n"+item.optString("attribution")+"\n"+source).setPositiveButton("Fechar",null).create());
            } else {
                Uri uri = Uri.parse(source); String host = uri.getHost();
                if ("https".equals(uri.getScheme()) && host != null && (host.equals("reactiongifs.com") || host.equals("www.reactiongifs.com") || host.equals("nekos.best") || host.equals("www.nekos.best"))) {
                    try { getContext().startActivity(new Intent(Intent.ACTION_VIEW,uri).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)); }
                    catch (android.content.ActivityNotFoundException error) { android.util.Log.w("Bolha","Navegador indisponível",error); }
                }
            }
        }).setNegativeButton("Cancelar",null).create();
        showDialog(dialog);
    }

    @SuppressWarnings("deprecation")
    private void showDialog(AlertDialog dialog) {
        if (!(getContext() instanceof Activity)) dialog.getWindow().setType(Build.VERSION.SDK_INT >= 26 ? WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY : WindowManager.LayoutParams.TYPE_PHONE);
        dialog.show();
    }
    @Override protected void onDetachedFromWindow() { release(true); paddle = false; super.onDetachedFromWindow(); }
    @Override public boolean performClick() { super.performClick(); return true; }
}
