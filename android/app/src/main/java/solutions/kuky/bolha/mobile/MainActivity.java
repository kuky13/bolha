// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.app.Activity;
import android.Manifest;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.*;
import org.json.JSONObject;

public final class MainActivity extends Activity implements Engine.Listener {
    private static final int NOTIFICATIONS_REQUEST = 1;
    private Engine engine;
    private Stage stage;
    private TextView status;
    private Button overlay;
    private boolean waitingPermission;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        waitingPermission = state != null && state.getBoolean("waitingOverlayPermission");
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
            if (Settings.canDrawOverlays(this)) prepareOverlay();
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

    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        state.putBoolean("waitingOverlayPermission",waitingPermission);
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
        } else prepareOverlay();
    }

    private void prepareOverlay() {
        SharedPreferences options = getSharedPreferences("options",0);
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED && !options.getBoolean("askedNotifications",false)) {
            options.edit().putBoolean("askedNotifications",true).apply();
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},NOTIFICATIONS_REQUEST);
        } else launchOverlay();
    }

    @Override public void onRequestPermissionsResult(int request, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(request,permissions,results);
        if (request == NOTIFICATIONS_REQUEST && Settings.canDrawOverlays(this)) launchOverlay();
    }

    private void launchOverlay() {
        Intent intent = new Intent(this,FloatingBolha.class);
        try {
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent); else startService(intent);
            moveTaskToBack(true);
        } catch (IllegalStateException | SecurityException error) {
            android.util.Log.e("Bolha","Iniciar modo flutuante",error);
            Toast.makeText(this,"Não foi possível iniciar o modo flutuante.",Toast.LENGTH_LONG).show();
        }
    }

    @Override public void frame(JSONObject state, String error) {
        String overlayLabel = FloatingBolha.active?"Parar de flutuar":"Flutuar";
        if (!overlayLabel.contentEquals(overlay.getText())) overlay.setText(overlayLabel);
        stage.setVisibility(FloatingBolha.active?View.INVISIBLE:View.VISIBLE);
        String statusLabel;
        if (error != null) statusLabel = error;
        else if (FloatingBolha.active) statusLabel = "A Bolha está flutuando.";
        else statusLabel = String.format(java.util.Locale.forLanguageTag("pt-BR"),
                "Energia %.0f%%  ·  %d neurônios",state.optDouble("energy",0)*100,state.optInt("neurons"));
        if (!statusLabel.contentEquals(status.getText())) status.setText(statusLabel);
        if (error != null) return;
        if (!FloatingBolha.active) Haptics.frame(this,state);
        stage.invalidate();
    }
}
