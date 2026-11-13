// SPDX-License-Identifier: GPL-3.0-or-later
// Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
package solutions.kuky.bolha.mobile;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.util.Locale;
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
        engine = Engine.get(this);
        LinearLayout page = MobileUi.column(this);
        MobileUi.applyWindow(this,page);
        LinearLayout header = MobileUi.row(this);
        header.setGravity(android.view.Gravity.CENTER_VERTICAL);
        header.setPadding(dp(18),dp(12),dp(12),dp(6));
        TextView title = MobileUi.text(this,"Bolha",30,MobileUi.GOLD);
        header.addView(title,new LinearLayout.LayoutParams(0,-2,1));
        header.addView(MobileUi.button(this,"Central da Bolha",() ->
            startActivity(new Intent(this,CentralActivity.class))));
        page.addView(header);
        status = MobileUi.text(this,"Abrindo a Bolha…",14,MobileUi.MUTED);
        status.setPadding(dp(20),0,dp(20),dp(8));
        page.addView(status);
        stage = new Stage(this,engine,"");
        page.addView(stage,new LinearLayout.LayoutParams(-1,0,1));
        TextView help = MobileUi.text(this,"Toque para dar carinho. Arraste e solte para brincar.",13,MobileUi.MUTED);
        help.setPadding(dp(20),dp(8),dp(20),dp(6));
        page.addView(help);
        LinearLayout actions = MobileUi.column(this);
        actions.setPadding(dp(12),0,dp(12),dp(10));
        LinearLayout play = MobileUi.row(this);
        MobileUi.addEqual(play,MobileUi.button(this,"Carinho",() -> action("caress")));
        MobileUi.addEqual(play,MobileUi.button(this,"Brinquedo",() -> action("ball")));
        actions.addView(play);
        LinearLayout rest = MobileUi.row(this);
        MobileUi.addEqual(rest,MobileUi.button(this,"Dormir / acordar",() ->
            action(engine.state().optBoolean("asleep")?"wake":"sleep")));
        overlay = MobileUi.button(this,"Flutuar",this::toggleOverlay);
        MobileUi.addEqual(rest,overlay);
        actions.addView(rest);
        page.addView(actions);
        setContentView(page);
    }

    @Override protected void onResume() {
        super.onResume();
        if (waitingPermission) {
            waitingPermission=false;
            if (Settings.canDrawOverlays(this)) prepareOverlay();
        }
        engine.listen(this);
        if (getIntent().getBooleanExtra("floatingRequested",false)) {
            getIntent().removeExtra("floatingRequested");
            if (!FloatingBolha.active) stage.post(this::toggleOverlay);
        }
        stage.post(this::resizeStage);
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
    }

    @Override protected void onPause() {
        engine.remove(this);
        super.onPause();
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        super.onSaveInstanceState(state);
        state.putBoolean("waitingOverlayPermission",waitingPermission);
    }

    private int dp(float value) { return MobileUi.dp(this,value); }

    private void resizeStage() {
        if (!FloatingBolha.active) {
            float density=getResources().getDisplayMetrics().density;
            engine.resize(stage.getWidth()/density,stage.getHeight()/density);
        }
    }

    private void action(String kind) { engine.action(kind,"",0,0,0,0); }

    private void toggleOverlay() {
        if (FloatingBolha.active) {
            stopService(new Intent(this,FloatingBolha.class));
            stage.postDelayed(this::resizeStage,150);
        } else if (!Settings.canDrawOverlays(this)) {
            waitingPermission=true;
            try {
                startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:"+getPackageName())));
            } catch (android.content.ActivityNotFoundException error) {
                waitingPermission=false;
                Toast.makeText(this,"Abra a permissão de sobreposição nas configurações do Android.",Toast.LENGTH_LONG).show();
            }
        } else prepareOverlay();
    }

    private void prepareOverlay() {
        SharedPreferences options=getSharedPreferences("options",0);
        if (Build.VERSION.SDK_INT>=33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                !=PackageManager.PERMISSION_GRANTED && !options.getBoolean("askedNotifications",false)) {
            options.edit().putBoolean("askedNotifications",true).apply();
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS},NOTIFICATIONS_REQUEST);
        } else launchOverlay();
    }

    @Override public void onRequestPermissionsResult(int request,String[] permissions,int[] results) {
        super.onRequestPermissionsResult(request,permissions,results);
        if (request==NOTIFICATIONS_REQUEST && Settings.canDrawOverlays(this)) launchOverlay();
    }

    private void launchOverlay() {
        Intent intent=new Intent(this,FloatingBolha.class);
        try {
            if (Build.VERSION.SDK_INT>=26) startForegroundService(intent); else startService(intent);
            moveTaskToBack(true);
        } catch (IllegalStateException | SecurityException error) {
            android.util.Log.e("Bolha","Iniciar modo flutuante",error);
            Toast.makeText(this,"Não foi possível iniciar o modo flutuante.",Toast.LENGTH_LONG).show();
        }
    }

    @Override public void frame(JSONObject state,String error) {
        String overlayLabel=FloatingBolha.active?"Parar de flutuar":"Flutuar";
        if (!overlayLabel.contentEquals(overlay.getText())) overlay.setText(overlayLabel);
        stage.setVisibility(FloatingBolha.active?View.INVISIBLE:View.VISIBLE);
        String label;
        if (error!=null) label=error;
        else if (FloatingBolha.active) label="A Bolha está flutuando. Você pode continuar por aqui.";
        else label=String.format(Locale.forLanguageTag("pt-BR"),"Energia %.0f%%  ·  %d neurônios",
            state.optDouble("energy",0)*100,state.optInt("neurons"));
        if (!label.contentEquals(status.getText())) status.setText(label);
        if (error!=null) return;
        if (!FloatingBolha.active) Haptics.frame(this,state);
        stage.frame(state);
    }
}
