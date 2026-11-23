// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.net.Uri;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONException;

public final class UpdateNotes extends BroadcastReceiver {
    static final String SUPPORT = "https://bolha.kuky.solutions/suporte/";

    private static SharedPreferences state(Context context) {
        return context.getSharedPreferences("welcome", Context.MODE_PRIVATE);
    }

    @Override public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_MY_PACKAGE_REPLACED.equals(intent.getAction())) {
            state(context).edit().putString("pending", BuildConfig.VERSION_NAME).apply();
        }
    }

    static void showPending(Activity activity) {
        SharedPreferences prefs = state(activity);
        String version = BuildConfig.VERSION_NAME;
        if (version.equals(prefs.getString("seen", ""))) return;
        boolean replaced = version.equals(prefs.getString("pending", ""));
        try {
            PackageInfo info = activity.getPackageManager().getPackageInfo(activity.getPackageName(), 0);
            // O Android pode adiar o broadcast se o APK anterior foi parado.
            replaced |= info.lastUpdateTime > info.firstInstallTime;
        } catch (PackageManager.NameNotFoundException ignored) {
            // O marcador do broadcast ainda pode confirmar a instalação.
        }
        if (replaced) {
            prefs.edit().remove("pending").putString("seen", version).apply();
            show(activity);
        }
    }

    static void show(Activity activity) {
        StringBuilder message = new StringBuilder("Versão ").append(BuildConfig.VERSION_NAME);
        try (InputStream stream = activity.getAssets().open("content/novidades.json")) {
            byte[] data = new byte[8192];
            int length = stream.read(data);
            JSONObject notes = new JSONObject(new String(data, 0, length, StandardCharsets.UTF_8));
            JSONArray highlights = notes.optJSONArray("highlights");
            if (BuildConfig.VERSION_NAME.equals(notes.optString("version")) && highlights != null) {
                for (int i = 0; i < Math.min(4, highlights.length()); i++) {
                    message.append("\n\n• ").append(highlights.optString(i));
                }
            }
        } catch (IOException | JSONException | IndexOutOfBoundsException ignored) {
            // O histórico no site permanece acessível se as notas locais falharem.
        }
        new AlertDialog.Builder(activity).setTitle("O que mudou na Bolha").setMessage(message)
            .setNeutralButton("Bugs e correções", (dialog, which) ->
                activity.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(SUPPORT))))
            .setPositiveButton("Entendi", null).show();
    }
}
