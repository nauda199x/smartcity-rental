/* Load the shared video player before wiring apartment gallery buttons. */
(function(){
  'use strict';
  function nap(src,done){
    var s=document.createElement('script');
    s.src=src;
    s.async=false;
    s.onload=s.onerror=function(){ if(done) done(); };
    document.head.appendChild(s);
  }
  nap('/assets/can-ho-detail-video-override.js?v=20260905-2',function(){
    nap('/assets/can-ho-detail-base.js?v=20260905-2',function(){
      try{ document.dispatchEvent(new CustomEvent('ngonngu:doi')); }catch(e){}
    });
  });
})();
