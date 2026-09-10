'use client';
import {useEffect,useRef,useState} from 'react';
import Matter from 'matter-js';
import {animate,useReducedMotion} from 'framer-motion';
import {ArrowUp,Move,Orbit,RotateCcw} from 'lucide-react';

type Piece={body:Matter.Body;node:HTMLElement;original:HTMLElement;x:number;y:number;visibility:string};
export default function AntiGravity({onExit}: {onExit:()=>void}) {
  const surface=useRef<HTMLDivElement>(null),engineRef=useRef<Matter.Engine|null>(null),returnRef=useRef<()=>void>(()=>{});
  const onExitRef=useRef(onExit);onExitRef.current=onExit;
  const [returning,setReturning]=useState(false),[inverted,setInverted]=useState(false);
  const reduced=useReducedMotion();
  useEffect(()=>{
    const host=surface.current;if(!host)return;
    const engine=Matter.Engine.create({gravity:{x:0,y:0}});engineRef.current=engine;
    const width=window.innerWidth,height=window.innerHeight;
    const pieces:Piece[]=[];
    const before=document.body.style.overflow;document.body.style.overflow='hidden';
    const app=document.getElementById('app-surface');if(app)app.inert=true;
    const sources=document.querySelectorAll<HTMLElement>('[data-physics]');
    sources.forEach(original=>{
      const r=original.getBoundingClientRect();
      if(r.bottom<=80 || r.top>=height || r.right<=0 || r.left>=width || r.width<20)return;
      const node=original.cloneNode(true) as HTMLElement;
      node.removeAttribute('id');node.removeAttribute('data-physics');node.setAttribute('aria-hidden','true');node.inert=true;
      node.querySelectorAll('[id]').forEach(el=>el.removeAttribute('id'));
      Object.assign(node.style,{position:'absolute',left:'0px',top:'0px',margin:'0',width:`${r.width}px`,height:`${r.height}px`,transformOrigin:'center',pointerEvents:'none',zIndex:'1',transition:'none',visibility:'visible',overflow:'hidden',borderRadius:'8px'});
      node.classList.add('physics-piece');host.appendChild(node);
      const body=Matter.Bodies.rectangle(r.x+r.width/2,r.y+r.height/2,r.width,r.height,{restitution:.85,friction:.02,frictionAir:.004,density:.001});
      Matter.Body.setVelocity(body,{x:(Math.random()-.5)*2,y:(Math.random()-.5)*2});
      pieces.push({body,node,original,x:r.x,y:r.y,visibility:original.style.visibility});original.style.visibility='hidden';
    });
    const wall={isStatic:true,restitution:.9};
    Matter.Composite.add(engine.world,[...pieces.map(p=>p.body),Matter.Bodies.rectangle(width/2,-50,width+200,100,wall),Matter.Bodies.rectangle(width/2,height+50,width+200,100,wall),Matter.Bodies.rectangle(-50,height/2,100,height+200,wall),Matter.Bodies.rectangle(width+50,height/2,100,height+200,wall)]);
    const mouse=Matter.Mouse.create(host) as Matter.Mouse & {mousewheel:EventListener;mousemove:EventListener;mousedown:EventListener;mouseup:EventListener};
    // Retain touch drag, but do not let Matter's wheel handler swallow zoom gestures.
    host.removeEventListener('wheel',mouse.mousewheel as EventListener);
    const constraint=Matter.MouseConstraint.create(engine,{mouse,constraint:{stiffness:.13,damping:.06,render:{visible:false}}});
    Matter.Composite.add(engine.world,constraint);
    let frame=0,last=performance.now(),alive=true,exiting=false;
    const paint=(time:number)=>{
      if(!alive)return;
      const dt=Math.min(time-last,1000/30);last=time;
      if(!exiting){
        Matter.Engine.update(engine,dt);
        pieces.forEach(p=>{
          const w=parseFloat(p.node.style.width),h=parseFloat(p.node.style.height);
          p.node.style.transform=`translate(${p.body.position.x-w/2}px, ${p.body.position.y-h/2}px) rotate(${p.body.angle}rad)`;
        });
      }
      frame=requestAnimationFrame(paint);
    };frame=requestAnimationFrame(paint);
    returnRef.current=()=>{
      if(exiting)return;exiting=true;setReturning(true);
      Matter.Composite.remove(engine.world,constraint);
      const springs=pieces.map(p=>animate(p.node,{transform:`translate(${p.x}px, ${p.y}px) rotate(0rad)`},{type:'spring',stiffness:100,damping:20,duration:reduced ? .01:1.1}));
      void Promise.all(springs.map(s=>Promise.resolve(s))).then(()=>{if(alive)onExitRef.current();});
    };
    const key=(e:KeyboardEvent)=>{if(e.key==='Tab'){const buttons=Array.from(host.parentElement?.querySelectorAll<HTMLButtonElement>('.gravity-toolbar button:not(:disabled)') || []);if(buttons.length){e.preventDefault();const i=buttons.indexOf(document.activeElement as HTMLButtonElement);buttons[(i+(e.shiftKey?-1:1)+buttons.length)%buttons.length].focus();}}if(e.key==='Escape' || ((e.ctrlKey||e.metaKey)&&e.shiftKey&&e.key.toLowerCase()==='g')){e.preventDefault();e.stopImmediatePropagation();returnRef.current();}};
    const resize=()=>returnRef.current();
    window.addEventListener('keydown',key,true);window.addEventListener('resize',resize);
    const button=host.parentElement?.querySelector<HTMLButtonElement>('[data-return]');button?.focus();
    return()=>{alive=false;cancelAnimationFrame(frame);window.removeEventListener('keydown',key,true);window.removeEventListener('resize',resize);document.body.style.overflow=before;if(app)app.inert=false;
      Matter.Mouse.clearSourceEvents(mouse);
      host.removeEventListener('mousemove',mouse.mousemove as EventListener);host.removeEventListener('mousedown',mouse.mousedown as EventListener);host.removeEventListener('mouseup',mouse.mouseup as EventListener);host.removeEventListener('touchmove',mouse.mousemove as EventListener);host.removeEventListener('touchstart',mouse.mousedown as EventListener);host.removeEventListener('touchend',mouse.mouseup as EventListener);
      Matter.World.clear(engine.world,false);Matter.Engine.clear(engine);engineRef.current=null;
      pieces.forEach(p=>{p.original.style.visibility=p.visibility;p.node.remove();});
      document.querySelector<HTMLButtonElement>('.gravity-button')?.focus();
    };
  },[reduced]);
  return <div className="antigravity" role="dialog" aria-modal="true" aria-label="Anti-gravity movie sandbox"><div className="physics-surface" ref={surface}/><div className="gravity-toolbar"><div className="gravity-label"><Orbit size={20}/><strong>ANTI-GRAVITY</strong><span>Drag. Fling. Discover.</span></div><button className={inverted?'enabled':''} disabled={returning} onClick={()=>{const next=!inverted;setInverted(next);if(engineRef.current)engineRef.current.gravity.y=next ? -.45:0;}}><ArrowUp size={17}/>{inverted?'Gravity inverted':'Zero gravity'}</button><button data-return disabled={returning} onClick={()=>returnRef.current()}><RotateCcw size={17}/>{returning?'Returning…':'Back to browsing'}</button></div><div className="gravity-hint"><Move size={15}/>Grab any card or panel to move it<span>ESC TO RETURN</span></div></div>;
}
