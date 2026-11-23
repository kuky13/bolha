// SPDX-License-Identifier: GPL-3.0-or-later
package solutions.kuky.bolha.mobile;

import android.app.Activity;
import android.app.ActivityManager;
import android.content.ClipData;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.util.DisplayMetrics;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.text.InputFilter;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Locale;
import java.util.UUID;
import java.util.regex.Pattern;
import org.json.JSONObject;
import org.json.JSONException;

public final class ReportActivity extends Activity {
    private static final int MIB = 1024 * 1024;
    private static final int PICK = 31;
    private static final Pattern RECEIPT = Pattern.compile("[A-Za-z0-9_-]{8,96}");
    private final ArrayList<Attachment> attachments = new ArrayList<>();
    private final String submission = UUID.randomUUID().toString();
    private EditText title, description, reproduce, technicalPreview, errorsPreview;
    private CheckBox technical, errors, consent;
    private TextView status;
    private LinearLayout form, files;
    private Button send;
    private boolean sending;

    @Override protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        form = MobileUi.column(this);
        form.setPadding(dp(20), dp(12), dp(20), dp(20));
        ScrollView scroll = new ScrollView(this);
        scroll.addView(form);
        MobileUi.applyWindow(this, scroll);
        setContentView(scroll);
        form.addView(MobileUi.title(this, "Relatar problema"));
        caption("O relato inclui a versão da Bolha e a plataforma. Você escolhe os demais dados.");
        title = field("Título do problema", 180, 1);
        description = field("O que aconteceu?", 4000, 3);
        reproduce = field("Como reproduzir", 4000, 3);
        technical = check("Incluir informações técnicas");
        technicalPreview = field("Prévia editável das informações técnicas", 4000, 4);
        technicalPreview.setVisibility(View.GONE);
        technical.setOnCheckedChangeListener((button, checked) -> {
            technicalPreview.setVisibility(checked ? View.VISIBLE : View.GONE);
            if (checked) technicalPreview.setText(technicalSummary());
        });
        errors = check("Incluir erros da Bolha");
        errorsPreview = field("Prévia editável dos erros", 4000, 2);
        errorsPreview.setVisibility(View.GONE);
        errors.setOnCheckedChangeListener((button, checked) -> {
            errorsPreview.setVisibility(checked ? View.VISIBLE : View.GONE);
            if (checked) {
                String error = Engine.get(this).state().optString("error", "");
                errorsPreview.setText(error.isEmpty() ? "" : "Falha registrada pelo motor da Bolha.");
            }
        });
        form.addView(MobileUi.button(this, "Escolher imagens ou vídeos", this::choose));
        files = MobileUi.column(this);
        form.addView(files);
        caption("O relato vai para um painel privado. Você pode revisar os dados e remover qualquer anexo antes do envio.");
        form.addView(MobileUi.button(this, "Política de privacidade", () -> startActivity(
            new Intent(Intent.ACTION_VIEW, Uri.parse(UpdateNotes.SUPPORT + "#privacidade")))));
        consent = check("Revisei o relato e autorizo o envio dos dados selecionados");
        status = MobileUi.text(this, "", 14, MobileUi.MUTED);
        status.setTextIsSelectable(true);
        form.addView(status);
        send = MobileUi.button(this, "Enviar relato", this::submit);
        send.setEnabled(false);
        form.addView(send);
        consent.setOnCheckedChangeListener((button, checked) -> send.setEnabled(checked && !sending));
    }

    private int dp(int value) { return MobileUi.dp(this, value); }

    @Override protected void onResume() {
        super.onResume();
        FloatingBolha.foregroundUi(this, true);
    }

    @Override protected void onPause() {
        FloatingBolha.foregroundUi(this, false);
        super.onPause();
    }

    private void caption(String text) {
        form.addView(MobileUi.text(this, text, 14, MobileUi.MUTED));
    }

    private EditText field(String name, int max, int lines) {
        EditText widget = new EditText(this);
        widget.setHint(name);
        widget.setContentDescription(name);
        widget.setTextColor(MobileUi.TEXT);
        widget.setHintTextColor(MobileUi.MUTED);
        widget.setFilters(new InputFilter[]{new InputFilter.LengthFilter(max)});
        widget.setMinLines(lines);
        form.addView(widget, new LinearLayout.LayoutParams(-1, -2));
        return widget;
    }

    private CheckBox check(String name) {
        CheckBox widget = new CheckBox(this);
        widget.setText(name);
        widget.setTextColor(MobileUi.TEXT);
        form.addView(widget);
        return widget;
    }

    private String technicalSummary() {
        ActivityManager.MemoryInfo memory = new ActivityManager.MemoryInfo();
        getSystemService(ActivityManager.class).getMemoryInfo(memory);
        DisplayMetrics screen = getResources().getDisplayMetrics();
        return "Android " + Build.VERSION.RELEASE + " · " + Build.SUPPORTED_ABIS[0]
            + "\nModelo: " + Build.MANUFACTURER + " " + Build.MODEL
            + "\nRAM total: " + memory.totalMem / MIB + " MiB"
            + "\nRAM disponível: " + memory.availMem / MIB + " MiB"
            + "\nTela: " + screen.widthPixels + "×" + screen.heightPixels;
    }

    private void choose() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[]{"image/*", "video/*"});
        intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
        startActivityForResult(intent, PICK);
    }

    @Override protected void onActivityResult(int request, int result, Intent intent) {
        super.onActivityResult(request, result, intent);
        if (request != PICK || result != RESULT_OK || intent == null) return;
        ClipData selection = intent.getClipData();
        ArrayList<Attachment> next = new ArrayList<>(attachments);
        try {
            if (selection == null) add(next, intent.getData());
            else for (int i = 0; i < selection.getItemCount(); i++) add(next, selection.getItemAt(i).getUri());
            long total = 0L;
            for (Attachment item : next) total += item.size;
            if (next.size() > 3 || total > 20L * MIB) throw new IOException();
            attachments.clear();
            attachments.addAll(next);
            renderFiles();
            status.setText("");
        } catch (IOException | SecurityException error) {
            status.setText("Escolha até três imagens ou vídeos com até 20 MB no total.");
        }
    }

    private void add(ArrayList<Attachment> list, Uri uri) throws IOException {
        if (uri == null || !"content".equals(uri.getScheme())) throw new IOException();
        for (Attachment item : list) if (item.uri.equals(uri)) return;
        try (Cursor cursor = getContentResolver().query(uri,
                new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE}, null, null, null)) {
            if (cursor == null || !cursor.moveToFirst() || cursor.isNull(0) || cursor.isNull(1)) throw new IOException();
            String name = cursor.getString(0);
            int dot = name.lastIndexOf('.');
            if (dot < 0) throw new IOException();
            String suffix = name.substring(dot).toLowerCase(Locale.ROOT);
            String mime = mime(suffix);
            long size = cursor.getLong(1);
            if (mime.isEmpty() || size <= 0 || size > limit(mime)) throw new IOException();
            list.add(new Attachment(uri, name, suffix, mime, size));
        }
    }

    private static String mime(String suffix) {
        switch (suffix) {
            case ".png": return "image/png";
            case ".jpg": case ".jpeg": return "image/jpeg";
            case ".gif": return "image/gif";
            case ".webp": return "image/webp";
            case ".mp4": return "video/mp4";
            case ".webm": return "video/webm";
            case ".mov": return "video/quicktime";
            default: return "";
        }
    }

    private static int limit(String type) { return (type.startsWith("image/") ? 5 : 15) * MIB; }

    private void renderFiles() {
        files.removeAllViews();
        for (Attachment item : attachments) {
            TextView label = MobileUi.text(this, item.name, 13, MobileUi.TEXT);
            label.setMaxLines(2);
            files.addView(label);
            files.addView(MobileUi.button(this, "Remover anexo", () -> {
                attachments.remove(item);
                renderFiles();
            }));
        }
    }

    private void submit() {
        if (!consent.isChecked() || sending) return;
        if (text(title).length() < 4 || text(description).length() < 8) {
            status.setText("Preencha o título e descreva o que aconteceu.");
            return;
        }
        JSONObject data = new JSONObject();
        try {
            data.put("title", text(title)).put("description", text(description)).put("steps", text(reproduce))
                .put("platform", "Android").put("version", BuildConfig.VERSION_NAME).put("consent", true)
                .put("technical", technical.isChecked() ? text(technicalPreview) : "")
                .put("errors", errors.isChecked() ? text(errorsPreview) : "").put("submissionId", submission);
        } catch (JSONException error) { return; }
        ArrayList<Attachment> snapshot = new ArrayList<>(attachments);
        sending = true;
        send.setEnabled(false);
        status.setText("Enviando relato…");
        new Thread(() -> {
            String receipt;
            try { receipt = upload(data, snapshot); }
            catch (IOException | JSONException | SecurityException error) { receipt = ""; }
            String result = receipt;
            runOnUiThread(() -> {
                if (isFinishing() || isDestroyed()) return;
                sending = false;
                if (result.isEmpty()) {
                    status.setText("Não foi possível enviar. Confira a conexão e os anexos.");
                    send.setEnabled(consent.isChecked());
                } else {
                    status.setText("Relato recebido. Protocolo " + result);
                    consent.setChecked(false);
                    consent.setEnabled(false);
                    send.setEnabled(false);
                }
            });
        }, "bolha-relato").start();
    }

    private static String text(EditText field) { return field.getText().toString().trim(); }

    private String upload(JSONObject data, ArrayList<Attachment> snapshot) throws IOException, JSONException {
        String boundary = UUID.randomUUID().toString();
        ByteArrayOutputStream buf = new ByteArrayOutputStream();
        write(buf, "--" + boundary + "\r\nContent-Disposition: form-data; name=\"data\"\r\n\r\n"
                + data + "\r\n");
        int index = 1;
        long total = 0;
        for (Attachment item : snapshot) {
            write(buf, "--" + boundary + "\r\nContent-Disposition: form-data; name=\"media\"; filename=\"anexo-"
                    + (index++) + item.suffix + "\"\r\nContent-Type: " + item.mime + "\r\n\r\n");
            try (InputStream input = getContentResolver().openInputStream(item.uri)) {
                if (input == null) throw new IOException();
                byte[] block = new byte[8192];
                int count;
                long size = 0;
                while ((count = input.read(block)) != -1) {
                    size += count;
                    total += count;
                    if (size > limit(item.mime) || total > 20L * MIB) throw new IOException();
                    buf.write(block, 0, count);
                }
                if (size == 0) throw new IOException();
            }
            write(buf, "\r\n");
        }
        write(buf, "--" + boundary + "--\r\n");
        HttpURLConnection connection = (HttpURLConnection) new URL(
            "https://relatos.kuky.solutions/v1/reports").openConnection();
        try {
            connection.setConnectTimeout(15000);
            connection.setReadTimeout(35000);
            connection.setInstanceFollowRedirects(false);
            connection.setRequestMethod("POST");
            connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);
            connection.setDoOutput(true);
            connection.setFixedLengthStreamingMode(buf.size());
            try (OutputStream output = connection.getOutputStream()) { buf.writeTo(output); }
            if (connection.getResponseCode() != 201) throw new IOException();
            try (InputStream input = connection.getInputStream()) {
                byte[] message = new byte[4096];
                int count = 0;
                while (count < message.length) {
                    int n = input.read(message, count, message.length - count);
                    if (n < 0) break;
                    count += n;
                }
                String receipt = new JSONObject(new String(message, 0, count, StandardCharsets.UTF_8))
                    .optString("protocol");
                if (!RECEIPT.matcher(receipt).matches()) throw new IOException();
                return receipt;
            }
        } finally { connection.disconnect(); }
    }

    private static void write(ByteArrayOutputStream output, String text) {
        byte[] utf8 = text.getBytes(StandardCharsets.UTF_8);
        output.write(utf8, 0, utf8.length);
    }

    private static final class Attachment {
        final Uri uri;
        final String name, suffix, mime;
        final long size;
        Attachment(Uri uri, String name, String suffix, String mime, long size) {
            this.uri = uri; this.name = name; this.suffix = suffix; this.mime = mime; this.size = size;
        }
    }
}
