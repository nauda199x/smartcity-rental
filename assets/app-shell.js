(function(){
  "use strict";
  function load(src){
    var s=document.createElement("script");
    s.src=src;
    s.async=false;
    document.head.appendChild(s);
  }
  load("/assets/app-shell-legacy-20260913.js?v=20260913-1");
  if(location.pathname.replace(/\/+$/,"")==="/gui-thue"){
    load("/assets/gui-thue-upload-fast-patch.js?v=20260913-1");
  }
})();
