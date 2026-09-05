/* Loader giữ nguyên UX chi tiết hiện tại và nạp lớp tối ưu video mobile. */
(function(){
  'use strict';
  function nap(src,done){
    var s=document.createElement('script');
    s.src=src;
    s.async=false;
    s.onload=function(){ if(done) done(); };
    document.head.appendChild(s);
  }
  nap('/assets/can-ho-detail-base.js?v=20260905-1',function(){
    nap('/assets/can-ho-detail-video-override.js?v=20260905-1',function(){
      try{ document.dispatchEvent(new CustomEvent('ngonngu:doi')); }catch(e){}
    });
  });
})();
