/* Shared apartment video player. Never mount two players or use Drive download URLs as media. */
(function () {
  'use strict';
  var closeCurrent = null;
  var strings = {
    vi: ['Video thực tế', 'Đóng video', 'Đang tải video…', 'Video tải chậm. Có thể thử lại hoặc mở video gốc.', 'Video chưa tải được. Thử lại hoặc mở video gốc.', 'Thử lại', 'Mở video gốc', 'Chọn video'],
    en: ['Apartment video', 'Close video', 'Loading video…', 'Loading slowly. Retry or open the original video.', 'Unable to load. Retry or open the original video.', 'Retry', 'Open original video', 'Choose video'],
    ko: ['실제 매물 영상', '영상 닫기', '영상 로딩 중…', '로딩이 느립니다. 다시 시도하거나 원본 영상을 여세요.', '영상을 불러올 수 없습니다. 다시 시도하거나 원본을 여세요.', '다시 시도', '원본 영상 열기', '영상 선택'],
    zh: ['房源实拍视频', '关闭视频', '视频加载中…', '加载较慢，请重试或打开原视频。', '视频暂时无法加载，请重试或打开原视频。', '重试', '打开原视频', '选择视频']
  };
  function text(n) { return (strings[(document.documentElement.lang || 'vi').split('-')[0]] || strings.vi)[n]; }
  function el(tag, cls, value) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value !== undefined) node.textContent = value;
    return node;
  }
  function safePreview(url) { return /^https:\/\/drive\.google\.com\/file\/d\/[A-Za-z0-9_-]+\/preview(?:[?#].*)?$/i.test(String(url || '')); }
  function safeSource(value) { return value && /^\/video-can-ho\/[a-f0-9]{20}\.mp4$/.test(value.src || ''); }

  var style = document.createElement('link');
  style.rel = 'stylesheet';
  style.href = '/assets/can-ho-video.css?v=20260905-2';
  document.head.appendChild(style);

  function open(options) {
    var urls = (options.urls || []).filter(safePreview);
    if (!urls.length) return;
    if (closeCurrent) closeCurrent();
    var previousFocus = document.activeElement;
    var scrollY = window.scrollY;
    var scrollX = window.scrollX;
    var originalStyles = {};
    ['position', 'top', 'left', 'width', 'overflow'].forEach(function (key) { originalStyles[key] = document.body.style[key]; });
    var modal = el('div', 'ct-video-modal');
    modal.id = 'ctVideoModal';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'ctVideoTitle');
    var dialog = el('div', 'ct-video-dialog');
    var head = el('div', 'ct-video-modal-head');
    var title = el('strong');
    title.id = 'ctVideoTitle';
    var close = el('button', 'ct-video-modal-close');
    close.type = 'button';
    close.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 6 12 12M18 6 6 18"/></svg>';
    head.appendChild(title);
    head.appendChild(close);
    var body = el('div', 'ct-video-modal-body');
    var status = el('span', 'ct-video-status');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    body.appendChild(status);
    var foot = el('div', 'ct-video-modal-foot');
    var pickerLabel, picker;
    if (urls.length > 1) {
      var pickerWrap = el('label', 'ct-video-picker');
      pickerLabel = el('span');
      picker = el('select');
      urls.forEach(function (url, i) {
        var option = el('option', '', (i + 1) + ' / ' + urls.length);
        option.value = String(i);
        picker.appendChild(option);
      });
      pickerWrap.appendChild(pickerLabel);
      pickerWrap.appendChild(picker);
      foot.appendChild(pickerWrap);
      picker.addEventListener('change', function () { load(Number(picker.value)); });
    }
    var retry = el('button', 'ct-video-retry');
    retry.type = 'button';
    retry.hidden = true;
    var original = el('a');
    original.target = '_blank';
    original.rel = 'noopener noreferrer';
    foot.appendChild(retry);
    foot.appendChild(original);
    dialog.appendChild(head);
    dialog.appendChild(body);
    dialog.appendChild(foot);
    modal.appendChild(dialog);
    document.body.appendChild(modal);
    document.body.classList.add('ct-video-modal-open');
    document.body.style.position = 'fixed';
    document.body.style.top = -scrollY + 'px';
    document.body.style.left = -scrollX + 'px';
    document.body.style.width = '100%';
    document.body.style.overflow = 'hidden';

    var current = null, timer = null, index = 0, disposed = false, disposeMedia = null;
    var statusKey = 2;
    function labels() {
      title.textContent = text(0) + (options.code ? ' · ' + options.code : '');
      close.setAttribute('aria-label', text(1));
      status.textContent = text(statusKey);
      retry.textContent = text(5);
      original.textContent = text(6);
      if (pickerLabel) pickerLabel.textContent = text(7);
    }
    function message(key, offerRetry) {
      statusKey = key;
      status.textContent = text(key);
      status.hidden = false;
      retry.hidden = !offerRetry;
    }
    function clearMedia() {
      clearTimeout(timer);
      if (disposeMedia) disposeMedia();
      disposeMedia = null;
      if (!current) return;
      if (current.tagName === 'VIDEO') {
        current.pause();
        current.removeAttribute('src');
        current.load();
      } else {
        current.src = 'about:blank';
      }
      current.remove();
      current = null;
    }
    function load(nextIndex) {
      clearMedia();
      index = nextIndex;
      var url = urls[index];
      original.href = url.replace('/preview', '/view');
      message(2, false);
      var source = (options.sources || {})[url];
      var media = el(safeSource(source) ? 'video' : 'iframe');
      current = media;
      var bindings = [];
      function on(event, handler) {
        media.addEventListener(event, handler);
        bindings.push([event, handler]);
      }
      disposeMedia = function () { bindings.forEach(function (pair) { media.removeEventListener(pair[0], pair[1]); }); };
      function ready() {
        if (disposed || current !== media) return;
        clearTimeout(timer);
        status.hidden = true;
        retry.hidden = true;
      }
      function failed() {
        if (disposed || current !== media) return;
        clearTimeout(timer);
        message(4, true);
      }
      on('error', failed);
      if (media.tagName === 'VIDEO') {
        media.controls = true;
        media.playsInline = true;
        media.preload = 'metadata';
        media.setAttribute('playsinline', '');
        media.setAttribute('webkit-playsinline', '');
        if (options.poster) media.poster = options.poster;
        on('loadeddata', ready);
        on('canplay', ready);
        on('playing', ready);
        on('waiting', function () { message(2, false); });
        body.insertBefore(media, status);
        media.src = source.src;
        // The source is known before the click: preserve iOS user activation.
        var play = media.play();
        if (play && play.catch) play.catch(function (error) {
          if (disposed || current !== media) return;
          if (error.name === 'NotAllowedError') ready();
          else if (error.name !== 'AbortError') failed();
        });
      } else {
        // A newly uploaded video may still be processing. Mount only the Drive
        // preview, never a hidden second player and never a timed source swap.
        media.title = title.textContent;
        media.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
        media.setAttribute('allowfullscreen', '');
        media.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
        on('load', ready);
        body.insertBefore(media, status);
        media.src = url;
      }
      timer = setTimeout(function () {
        if (!disposed && current === media && !status.hidden) message(3, true);
      }, 15000);
    }
    function fitViewport() {
      var view = window.visualViewport;
      modal.style.height = (view ? view.height : window.innerHeight) + 'px';
      modal.style.top = (view ? view.offsetTop : 0) + 'px';
    }
    function finish() {
      if (disposed) return;
      disposed = true;
      clearMedia();
      document.removeEventListener('keydown', keyboard);
      document.removeEventListener('ngonngu:doi', labels);
      window.removeEventListener('resize', fitViewport);
      window.removeEventListener('pagehide', finish);
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', fitViewport);
        window.visualViewport.removeEventListener('scroll', fitViewport);
      }
      modal.remove();
      document.body.classList.remove('ct-video-modal-open');
      Object.keys(originalStyles).forEach(function (key) { document.body.style[key] = originalStyles[key]; });
      window.scrollTo({ left: scrollX, top: scrollY, behavior: 'instant' });
      if (previousFocus && previousFocus.isConnected) previousFocus.focus({ preventScroll: true });
      closeCurrent = null;
    }
    function keyboard(event) {
      if (event.key === 'Escape') { event.preventDefault(); finish(); }
      if (event.key !== 'Tab') return;
      var focusable = Array.prototype.slice.call(dialog.querySelectorAll('button:not([hidden]), a[href], select, video, iframe'));
      var first = focusable[0], last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    close.addEventListener('click', finish);
    retry.addEventListener('click', function () { load(index); });
    modal.addEventListener('click', function (event) { if (event.target === modal) finish(); });
    document.addEventListener('keydown', keyboard);
    document.addEventListener('ngonngu:doi', labels);
    window.addEventListener('resize', fitViewport);
    window.addEventListener('pagehide', finish);
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', fitViewport);
      window.visualViewport.addEventListener('scroll', fitViewport);
    }
    closeCurrent = finish;
    labels();
    fitViewport();
    close.focus({ preventScroll: true });
    load(0);
  }
  window.CTDetailVideo = { open: open };
})();
