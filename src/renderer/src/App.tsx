// SPDX-License-Identifier: GPL-3.0-only
import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { X, Settings, Music2, Sparkles, Brain, Pause, Play, SkipBack, SkipForward, Heart, Circle, Laptop, Moon, Flag, Hand, EyeOff, Download, Copy, RotateCcw, Power } from 'lucide-react';
import { DrippyAsciiAvatar } from './components/avatar/DrippyAsciiAvatar';
import { areaAt } from '../../shared/roaming';
import { formatAccelerator } from '../../shared/shortcuts';
import type { Bootstrap, BrainEvent, BrainSnapshot, LogEntry, MediaState, Preferences, SceneObject, UpdateState } from '../../shared/types';

const api = window.bolha;
const MEMES = import.meta.glob('../../../assets/drippy/content/memes/**/*.svg', { query: '?url', import: 'default', eager: true }) as Record<string,string>;
const memeURL = (name?: string) => Object.entries(MEMES).find(([key]) => key.endsWith('/'+name+'.svg'))?.[1];
const emotionName: Record<string,string> = { observando:'De olho no mundo', contente:'De boa', feliz:'Feliz', curioso:'Curiosa', bravo:'Bravinha', triste:'Meio nublada', assustado:'Assustada', dramatico:'Dramática', dormindo:'Tirando um cochilo' };
const avatarState = (state: BrainSnapshot) => state.caressing ? 'happy' : state.phase === 'shy' ? 'shy' : ({ feliz:'happy', contente:'idle', observando:'idle', curioso:'curious', bravo:'angry', triste:'sad', assustado:'scared', dramatico:'dramatic', dormindo:'asleep' } as const)[state.emotion as 'feliz'] ?? 'idle';

function NeuralCanvas({ state }: { state: BrainSnapshot }) {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const canvas=ref.current, neural=state.neural;
    if (!canvas || !neural) return;
    const ctx=canvas.getContext('2d'); if (!ctx) return;
    ctx.clearRect(0,0,canvas.width,canvas.height);
    for (let i=0;i<neural.positions.length;i++) {
      const point=neural.positions[i];
      const activity=Math.max(.1,neural.trace[i] ?? 0);
      ctx.fillStyle=`rgba(254,200,51,${activity})`;
      ctx.beginPath();ctx.arc(18+point[0]*(canvas.width-36),18+point[1]*(canvas.height-36),activity>.5?2.5:1.4,0,Math.PI*2);ctx.fill();
    }
  },[state.neural]);
  return <canvas width={420} height={240} ref={ref} aria-label="Atividade real dos 470 neurônios da Drippy" role="img" />;
}

function Toggle({ label, detail, value, onChange }: {label:string;detail?:string;value:boolean;onChange:(next:boolean)=>void}) {
  return <label className="setting-row"><span><strong>{label}</strong>{detail && <small>{detail}</small>}</span><input type="checkbox" role="switch" checked={value} onChange={e=>onChange(e.target.checked)} /></label>;
}

export function App() {
  const [boot,setBoot]=useState<Bootstrap|null>(null);
  const [state,setState]=useState<BrainSnapshot|null>(null);
  const [prefs,setPrefs]=useState<Preferences|null>(null);
  const [panel,setPanel]=useState<'settings'|'brain'|null>(null);
  const [tab,setTab]=useState<'look'|'music'|'behavior'|'privacy'|'system'>('look');
  const [update,setUpdate]=useState<UpdateState>({phase:'idle'});
  const [media,setMedia]=useState<MediaState|null>(null);
  const [startup,setStartup]=useState(false);
  const [logs,setLogs]=useState<LogEntry[]>([]);
  const [notice,setNotice]=useState('');
  const [error,setError]=useState('');
  const [clock,setClock]=useState(Date.now());
  const [shortcutKey,setShortcutKey]=useState<keyof Preferences['shortcuts']|null>(null);
  const drag=useRef<{id?:string;x:number;y:number;time:number;vx:number;vy:number;startX:number;startY:number;moved:boolean}|null>(null);
  const lastRub=useRef({x:0,dir:0,changes:0,time:0});
  const interactive=useRef(false);
  const panelAnchor=useRef<{x:number;y:number}|null>(null);
  const desktopRef=useRef<Bootstrap['desktop']|null>(null);
  const event=(value:BrainEvent)=>api.brainEvent(value);
  const fail=(cause:unknown)=>setError(String(cause).replace(/^Error: /,''));
  const save=(patch:Partial<Preferences>)=>{void api.savePreferences(patch).then(setPrefs).catch(fail);};

  useEffect(()=>{
    let active=true;
    const stop=[api.onBrain(value=>{if(active)setState(value);}),api.onUpdate(setUpdate),api.onPreferences(setPrefs),api.onDesktop(desktop=>{
      desktopRef.current=desktop;setBoot(b=>b?{...b,desktop}:b);
    }),api.onOpenSettings(()=>setPanel('settings'))];
    void api.bootstrap().then(value=>{if(!active)return;setBoot(value);desktopRef.current=value.desktop;setPrefs(value.preferences);setState(value.brain);setStartup(value.startup);setUpdate(value.update);void api.ready();}).catch(fail);
    return ()=>{active=false;stop.forEach(fn=>fn());};
  },[]);
  useEffect(()=>{panelAnchor.current=panel&&state?{x:state.x,y:state.y}:null;event({type:'panel',value:panel==='settings'});event({type:'monitor',value:panel==='brain'});return()=>{event({type:'panel',value:false});event({type:'monitor',value:false});};},[panel]);
  useEffect(()=>{if(state?.panicked||(state?.blocked?.length&&state.blocked.length===boot?.desktop.areas.length))setPanel(null);},[state?.panicked]);
  useEffect(()=>{
    const timer=setInterval(()=>setClock(Date.now()),1000);return()=>clearInterval(timer);
  },[]);
  useEffect(()=>{
    if (!prefs?.mediaEnabled) { setMedia(null);event({type:'music',value:false});return; }
    let active=true, busy=false;
    const read=async()=>{if(busy)return;busy=true;try{const value=await api.media('state');if(active){setMedia(value);event({type:'music',value:!!value?.isPlaying});}}catch(fail){if(active)setNotice(String(fail));}finally{busy=false;}};
    void read();const timer=setInterval(()=>void read(),2000);
    return()=>{active=false;clearInterval(timer);};
  },[prefs?.mediaEnabled]);
  useEffect(()=>{
    if(!shortcutKey)return;
    const listener=(e:KeyboardEvent)=>{e.preventDefault();if(e.key==='Escape'){setShortcutKey(null);return;}const key=formatAccelerator(e);if(key&&prefs){save({shortcuts:{...prefs.shortcuts,[shortcutKey]:key}});setShortcutKey(null);}};
    window.addEventListener('keydown',listener);return()=>window.removeEventListener('keydown',listener);
  },[shortcutKey,prefs]);
  useEffect(()=>{
    const hit=(x:number,y:number)=>!!document.elementFromPoint(x,y)?.closest('[data-solid]');
    const check=(e:MouseEvent)=>{
      if(drag.current)return;
      const solid=hit(e.clientX,e.clientY);
      if(interactive.current!==solid){interactive.current=solid;api.setClickThrough(!solid);event({type:'hover',value:solid});}
    };
    const release=()=>{const g=drag.current;if(g)api.brainEvent({type:'drag-end',id:g.id,x:g.x,y:g.y,vx:0,vy:0});drag.current=null;interactive.current=false;api.setClickThrough(true);event({type:'hover',value:false});};
    window.addEventListener('mousemove',check,true);window.addEventListener('blur',release);
    return()=>{window.removeEventListener('mousemove',check,true);window.removeEventListener('blur',release);};
  },[]);

  if (!boot || !prefs) return <div className="startup-status" role="status">{error||'Acordando a Drippy…'}</div>;
  const bounds=boot.desktop.bounds;
  const point=state ?? {x:bounds.x+bounds.width*.7,y:bounds.y+bounds.height*.6};
  const bodyArea=areaAt(point,boot.desktop.areas);
  const freeAreas=boot.desktop.areas.filter((_,index)=>!state?.blocked?.includes(index));
  const area=areaAt(panelAnchor.current??point,freeAreas.length?freeAreas:boot.desktop.areas);
  const panelWidth=Math.min(450,area.width-24),panelHeight=Math.min(630,area.height-32);
  const panelX=Math.max(area.x+12,Math.min(area.x+area.width-panelWidth-12,point.x+prefs.avatarSize/2+26))-bounds.x;
  const panelY=Math.max(area.y+16,Math.min(area.y+area.height-panelHeight-16,point.y-panelHeight/2))-bounds.y;
  const updating=update.phase==='ready'||update.phase==='downloading'||update.phase==='installing';
  const seconds=Math.max(0,Math.ceil(((update.installAt??clock)-clock)/1000));

  function pointerDown(e:ReactPointerEvent<HTMLElement>,id?:string) {
    if(e.button!==0)return;
    const d=desktopRef.current!;
    e.currentTarget.setPointerCapture(e.pointerId);
    api.setClickThrough(false);interactive.current=true;
    drag.current={id,x:e.clientX+d.bounds.x,y:e.clientY+d.bounds.y,time:performance.now(),vx:0,vy:0,startX:e.clientX,startY:e.clientY,moved:false};
    event({type:'drag-start',id,x:e.clientX+d.bounds.x,y:e.clientY+d.bounds.y});
  }
  function pointerMove(e:ReactPointerEvent<HTMLElement>) {
    const d=desktopRef.current!,now=performance.now(),g=drag.current;
    if(g){const x=e.clientX+d.bounds.x,y=e.clientY+d.bounds.y,dt=Math.max(.016,(now-g.time)/1000);g.vx=(x-g.x)/dt;g.vy=(y-g.y)/dt;g.x=x;g.y=y;g.time=now;g.moved ||= Math.hypot(e.clientX-g.startX,e.clientY-g.startY)>5;event({type:'drag',id:g.id,x,y});return;}
    const rub=lastRub.current,dx=e.clientX-rub.x;
    if(Math.abs(dx)>3){const dir=Math.sign(dx);if(now-rub.time>1400)rub.changes=0;if(dir!==rub.dir&&rub.dir!==0)rub.changes++;rub.dir=dir;rub.x=e.clientX;rub.time=now;if(rub.changes>=3){event({type:'caress'});rub.changes=0;}}
  }
  function pointerUp(e:ReactPointerEvent<HTMLElement>) {
    const g=drag.current;if(!g)return;
    if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);
    drag.current=null;
    const still=performance.now()-g.time>100;
    event({type:'drag-end',id:g.id,x:g.x,y:g.y,vx:still?0:g.vx,vy:still?0:g.vy});
    if(!g.moved&&!g.id)event({type:'poke'});
  }
  const action=(type:BrainEvent['type'])=>()=>event({type});
  function renderObject(obj:SceneObject) {
    const movable=['ball','notebook','corner'].includes(obj.kind);
    return <div key={obj.id} data-solid={movable||['note','meme','sign'].includes(obj.kind)?'':undefined} data-scene-kind={obj.kind}
      className={'scene-object scene-'+obj.kind} style={{left:obj.x-bounds.x-obj.width/2,top:obj.y-bounds.y-obj.height/2,width:obj.width,height:obj.height,transform:`rotate(${obj.angle}deg)`}}
      onPointerDown={movable?e=>pointerDown(e,obj.id):undefined} onPointerMove={movable?pointerMove:undefined} onPointerUp={movable?pointerUp:undefined}
      onClick={['note','meme','sign'].includes(obj.kind)?()=>event({type:'dismiss',id:obj.id}):undefined}>
      {obj.kind==='ball'&&<span className="tennis-line"/>}
      {obj.kind==='paper'&&'✧'}
      {obj.kind==='notebook'&&<><div className="laptop-screen"><span>{obj.working?'▰ ▰ ▰':'♡'}</span><small>{obj.working?'drippy trabalhando…':'meu cantinho'}</small></div><div className="laptop-base"/></>}
      {obj.kind==='corner'&&<><span>CANTINHO<br/>DO CASTIGO</span><i/><i/></>}
      {(obj.kind==='note'||obj.kind==='sign')&&<span>{obj.text}</span>}
      {obj.kind==='meme'&&(memeURL(obj.image)?<img alt="Meme da Drippy" src={memeURL(obj.image)}/>:<span>Eu tinha um meme aqui…</span>)}
      {obj.kind==='fireworks'&&Array.from({length:16},(_,i)=><i key={i} style={{'--angle':`${i*22.5}deg`,'--delay':`${(i%3)*.1}s`} as React.CSSProperties}/>)}
    </div>;
  }

  return <div className="desktop" data-app-ready="true">
    {state?.objects.map(renderObject)}
    {state?.ready&&state.visible&&<div className="companion" data-flip-controls={state.y+prefs.avatarSize/2+130>bodyArea.y+bodyArea.height} data-solid data-testid="drippy" style={{left:state.x-bounds.x-prefs.avatarSize/2,top:state.y-bounds.y-prefs.avatarSize/2,width:prefs.avatarSize,height:prefs.avatarSize}}
      onPointerDown={e=>pointerDown(e)} onPointerMove={pointerMove} onPointerUp={pointerUp} onPointerCancel={pointerUp}
      onContextMenu={e=>{e.preventDefault();setPanel(p=>p?null:'settings');}} onWheel={e=>{event({type:'spin',value:Math.sign(e.deltaY)*100});}}
      onDoubleClick={()=>setPanel(p=>p?null:'brain')}>
      <div className="avatar-physical" style={{transform:`rotate(${state.angle}deg) scale(${1-state.shyness*.12})`}}><DrippyAsciiAvatar state={avatarState(state)} size={prefs.avatarSize} draggable={false} musicPlaying={!!media?.isPlaying} bubbleOpacity={prefs.opacity} held={state.held} gaze={state.gaze} eyesClosed={state.phase==='shy'&&state.shyness>.5}/></div>
      {state.speech&&<div className="speech" role="status">{state.speech}</div>}
      <div className="companion-actions"><button onPointerDown={e=>e.stopPropagation()} onClick={()=>setPanel('settings')} aria-label="Configurações"><Settings size={15}/></button><button onPointerDown={e=>e.stopPropagation()} onClick={()=>setPanel('brain')} aria-label="Ver cérebro"><Brain size={15}/></button></div>
      {prefs.mediaEnabled&&prefs.showMedia&&<div data-solid className="media-bar" onPointerDown={e=>e.stopPropagation()}>
        <span title={media?.title}>{media?.title||'Nada tocando'}</span><div><button aria-label="Faixa anterior" onClick={()=>void api.media('previous').then(setMedia)}><SkipBack size={16}/></button><button aria-label={media?.isPlaying?'Pausar música':'Tocar música'} onClick={()=>void api.media('playpause').then(setMedia)}>{media?.isPlaying?<Pause size={16}/>:<Play size={16}/>}</button><button aria-label="Próxima faixa" onClick={()=>void api.media('next').then(setMedia)}><SkipForward size={16}/></button></div>
      </div>}
    </div>}
    {state?.phase==='burst'&&<div className="burst" style={{left:point.x-bounds.x,top:point.y-bounds.y}}>{Array.from({length:12},(_,i)=><i key={i} style={{'--angle':`${i*30}deg`} as React.CSSProperties}/>)}</div>}
    {panel&&<section data-solid className="panel" aria-label={panel==='brain'?'Cérebro da Drippy':'Configurações da Bolha'} style={{left:panelX,top:panelY,width:panelWidth,maxHeight:panelHeight}}>
      <header className="panel-header"><div className="app-mark">○</div><div><h1>{panel==='brain'?'Por dentro da Drippy':'Bolha'}</h1><small>{panel==='brain'?'Um cérebro local. Um jeito só dela.':'Sua pequena companhia de tela'}</small></div><button className="icon-button" onClick={()=>setPanel(null)} aria-label="Fechar painel"><X size={18}/></button></header>
      {panel==='brain'&&state?<div className="panel-content neural-panel"><p className="eyebrow">AGORA ELA ESTÁ</p><h2>{state.phase==='shy'?'Um pouquinho tímida':emotionName[state.emotion]??state.emotion}</h2><p className="muted">{state.neurons} neurônios • memória neste computador</p><NeuralCanvas state={state}/><div className="meters">{[['Energia',state.energy],['Estímulo',state.stimulation],['Carência',state.lonely]] .map(([label,value])=><label key={label}>{label}<meter min="0" max="1" value={Number(value)}/></label>)}</div><h3>O que a rede quer fazer</h3><div className="motor-list">{Object.entries(state.motors).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([name,value])=><div key={name}><span>{name}</span><b>{value.toFixed(1)} Hz</b></div>)}</div><h3>Associações aprendidas</h3>{state.learned.length?state.learned.map(([from,to,value])=><p key={from+to} className="learned">{from} → {to}<span>{value.toFixed(4)}</span></p>):<p className="muted">Ainda está descobrindo o mundo. Faça carinho enquanto ela brinca.</p>}<p className="muted">Protesto: {state.protest} • Fugas aprendidas: {state.escapes}</p></div>:<>
        <nav className="tabs" aria-label="Configurações">{([['look','Bolha',Sparkles],['music','Música',Music2],['behavior','Vida',Heart],['privacy','Contexto',Hand],['system','App',Settings]] as const).map(([id,label,Icon])=><button key={id} aria-selected={tab===id} onClick={()=>setTab(id)}><Icon size={16}/>{label}</button>)}</nav>
        <div className="panel-content">
          {tab==='look'&&<><p className="eyebrow">DO SEU JEITO</p><h2>Uma bolha com personalidade.</h2><p className="muted">Arraste para levar junto. Faça carinho com o mouse. Clique direito para voltar aqui.</p><label className="range-label">Tamanho <strong>{prefs.avatarSize}px</strong><input type="range" min="80" max="200" value={prefs.avatarSize} onChange={e=>save({avatarSize:Number(e.target.value)})}/></label><label className="range-label">Opacidade da esfera <strong>{Math.round(prefs.opacity*100)}%</strong><input type="range" min="20" max="100" value={prefs.opacity*100} onChange={e=>save({opacity:Number(e.target.value)/100})}/></label><Toggle label="Passear pelos monitores" detail="Pula, quica e visita as telas disponíveis." value={prefs.roaming} onChange={roaming=>save({roaming})}/><div className="action-grid"><button onClick={action('caress')}><Heart size={17}/>Carinho</button><button onClick={action('ball')}><Circle size={17}/>Bolinha</button><button onClick={action('work')}><Laptop size={17}/>Trabalhar junto</button><button onClick={action('sleep')}><Moon size={17}/>Cochilar</button><button onClick={action('corner')}><Flag size={17}/>Cantinho</button><button onClick={action('notebook')}><Laptop size={17}/>Notebook</button></div></>}
          {tab==='music'&&<><p className="eyebrow">NO SEU RITMO</p><h2>Uma companhia para a música.</h2><Toggle label="Controle de música" detail="Usa o player do Windows. Sem vincular contas." value={prefs.mediaEnabled} onChange={mediaEnabled=>save({mediaEnabled})}/><Toggle label="Botões junto da bolha" value={prefs.showMedia} onChange={showMedia=>save({showMedia})}/><h3>Atalhos</h3>{([['playPause','Tocar / pausar'],['previous','Faixa anterior'],['next','Próxima faixa']] as const).map(([key,label])=><div className="setting-row" key={key}><strong>{label}</strong><button className="shortcut" onClick={()=>setShortcutKey(key)}>{shortcutKey===key?'Pressione as teclas…':prefs.shortcuts[key]}</button></div>)}<p className="muted">Atalhos indisponíveis em outro aplicativo continuam sem efeito aqui. Esc cancela a gravação.</p></>}
          {tab==='behavior'&&<><p className="eyebrow">UM POUCO DE BAGUNÇA</p><h2>Brincar também é aprender.</h2><Toggle label="Memes e recadinhos" detail="Só conteúdo local da própria Drippy." value={prefs.mischiefEnabled} onChange={mischiefEnabled=>save({mischiefEnabled})}/><label className="range-label">Intervalo mínimo <strong>{prefs.mischiefInterval/60} min</strong><input type="range" min="60" max="1800" step="60" value={prefs.mischiefInterval} onChange={e=>save({mischiefInterval:Number(e.target.value)})}/></label><label className="range-label">Objetos de travessura <strong>{prefs.maxObjects}</strong><input type="range" min="1" max="5" value={prefs.maxObjects} onChange={e=>save({maxObjects:Number(e.target.value)})}/></label><label className="range-label">Arremessos fortes antes de estourar <strong>{prefs.burstLimit}/min</strong><input type="range" min="6" max="30" value={prefs.burstLimit} onChange={e=>save({burstLimit:Number(e.target.value)})}/></label><p className="muted">Depois de muitos arremessos ela some por 30 segundos e volta tímida. Carinho ajuda a recuperar a confiança.</p><button className="wide-button" onClick={()=>setPanel('brain')}><Brain size={17}/>Acompanhar o cérebro</button></>}
          {tab==='privacy'&&<><p className="eyebrow">TUDO NESTE COMPUTADOR</p><h2>Escolha o que ela percebe.</h2><Toggle label="Programa em primeiro plano" detail="Somente o nome do processo, para reconhecer atividades." value={prefs.senseApp} onChange={senseApp=>save({senseApp})}/><Toggle label="Tempo sem usar o computador" value={prefs.senseIdle} onChange={senseIdle=>save({senseIdle})}/><Toggle label="Posição do cursor" detail="Para olhar, brincar e reagir à sua aproximação." value={prefs.senseCursor} onChange={senseCursor=>save({senseCursor})}/><Toggle label="Geometria e tela cheia" detail="Para pousar nas janelas e evitar monitores ocupados." value={prefs.senseWindows} onChange={senseWindows=>save({senseWindows})}/><p className="muted">Não lê títulos, textos, páginas ou conversas. A rede aprende e guarda sua memória localmente.</p><p className="muted">Ctrl + Alt + Shift + B pausa tudo. Use o mesmo atalho para voltar.</p></>}
          {tab==='system'&&<><p className="eyebrow">BOLHA {boot.version}</p><h2>Pequena por fora. Viva por dentro.</h2><Toggle label="Abrir com o Windows" value={startup} onChange={value=>{void api.setStartup(value).then(setStartup).catch(fail);}}/><button className="wide-button" onClick={()=>void api.checkUpdates()}><Download size={17}/>Verificar atualização</button>{update.message&&<p className="muted">{update.message}</p>}<button className="wide-button" onClick={()=>{void api.logs().then(setLogs);void api.copyDiagnostics().then(()=>setNotice('Relatório copiado.')).catch(fail);}}><Copy size={17}/>Copiar diagnóstico local</button>{logs.length>0&&<pre className="log-view">{logs.slice(-12).map(e=>`${e.time.slice(11,19)} ${e.message}`).join('\n')}</pre>}<button className="wide-button" onClick={()=>void api.resetPreferences().then(setPrefs)}><RotateCcw size={17}/>Restaurar configurações visuais</button><button className="wide-button" onClick={()=>void api.hide()}><EyeOff size={17}/>Esconder pela bandeja</button><button className="wide-button" onClick={()=>void api.quit()}><Power size={17}/>Sair da Bolha</button><p className="license-note">Código GPLv3 • Artes da Drippy CC BY-NC 4.0<br/>Cérebro baseado no Pestinha, com créditos no repositório.</p></>}
        </div></>}
      <footer className="panel-footer"><span className="local-dot"/>Cérebro local • {state?.ready?'Drippy acordada':'Acordando…'}</footer>
    </section>}
    {updating&&<aside data-solid className="update-toast" style={{left:area.x-bounds.x+20,top:area.y-bounds.y+20}} role="status"><Download size={18}/><div><strong>{update.phase==='downloading'?`Baixando atualização · ${Math.round(update.percent??0)}%`:update.phase==='ready'?`Nova versão ${update.version}`:'Instalando atualização'}</strong>{update.phase==='ready'&&<p>{seconds>60?`Adiada por ${Math.ceil(seconds/60)} minutos`:`A Drippy volta em ${seconds}s com a nova versão.`}</p>}{update.phase==='ready'&&<button onClick={()=>void api.deferUpdate()}>Adiar por 1 hora</button>}</div></aside>}
    {(error||notice||state?.error)&&<div data-solid className="notice" role="status" style={{left:area.x-bounds.x+20,bottom:bounds.height-(area.y-bounds.y+area.height)+20}} onClick={()=>{setError('');setNotice('');}}>{error||state?.error||notice}</div>}
    {!state?.ready&&!panel&&<button data-solid className="startup-status" onClick={()=>setPanel('settings')}>{state?.error||'Acordando o cérebro da Drippy…'}</button>}
  </div>;
}
