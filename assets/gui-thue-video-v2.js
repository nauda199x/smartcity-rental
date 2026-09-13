/* /gui-thue/: video upload nhanh, chạy độc lập với luồng ảnh. */
(function(){
  "use strict";
  if(location.pathname.replace(/\/+$/,"")!=="/gui-thue") return;

  var PROJECT="owwqrgwezuwonwdzphie";
  var PUBLIC_BASE="https://"+PROJECT+".supabase.co";
  var UPLOAD_BASE="https://"+PROJECT+".storage.supabase.co";
  var KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93d3FyZ3dlenV3b253ZHpwaGllIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgxNDUyMTcsImV4cCI6MjEwMzcyMTIxN30.F8OA1tRSN2fv-Alpbe3PHZDE6mvUuU4WU2wkFIBD04Q";
  var BUCKET="timthuesmartcity-owner-videos";
  var MAX_VIDEO=2,MAX_SIZE=120*1024*1024;
  var MIME=["video/mp4","video/quicktime","video/webm"];
  var ds=[];

  function $(id){return document.getElementById(id)}
  function id(){return crypto&&crypto.randomUUID?crypto.randomUUID():("v"+Date.now().toString(36)+Math.random().toString(36).slice(2))}
  function ext(f){var t=(f.type||"").toLowerCase();return t==="video/quicktime"?"mov":t==="video/webm"?"webm":"mp4"}
  function enc(p){return p.split("/").map(encodeURIComponent).join("/")}
  function mb(n){return (n/1048576).toFixed(n>=10485760?0:1)+" MB"}
  function loi(t){var h=$("hopLoi");if(h){h.textContent=t;h.classList.add("hien");try{h.scrollIntoView({behavior:"smooth",block:"center"})}catch(e){}}else alert(t)}
  function taoPath(f){var d=new Date(),m=d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0");return "pending/"+m+"/"+id()+"."+ext(f)}

  function pctTong(){var total=0,done=0;ds.forEach(function(x){total+=x.file.size;done+=Math.min(x.file.size,x.loaded||0)});return total?Math.round(done/total*100):0}
  function dem(){
    var el=$("demAnh"),grid=$("luoiAnh");if(!el||!grid)return;
    var a=grid.querySelectorAll(".o-anh:not([data-owner-video]) img").length,v=ds.length,parts=[];
    if(!a&&!v){el.textContent="Chưa chọn ảnh/video. Có thể bỏ qua bước này và tiếp tục.";return}
    if(a)parts.push(a+" ảnh");if(v)parts.push(v+" video");
    var running=ds.some(function(x){return x.promise&&!x.done}),all=v&&ds.every(function(x){return x.done}),s="";
    if(running)s=" · video đang tải nền "+pctTong()+"%";else if(all)s=" · video đã tải xong";
    el.textContent="Đã chọn "+parts.join(" + ")+s+". Ảnh đầu tiên dùng làm ảnh bìa."
  }
  function progress(){
    dem();var n=$("nutGui");if(!n||!n.disabled)return;
    var c=$("chuTienTrinh"),bar=$("thanhChay"),p=pctTong();if(c&&p<100)c.textContent="Video đang hoàn tất · "+p+"%";
    if(bar&&p<100){var old=parseFloat(bar.style.width||"0")||0,next=10+Math.round(p*.55);if(next>old)bar.style.width=Math.min(65,next)+"%"}
    var grid=$("luoiAnh");if(grid)ds.forEach(function(x){var b=grid.querySelector('[data-owner-video="'+x.uid+'"] .owner-video-progress');if(b)b.textContent=x.done?"100%":Math.round((x.loaded||0)/Math.max(1,x.file.size)*100)+"%"})
  }
  function render(){
    var grid=$("luoiAnh");if(!grid)return;Array.prototype.slice.call(grid.querySelectorAll("[data-owner-video]")).forEach(function(n){n.remove()});
    ds.forEach(function(x){var box=document.createElement("div");box.className="o-anh owner-video-item";box.dataset.ownerVideo=x.uid;var v=document.createElement("video");v.src=x.preview;v.controls=true;v.preload="metadata";v.playsInline=true;v.setAttribute("playsinline","");var badge=document.createElement("span");badge.className="owner-video-badge";badge.textContent="VIDEO";var pr=document.createElement("span");pr.className="owner-video-progress";pr.textContent=x.done?"100%":"0%";var del=document.createElement("button");del.type="button";del.className="owner-video-delete";del.textContent="×";del.setAttribute("aria-label","Xóa video");del.onclick=function(e){e.preventDefault();e.stopPropagation();if(x.xhr)try{x.xhr.abort()}catch(_e){};URL.revokeObjectURL(x.preview);ds=ds.filter(function(y){return y.uid!==x.uid});render()};box.appendChild(v);box.appendChild(badge);box.appendChild(pr);box.appendChild(del);grid.appendChild(box)});dem()
  }

  function uploadOne(x){
    if(x.done)return Promise.resolve(x.publicUrl);if(x.promise)return x.promise;
    x.promise=new Promise(function(resolve,reject){var u=UPLOAD_BASE+"/storage/v1/object/"+BUCKET+"/"+enc(x.path),xhr=new XMLHttpRequest();x.xhr=xhr;xhr.open("POST",u,true);xhr.timeout=8*60*1000;xhr.setRequestHeader("Authorization","Bearer "+KEY);xhr.setRequestHeader("apikey",KEY);xhr.setRequestHeader("Content-Type",x.file.type||"video/mp4");xhr.setRequestHeader("x-upsert","false");xhr.upload.onprogress=function(e){if(e.lengthComputable){x.loaded=e.loaded;progress()}};xhr.onerror=function(){reject(new Error("Mạng bị gián đoạn khi tải video."))};xhr.ontimeout=function(){reject(new Error("Tải video quá lâu. Anh/chị thử lại khi mạng ổn định hơn."))};xhr.onabort=function(){reject(new Error("Video đã được hủy."))};xhr.onload=function(){if(xhr.status>=200&&xhr.status<300){x.loaded=x.file.size;x.done=true;x.xhr=null;progress();resolve(x.publicUrl)}else reject(new Error("Không tải được video (mã "+xhr.status+")."))};xhr.send(x.file)});
    x.promise=x.promise.catch(function(e){x.promise=null;x.xhr=null;throw e});return x.promise
  }
  function uploadAll(){return Promise.all(ds.slice().map(uploadOne))}
  function urls(){return ds.map(function(x){return x.publicUrl})}

  function addVideos(files){
    var left=MAX_VIDEO-ds.length;if(left<=0){loi("Mỗi căn nhận tối đa 2 video.");return}var added=[];
    files.slice(0,left).forEach(function(f){var t=(f.type||"").toLowerCase();if(MIME.indexOf(t)<0){loi("Video chưa đúng định dạng. Chọn MP4, MOV hoặc WebM giúp em.");return}if(f.size>MAX_SIZE){loi("Video "+f.name+" nặng "+mb(f.size)+". Mỗi video tối đa 120 MB.");return}var p=taoPath(f);added.push({uid:id(),file:f,path:p,publicUrl:PUBLIC_BASE+"/storage/v1/object/public/"+BUCKET+"/"+enc(p),preview:URL.createObjectURL(f),loaded:0,done:false,promise:null,xhr:null})});
    if(files.length>left)loi("Mỗi căn nhận tối đa 2 video, video thừa đã được bỏ qua.");ds=ds.concat(added);render();uploadAll().catch(function(){})
  }

  function onFiles(e){var input=e.target;if(!input||input.id!=="chonAnh")return;var files=Array.prototype.slice.call(input.files||[]),imgs=[],vids=[];if(!files.length)return;files.forEach(function(f){((f.type||"").toLowerCase().indexOf("video/")===0?vids:imgs).push(f)});if(!vids.length)return;addVideos(vids);try{var dt=new DataTransfer();imgs.forEach(function(f){dt.items.add(f)});input.files=dt.files}catch(err){if(!imgs.length){e.stopImmediatePropagation();input.value=""}}setTimeout(render,0)}

  function patchFetch(){
    if(!window.fetch||window.fetch.__ownerVideoFastStandalone)return;var raw=window.fetch.bind(window);
    var f=async function(input,init){var o=init;try{if(o&&typeof o.body==="string"){var p=JSON.parse(o.body);if(p&&p.action==="chuNhaGuiCan"&&ds.length){uploadAll().catch(function(){});var u=urls();p.videoUrls=u;p.soVideo=u.length;p.video=u[0]||"";if(u.length){var line="Video căn hộ: "+u.join(" | ");p.ghiChu=p.ghiChu?(p.ghiChu+"\n"+line):line}o=Object.assign({},o,{body:JSON.stringify(p)})}if(p&&p.action==="chuNhaGuiXong"&&ds.length)await uploadAll()}}catch(e){if(/video|tải|mạng/i.test(String(e&&e.message||e)))throw e}return raw(input,o)};f.__ownerVideoFastStandalone=true;window.fetch=f
  }
  function ui(){var input=$("chonAnh");if(!input)return;input.setAttribute("accept","image/*,video/mp4,video/quicktime,video/webm");var lead=document.querySelector(".gui-photo-lead"),b=lead&&lead.querySelector("strong"),s=lead&&lead.querySelector("span");if(b)b.textContent="Ảnh / video là tùy chọn";if(s)s.textContent="Video tự tải nền ngay khi chọn để giảm thời gian chờ lúc gửi căn.";var lab=document.querySelector('label.nut-anh[for="chonAnh"]'),bb=lab&&lab.querySelector("b"),sm=lab&&lab.querySelector("small");if(bb)bb.textContent="Chọn ảnh hoặc video căn hộ";if(sm)sm.textContent="Chọn nhiều ảnh và tối đa 2 video. Video sẽ tải nền ngay sau khi chọn.";var safe=document.querySelector('[data-step="2"] .gui-safe');if(safe)safe.textContent="Có thể bấm Tiếp tục ngay; video vẫn tải nền trong lúc anh/chị điền liên hệ."}
  function style(){var st=document.createElement("style");st.textContent=".owner-video-item{position:relative;background:#0b1728;overflow:hidden}.owner-video-item video{display:block;width:100%;height:100%;min-height:130px;object-fit:cover;background:#0b1728}.owner-video-badge,.owner-video-progress{position:absolute;left:7px;padding:3px 7px;border-radius:999px;background:rgba(8,25,48,.82);color:#fff;font-size:10px;font-weight:700;pointer-events:none}.owner-video-badge{top:7px}.owner-video-progress{bottom:7px}.owner-video-delete{position:absolute;right:7px;top:7px;width:29px;height:29px;border:0;border-radius:50%;background:rgba(255,255,255,.94);color:#163a68;font-size:20px;display:grid;place-items:center;cursor:pointer}";document.head.appendChild(st)}
  function init(){if(!$("chonAnh")||!$("mauGui"))return;ui();style();patchFetch();document.addEventListener("change",onFiles,true);var grid=$("luoiAnh");if(grid&&window.MutationObserver)new MutationObserver(function(){if(!grid.querySelector("[data-owner-video]")&&ds.length)render();else dem()}).observe(grid,{childList:true});window.addEventListener("beforeunload",function(){ds.forEach(function(x){URL.revokeObjectURL(x.preview)})})}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init()
})();
