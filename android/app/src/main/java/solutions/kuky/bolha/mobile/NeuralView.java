// SPDX-License-Identifier: GPL-3.0-or-later
// Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
package solutions.kuky.bolha.mobile;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.view.MotionEvent;
import android.view.View;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

final class NeuralView extends View {
    interface Selection { void changed(String description); }
    private static final int[] COLORS={0xffe7be64,0xffaa96ef,0xff6bc7b9,0xfff29aa9};
    private static final String[] KINDS={"sensorial","excitatório","inibitório","motor"};
    private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
    private JSONObject neural=new JSONObject();
    private int selected=-1;
    private Selection listener;

    NeuralView(Context context) {
        super(context);
        setMinimumHeight(MobileUi.dp(context,300));
        setBackground(MobileUi.background(context,0xff181420,14));
        setContentDescription("Atividade dos neurônios da Bolha. Toque em um ponto para inspecionar.");
        setClickable(true);
    }

    void onSelection(Selection listener) { this.listener=listener; }
    int selectedIndex() { return selected; }

    void frame(JSONObject state) {
        JSONObject next=state.optJSONObject("neural");
        if (next!=null && next.has("positions")) {
            neural=next;
            invalidate();
        }
    }

    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        JSONArray positions=neural.optJSONArray("positions");
        if (positions==null) {
            paint.setColor(MobileUi.MUTED);
            paint.setTextSize(MobileUi.dp(getContext(),14));
            canvas.drawText("Aguardando atividade da rede…",MobileUi.dp(getContext(),16),getHeight()/2f,paint);
            return;
        }
        float margin=MobileUi.dp(getContext(),12);
        float width=getWidth()-2*margin,height=getHeight()-2*margin;
        JSONArray traces=neural.optJSONArray("trace");
        JSONArray kinds=neural.optJSONArray("kind");
        JSONArray edges=neural.optJSONArray("connections");
        if (selected>=0 && edges!=null) drawConnections(canvas,positions,edges,margin,width,height);
        for (int index=0;index<positions.length();index++) {
            JSONArray point=positions.optJSONArray(index);
            if (point==null) continue;
            float x=margin+(float)point.optDouble(0)*width;
            float y=margin+(float)point.optDouble(1)*height;
            double activity=traces==null?0:Math.max(0,traces.optDouble(index));
            float strength=(float)Math.min(1,activity/2.);
            int kind=kinds==null?0:Math.max(0,Math.min(3,kinds.optInt(index)));
            paint.setColor(COLORS[kind]);
            paint.setAlpha(100+(int)(155*strength));
            float radius=MobileUi.dp(getContext(),1.5f+1.8f*strength);
            canvas.drawCircle(x,y,radius,paint);
            if (strength>.25f) {
                paint.setAlpha((int)(35*strength));
                canvas.drawCircle(x,y,radius*2.3f,paint);
            }
            if (index==selected) {
                paint.setColor(MobileUi.TEXT);
                paint.setAlpha(255);
                paint.setStyle(Paint.Style.STROKE);
                paint.setStrokeWidth(MobileUi.dp(getContext(),1));
                canvas.drawCircle(x,y,MobileUi.dp(getContext(),7),paint);
                paint.setStyle(Paint.Style.FILL);
            }
        }
        paint.setAlpha(255);
    }

    private void drawConnections(Canvas canvas,JSONArray positions,JSONArray edges,float margin,float width,float height) {
        for (int index=0;index<edges.length();index++) {
            JSONObject edge=edges.optJSONObject(index);
            if (edge==null || (edge.optInt("source")!=selected && edge.optInt("target")!=selected)) continue;
            JSONArray first=positions.optJSONArray(edge.optInt("source"));
            JSONArray second=positions.optJSONArray(edge.optInt("target"));
            if (first==null || second==null) continue;
            paint.setColor(edge.optDouble("weight",1)<0?0x886bc7b9:0x88e7be64);
            paint.setStrokeWidth(MobileUi.dp(getContext(),1));
            canvas.drawLine(margin+(float)first.optDouble(0)*width,margin+(float)first.optDouble(1)*height,
                margin+(float)second.optDouble(0)*width,margin+(float)second.optDouble(1)*height,paint);
        }
    }

    @Override public boolean onTouchEvent(MotionEvent event) {
        if (event.getActionMasked()!=MotionEvent.ACTION_UP) return true;
        JSONArray positions=neural.optJSONArray("positions");
        if (positions==null) return performClick();
        float margin=MobileUi.dp(getContext(),12),best=Float.MAX_VALUE;
        for (int index=0;index<positions.length();index++) {
            JSONArray point=positions.optJSONArray(index);
            if (point==null) continue;
            float x=margin+(float)point.optDouble(0)*(getWidth()-2*margin);
            float y=margin+(float)point.optDouble(1)*(getHeight()-2*margin);
            float distance=(float)Math.hypot(x-event.getX(),y-event.getY());
            if (distance<best) { best=distance;selected=index; }
        }
        if (listener!=null) listener.changed(selectionDescription());
        invalidate();
        return performClick();
    }

    String selectionDescription() {
        JSONArray kinds=neural.optJSONArray("kind"),traces=neural.optJSONArray("trace");
        int kind=kinds==null?0:Math.max(0,Math.min(3,kinds.optInt(selected)));
        return String.format(Locale.forLanguageTag("pt-BR"),"Neurônio %d · %s · atividade %.3f",
            selected+1,KINDS[kind],traces==null?0:traces.optDouble(selected));
    }

    @Override public boolean performClick() { super.performClick();return true; }
}
