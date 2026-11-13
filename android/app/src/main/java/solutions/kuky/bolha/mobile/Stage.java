// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.content.Context;
import android.graphics.*;
import android.view.MotionEvent;
import android.view.VelocityTracker;
import android.view.View;
import org.json.JSONArray;
import org.json.JSONObject;

final class Stage extends View {
    private final Engine engine;
    private final String layer;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private float originX, originY, downX, downY, offsetX, offsetY;
    private String held;
    private VelocityTracker velocity;
    private boolean moved;
    private double previousImpact;
    private float impactX, impactY;
    private long impactAt;

    Stage(Context context, Engine engine, String layer) {
        super(context);
        this.engine = engine;
        this.layer = layer;
        setLayerType(View.LAYER_TYPE_SOFTWARE, null);
        setContentDescription(layer.equals("toy") ? "Brinquedo da Bolha" : "Bolha");
        setClickable(true);
    }

    void origin(float x, float y) { originX = x; originY = y; }
    private float n(JSONObject o, String key, float fallback) { return (float)o.optDouble(key, fallback); }
    private int color(String value) { return Color.parseColor(value); }

    @Override protected void onSizeChanged(int w, int h, int oldW, int oldH) {
        if (layer.isEmpty()) engine.resize(w, h);
    }

    @Override protected void onDraw(Canvas canvas) {
        JSONObject s = engine.state();
        if (layer.isEmpty()) canvas.drawColor(color("#181420"));
        canvas.save();
        canvas.translate(-originX, -originY);
        if (!layer.equals("toy")) {
            float x = n(s,"x",getWidth()/2f), y = n(s,"y",getHeight()/2f), r = n(s,"radius",38);
            if (!layer.equals("message")) pet(canvas,s,x,y,r);
            if (layer.isEmpty()) {
                JSONObject notebook = s.optJSONObject("notebook");
                if (notebook != null) notebook(canvas,notebook);
                if (s.optBoolean("toyVisible")) toy(canvas,s);
            }
            String text = s.optString("text");
            if (!text.isEmpty() && (layer.isEmpty() || layer.equals("message"))) message(canvas, text, x, y, r);
            double impact = s.optDouble("impact");
            if (impact > 0 && impact != previousImpact) {
                previousImpact = impact;
                impactX = n(s,"impactX",x);
                impactY = n(s,"impactY",y);
                impactAt = android.os.SystemClock.uptimeMillis();
            }
            float age = (android.os.SystemClock.uptimeMillis()-impactAt)/250f;
            if (age >= 0 && age < 1) {
                paint.setColor(color("#D5FFFF")); paint.setAlpha((int)(190*(1-age)));
                paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(2);
                canvas.drawCircle(impactX,impactY,5+17*age,paint);
                paint.setStyle(Paint.Style.FILL); paint.setAlpha(255);
            }
        } else {
            toy(canvas,s);
        }
        canvas.restore();
    }

    private void pet(Canvas c, JSONObject s, float x, float y, float r) {
        boolean angry = s.optString("emotion").equals("bravo");
        float scale = r/49f;
        c.save(); c.translate(x,y); c.rotate(n(s,"angle",0)); c.scale(scale,scale);
        int rim = color(angry ? "#EE3953" : "#B983E2");
        paint.setColor(rim); paint.setAlpha(60); c.drawCircle(0,0,53,paint);
        paint.setAlpha(255); c.drawCircle(0,0,49,paint);
        paint.setShader(new RadialGradient(-12,-16,77,new int[]{color(angry?"#831D30":"#2B2633"),color("#0C0910")},null,Shader.TileMode.CLAMP));
        c.drawCircle(0,0,46.8f,paint); paint.setShader(null);
        JSONArray gaze = s.optJSONArray("gaze");
        float gx = gaze == null ? 0 : (float)gaze.optDouble(0,0)*6;
        float gy = gaze == null ? 0 : (float)gaze.optDouble(1,0)*3;
        paint.setColor(color("#FFD364")); paint.setStrokeWidth(2.5f); paint.setStrokeCap(Paint.Cap.ROUND);
        boolean closed = s.optBoolean("asleep") || s.optBoolean("caressing");
        for (int side : new int[]{-1,1}) {
            float ex = side*17+gx;
            c.drawLine(ex-4,-19,ex,-27,paint); c.drawLine(ex,-27,ex+4,-19,paint);
            if (closed) c.drawLine(ex-4,gy,ex+4,gy,paint);
            else c.drawOval(ex-5,gy-(angry?3:7),ex+5,gy+(angry?3:7),paint);
        }
        if (s.optBoolean("asleep")) {
            paint.setTextSize(9); c.drawText("zzz",22,-30,paint);
        }
        c.restore();
    }

    private void toy(Canvas c, JSONObject s) {
        float r = n(s,"toyRadius",14), x = n(s,"toyX",0), y = n(s,"toyY",0);
        c.save(); c.translate(x,y); c.rotate(n(s,"toyAngle",0));
        boolean peanut = s.optString("toyAppearance").equals("peanut");
        paint.setShader(new RadialGradient(-r*.3f,-r*.5f,1.5f*r, peanut
                ? new int[]{color("#F4D293"),color("#BD8045"),color("#694425")}
                : new int[]{color("#E2FFA8"),color("#4A9732"),color("#2A461D")},null,Shader.TileMode.CLAMP));
        if (peanut) {
            c.drawOval(-r,-r*.60f,r,r*.60f,paint);
            c.drawOval(-r,-r*.72f,r*.12f,r*.72f,paint);
            c.drawOval(-r*.12f,-r*.70f,r,r*.70f,paint);
        } else c.drawCircle(0,0,r,paint);
        paint.setShader(null);
        paint.setColor(color(peanut?"#EFC284":"#DDF6B6")); paint.setStrokeWidth(1.8f);
        c.drawLine(-r*.8f,-r*.43f,r*.65f,r*.56f,paint);
        c.restore();
    }

    private void notebook(Canvas c, JSONObject object) {
        float x = n(object,"x",0), y = n(object,"y",0);
        float w = n(object,"width",100), h = n(object,"height",65);
        paint.setColor(color("#8776A8"));
        c.drawRoundRect(x-w/2,y-h/2,x+w/2,y+h/2,7,7,paint);
        paint.setColor(color("#211B2B"));
        c.drawRoundRect(x-w*.45f,y-h*.44f,x+w*.45f,y+h*.24f,5,5,paint);
        paint.setColor(color("#F0C56F"));
        for (int i=0;i<3;i++) c.drawRect(x-w*.31f,y-h*.31f+i*7,x+w*(.15f+i*.05f),y-h*.29f+i*7,paint);
    }

    private void message(Canvas c, String text, float x, float y, float radius) {
        paint.setTextSize(Math.max(13,radius*.31f));
        float w = paint.measureText(text) + 20;
        float left = Math.max(originX+2, Math.min(originX+getWidth()-w-2,x-w/2));
        float top = layer.equals("message") ? originY+2 : y-radius-37;
        if (top < originY+2) top = y+radius+5;
        paint.setColor(0xEF2D2439); c.drawRoundRect(left,top,left+w,top+31,9,9,paint);
        paint.setColor(color("#FFF1C7")); c.drawText(text,left+10,top+20,paint);
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        if (layer.equals("message")) return false;
        float x = event.getX()+originX, y = event.getY()+originY;
        JSONObject s = engine.state();
        switch (event.getActionMasked()) {
            case MotionEvent.ACTION_DOWN:
                float px=n(s,"x",0), py=n(s,"y",0), tx=n(s,"toyX",0), ty=n(s,"toyY",0);
                if (!layer.equals("pet") && s.optBoolean("toyVisible") &&
                        (layer.equals("toy") || Math.hypot(tx-x,ty-y) <= n(s,"toyRadius",14)+12)) {
                    held="toy"; offsetX=tx-x; offsetY=ty-y;
                } else if (!layer.equals("toy") && Math.hypot(px-x,py-y) <= n(s,"radius",38)+7) {
                    held="pet"; offsetX=px-x; offsetY=py-y;
                } else return false;
                downX=x; downY=y; moved=false;
                velocity=VelocityTracker.obtain();
                sample(event,x,y);
                engine.action("drag-start",held,x+offsetX,y+offsetY,0,0);
                return true;
            case MotionEvent.ACTION_MOVE:
                if (held==null) return false;
                sample(event,x,y);
                moved |= Math.hypot(x-downX,y-downY)>7;
                engine.action("drag",held,x+offsetX,y+offsetY,0,0);
                return true;
            case MotionEvent.ACTION_UP:
            case MotionEvent.ACTION_CANCEL:
                if (held==null) return false;
                sample(event,x,y);
                velocity.computeCurrentVelocity(1000,1450);
                boolean cancel=event.getActionMasked()==MotionEvent.ACTION_CANCEL;
                engine.action("drag-end",cancel?"cancel-"+held:held,x+offsetX,y+offsetY,
                        moved&&!cancel?velocity.getXVelocity():0,moved&&!cancel?velocity.getYVelocity():0);
                if (!moved && !cancel) {
                    if (held.equals("pet")) engine.action("caress","",0,0,0,0);
                    else engine.action("lift","",0,0,0,0);
                    if (Haptics.enabled(getContext())) performHapticFeedback(android.view.HapticFeedbackConstants.VIRTUAL_KEY);
                    performClick();
                }
                velocity.recycle(); velocity=null; held=null;
                return true;
        }
        return true;
    }

    private void sample(MotionEvent event, float x, float y) {
        MotionEvent copy = MotionEvent.obtain(event);
        copy.setLocation(x,y);
        velocity.addMovement(copy);
        copy.recycle();
    }

    @Override protected void onDetachedFromWindow() {
        if (held != null) {
            JSONObject state = engine.state();
            boolean toy = held.equals("toy");
            engine.action("drag-end","cancel-"+held,n(state,toy?"toyX":"x",0),
                    n(state,toy?"toyY":"y",0),0,0);
            velocity.recycle();
            velocity = null;
            held = null;
        }
        super.onDetachedFromWindow();
    }

    @Override public boolean performClick() { super.performClick(); return true; }
}
