    <!-- ══ KHỐI NAP (thêm 29/08/2026) ═════════════════════════════════════
         NAP = Name – Address – Phone. Ba thông tin này phải giống hệt nhau
         giữa website, hồ sơ Google Business Profile và các kênh mạng xã hội.
         Lệch một ký tự là loãng tín hiệu thực thể — đổi ở đây thì phải đổi
         cả trên hồ sơ Google.

         VIẾT THẲNG VÀO HTML, KHÔNG DỰNG BẰNG JS. Công cụ thu thập của Google
         và của các bên thứ ba đều bỏ các thẻ script; NAP dựng bằng JS coi như
         không tồn tại với chúng.

         data-site-identity="true" là mốc để assets/app-shell.js nhận ra khối
         tĩnh đã có sẵn và KHÔNG chèn thêm bản dựng bằng JS (tránh lặp hai lần).

         Nguồn duy nhất của khối này: scripts/khoi-nap.tpl
         Chèn vào các trang tĩnh bằng: python3 scripts/chen-khoi-nap.py
         ═══════════════════════════════════════════════════════════════════ -->
    <div class="shell site-nap" data-site-identity="true">
      <p class="nap-ten">Cho thuê chung cư Smart City</p>
      <p class="nap-diachi">Vinhomes Smart City, phường Tây Mỗ, thành phố Hà Nội</p>
      <p class="nap-dienthoai">Hotline &amp; Zalo:
        <a href="tel:+84977923284">0977 923 284</a> ·
        <a href="https://zalo.me/0977923284" target="_blank" rel="noopener nofollow">Nhắn Zalo</a>
      </p>
      <p class="nap-minhbach"><strong>Thông tin minh bạch:</strong> TimThueSmartCity.com
        là nền tảng/môi giới cho thuê căn hộ độc lập, không phải website chính thức
        và không đại diện cho Vinhomes/Vingroup.</p>
      <p class="nap-lienket">
        <a href="/gioi-thieu-lien-he.html">Giới thiệu &amp; Liên hệ</a>
        <a href="/cam-nang-thue-nha.html">Cẩm nang thuê nhà</a>
        <a href="/gui-thue/">Chủ nhà gửi căn</a>
        <a href="/chinh-sach-quyen-rieng-tu.html">Chính sách quyền riêng tư</a>
      </p>
    </div>
