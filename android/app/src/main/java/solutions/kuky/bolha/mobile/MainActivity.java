// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.*;
import org.json.JSONObject;

public final class MainActivity extends Activity implements Engine.Listener {
    private Engine engine;
    private Stage stage;
    private TextView status;
    private Button overlay;
    private boolean waitingPermission;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.rgb(24,20,32));
        engine = Engine.get(this);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        if (Build.VERSION.SDK_INT >= 30) page.setOnApplyWindowInsetsListener((view, insets) -> {
            android.graphics.Insets bars = insets.getInsets(android.view.WindowInsets.Type.systemBars()
                    | android.view.WindowInsets.Type.displayCutout());
            view.setPadding(bars.left,bars.top,bars.right,bars.bottom);
            return insets;
        });
        TextView title = new TextView(this);
        title.setText("Bolha");
        title.setTextSize(26);
        title.setTextColor(Color.rgb(255,211,100));
        title.setPadding(dp(16),dp(8),dp(16),0);
        page.addView(title);
        status = new TextView(this);
        status.setText("Abrindo a Bolha…");
        status.setPadding(dp(16),0,dp(16),dp(4));
        page.addView(status);
        stage = new Stage(this,engine,"");
        page.addView(stage,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout play = new LinearLayout(this);
        add(play,"Carinho",() -> action("caress"));
        add(play,"Bicuda",() -> action("kick"));
        add(play,"Jogar para cima",() -> action("lift"));
        page.addView(play);
        LinearLayout rest = new LinearLayout(this);
        add(rest,"Brinquedo",() -> action("ball"));
        add(rest,"Notebook",() -> action("notebook"));
        add(rest,"Dormir / acordar",() -> action(engine.state().optBoolean("asleep")?"wake":"sleep"));
        page.addView(rest);
        LinearLayout settings = new LinearLayout(this);
        overlay = add(settings,"Flutuar",this::toggleOverlay);
        add(settings,"Bola / amendoim",() -> action("toy-style"));
        Switch haptics = new Switch(this);
        haptics.setText("Vibração");
        haptics.setPadding(dp(8),0,dp(12),0);
        SharedPreferences prefs = getSharedPreferences("options",0);
        haptics.setChecked(Haptics.enabled(this));
        haptics.setOnCheckedChangeListener((button,on) -> prefs.edit().putBoolean("haptics",on).apply());
        settings.addView(haptics);
        page.addView(settings);
        setContentView(page);
    }

    @Override protected void onResume() {
        super.onResume();
        if (waitingPermission) {
            waitingPermission=false;
            if (Settings.canDrawOverlays(this)) launchOverlay();
        }
        engine.listen(this);
        stage.post(() -> {
            if (!FloatingBolha.active) engine.resize(stage.getWidth(),stage.getHeight());
        });
    }

    @Override protected void onPause() {
        engine.remove(this);
        super.onPause();
    }

    private Button add(LinearLayout row,String text,Runnable action) {
        Button button = new Button(this);
        button.setText(text);
        button.setAllCaps(false);
        button.setOnClickListener(view -> action.run());
        row.addView(button,new LinearLayout.LayoutParams(0,-2,1));
        return button;
    }

    private int dp(float value) { return Math.round(value*getResources().getDisplayMetrics().density); }
    private void action(String kind) {
        if (FloatingBolha.active) {
            Toast.makeText(this,"Pare o modo flutuante para brincar aqui.",Toast.LENGTH_SHORT).show();
            return;
        }
        engine.action(kind,"",0,0,0,0);
    }

    private void toggleOverlay() {
        if (FloatingBolha.active) {
            stopService(new Intent(this,FloatingBolha.class));
            stage.postDelayed(() -> engine.resize(stage.getWidth(),stage.getHeight()),150);
        } else if (!Settings.canDrawOverlays(this)) {
            waitingPermission=true;
            try { startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:"+getPackageName()))); }
            catch (android.content.ActivityNotFoundException error) {
                waitingPermission=false;
                Toast.makeText(this,"Abra a permissão de sobreposição nas configurações do Android.",Toast.LENGTH_LONG).show();
            }
        } else launchOverlay();
    }

    private void launchOverlay() {
        Intent intent = new Intent(this,FloatingBolha.class);
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent); else startService(intent);
        moveTaskToBack(true);
    }

    @Override public void frame(JSONObject state, String error) {
        if (error != null) { status.setText(error); return; }
        overlay.setText(FloatingBolha.active?"Parar de flutuar":"Flutuar");
        stage.setVisibility(FloatingBolha.active?View.INVISIBLE:View.VISIBLE);
        status.setText(FloatingBolha.active?"A Bolha está flutuando."
                : String.format(java.util.Locale.forLanguageTag("pt-BR"),"Energia %.0f%%  ·  %d neurônios",
                state.optDouble("energy",0)*100,state.optInt("neurons")));
        if (!FloatingBolha.active) Haptics.frame(this,state);
        stage.invalidate();
    }
}
