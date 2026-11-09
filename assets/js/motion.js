/* ==========================================================================
   MOTION LAYER, script part. Add AFTER your own <script>, just before </body>:
   <script src="motion.js"></script>
   It does not change your code. It only adds classes, small animations and listeners.
   ========================================================================== */
(()=>{
const root=document.documentElement; root.classList.add('motion');
const reduce=matchMedia('(prefers-reduced-motion:reduce)').matches;
const EASE='cubic-bezier(0.22,1,0.36,1)';
/* REPLAY = true  : every element tumbles in each time it comes back on screen, scrolling down OR up.
   REPLAY = false : each element tumbles only the first time (the skill's default). */
const REPLAY=true;
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];

/* TUMBLE for script-driven moments (tab click, slide change). Same shape as @keyframes m-tumble in motion.css:
   start above and turned, swing past once, settle. dy = start height, r = start turn in degrees, s = start size, x = sideways start */
const tumble=(el,o={})=>{const {dy=-24,r=-8,s=.9,x=0,dur=600,delay=0}=o;
  return el.animate(reduce?[{opacity:0},{opacity:1}]:[
    {opacity:0,transform:`translate(${x}px,${dy}px) rotate(${r}deg) scale(${s})`},
    {opacity:1,offset:.55,transform:`translate(${-x*.12}px,${-dy*.12}px) rotate(${-r*.35}deg) scale(1.03)`},
    {offset:.78,transform:`translate(0,${dy*.04}px) rotate(${r*.12}deg) scale(.995)`},
    {opacity:1,transform:'none'}],{duration:dur,delay,easing:EASE,fill:'backwards'})};

/* 1. HERO title: split into letters (screen readers still read "Portfolio") */
const h1=$('.title h1');
if(h1){const t=h1.textContent.trim();h1.setAttribute('aria-label',t);
  h1.innerHTML=[...t].map((c,k)=>`<span aria-hidden="true" style="--k:${k}">${c}</span>`).join('')}

/* 2. Number the items in skills, process and experience so CSS can stagger them (60ms apart, capped at 400ms) */
$$('.steps,.tl,.chips,.tabs,.links').forEach(g=>[...g.children].filter(x=>x.tagName!='B').forEach((c,k)=>c.style.setProperty('--k',k)));

/* 3. PROJECT CARDS: tumble in when they enter the screen. With REPLAY they reset once fully off screen, so they tumble again from either direction */
const cio=new IntersectionObserver(es=>{
  es.filter(e=>e.intersectionRatio>=.1&&!e.target.classList.contains('pop')).forEach((e,k)=>{e.target.style.setProperty('--k',k);e.target.classList.add('pop')});
  if(REPLAY)es.filter(e=>!e.isIntersecting).forEach(e=>e.target.classList.remove('pop'));
},{threshold:[0,.1],rootMargin:'0px 0px -5% 0px'});
$$('.card').forEach(c=>cio.observe(c));
$('.tabs')?.addEventListener('click',e=>{ const tb=e.target.closest('button');if(!tb)return;tumble(tb,{dy:-14,r:-8,s:.88}); // the tab you press tumbles
  requestAnimationFrame(()=>$$('.card').forEach(c=>{c.classList.remove('pop');cio.unobserve(c);cio.observe(c)}))}); // runs after your own filter code

/* 3b. SECTIONS (skills, process, experience, projects...): add "in" when 10% is visible, remove it when fully off screen so the tumble can replay */
const rio=new IntersectionObserver(es=>es.forEach(e=>{
  if(e.intersectionRatio>=.1)e.target.classList.add('in');
  else if(REPLAY&&!e.isIntersecting)e.target.classList.remove('in')}),{threshold:[0,.1]});
$$('.rise').forEach(el=>rio.observe(el));

/* 3c. TAGLINE WORDS: light up going down, dim again going up (words above the screen stay lit) */
const wio2=new IntersectionObserver(es=>es.forEach(e=>{
  if(e.isIntersecting)e.target.classList.add('on');
  else if(e.boundingClientRect.top<0)e.target.classList.add('on');          // already scrolled past (even if you jumped): stay lit
  else if(REPLAY)e.target.classList.remove('on')}),{rootMargin:'0px 0px -35% 0px'});
$$('.tagline .w').forEach(w=>wio2.observe(w));

/* 3d. HERO: when it is fully off screen, reset it; scrolling back to the top plays the entrance again */
const hero=$('.hero');
if(hero&&REPLAY)new IntersectionObserver(es=>es.forEach(e=>hero.classList.toggle('hero-reset',!e.isIntersecting))).observe(hero);

/* 4. SCROLL: progress bar + gentle lag on the hero text. One requestAnimationFrame per frame, only transform and opacity change */
const bar=document.createElement('div');bar.className='progress';bar.setAttribute('aria-hidden','true');document.body.prepend(bar);
const lag=[['.title',.25],['.who',.12],['.year',.12]].map(([s,f])=>[$(s),f]).filter(([el])=>el);
let queued=false;
const frame=()=>{queued=false;
  const y=scrollY,max=root.scrollHeight-innerHeight;
  bar.style.setProperty('--p',max>0?Math.min(y/max,1):0);
  if(reduce)return;
  const yy=Math.min(y,innerHeight*1.2),fade=Math.min(yy/(innerHeight*.8),1);
  lag.forEach(([el,f])=>{el.style.transform=`translateY(${yy*f}px)`;el.style.opacity=1-fade*.9});
};
const onScroll=()=>{if(!queued){queued=true;requestAnimationFrame(frame)}};
addEventListener('scroll',onScroll,{passive:true});addEventListener('resize',onScroll);frame();

/* 5. PROJECT POP UP (Keep modal open/close tumble, disable inside slide tumble) */
const dlg=$('#dlg');
if(dlg){
  // 5a. Fade and sink out when closing modal
  const realClose=dlg.close.bind(dlg);let closing=false;
  dlg.close=rv=>{ if(!dlg.open||closing)return; closing=true; dlg.classList.add('closing');
    setTimeout(()=>{realClose(rv);dlg.classList.remove('closing');closing=false},300)};
  dlg.addEventListener('cancel',e=>{e.preventDefault();dlg.close()});

  // 5b. Keyboard navigation
  document.addEventListener('keydown',e=>{ if(!dlg.open)return;
    if(e.key=='ArrowLeft')$('.prev-btn',dlg)?.click(); if(e.key=='ArrowRight')$('.next-btn',dlg)?.click()});
}

// const dlg=$('#dlg');
// if(dlg){
//   // 5a. fade and sink out instead of vanishing (button, backdrop click and Escape all go through here)
//   const realClose=dlg.close.bind(dlg);let closing=false;
//   dlg.close=rv=>{ if(!dlg.open||closing)return; closing=true; dlg.classList.add('closing');
//     setTimeout(()=>{realClose(rv);dlg.classList.remove('closing');closing=false},300)};
//   dlg.addEventListener('cancel',e=>{e.preventDefault();dlg.close()});

//   // 5b. slide change: remember which way you went, then tumble the new picture and text in from that side
//   let dir=1;
//   dlg.addEventListener('click',e=>{
//     if(e.target.closest('.prev-btn'))dir=-1;
//     else if(e.target.closest('.next-btn'))dir=1;
//     else{const d=e.target.closest('.dot');if(d){const act=$$('.dot',dlg).findIndex(x=>x.classList.contains('active'));dir=+d.dataset.idx>act?1:-1}}
//   },true);
//   const play=(el,delay=0)=>tumble(el,{x:dir*28,dy:0,r:dir*6,s:.92,delay});
//   new MutationObserver(ms=>ms.forEach(m=>{
//     const t=m.target.nodeType==3?m.target.parentElement:m.target;
//     if(m.type=='attributes'&&t.id=='dlg-main-img'){            // new picture: stay hidden until it has loaded, then ease in
//       t.style.opacity=0;
//       const show=()=>{t.style.opacity='';play(t)};
//       t.addEventListener('load',show,{once:true});t.addEventListener('error',show,{once:true});
//     }else if(t&&t.id=='dlg-desc'&&m.type!='attributes')play(t,100); // new caption follows the picture
//   })).observe(dlg,{subtree:true,attributes:true,attributeFilter:['src'],childList:true,characterData:true});

//   // 5c. keyboard: left and right arrows change slide
//   document.addEventListener('keydown',e=>{ if(!dlg.open)return;
//     if(e.key=='ArrowLeft')$('.prev-btn',dlg)?.click(); if(e.key=='ArrowRight')$('.next-btn',dlg)?.click()});
// }
})();