// SPDX-License-Identifier: GPL-3.0-or-later
// Bolha is based on Pestinha by @mille-okws and contributors; see NOTICE.md.
package solutions.kuky.bolha.mobile;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.SystemClock;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.Spinner;
import android.widget.Switch;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

public final class CentralActivity extends Activity implements Engine.Listener {
    private static final String[] SECTIONS={"Aparência","Comportamento","Cérebro","Atividades","Privacidade","App"};
    private final Map<String,Switch> toggles=new LinkedHashMap<>();
    private final Map<String,SeekBar> sliders=new LinkedHashMap<>();
    private final Map<String,TextView> values=new HashMap<>();
    private final Map<String,int[]> sliderRanges=new HashMap<>();
    private final Set<String> tracking=new HashSet<>();
    private final ArrayList<Button> navigation=new ArrayList<>();
    private Engine engine;
    private LinearLayout content;
    private TextView status,brainStatus,decisionStatus,selectedNeuron,usageStatus,motionStatus;
    private NeuralView neural;
    private Stage expressionPreview;
    private Spinner toyAppearance,expression;
    private JSONObject preferences=new JSONObject();
    private String lastPreferences="";
    private String[] expressionNames=new String[0];
    private int section;
    private long lastBrainText;
    private boolean loading,waitingUsage;

    @Override protected void onCreate(Bundle saved) {
        super.onCreate(saved);
        engine=Engine.get(this);
        section=saved==null?0:saved.getInt("section",0);
        waitingUsage=saved!=null && saved.getBoolean("waitingUsage");
        LinearLayout page=MobileUi.column(this);
        MobileUi.applyWindow(this,page);
        LinearLayout header=MobileUi.row(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(10),dp(8),dp(16),dp(8));
        header.addView(MobileUi.button(this,"Voltar",this::finish));
        TextView title=MobileUi.text(this,"Central da Bolha",22,MobileUi.TEXT);
        title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        title.setPadding(dp(14),0,0,0);
        header.addView(title,new LinearLayout.LayoutParams(0,-2,1));
        page.addView(header);

        boolean wide=getResources().getConfiguration().screenWidthDp>=720;
        LinearLayout body=wide?MobileUi.row(this):MobileUi.column(this);
        page.addView(body,new LinearLayout.LayoutParams(-1,0,1));
        LinearLayout nav=wide?MobileUi.column(this):MobileUi.row(this);
        nav.setPadding(dp(8),dp(2),dp(8),dp(8));
        for (int index=0;index<SECTIONS.length;index++) {
            final int target=index;
            Button button=MobileUi.button(this,SECTIONS[index],() -> showSection(target));
            navigation.add(button);
            nav.addView(button,new LinearLayout.LayoutParams(wide?dp(175):-2,-2));
        }
        if (wide) body.addView(nav,new LinearLayout.LayoutParams(dp(191),-1));
        else {
            HorizontalScrollView scroll=new HorizontalScrollView(this);
            scroll.setHorizontalScrollBarEnabled(false);
            scroll.addView(nav);
            body.addView(scroll,new LinearLayout.LayoutParams(-1,-2));
        }
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);
        content=MobileUi.column(this);
        int padding=dp(wide?28:20);
        content.setPadding(padding,dp(12),padding,dp(28));
        scroll.addView(content);
        body.addView(scroll,wide?new LinearLayout.LayoutParams(0,-1,1):new LinearLayout.LayoutParams(-1,0,1));
        status=MobileUi.text(this,"As configurações ficam neste aparelho.",13,MobileUi.MUTED);
        status.setPadding(dp(20),dp(8),dp(20),dp(12));
        page.addView(status);
        setContentView(page);
        showSection(section);
    }

    @Override protected void onResume() {
        super.onResume();
        engine.listen(this);
        command("panel",true);
        command("monitor",section==2);
        if (waitingUsage) {
            waitingUsage=false;
            change("senseApp",UsageContext.permitted(this));
        }
    }

    @Override protected void onPause() {
        command("monitor",false);
        command("panel",false);
        engine.remove(this);
        super.onPause();
    }

    @Override protected void onSaveInstanceState(Bundle saved) {
        super.onSaveInstanceState(saved);
        saved.putInt("section",section);
        saved.putBoolean("waitingUsage",waitingUsage);
    }

    private int dp(float value) { return MobileUi.dp(this,value); }

    private void showSection(int next) {
        section=next;
        lastBrainText=0;
        toggles.clear();sliders.clear();values.clear();sliderRanges.clear();tracking.clear();
        neural=null;brainStatus=null;decisionStatus=null;selectedNeuron=null;
        usageStatus=null;motionStatus=null;expressionPreview=null;toyAppearance=null;expression=null;
        content.removeAllViews();
        for (int index=0;index<navigation.size();index++) {
            Button button=navigation.get(index);
            button.setTextColor(index==section?MobileUi.BACKGROUND:MobileUi.TEXT);
            button.setBackgroundTintList(ColorStateList.valueOf(index==section?MobileUi.GOLD:MobileUi.SURFACE));
            button.setSelected(index==section);
        }
        JSONObject current=engine.state().optJSONObject("preferences");
        if (current!=null) preferences=current;
        loading=true;
        switch (section) {
            case 0: appearance();break;
            case 1: behavior();break;
            case 2: brain();break;
            case 3: activities();break;
            case 4: privacy();break;
            default: application();break;
        }
        loading=false;
        loadPreferences();
        command("monitor",section==2);
    }

    private void heading(String label) { content.addView(MobileUi.title(this,label)); }

    private TextView description(String label) {
        TextView text=MobileUi.text(this,label,14,MobileUi.MUTED);
        text.setPadding(0,0,0,dp(16));
        content.addView(text);
        return text;
    }

    private void divider(String label) {
        TextView text=MobileUi.text(this,label,17,MobileUi.TEXT);
        text.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        text.setPadding(0,dp(22),0,dp(8));
        content.addView(text);
    }

    private void toggle(String key,String label,String help) {
        Switch view=new Switch(this);
        view.setText(label);
        view.setTextSize(16);
        view.setTextColor(MobileUi.TEXT);
        view.setMinHeight(dp(54));
        view.setPadding(0,dp(4),0,dp(4));
        view.setButtonTintList(ColorStateList.valueOf(MobileUi.GOLD));
        view.setChecked(preferences.optBoolean(key,key.equals("mouthEnabled")||key.equals("hapticsEnabled")));
        view.setOnCheckedChangeListener((button,enabled) -> {
            if (loading) return;
            if (key.equals("senseApp") && enabled && !UsageContext.permitted(this)) {
                loading=true;view.setChecked(false);loading=false;
                waitingUsage=true;
                startActivity(new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS));
                status.setText("Autorize o acesso de uso para ler o nome do aplicativo ativo.");
                return;
            }
            change(key,enabled);
        });
        toggles.put(key,view);
        content.addView(view,new LinearLayout.LayoutParams(-1,-2));
        if (!help.isEmpty()) description(help);
    }

    private void slider(String key,String label,int min,int max,int initial,String suffix) {
        TextView value=MobileUi.text(this,label,16,MobileUi.TEXT);
        value.setPadding(0,dp(12),0,0);
        values.put(key,value);
        sliderRanges.put(key,new int[]{min,max});
        content.addView(value);
        SeekBar slider=new SeekBar(this);
        slider.setMax(max-min);
        slider.setProgress(Math.max(0,Math.min(max-min,initial-min)));
        slider.setMinHeight(dp(48));
        slider.setContentDescription(label);
        slider.setProgressTintList(ColorStateList.valueOf(MobileUi.PURPLE));
        slider.setThumbTintList(ColorStateList.valueOf(MobileUi.GOLD));
        value.setText(label+"  "+(slider.getProgress()+min)+suffix);
        slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar bar,int progress,boolean fromUser) {
                value.setText(label+"  "+(progress+min)+suffix);
            }
            @Override public void onStartTrackingTouch(SeekBar bar) { tracking.add(key); }
            @Override public void onStopTrackingTouch(SeekBar bar) {
                tracking.remove(key);
                double result=bar.getProgress()+min;
                if (key.equals("opacity") || key.equals("shakeSensitivity") || key.startsWith("scale:")) result/=100.;
                if (key.equals("mischiefInterval")) result*=60.;
                if (key.startsWith("scale:")) {
                    JSONObject scales=new JSONObject();
                    put(scales,key.substring(6),result);
                    change("objectScales",scales);
                } else if (key.equals("popThrowLimit")) change(key,(int)result);
                else change(key,result);
            }
        });
        sliders.put(key,slider);
        content.addView(slider,new LinearLayout.LayoutParams(-1,-2));
    }

    private void appearance() {
        heading("Aparência");
        description("O mesmo rosto da Bolha do computador, com tamanho e área de toque adaptados ao celular.");
        slider("avatarSize","Tamanho da Bolha",48,200,136," dp");
        slider("opacity","Opacidade",20,100,100,"%");
        toggle("mouthEnabled","Boca nas expressões","A boca acompanha o olhar, a emoção e a rotação do corpo.");
        divider("Brinquedo");
        toyAppearance=spinner(new String[]{"Amendoim","Bolinha"});
        toyAppearance.setSelection(preferences.optString("toyAppearance","peanut").equals("ball")?1:0);
        toyAppearance.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(android.widget.AdapterView<?> parent,View view,int position,long id) {
                String value=position==1?"ball":"peanut";
                if (!loading && !value.equals(preferences.optString("toyAppearance","peanut"))) change("toyAppearance",value);
            }
            @Override public void onNothingSelected(android.widget.AdapterView<?> parent) {}
        });
        divider("Tamanho de cada objeto");
        String[] keys={"toy","notebook","reaction","note","sign","corner","effects"};
        String[] labels={"Brinquedo","Notebook","GIFs e memes","Bilhetes","Cartazes","Cantinho","Efeitos"};
        for (int index=0;index<keys.length;index++) slider("scale:"+keys[index],labels[index],60,180,100,"%");
        button("Restaurar aparência",() -> {
            JSONObject patch=new JSONObject();
            put(patch,"avatarSize",136);put(patch,"opacity",1.);put(patch,"mouthEnabled",true);
            JSONObject scales=new JSONObject();
            for (String key:keys) put(scales,key,1.);
            put(patch,"objectScales",scales);engine.configure(patch);
        });
    }

    private void behavior() {
        heading("Comportamento");
        description("O cérebro escolhe o que fazer a partir do humor, das necessidades e das experiências da Bolha.");
        toggle("roaming","Passear e explorar","Pausar o passeio mantém as reações às suas interações.");
        toggle("adaptiveBehavior","Objetivos e aprendizado adaptativo","Usa as decisões aprendidas para brincar, descansar e procurar atenção.");
        toggle("learnRoutine","Aprender hábitos por horário","A rotina e as associações ficam salvas neste aparelho.");
        divider("Chacoalhar o celular");
        toggle("shakeEnabled","Reagir ao chacoalhar","A Bolha e os brinquedos soltos caem e quicam. O objeto segurado continua na sua mão.");
        motionStatus=description("");
        slider("shakeSensitivity","Sensibilidade",50,200,100,"%");
        toggle("hapticsEnabled","Vibração","Pulsos leves acompanham carinho, impacto e irritação.");
        divider("Travessuras");
        toggle("mischiefEnabled","Memes, bilhetes e travessuras","");
        toggle("speechEnabled","Falas e pensamentos","Balões curtos acompanham as interações e as decisões da Bolha.");
        toggle("onlineReactions","Buscar memes e GIFs online","A pesquisa usa o humor da Bolha. As imagens ficam apenas na memória enquanto aparecem.");
        slider("mischiefInterval","Intervalo mínimo",1,30,5," min");
        slider("maxObjects","Máximo de objetos",1,5,3,"");
        divider("Estouro");
        toggle("popEnabled","Estourar após muitos arremessos fortes","Ela some por um momento e volta tímida pelo canto da tela.");
        slider("popThrowLimit","Arremessos fortes por minuto",5,30,12,"");
    }

    private void brain() {
        heading("Cérebro");
        description("Atividade real da rede de 470 neurônios. Toque em um neurônio para inspecionar.");
        neural=new NeuralView(this);
        neural.onSelection(text -> {
            selectedNeuron.setText(text);
            JSONObject command=new JSONObject();
            put(command,"type","inspect-neuron");put(command,"index",neural.selectedIndex());
            engine.control(command);
        });
        content.addView(neural,new LinearLayout.LayoutParams(-1,dp(320)));
        selectedNeuron=description("Sensoriais dourados, excitatórios lilases, inibitórios verdes e motores rosados.");
        brainStatus=description("Aguardando o próximo ciclo do cérebro…");
        divider("Decisões e aprendizado");
        decisionStatus=description("");
        button("Copiar diagnóstico",this::copyDiagnostics);
    }

    private void activities() {
        heading("Atividades");
        description("Os pedidos entram no cérebro da Bolha. Humor, energia e o que ela está fazendo influenciam a resposta.");
        actionRow("Carinho","caress","Dormir / acordar","toggle-sleep");
        actionRow("Mostrar / guardar brinquedo","ball","Bicuda","kick");
        actionRow("Jogar para cima","lift","Pingue-pongue","pingpong");
        actionRow("Notebook","notebook","Vem trabalhar comigo","work");
        actionRow("Comemorar","celebrate","Trazer uma travessura","mischief");
        actionRow("Cantinho do castigo","corner","Pedir sossego","quiet");
        button("Pedir meme ou GIF",() -> action("reaction-now"));
        divider("Testar expressões");
        description("Veja as poses e os efeitos sem criar uma nova experiência de aprendizado.");
        expressionPreview=new Stage(this,engine,"preview");
        content.addView(expressionPreview,new LinearLayout.LayoutParams(-1,dp(230)));
        JSONArray names=engine.state().optJSONArray("expressionNames");
        if (names==null || names.length()==0) {
            names=new JSONArray();
            for (String name:new String[]{"held","sleeping","caress","bravo","tonto","correndo","wink","pop","pop_return"}) names.put(name);
        }
        expressionNames=new String[names.length()];
        for (int index=0;index<names.length();index++) expressionNames[index]=names.optString(index);
        expression=spinner(expressionNames);
        actionRow("Ver expressão","test-expression","Encerrar teste","end-expression");
    }

    private void privacy() {
        heading("Privacidade");
        description("Você escolhe quais sinais locais entram no cérebro da Bolha.");
        toggle("senseCursor","Usar a posição do toque","Considera o dedo dentro da Bolha e dos brinquedos para olhar e brincar.");
        toggle("senseIdle","Tempo sem interagir com a Bolha","Usa a inatividade observada pela própria Bolha enquanto ela está funcionando.");
        toggle("senseApp","Reconhecer aplicativo ativo","Lê somente o nome do aplicativo após você autorizar o acesso de uso no Android.");
        usageStatus=description(UsageContext.permitted(this)?"Acesso de uso autorizado no Android.":"Acesso de uso ainda desligado no Android.");
        button("Abrir acesso de uso do Android",() -> startActivity(new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS)));
        divider("Janelas e conteúdo");
        description("No celular, a Bolha usa os limites da tela e das suas próprias janelas flutuantes. A leitura de bordas de outros aplicativos pertence à edição de computador.");
        description("O conteúdo da tela e o texto digitado ficam fora das leituras da Bolha. Memória e aprendizado são armazenados no aparelho.");
    }

    private void application() {
        heading("App");
        description("Bolha "+BuildConfig.VERSION_NAME);
        button(FloatingBolha.active?"Parar de flutuar":"Flutuar sobre outros apps",() -> {
            if (FloatingBolha.active) stopService(new Intent(this,FloatingBolha.class));
            else {
                Intent open=new Intent(this,MainActivity.class);
                open.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);
                open.putExtra("floatingRequested",true);startActivity(open);finish();
            }
        });
        button("Permissão de sobreposição",() -> startActivity(new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,Uri.parse("package:"+getPackageName()))));
        button("Abrir versões no GitHub",() -> startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("https://github.com/kuky13/bolha/releases/latest"))));
        divider("Diagnóstico e dados");
        button("Copiar diagnóstico local",this::copyDiagnostics);
        button("Apagar aprendizado…",() -> new AlertDialog.Builder(this)
            .setTitle("Reiniciar o aprendizado?")
            .setMessage("A Bolha vai guardar uma cópia de segurança e reiniciar as associações aprendidas neste aparelho.")
            .setNegativeButton("Cancelar",null)
            .setPositiveButton("Reiniciar",(dialog,which) -> { action("reset-memory");status.setText("Reinício solicitado. O diagnóstico mostrará o resultado."); })
            .show());
        divider("Comunidade");
        description("Código, artes e animações da Bolha sob GPLv3. Projeto baseado no Pestinha, de mille-okws e colaboradores.");
        button("Código e créditos",() -> startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse("https://github.com/kuky13/bolha"))));
    }

    private Spinner spinner(String[] options) {
        Spinner spinner=new Spinner(this);
        ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_item,options);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(adapter);spinner.setMinimumHeight(dp(52));
        content.addView(spinner,new LinearLayout.LayoutParams(-1,-2));
        return spinner;
    }

    private void actionRow(String first,String firstAction,String second,String secondAction) {
        LinearLayout row=MobileUi.row(this);
        MobileUi.addEqual(row,MobileUi.button(this,first,() -> action(firstAction)));
        MobileUi.addEqual(row,MobileUi.button(this,second,() -> action(secondAction)));
        content.addView(row);
    }

    private void button(String label,Runnable action) {
        Button button=MobileUi.button(this,label,action);
        LinearLayout.LayoutParams params=new LinearLayout.LayoutParams(-1,-2);
        params.setMargins(0,dp(5),0,dp(5));
        content.addView(button,params);
    }

    private void action(String kind) {
        if (kind.equals("toggle-sleep")) kind=engine.state().optBoolean("asleep")?"wake":"sleep";
        if (kind.equals("test-expression") || kind.equals("end-expression")) {
            JSONObject command=new JSONObject();put(command,"type","expression");
            put(command,"name",kind.equals("end-expression")?"":expressionNames[expression.getSelectedItemPosition()]);
            engine.control(command);return;
        }
        engine.action(kind,"",0,0,0,0);
    }

    private void command(String type,boolean value) {
        JSONObject command=new JSONObject();put(command,"type",type);put(command,"value",value);
        engine.control(command);
    }

    private void change(String key,Object value) {
        JSONObject patch=new JSONObject();put(patch,key,value);engine.configure(patch);
        status.setText("Salvando no aparelho…");
    }

    private static void put(JSONObject object,String key,Object value) {
        try { object.put(key,value); }
        catch (JSONException impossible) { throw new IllegalArgumentException(key,impossible); }
    }

    private void loadPreferences() {
        loading=true;
        for (Map.Entry<String,Switch> entry:toggles.entrySet())
            entry.getValue().setChecked(preferences.optBoolean(entry.getKey(),entry.getKey().equals("mouthEnabled")||entry.getKey().equals("hapticsEnabled")));
        for (Map.Entry<String,SeekBar> entry:sliders.entrySet()) {
            String key=entry.getKey();
            if (tracking.contains(key)) continue;
            double value=preferences.optDouble(key,key.equals("avatarSize")?136:key.equals("mischiefInterval")?300:key.equals("maxObjects")?3:key.equals("popThrowLimit")?12:1);
            if (key.startsWith("scale:")) {
                JSONObject scales=preferences.optJSONObject("objectScales");
                value=scales==null?1:scales.optDouble(key.substring(6),1);
            }
            if (key.equals("opacity")||key.equals("shakeSensitivity")||key.startsWith("scale:")) value*=100;
            if (key.equals("mischiefInterval")) value/=60;
            int[] range=sliderRanges.get(key);
            entry.getValue().setProgress(Math.max(0,Math.min(range[1]-range[0],(int)Math.round(value)-range[0])));
        }
        if (toyAppearance!=null) toyAppearance.setSelection(preferences.optString("toyAppearance","peanut").equals("ball")?1:0);
        loading=false;
    }

    private void copyDiagnostics() {
        String text=engine.state().optString("diagnostics","Bolha "+BuildConfig.VERSION_NAME);
        ClipboardManager clipboard=getSystemService(ClipboardManager.class);
        clipboard.setPrimaryClip(ClipData.newPlainText("Diagnóstico da Bolha",text));
        status.setText("Diagnóstico copiado. Você escolhe onde compartilhar.");
    }

    private static void updateText(TextView view,String text) {
        if (view!=null && !text.contentEquals(view.getText())) view.setText(text);
    }

    @Override public void frame(JSONObject state,String error) {
        if (error!=null) { updateText(status,error);return; }
        JSONObject next=state.optJSONObject("preferences");
        if (next!=null && !next.toString().equals(lastPreferences)) {
            preferences=next;lastPreferences=next.toString();loadPreferences();
            updateText(status,"Configurações salvas neste aparelho.");
        }
        if (usageStatus!=null) updateText(usageStatus,state.optBoolean("usageAccess")?
                "Acesso de uso autorizado no Android.":"Acesso de uso ainda desligado no Android.");
        if (motionStatus!=null) {
            boolean available=state.optBoolean("motionAvailable");
            Switch toggle=toggles.get("shakeEnabled");
            if (toggle.isEnabled()!=available) toggle.setEnabled(available);
            updateText(motionStatus,available?"Sensor de movimento disponível.":"Este aparelho não oferece um sensor de movimento compatível.");
        }
        if (expressionPreview!=null) expressionPreview.frame(state);
        if (neural!=null) {
            neural.frame(state);
            long now=SystemClock.elapsedRealtime();
            if (now-lastBrainText<1500) return;
            lastBrainText=now;
            if (neural.selectedIndex()>=0) updateText(selectedNeuron,neural.selectionDescription());
            JSONObject intelligence=state.optJSONObject("intelligence");
            String goal=intelligence==null?"Observando":intelligence.optString("label","Observando");
            updateText(brainStatus,String.format(Locale.forLanguageTag("pt-BR"),
                "%s\nHumor %s\nEnergia %.0f%% · carência %.0f%% · estímulo %.0f%%",
                goal,state.optString("emotion"),state.optDouble("energy")*100,
                state.optDouble("lonely")*100,state.optDouble("stimulation")*100));
            updateText(decisionStatus,decisionText(state));
        }
    }

    private String decisionText(JSONObject state) {
        StringBuilder text=new StringBuilder();
        JSONArray decisions=state.optJSONArray("decisionLog");
        if (decisions!=null) for (int index=Math.max(0,decisions.length()-6);index<decisions.length();index++) {
            JSONObject decision=decisions.optJSONObject(index);
            if (decision==null) continue;
            text.append(decision.optString("action")).append(" → ").append(decision.optString("target",""));
            if (decision.has("source")) text.append("\n").append(decision.optString("source"));
            text.append("\n\n");
        }
        JSONArray learned=state.optJSONArray("learned");
        if (learned!=null && learned.length()>0) text.append("Associações aprendidas\n").append(learned.toString());
        return text.length()==0?"Aguardando a próxima decisão do cérebro.":text.toString().trim();
    }
}
