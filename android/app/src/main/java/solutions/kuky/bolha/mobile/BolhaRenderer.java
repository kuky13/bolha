// SPDX-License-Identifier: GPL-3.0-or-later
// Adapted from Bolha's Qt renderer and Pestinha by mille-okws. See NOTICE.md.
package solutions.kuky.bolha.mobile;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RadialGradient;
import android.graphics.RectF;
import android.graphics.Shader;
import org.json.JSONArray;
import org.json.JSONObject;

/** Canvas counterpart of bolha/character.py, driven by the shared Python poses. */
final class BolhaRenderer {
    private static final int GOLD = Color.rgb(255, 211, 100);
    private static final float TAU = (float)(Math.PI * 2);
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final Path path = new Path();
    private final Path spiral = new Path();
    private final Path angerMark = new Path();
    private final Path popDrop = new Path();

    BolhaRenderer() {
        paint.setStrokeCap(Paint.Cap.ROUND);
        paint.setStrokeJoin(Paint.Join.ROUND);
        for (int index = 0; index <= 40; index++) {
            float phase = index / 40f, radius = .25f + 5.6f * phase;
            float x = (float)Math.cos(phase * TAU * 1.55f) * radius;
            float y = (float)Math.sin(phase * TAU * 1.55f) * radius;
            if (index == 0) spiral.moveTo(x, y); else spiral.lineTo(x, y);
        }
        for (int sx : new int[]{-1, 1}) for (int sy : new int[]{-1, 1}) {
            angerMark.moveTo(1.7f * sx, 8 * sy);
            angerMark.quadTo(2.2f * sx, 2.2f * sy, 8 * sx, 1.7f * sy);
        }
        popDrop.moveTo(-1.45f, 0);
        popDrop.cubicTo(-.51f, -.34f, .05f, -.69f, .53f, -.57f);
        popDrop.cubicTo(1.26f, -.41f, 1.12f, .44f, .51f, .57f);
        popDrop.cubicTo(-.03f, .68f, -.59f, .33f, -1.45f, 0);
        popDrop.close();
    }

    static float number(JSONObject value, String key, float fallback) {
        double n = value == null ? fallback : value.optDouble(key, fallback);
        return Double.isFinite(n) ? (float)n : fallback;
    }
    private static float clamp(float value, float low, float high) { return Math.max(low, Math.min(high, value)); }
    private static float unit(float value) { return clamp(value, 0, 1); }
    private static float wave(float value) { return (float)Math.sin(value); }
    private static float cos(float value) { return (float)Math.cos(value); }
    private static float fract(float value) { return value - (float)Math.floor(value); }
    private static int color(String value) { return Color.parseColor(value); }
    private static int alpha(int rgb, float value) { return (rgb & 0x00ffffff) | (Math.round(unit(value) * 255) << 24); }
    private static int mix(String first, String second, float amount, float opacity) {
        int a = color(first), b = color(second); amount = unit(amount);
        return Color.argb(Math.round(unit(opacity) * 255),
                Math.round(Color.red(a) + (Color.red(b) - Color.red(a)) * amount),
                Math.round(Color.green(a) + (Color.green(b) - Color.green(a)) * amount),
                Math.round(Color.blue(a) + (Color.blue(b) - Color.blue(a)) * amount));
    }
    private void fill(int value) { paint.setShader(null); paint.setStyle(Paint.Style.FILL); paint.setColor(value); }
    private void stroke(int value, float width) { paint.setShader(null); paint.setStyle(Paint.Style.STROKE); paint.setColor(value); paint.setStrokeWidth(width); }

    void draw(Canvas canvas, JSONObject state) {
        JSONObject pose = state.optJSONObject("pose");
        if (pose == null) pose = new JSONObject();
        float x = number(state, "x", 100), y = number(state, "y", 100);
        float radius = number(state, "radius", 68);
        float scale = radius / 49f * number(pose, "visual_scale", 1);
        float squash = clamp(number(pose, "squash", 0), -.25f, .25f);
        float angle = number(state, "angle", 0) + number(pose, "angle_offset", 0);
        String mode = state.optString("poseMode");
        boolean floor = mode.equals("deitada") || mode.equals("embaixadinha") || mode.startsWith("pouso_");
        float floorSquash = floor ? squash : 0;
        float clearance = Math.max(0, number(state, "surface", y + radius) - y - radius);
        float shift = radius * floorSquash * Math.max(0, 1 - clearance / 24f);
        if (floor) squash = 0;
        JSONArray corner = pose.optJSONArray("corner_peek");
        JSONArray bounds = state.optJSONArray("bounds");
        if (corner != null && bounds != null) {
            float inward = (float)corner.optDouble(0, 1), depth = (float)corner.optDouble(1, 0);
            float emerge = (float)corner.optDouble(2, 1);
            float edge = (float)bounds.optDouble(inward > 0 ? 0 : 2, x);
            x += (edge + inward * radius * depth - x) * (1 - emerge);
        }
        canvas.save();
        if (corner != null && bounds != null) canvas.clipRect((float)bounds.optDouble(0),-100000,(float)bounds.optDouble(2),100000);
        if (!state.isNull("deskTop")) canvas.clipRect(-100000, -100000, 100000, number(state, "deskTop", y + radius));
        canvas.translate(x, y + shift);
        canvas.scale(1 + floorSquash, 1 - floorSquash);
        canvas.rotate(angle);
        canvas.scale(scale * (1 + squash), scale * (1 - squash));
        float opacity = unit(number(pose, "body_opacity", 1));
        if (state.optBoolean("visible", true) && opacity > 0) {
            int layer = canvas.saveLayerAlpha(-85, -90, 85, 90, Math.round(opacity * 255));
            JSONObject prefs = state.optJSONObject("preferences");
            drawBody(canvas, unit(number(pose, "anger", state.optString("emotion").equals("bravo") ? .75f : 0)),
                     number(prefs, "opacity", 1));
            drawFace(canvas, state, pose, scale);
            canvas.restoreToCount(layer);
        }
        drawSleep(canvas, number(pose, "zzz_phase", 0), unit(number(pose, "zzz_strength", 0)));
        String effect = pose.optString("effect");
        if (!effect.equals("rebatida") || !pose.has("impact_point")) {
            drawEffect(canvas, effect, number(pose, "effect_phase", 0),
                    unit(number(pose, "effect_strength", 0)), number(pose, "effect_angle", 0));
        }
        canvas.restore();
        JSONArray impact = pose.optJSONArray("impact_point");
        if (impact != null) {
            canvas.save();
            canvas.translate((float)impact.optDouble(0, x), (float)impact.optDouble(1, y));
            canvas.rotate(number(pose, "impact_angle", 0));
            canvas.scale(radius / 49f, radius / 49f);
            drawImpact(canvas, number(pose, "impact_phase", 0), number(pose, "impact_strength", 0), true);
            canvas.restore();
        }
    }

    private void drawBody(Canvas canvas, float rage, float opacity) {
        fill(Color.WHITE);
        paint.setShader(new RadialGradient(0, 0, 59,
                new int[]{mix("#6f59c8", "#e01b38", rage, 0), mix("#6f59c8", "#e01b38", rage, 0),
                    mix("#6f59c8", "#e01b38", rage, .15f + .14f * rage), mix("#9474ec", "#ff2a48", rage, .32f + .24f * rage),
                    mix("#6b45ac", "#b8122a", rage, .14f + .12f * rage), mix("#6b45ac", "#b8122a", rage, 0)},
                new float[]{0, .77f, .82f, .88f, .93f, 1}, Shader.TileMode.CLAMP));
        paint.setAlpha(Math.round(unit(opacity) * 255));
        canvas.drawCircle(0, 0, 59, paint);
        paint.setShader(new LinearGradient(-47, -47, 47, 47,
                new int[]{mix("#b45da6", "#ff2e4c", rage, 1), mix("#8a79c1", "#de1d38", rage, 1), mix("#6c96b5", "#a81428", rage, 1)},
                new float[]{0, .5f, 1}, Shader.TileMode.CLAMP));
        canvas.drawCircle(0, 0, 49, paint);
        paint.setShader(new RadialGradient(-15, -19, 91,
                new int[]{mix("#25252c", "#961e2e", rage, 1), mix("#151519", "#52111c", rage, 1), mix("#0b0b0e", "#26080d", rage, 1)},
                new float[]{0, .55f, 1}, Shader.TileMode.CLAMP));
        canvas.drawCircle(0, 0, 46.8f, paint);
        if (rage > 0) {
            paint.setShader(new RadialGradient(0, -8, 42,
                    new int[]{alpha(color("#e31e39"), .42f * rage), alpha(color("#9e1125"), .22f * rage), Color.TRANSPARENT},
                    new float[]{0, .65f, 1}, Shader.TileMode.CLAMP));
            canvas.drawCircle(0, 0, 46.8f, paint);
        }
        paint.setShader(null); paint.setAlpha(255);
    }

    private float[] profile(String emotion) {
        switch (emotion) {
            case "contente": return new float[]{5.2f, 6, 0, 2, .4f};
            case "feliz": return new float[]{5.2f, 6.4f, 0, 6, 1};
            case "curioso": return new float[]{5.7f, 7.2f, -.4f, -5, 1.7f};
            case "bravo": return new float[]{5.8f, 5.4f, .2f, -26, -2.2f};
            case "triste": return new float[]{5.4f, 6.1f, 1.3f, 28, -3.2f};
            case "assustado": return new float[]{6.1f, 9.8f, -.3f, -6, 2.8f};
            case "dramatico": return new float[]{5.7f, 7.4f, -.1f, -11, 1.4f};
            case "dormindo": return new float[]{5.2f, 6.4f, 1, 21, -2.9f};
            case "sonolento": return new float[]{5.4f, 3.2f, 1, 12, -1.4f};
            case "timido": return new float[]{4.9f, 4.8f, 1.1f, -11, -.5f};
            case "atento": return new float[]{5.4f, 7.4f, -.7f, 0, 2.2f};
            case "entediado": return new float[]{5.7f, 2.5f, 1.1f, 17, -2.1f};
            case "travesso": return new float[]{5.6f, 4.7f, -.1f, -7, .9f};
            case "tonto": return new float[]{5.8f, 6.2f, .2f, 19, -.9f};
            case "comemorando": return new float[]{6.4f, 7.2f, -.3f, 7, 2};
            default: return new float[]{5.2f, 6.4f, 0, 0, 0};
        }
    }

    private void drawFace(Canvas canvas, JSONObject state, JSONObject pose, float scale) {
        String emotion = pose.optString("emotion", state.optString("emotion", "observando"));
        float[] profile = profile(emotion);
        float detail = clamp(.7f / Math.max(.05f, scale), 1, 1.3f);
        float rx = profile[0] * (1 + .2f * (detail - 1)), ry = profile[1] * (1 + .2f * (detail - 1));
        float tilt = clamp(profile[3] + number(pose, "ear_tilt", 0), -35, 35);
        float raise = clamp(profile[4] + number(pose, "ear_raise", 0), -5, 5);
        JSONArray gaze = pose.optJSONArray("gaze");
        if (gaze == null) gaze = state.optJSONArray("gaze");
        JSONArray earGaze = state.optJSONArray("earGaze");
        if (earGaze == null) earGaze = gaze;
        float gx = gaze == null ? 0 : clamp((float)gaze.optDouble(0, 0), -1, 1);
        float gy = gaze == null ? 0 : clamp((float)gaze.optDouble(1, 0), -1, 1);
        float ex = earGaze == null ? gx : clamp((float)earGaze.optDouble(0, 0), -1, 1);
        float ey = earGaze == null ? gy : clamp((float)earGaze.optDouble(1, 0), -1, 1);
        if (emotion.equals("dormindo")) gx = gy = ex = ey = 0;
        canvas.save();
        path.reset(); path.addCircle(0, 0, 43, Path.Direction.CW); canvas.clipPath(path);
        for (int side : new int[]{-1, 1}) {
            canvas.save();
            canvas.translate(side * 17.5f + ex * 4.4f, -18 - raise + ey * 2.8f - side * ex * 1.2f);
            canvas.rotate(side * tilt + ex * 14);
            path.reset(); path.moveTo(-4.8f, -2); path.quadTo(-1, -12, 0, -12); path.quadTo(1, -12, 4.8f, -2);
            stroke(GOLD, 2.5f * detail); canvas.drawPath(path, paint); canvas.restore();
        }
        float opening = clamp(number(pose, "eye_open", 1), 0, 1.3f);
        float blink = emotion.equals("dormindo") ? 1 : unit(number(pose, "blink", 0));
        float closing = Math.max(blink, 1 - Math.min(1, opening));
        boolean intentional = !pose.isNull("blink_left") || !pose.isNull("blink_right");
        for (int side : new int[]{-1, 1}) {
            String key = side < 0 ? "blink_left" : "blink_right";
            float eyeClosing = pose.isNull(key) ? closing : Math.max(closing, unit(number(pose, key, 0)));
            float x = side * 18 * (1 - .12f * Math.abs(gx)) + gx * 7.1f, y = profile[2] + gy * 3.6f;
            path.reset();
            if (eyeClosing > .94f || emotion.equals("feliz") && !intentional) {
                boolean happy = emotion.equals("feliz") && eyeClosing <= .94f;
                path.moveTo(x - 5.3f, y + (happy ? 2 : -1));
                path.quadTo(x, y + (happy ? -5 : 3), x + 5.3f, y + (happy ? 2 : -1));
                stroke(GOLD, 2.5f * detail); canvas.drawPath(path, paint);
            } else if (emotion.equals("tonto")) {
                canvas.save(); canvas.translate(x, y); canvas.scale(1, Math.max(.12f, (1 - eyeClosing) * opening));
                stroke(GOLD, 1.9f * detail); canvas.drawPath(spiral, paint); canvas.restore();
            } else if (emotion.equals("comemorando")) {
                star(path, x, y, 6.3f, 7 * (1 - eyeClosing)); fill(GOLD); canvas.drawPath(path, paint);
            } else {
                float h = ry * (1 - eyeClosing) * Math.max(1, opening) + .7f * eyeClosing;
                path.addOval(x - rx, y - h, x + rx, y + h, Path.Direction.CW);
                if (emotion.equals("bravo") || emotion.equals("triste") || emotion.equals("entediado") || emotion.equals("sonolento") || emotion.equals("travesso")) {
                    float anger = unit(number(pose, "anger", 0));
                    float slope = side * (emotion.equals("bravo") ? -.43f - .14f * anger : emotion.equals("triste") ? .26f : 0);
                    float lidY = y - h * (emotion.equals("bravo") ? .14f - .12f * anger : emotion.equals("triste") ? .30f : .48f);
                    float edge = rx + 1;
                    Path lid = new Path(); lid.moveTo(x - edge, lidY - slope * edge); lid.lineTo(x + edge, lidY + slope * edge);
                    lid.lineTo(x + edge, y + h + 1); lid.lineTo(x - edge, y + h + 1); lid.close(); path.op(lid, Path.Op.INTERSECT);
                }
                fill(alpha(GOLD, .12f)); canvas.drawOval(x - rx - 1, y - h - 1, x + rx + 1, y + h + 1, paint);
                fill(GOLD); canvas.drawPath(path, paint);
                if (h > 3) {
                    canvas.save(); canvas.clipPath(path); fill(color("#fff4cf"));
                    canvas.drawCircle(x - 1.2f + gx * 1.45f, y - 2 + gy * 1.1f, 1.05f, paint); canvas.restore();
                }
            }
        }
        JSONObject preferences=state.optJSONObject("preferences");
        if (pose.optBoolean("mouth_enabled",preferences==null || preferences.optBoolean("mouthEnabled",true))) drawMouth(canvas,pose);
        canvas.restore();
    }

    private void drawMouth(Canvas canvas,JSONObject pose) {
        float opening=unit(number(pose,"mouth_open",0));
        float curve=clamp(number(pose,"mouth_curve",.3f),-1,1);
        float chew=unit(number(pose,"mouth_chew",0));
        float width=(7.2f+9.5f*opening)*clamp(number(pose,"mouth_width",1),.55f,1.2f);
        float height=16*opening, y=18+chew*.75f, middle=y+6*curve;
        float slant=2.5f*clamp(number(pose,"mouth_skew",0),-1,1);
        if (opening<=.025f) {
            path.reset(); path.moveTo(-width,y+slant); path.quadTo(0,middle,width,y-slant);
            stroke(GOLD,2); canvas.drawPath(path,paint);
        } else {
            Path mouth=new Path(); mouth.moveTo(-width,y+slant);
            mouth.quadTo(0,middle-height*.8f,width,y-slant);
            mouth.quadTo(0,middle+height*1.2f,-width,y+slant); mouth.close();
            fill(color("#2f1026")); canvas.drawPath(mouth,paint);
            stroke(GOLD,1.75f); canvas.drawPath(mouth,paint);
            float tongue=unit(number(pose,"tongue",0));
            if ((curve>.4f && opening>.23f) || tongue>.05f) {
                canvas.save(); canvas.clipPath(mouth); fill(color("#f9b3bd"));
                float spot=y+height*.55f+3, radius=height*.32f+1;
                canvas.drawOval(-width*.55f,spot-radius,width*.55f,spot+radius,paint); canvas.restore();
            }
        }
        if (chew>0) {
            stroke(alpha(GOLD,chew*.5f),1.2f);
            canvas.drawArc(-20,y-4,-11,y+7,110,100,false,paint);
            canvas.drawArc(11,y-4,20,y+7,-30,100,false,paint);
        }
        if (pose.optBoolean("cursor_inside")) {
            path.reset(); path.moveTo(-3,y-5); path.lineTo(-3,y+6); path.lineTo(1,y+3); path.lineTo(5,y+5); path.lineTo(6,y+3); path.lineTo(2,y+1); path.close();
            fill(color("#fff4cf")); canvas.drawPath(path,paint);
        }
    }

    private static void star(Path result, float x, float y, float width, float height) {
        result.reset(); result.moveTo(x, y - height);
        result.lineTo(x + width * .3f, y - height * .3f); result.lineTo(x + width, y);
        result.lineTo(x + width * .3f, y + height * .3f); result.lineTo(x, y + height);
        result.lineTo(x - width * .3f, y + height * .3f); result.lineTo(x - width, y);
        result.lineTo(x - width * .3f, y - height * .3f); result.close();
    }

    private void drawSleep(Canvas canvas, float phase, float strength) {
        if (strength <= 0) return;
        for (int index = 0; index < 3; index++) {
            float progress = fract(phase / 2.4f + index / 3f);
            float opacity = Math.min(1, Math.min(progress / .2f, (1 - progress) / .25f)) * strength;
            float size = 4.2f + progress * 2.3f, x = 31 + progress * 8, y = -25 - progress * 20;
            path.reset(); path.moveTo(x, y - size); path.lineTo(x + size * .8f, y - size);
            path.lineTo(x, y); path.lineTo(x + size * .8f, y);
            stroke(alpha(GOLD, opacity), 1.25f); canvas.drawPath(path, paint);
        }
    }

    private void drawEffect(Canvas canvas, String kind, float phase, float strength, float angle) {
        if (strength <= 0) return;
        switch (kind) {
            case "carinho":
                for (int index = 0; index < 3; index++) {
                    float p = fract(phase / 1.8f + index / 3f), x = (index % 2 == 0 ? -34 : 35) + wave(p * (float)Math.PI) * 2;
                    float y = -24 - p * 20, size = 3.7f + p * 1.8f;
                    float fade = Math.min(1, Math.min(p / .2f, (1 - p) / .3f)) * strength;
                    path.reset(); path.moveTo(x, y + size); path.cubicTo(x - size * 2, y - size * .2f, x - size, y - size * 1.7f, x, y - size * .5f);
                    path.cubicTo(x + size, y - size * 1.7f, x + size * 2, y - size * .2f, x, y + size); path.close();
                    fill(alpha(GOLD, fade)); canvas.drawPath(path, paint);
                }
                break;
            case "tonto":
            case "comemorando":
                for (int index = 0; index < 3; index++) {
                    float orbit = phase * (kind.equals("tonto") ? 2.6f : 2.5f) + index * TAU / 3;
                    float x = cos(orbit) * (kind.equals("tonto") ? 40 : 34), y = (kind.equals("tonto") ? -41 : -30) + wave(orbit) * (kind.equals("tonto") ? 6 : 10);
                    float size = 3.1f + .5f * wave(orbit * 2);
                    star(path, x, y, size, size); fill(alpha(GOLD, strength * .9f)); canvas.drawPath(path, paint);
                }
                break;
            case "bravo": drawAnger(canvas, phase, strength); break;
            case "perseguindo":
                canvas.save(); canvas.rotate(angle);
                for (int index = 0; index < 3; index++) {
                    float p = phase * 8 + index * TAU / 3, x = -48 - 2 * wave(p), y = (index - 1) * 11;
                    stroke(alpha(color("#a8efff"), strength * (.45f + .18f * index)), 1.7f + index * .35f);
                    canvas.drawLine(x - 5, y, x + 2, y, paint);
                }
                canvas.restore(); break;
            case "rebatida": canvas.save(); canvas.rotate(angle); drawImpact(canvas, phase, strength, false); canvas.restore(); break;
            case "pop": drawPop(canvas, phase, strength); break;
            default: break;
        }
    }

    private void drawAnger(Canvas canvas, float phase, float strength) {
        for (int index = 0; index < 2; index++) {
            float delay = index == 0 ? 0 : .23f, beat = (float)Math.pow(.5 + .5 * cos((phase - delay) * TAU * 1.8f), 2);
            float size = (index == 0 ? 1 : .68f) * (.76f + .20f * strength * beat);
            canvas.save(); canvas.translate(index == 0 ? -37 : 47, (index == 0 ? -36 : -18) - 1.5f * beat);
            canvas.rotate((index == 0 ? -13 : 18) + 4 * wave((phase - delay) * 8)); canvas.scale(size, size);
            stroke(alpha(color("#3b1026"), .90f * strength), 5.1f); canvas.drawPath(angerMark, paint);
            stroke(alpha(color("#ff455f"), strength), 3.2f); canvas.drawPath(angerMark, paint);
            stroke(alpha(color("#ffbec2"), (.68f + .32f * beat) * strength), 1.2f); canvas.drawPath(angerMark, paint);
            canvas.restore();
        }
        float[] directions = {-2.77f, -1.92f, -.55f};
        for (int index = 0; index < directions.length; index++) {
            float p = fract(phase * 1.55f + .15f * index);
            if (p >= .6f) continue;
            float d = 50 + 12 * p, x = cos(directions[index]), y = wave(directions[index]);
            stroke(alpha(color("#ff5f6d"), strength * strength * .78f * wave((float)Math.PI * p / .6f)), 1.8f);
            canvas.drawLine(x * d, y * d, x * (d + 3), y * (d + 3), paint);
        }
    }

    private void drawImpact(Canvas canvas, float phase, float strength, boolean atContact) {
        float p = unit(phase / .24f), x = (atContact ? -2 : 47) + 6 * p, h = 7 + 4 * p;
        path.reset(); path.moveTo(x - 2, -h); path.quadTo(x + 7, 0, x - 2, h);
        stroke(alpha(color("#6ce7f3"), strength * .45f), 4.4f); canvas.drawPath(path, paint);
        stroke(alpha(color("#d5ffff"), strength), 1.8f); canvas.drawPath(path, paint);
        stroke(alpha(GOLD, strength), 1.8f);
        for (int side : new int[]{-1, 1}) canvas.drawLine(x + 2, side * (h + 1), x + 5, side * (h + 4), paint);
    }

    private void drawPop(Canvas canvas, float phase, float strength) {
        float p = unit(phase / .62f), spread = 1 - (float)Math.pow(1 - p, 3.2);
        float flash = (float)Math.pow(1 - unit(phase / .14f), 1.6) * strength;
        if (flash > 0) {
            fill(Color.WHITE); paint.setShader(new RadialGradient(0, 0, 39,
                    new int[]{alpha(color("#fff2ba"), .56f * flash), alpha(color("#f4b0ff"), .48f * flash), Color.TRANSPARENT},
                    new float[]{0, .45f, 1}, Shader.TileMode.CLAMP)); canvas.drawCircle(0, 0, 39, paint);
            star(path, 0, 0, 21 + 13 * spread, 21 + 13 * spread); fill(alpha(color("#fff5d7"), flash)); canvas.drawPath(path, paint);
        }
        float shell = (float)Math.pow(1 - unit(phase / .46f), 1.35) * strength, radius = 41 + 23 * spread;
        int[] starts = {12, 78, 148, 225, 309}, arcs = {47, 46, 54, 54, 37};
        String[] shades = {"#eed0ff", "#fff1b7", "#b9d4ff", "#dfa6ff", "#ffd4fb"};
        RectF rect = new RectF(-radius, -radius, radius, radius);
        for (int index = 0; index < starts.length; index++) {
            float gap = Math.round(11 * spread);
            stroke(alpha(color(shades[index]), shell), 3.4f - 1.7f * spread);
            canvas.drawArc(rect, -starts[index] - gap, -arcs[index] + 2 * gap, false, paint);
        }
        float drop = (float)Math.pow(1 - Math.pow(p, 1.65), 1.25) * strength;
        for (int index = 0; index < 14; index++) {
            float degrees = -169 + index * 25.4f, radians = degrees * (float)Math.PI / 180;
            float d = 35 + (57 + index % 4 * 3 - 35) * spread, size = (2.3f + index % 3 * 1.2f) * (1 - .55f * p);
            canvas.save(); canvas.translate(cos(radians) * d, wave(radians) * d + 6 * p * p);
            canvas.rotate(degrees + (index % 3 - 1) * 25 * p); canvas.scale(size, size);
            fill(alpha(color(shades[index % shades.length]), drop)); canvas.drawPath(popDrop, paint);
            fill(alpha(color("#fff9e5"), .86f * drop)); canvas.drawOval(.19f, -.36f, .75f, -.08f, paint);
            canvas.restore();
        }
    }
}
