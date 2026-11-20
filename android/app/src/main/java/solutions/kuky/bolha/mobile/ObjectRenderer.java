// SPDX-License-Identifier: GPL-3.0-or-later
// Notebook and ball are adapted from Pestinha and Bolha's Qt art. See NOTICE.md.
package solutions.kuky.bolha.mobile;

import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RadialGradient;
import android.graphics.RectF;
import android.graphics.Shader;
import android.text.Layout;
import android.text.StaticLayout;
import android.text.TextPaint;
import android.view.View;
import org.json.JSONObject;
import org.json.JSONArray;
import org.json.JSONException;

final class ObjectRenderer {
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final TextPaint text = new TextPaint(Paint.ANTI_ALIAS_FLAG);
    private final Path path = new Path();
    private final ReactionMediaCache media;
    private final float fontScale;
    ObjectRenderer(Engine engine,float fontScale) { media = ReactionMediaCache.get(engine); this.fontScale=fontScale; }
    private static int color(String value) { return Color.parseColor(value); }
    private static float n(JSONObject value, String key, float fallback) { return BolhaRenderer.number(value,key,fallback); }
    private void fill(String color) { paint.setShader(null); paint.setStyle(Paint.Style.FILL); paint.setColor(color(color)); }
    private void stroke(String color, float width) { paint.setShader(null); paint.setStyle(Paint.Style.STROKE); paint.setColor(color(color)); paint.setStrokeWidth(width); }

    void draw(Canvas canvas, JSONObject object, float phase, View view) {
        float x = n(object,"x",0), y = n(object,"y",0), w = n(object,"width",100), h = n(object,"height",70);
        RectF rect = new RectF(x-w/2,y-h/2,x+w/2,y+h/2);
        canvas.save();
        if (!object.optString("kind").equals("sign")) canvas.rotate(n(object,"angle",0),x,y);
        switch (object.optString("kind")) {
            case "notebook": notebook(canvas,rect,object.optBoolean("working"),
                object.optInt("typingKey",-1),n(object,"typingTap",0),object.optInt("typingProgress"),object.optBoolean("caret")); break;
            case "meme": media.draw(canvas,object,rect,view); break;
            case "note":
                int layer=canvas.saveLayerAlpha(rect,Math.round(255*Math.max(0,Math.min(1,n(object,"opacity",1)))));
                bubble(canvas,rect,object.optString("text"),true,object.optBoolean("tailTop"),
                       rect.left+rect.width()*n(object,"anchor",.5f));
                canvas.restoreToCount(layer);
                break;
            case "sign": placard(canvas,object); break;
            case "projectile":
            case "paper":
                toyShape(canvas,x,y,n(object,"radius",Math.min(w,h)*17/42),0,object.optString("appearance","ball")); break;
            case "corner":
                fill("#272130"); canvas.drawRoundRect(rect,10,10,paint);
                stroke("#9c83b7",1.2f); canvas.drawRoundRect(rect,10,10,paint);
                drawText(canvas,object.optString("text","CANTINHO DO CASTIGO"),rect,12); break;
            case "fireworks": fireworks(canvas,rect,phase); break;
            default: break;
        }
        canvas.restore();
    }

    void toy(Canvas canvas, JSONObject state) {
        float x=n(state,"toyX",0), y=n(state,"toyY",0), r=n(state,"toyRadius",18);
        toyShape(canvas,x,y,r,n(state,"toyAngle",0),state.optString("toyAppearance"));
    }

    private void toyShape(Canvas canvas,float x,float y,float r,float angle,String appearance) {
        canvas.save(); canvas.translate(x,y); canvas.rotate(angle);
        if (appearance.equals("peanut")) {
            canvas.scale(r/17,r/17);
            path.reset(); path.moveTo(-16,0); path.cubicTo(-18,-12,-11,-16,-5,-11);
            path.quadTo(0,-7,5,-11); path.cubicTo(11,-16,18,-12,16,0);
            path.cubicTo(18,12,11,16,5,11); path.quadTo(0,7,-5,11); path.cubicTo(-11,16,-18,12,-16,0); path.close();
            fill("#d6aa65"); paint.setShader(new LinearGradient(-9,-13,8,13,new int[]{color("#f2d9a2"),color("#d6aa65"),color("#b57b3e")},new float[]{0,.5f,1},Shader.TileMode.CLAMP));
            canvas.drawPath(path,paint); stroke("#7d512a",1.3f); canvas.drawPath(path,paint);
            canvas.save(); canvas.clipPath(path); stroke("#a57742",.65f);
            for (int offset=-30;offset<=30;offset+=6) { canvas.drawLine(offset-18,-20,offset+18,20,paint); canvas.drawLine(offset+18,-20,offset-18,20,paint); }
            path.reset(); path.moveTo(-15,0); path.cubicTo(-8,-1,8,1,15,0); stroke("#f8dfa8",.9f); canvas.drawPath(path,paint); canvas.restore();
        } else {
            fill("#63e56f"); paint.setShader(new RadialGradient(-r*5/18,-r/3,r*1.4f,new int[]{color("#f4fff6"),color("#63e56f"),color("#1f7a36")},new float[]{0,.5f,1},Shader.TileMode.CLAMP));
            canvas.drawCircle(0,0,r,paint); stroke("#14401f",Math.max(.8f,r/12)); canvas.drawCircle(0,0,r,paint); canvas.drawLine(-r*.8f,0,r*.8f,0,paint);
        }
        canvas.restore();
    }

    void notebook(Canvas canvas, RectF rect, boolean working, int key, float tap, int progress, boolean caret) {
        float scale=Math.min(rect.width()/132,rect.height()/96);
        canvas.save(); canvas.translate(rect.centerX()-66*scale,rect.centerY()-48*scale); canvas.scale(scale,scale);
        fill("#baaacc"); paint.setShader(new LinearGradient(0,7,0,72,color("#baaacc"),color("#746780"),Shader.TileMode.CLAMP));
        canvas.drawRoundRect(21,7,111,72,9,9,paint);
        stroke("#d2c1e2",1.1f); canvas.drawRoundRect(21,7,111,72,9,9,paint);
        fill("#34374f"); paint.setShader(new LinearGradient(26,13,100,64,color("#34374f"),color("#182133"),Shader.TileMode.CLAMP));
        canvas.drawRoundRect(25.5f,13,106.5f,64,4,4,paint);
        stroke("#51465f",.9f); canvas.drawRoundRect(25.5f,13,106.5f,64,4,4,paint);
        fill("#3d3249"); canvas.drawCircle(66,9.8f,.8f,paint);
        fill("#83738f"); canvas.drawRoundRect(57,67,75,68.1f,.5f,.5f,paint);
        fill("#242b40"); canvas.drawRoundRect(31,18,101,58,2,2,paint);
        fill("#817895"); canvas.drawRoundRect(35,22,52,23.5f,.6f,.6f,paint);
        fill("#ffd16e"); canvas.drawRoundRect(35,29,63,31.4f,1,1,paint);
        fill("#ddd3e8"); canvas.drawRoundRect(35,36,53,37.8f,.7f,.7f,paint);
        fill("#9f9ab9"); canvas.drawRoundRect(35,41,78,42.6f,.6f,.6f,paint);
        canvas.drawRoundRect(57,36,88,37.8f,.7f,.7f,paint);
        fill("#efd29b");
        for (int i=0;i<progress;i++) {
            float left=35+4.6f*i;
            canvas.drawRoundRect(left,48,left+3,49.8f,.6f,.6f,paint);
        }
        if (!working || key>=0 || caret) {
            fill("#ffd16e");
            float cursor=35+4.6f*progress;
            canvas.drawRoundRect(cursor,46.5f,cursor+1.2f,51,.5f,.5f,paint);
        }
        paint.setStrokeCap(Paint.Cap.BUTT); paint.setStrokeJoin(Paint.Join.MITER);
        fill("#51465f"); canvas.drawRoundRect(12,68,120,78,4,4,paint);
        fill("#c3b2d2"); canvas.drawRoundRect(28,69,36,73,1.5f,1.5f,paint);
        canvas.drawRoundRect(96,69,104,73,1.5f,1.5f,paint);
        path.reset(); path.moveTo(18,72); path.lineTo(114,72); path.quadTo(119,72,121,76);
        path.lineTo(130,85); path.quadTo(131,91,125,91); path.lineTo(7,91);
        path.quadTo(1,91,2,85); path.lineTo(11,76); path.quadTo(14,72,18,72); path.close();
        fill("#c6b8d7"); paint.setShader(new LinearGradient(0,72,0,91,new int[]{color("#c6b8d7"),color("#998ba9"),color("#6a5c7a")},new float[]{0,.8f,1},Shader.TileMode.CLAMP));
        canvas.drawPath(path,paint); stroke("#d2c1e2",1); canvas.drawPath(path,paint);
        stroke("#776785",.7f); canvas.drawLine(8,88,124,88,paint);
        paint.setStyle(Paint.Style.FILL);
        for (int row=0;row<2;row++) {
            for (int col=0;col<8;col++) {
                float pressed=col==key && row==key%2?tap:0;
                paint.setColor(Color.rgb(Math.round(77+178*pressed),Math.round(66+143*pressed),Math.round(92+18*pressed)));
                float left=24+11*col-row, top=74.5f+4*row+.35f*pressed;
                canvas.drawRoundRect(left,top,left+7.8f,top+2.6f,.7f,.7f,paint);
            }
        }
        fill("#d3c7df"); canvas.drawRoundRect(53,83,79,86.5f,1,1,paint);
        stroke("#7a698a",.65f); canvas.drawRoundRect(53,83,79,86.5f,1,1,paint);
        fill(working?"#ffd16e":"#756b80"); canvas.drawRoundRect(112.5f,84.3f,115.5f,85.7f,.7f,.7f,paint); canvas.restore();
    }

    void bubble(Canvas canvas, RectF rect, String value, boolean thought) {
        bubble(canvas,rect,value,thought,false,rect.centerX());
    }

    void bubble(Canvas canvas,RectF rect,String value,boolean thought,boolean tailTop,float anchor) {
        float top=rect.top+(tailTop?12:0), bottom=rect.bottom-(tailTop?0:12);
        fill("#25212f"); canvas.drawRoundRect(rect.left+1,top+1,rect.right-1,bottom,10,10,paint);
        stroke("#9383af",1); canvas.drawRoundRect(rect.left+1,top+1,rect.right-1,bottom,10,10,paint);
        float x=Math.max(rect.left+14,Math.min(rect.right-14,anchor)),edge=tailTop?top:bottom,sign=tailTop?-1:1;
        if (thought) { fill("#9383af"); canvas.drawOval(x-3,edge+sign*5-2,x+3,edge+sign*5+2,paint); canvas.drawCircle(x-2,edge+sign*10,1.5f,paint); }
        else { path.reset(); path.moveTo(x-7,edge-sign); path.quadTo(x-3,edge+sign*4,x-2,edge+sign*10); path.quadTo(x+3,edge+sign*4,x+7,edge-sign); stroke("#9383af",1); canvas.drawPath(path,paint); }
        drawText(canvas,value,new RectF(rect.left+10,top+7,rect.right-10,bottom-7),12);
    }

    private StaticLayout textLayout(String value,int width,float size) {
        text.setColor(color("#fff1c7")); text.setTextSize(size*fontScale);
        return StaticLayout.Builder.obtain(value,0,value.length(),text,Math.max(1,width))
            .setAlignment(Layout.Alignment.ALIGN_CENTER).setIncludePad(false).build();
    }

    private void drawText(Canvas canvas, String value, RectF rect, float size) {
        StaticLayout layout=textLayout(value,(int)rect.width(),size);
        int pageStart=0, pageEnd=layout.getLineCount();
        java.util.ArrayList<int[]> pages=new java.util.ArrayList<>();
        for (int line=0;line<layout.getLineCount();line++) {
            if (line>pageStart && layout.getLineBottom(line)-layout.getLineTop(pageStart)>rect.height()) {
                pages.add(new int[]{pageStart,line});pageStart=line;
            }
        }
        pages.add(new int[]{pageStart,pageEnd});
        int[] page=pages.get((int)((android.os.SystemClock.uptimeMillis()/4500)%pages.size()));
        int top=layout.getLineTop(page[0]),bottom=page[1]>page[0]?layout.getLineBottom(page[1]-1):top;
        float height=bottom-top;
        canvas.save();
        float y=rect.top+Math.max(0,(rect.height()-height)/2);
        canvas.clipRect(rect.left,y,rect.right,y+height);
        canvas.translate(rect.left,y-top);layout.draw(canvas);canvas.restore();
    }

    private void placard(Canvas canvas,JSONObject object) {
        float bx=n(object,"boardX",n(object,"x",0)),by=n(object,"boardY",n(object,"y",0));
        float width=n(object,"boardWidth",n(object,"width",120)),height=n(object,"boardHeight",n(object,"height",80));
        stroke("#bb8f61",5);paint.setStrokeCap(Paint.Cap.ROUND);
        canvas.drawLine(bx,by,n(object,"shaftX",bx),n(object,"shaftY",by),paint);
        paint.setStrokeCap(Paint.Cap.BUTT);
        canvas.save();canvas.rotate(n(object,"angle",0),bx,by);
        RectF board=new RectF(bx-width/2,by-height/2,bx+width/2,by+height/2);
        fill("#32283e");canvas.drawRoundRect(board,9,9,paint);
        stroke("#b9a0d8",1.3f);canvas.drawRoundRect(board,9,9,paint);
        board.inset(12,9);drawText(canvas,object.optString("text"),board,12);
        canvas.restore();
    }

    static void fitTextObjects(JSONObject state,float fontScale) {
        JSONArray items=state.optJSONArray("objects"),area=state.optJSONArray("bounds");
        if (items==null) return;
        float left=area==null?0:(float)area.optDouble(0),top=area==null?0:(float)area.optDouble(1);
        float right=area==null?360:(float)area.optDouble(2,360),bottom=area==null?720:(float)area.optDouble(3,720);
        TextPaint paint=new TextPaint(Paint.ANTI_ALIAS_FLAG);paint.setTextSize(12*fontScale);
        for (int i=0;i<items.length();i++) {
            JSONObject item=items.optJSONObject(i);
            if (item==null) continue;
            String kind=item.optString("kind");
            if (!kind.equals("note") && !kind.equals("sign")) continue;
            if (item.optDouble("textFitScale",-1)==fontScale) continue;
            try { item.put("textFitScale",fontScale); } catch (JSONException error) { continue; }
            boolean sign=kind.equals("sign");
            float width=n(item,sign?"boardWidth":"width",140);
            float padding=sign?24:20;
            String value=item.optString("text");
            StaticLayout layout=StaticLayout.Builder.obtain(value,0,value.length(),paint,Math.max(1,(int)(width-padding)))
                .setAlignment(Layout.Alignment.ALIGN_CENTER).setIncludePad(false).build();
            float height=Math.max(n(item,sign?"boardHeight":"height",60),layout.getHeight()+(sign?21:29));
            height=Math.min(Math.max(40,bottom-top-16),height);
            try {
                if (sign) {
                    item.put("boardHeight",height);
                    double rad=Math.toRadians(n(item,"angle",0));
                    float ex=(float)(Math.abs(Math.cos(rad))*width/2+Math.abs(Math.sin(rad))*height/2);
                    float ey=(float)(Math.abs(Math.sin(rad))*width/2+Math.abs(Math.cos(rad))*height/2);
                    float fit=Math.min(1,Math.min(Math.max(1,right-left-10)/(2*ex),Math.max(1,bottom-top-10)/(2*ey)));
                    width*=fit;height*=fit;ex*=fit;ey*=fit;
                    item.put("boardWidth",width);item.put("boardHeight",height);
                    float bx=Math.max(left+ex+3,Math.min(right-ex-3,n(item,"boardX",n(item,"x",0))));
                    float by=Math.max(top+ey+3,Math.min(bottom-ey-3,n(item,"boardY",n(item,"y",0))));
                    float sx=Math.max(left+3,Math.min(right-3,n(item,"shaftX",bx))),sy=Math.max(top+3,Math.min(bottom-3,n(item,"shaftY",by)));
                    item.put("shaftX",sx);item.put("shaftY",sy);
                    float minX=Math.min(bx-ex,sx)-3,maxX=Math.max(bx+ex,sx)+3;
                    float minY=Math.min(by-ey,sy)-3,maxY=Math.max(by+ey,sy)+3;
                    item.put("boardX",bx);item.put("boardY",by);
                    item.put("x",(minX+maxX)/2);item.put("y",(minY+maxY)/2);
                    item.put("width",maxX-minX);item.put("height",maxY-minY);
                } else {
                    item.put("height",height);
                    item.put("x",Math.max(left+width/2+3,Math.min(right-width/2-3,n(item,"x",0))));
                    item.put("y",Math.max(top+height/2+3,Math.min(bottom-height/2-3,n(item,"y",0))));
                }
            } catch (JSONException error) { android.util.Log.w("Bolha","Texto do objeto",error); }
        }
    }

    private void fireworks(Canvas canvas, RectF rect, float phase) {
        String[] colors={"#ffd364","#cdb0fa","#80d9e5"};
        for (int burst=0;burst<3;burst++) {
            float progress=(phase*.65f+burst*.31f)%1;
            float x=rect.left+rect.width()*(.2f+burst*.3f),y=rect.top+rect.height()*(.3f+(burst%2)*.2f);
            stroke(colors[burst],1.8f); paint.setAlpha(Math.round(255*(1-progress)));
            for (int ray=0;ray<9;ray++) { double angle=ray*Math.PI*2/9; float d=5+progress*rect.width()*.15f; canvas.drawLine(x+(float)Math.cos(angle)*d*.65f,y+(float)Math.sin(angle)*d*.65f,x+(float)Math.cos(angle)*d,y+(float)Math.sin(angle)*d+progress*5,paint); }
        }
        paint.setAlpha(255);
    }
}
