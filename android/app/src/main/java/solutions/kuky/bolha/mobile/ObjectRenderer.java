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
        canvas.save(); canvas.rotate(n(object,"angle",0),x,y);
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
            case "sign": bubble(canvas,rect,object.optString("text"),false); break;
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
        canvas.save(); canvas.translate(x,y); canvas.rotate(n(state,"toyAngle",0));
        if (state.optString("toyAppearance").equals("peanut")) {
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
        float scale=Math.min(rect.width()/110,rect.height()/70);
        canvas.save(); canvas.translate(rect.centerX()-55*scale,rect.centerY()-35*scale); canvas.scale(scale,scale);
        fill("#49435d"); paint.setShader(new LinearGradient(4,3,106,59,new int[]{color("#77708e"),color("#49435d"),color("#282637")},new float[]{0,.45f,1},Shader.TileMode.CLAMP));
        canvas.drawRoundRect(4,3,106,59,6,6,paint); stroke(working?"#c6a8ee":"#91829e",working?2.5f:1.2f); canvas.drawRoundRect(4,3,106,59,6,6,paint);
        fill("#11131d"); canvas.drawRoundRect(10,9,100,44,2,2,paint); stroke("#16141d",1.5f); canvas.drawRoundRect(10,9,100,44,2,2,paint);
        canvas.save(); canvas.clipRect(11,10,99,43);
        fill("#272740"); paint.setShader(new LinearGradient(10,9,100,44,color("#272740"),color("#131622"),Shader.TileMode.CLAMP)); canvas.drawRect(10,9,100,44,paint);
        fill("#38304c"); canvas.drawRect(11,10,99,15,paint);
        fill("#242132"); canvas.drawRect(11,15,26,43,paint); stroke("#746484",.7f); canvas.drawLine(27,15,27,43,paint);
        fill("#d49cb9"); canvas.drawCircle(14,12.5f,.85f,paint);
        fill("#ffd364"); canvas.drawCircle(18,12.5f,.85f,paint);
        fill("#90d9c9"); canvas.drawCircle(22,12.5f,.85f,paint);
        int[] sideLengths={8,6,9,5}, indents={0,4,4,8}, lengths={29,37,23,29};
        String[] colors={"#cbb6f2","#f2ca83","#91c8c7","#cbb6f2"};
        for (int row=0;row<4;row++) {
            fill(row==0?"#b6a0d3":"#665c7c"); canvas.drawRoundRect(14,19+row*5,14+sideLengths[row],20.5f+row*5,.6f,.6f,paint);
            fill(colors[row]); float left=33+indents[row]; canvas.drawRoundRect(left,18+row*4.8f,left+lengths[row],19.5f+row*4.8f,.7f,.7f,paint);
        }
        float length=9+progress*3.6f;
        fill("#ffd364"); paint.setAlpha(working?Math.round(135+110*tap):85);
        canvas.drawRoundRect(33,39,33+length,40.7f,.7f,.7f,paint);
        if (working && (key>=0 || caret)) { fill("#fff0bb"); canvas.drawRect(34+length,37.5f,35+length,41.9f,paint); }
        fill("#e0d9ff"); paint.setAlpha(10); path.reset(); path.moveTo(10,9); path.lineTo(55,9); path.lineTo(27,44); path.lineTo(10,44); path.close(); canvas.drawPath(path,paint); paint.setAlpha(255); canvas.restore();
        fill("#11121a"); canvas.drawCircle(55,6.2f,.9f,paint); fill("#a491bb"); canvas.drawCircle(55,6,.3f,paint);
        stroke("#aaa0b8",1.2f); canvas.drawLine(18,47,30,47,paint); canvas.drawLine(80,47,92,47,paint);
        for (int row=0;row<2;row++) for (int col=0;col<11;col++) {
            float pressed=key>=0 && row==key%2 && col==1+key?tap:0;
            paint.setStyle(Paint.Style.FILL);
            paint.setColor(Color.rgb(Math.round(117+135*pressed),Math.round(108+95*pressed),Math.round(138-28*pressed)));
            float left=16+col*7.2f,top=50+row*3.4f+.45f*pressed;
            canvas.drawRoundRect(left,top,left+5.6f,top+2.2f,.6f,.6f,paint);
        }
        fill("#827d92"); paint.setShader(new LinearGradient(2,57,2,66,new int[]{color("#b6afc5"),color("#827d92"),color("#4d4a5c")},new float[]{0,.5f,1},Shader.TileMode.CLAMP)); canvas.drawRoundRect(2,57,108,66,3,3,paint);
        stroke("#464151",1); canvas.drawRoundRect(2,57,108,66,3,3,paint); fill("#a29aaf"); canvas.drawRoundRect(42,59,68,62.5f,1,1,paint);
        stroke("#d8cfdf",.5f); canvas.drawLine(10,60,15,59.4f,paint); canvas.drawLine(91,62,94,61.4f,paint);
        fill("#473957"); canvas.drawOval(17.6f,58.9f,28.4f,64.1f,paint);
        fill("#f6cd82"); canvas.drawCircle(21.5f,61.3f,.7f,paint); canvas.drawCircle(24.5f,61.3f,.7f,paint);
        fill(working?"#ffd364":"#695f7e"); canvas.drawCircle(98,61.5f,1,paint); canvas.restore();
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

    private void drawText(Canvas canvas, String value, RectF rect, float size) {
        text.setColor(color("#fff1c7")); text.setTextSize(size*fontScale);
        StaticLayout layout=StaticLayout.Builder.obtain(value,0,value.length(),text,Math.max(1,(int)rect.width())).setAlignment(Layout.Alignment.ALIGN_CENTER).setIncludePad(false).build();
        canvas.save(); canvas.clipRect(rect); canvas.translate(rect.left,rect.top+Math.max(0,(rect.height()-layout.getHeight())/2)); layout.draw(canvas); canvas.restore();
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
