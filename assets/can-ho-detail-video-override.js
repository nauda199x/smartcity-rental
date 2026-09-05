/* Mobile video UX override: dùng native HTML5 video thay cho Drive iframe. */
(function(){
  'use strict';
  if (!window.matchMedia || !window.matchMedia('(max-width:640px)').matches) return;

  function q(s,r){ return (r||document).querySelector(s); }
  function driveId(url){ var m=String(url||'').match(/\/file\/d\/([A-Za-z0-9_-]+)/i); return m?m[1]:''; }
  function directUrl(url){ var id=driveId(url); return id ? 'https://drive.google.com/uc?export=download&id='+encodeURIComponent(id) : ''; }

  var st=document.createElement('style');
  st.id='ctNativeVideoOverrideStyle';
  st.textContent=[
    '.ct-video-modal{background:#000!important}',
    '.ct-video-modal-head{height:50px!important;min-height:50px!important;padding:0 10px 0 14px!important;background:rgba(4,8,15,.97)!important;border-bottom:1px solid rgba(255,255,255,.08)!important}',
    '.ct-video-modal-head strong{font-size:.82rem!important;font-weight:700!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}',
    '.ct-video-modal-close{width:36px!important;height:36px!important;border-radius:11px!important;font-size:23px!important}',
    '.ct-video-modal-body{display:grid!important;place-items:center!important;background:#000!important;overflow:hidden!important}',
    '.ct-native-video{display:block;width:100%;height:100%;max-width:100vw;max-height:calc(100dvh - 50px - env(safe-area-inset-top) - env(safe-area-inset-bottom));object-fit:contain;background:#000}',
    '.ct-native-loading{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);z-index:3;padding:7px 11px;border-radius:999px;background:rgba(15,23,42,.75);color:#fff;font-size:.7rem;pointer-events:none}',
    'body.ct-video-modal-open .ct-mobile-actions,body.ct-video-modal-open .tabbar,body.ct-video-modal-open .zalo-noi{visibility:hidden!important;pointer-events:none!important}',
    '@media (orientation:landscape) and (max-width:900px){.ct-video-modal-head{height:44px!important;min-height:44px!important}.ct-native-video{max-height:calc(100dvh - 44px - env(safe-area-inset-top) - env(safe-area-inset-bottom))}}'
  ].join('\n');
  document.head.appendChild(st);

  function posterHienTai(){
    var img=q('.ct-video-launch img');
    return img ? (img.currentSrc||img.src||'') : '';
  }

  function nangModal(modal){
    if (!modal || modal.dataset.nativeVideo==='1') return;
    modal.dataset.nativeVideo='1';
    var body=q('.ct-video-modal-body',modal);
    var old=q('iframe',body);
    if (!body || !old) return;
    var preview=old.src||old.getAttribute('src')||'';
    var direct=directUrl(preview);
    if (!direct) return;

    var loading=document.createElement('span');
    loading.className='ct-native-loading';
    loading.textContent='Đang mở video…';

    var v=document.createElement('video');
    v.className='ct-native-video';
    v.controls=true;
    v.autoplay=true;
    v.playsInline=true;
    v.preload='metadata';
    v.setAttribute('playsinline','');
    v.setAttribute('webkit-playsinline','');
    v.setAttribute('controlslist','nodownload');
    v.setAttribute('disablepictureinpicture','');
    var poster=posterHienTai();
    if (poster) v.poster=poster;

    var fallbackDone=false;
    function fallback(){
      if (fallbackDone || !document.body.contains(modal)) return;
      fallbackDone=true;
      try{v.pause();}catch(e){}
      if (loading.parentNode) loading.remove();
      if (v.parentNode) v.remove();
      old.style.display='block';
      if (!old.parentNode) body.appendChild(old);
    }

    old.style.display='none';
    body.appendChild(loading);
    body.appendChild(v);
    v.src=direct;

    v.addEventListener('loadedmetadata',function(){
      if (loading.parentNode) loading.remove();
      var p=v.play(); if (p && p.catch) p.catch(function(){});
    },{once:true});
    v.addEventListener('canplay',function(){ if (loading.parentNode) loading.remove(); },{once:true});
    v.addEventListener('error',fallback,{once:true});

    setTimeout(function(){
      if (!document.body.contains(modal) || fallbackDone) return;
      if (!v.duration || !isFinite(v.duration)) fallback();
    },5500);
  }

  var ob=new MutationObserver(function(muts){
    muts.forEach(function(m){
      Array.prototype.forEach.call(m.addedNodes||[],function(n){
        if (!n || n.nodeType!==1) return;
        if (n.id==='ctVideoModal' || (n.matches && n.matches('.ct-video-modal'))) nangModal(n);
        var nested=n.querySelector && n.querySelector('.ct-video-modal');
        if (nested) nangModal(nested);
      });
    });
  });
  ob.observe(document.documentElement,{childList:true,subtree:true});
  var now=q('.ct-video-modal'); if (now) nangModal(now);
})();
