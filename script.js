const APPS_SCRIPT_API_URL = "YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL";
const FALLBACK_IMAGE = "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1200&q=80";
const ZALO_NUMBER = "09xxxxxxx";

const apartmentsData = [
    {
        id: "1",
        name: "Căn hộ Studio Luxury View Hồ",
        building: "S2.05",
        area: 35,
        furniture: "Full nội thất cao cấp",
        price: "7.5 Tr/tháng",
        driveFolder: "https://drive.google.com/drive/folders/1xxxxxxxxxxxxxx_your_folder_id_1",
        badge: "vongay"
    },
    {
        id: "2",
        name: "Căn 2PN+1 Thiết Kế Hiện Đại",
        building: "S1.12",
        area: 68,
        furniture: "Cơ bản chủ đầu tư",
        price: "11 Tr/tháng",
        driveFolder: "https://drive.google.com/drive/folders/1xxxxxxxxxxxxxx_your_folder_id_2",
        badge: "giamgia"
    }
];

const driveCache = {};
let activeGallery = { images: [], currentIndex: 0 };

async function fetchImagesForFolder(folderUrl) {
    if (!folderUrl) return [{ url: FALLBACK_IMAGE, thumbnail: FALLBACK_IMAGE }];
    if (driveCache[folderUrl]) return driveCache[folderUrl];

    try {
        const response = await fetch(`${APPS_SCRIPT_API_URL}?folderUrl=${encodeURIComponent(folderUrl)}`);
        const data = await response.json();
        if (Array.isArray(data) && data.length > 0) {
            driveCache[folderUrl] = data;
            return data;
        }
    } catch (error) {
        console.error("Lỗi nạp ảnh từ Drive Folder:", error);
    }
    return [{ url: FALLBACK_IMAGE, thumbnail: FALLBACK_IMAGE }];
}

function renderApartments() {
    const grid = document.getElementById('apartments-grid');
    if (!grid) return;
    grid.innerHTML = '';

    apartmentsData.forEach(item => {
        const card = document.createElement('div');
        card.className = 'apartment-card';
        card.dataset.id = item.id;

        let badgeHtml = '';
        if (item.badge === 'vongay') badgeHtml = '<span class="badge vongay">🔥 Vào ngay</span>';
        if (item.badge === 'colich') badgeHtml = '<span class="badge colich">📅 Có lịch vào</span>';
        if (item.badge === 'giamgia') badgeHtml = '<span class="badge giamgia">🏷 Đã giảm giá</span>';

        card.innerHTML = `
            <div class="card-media loading" id="media-${item.id}">
                <div class="badge-container">${badgeHtml}</div>
                <div class="img-counter" id="counter-${item.id}" style="display:none;">📷 1/1</div>
                <img src="" alt="${item.name}" class="card-img" id="img-${item.id}" loading="lazy" style="display:none;">
            </div>
            <div class="card-info">
                <div class="info-header">
                    <h3 class="apartment-name">${item.name}</h3>
                    <span class="apartment-price">${item.price}</span>
                </div>
                <div class="apartment-details">
                    <span>🏢 Tòa: <strong>${item.building}</strong></span> • 
                    <span>📐 ${item.area} m²</span> • 
                    <span>🛋 ${item.furniture}</span>
                </div>
                <div class="card-actions">
                    <button class="btn btn-detail" onclick="event.stopPropagation(); openGalleryForCard('${item.id}', 0)">Xem chi tiết</button>
                    <a href="https://zalo.me/${ZALO_NUMBER}" target="_blank" rel="noopener" class="btn btn-zalo" onclick="event.stopPropagation();">Chat Zalo</a>
                </div>
            </div>
        `;
        grid.appendChild(card);
        loadCardImages(item);
    });
}

async function loadCardImages(apartment) {
    const imgElement = document.getElementById(`img-${apartment.id}`);
    const mediaBox = document.getElementById(`media-${apartment.id}`);
    const counterBox = document.getElementById(`counter-${apartment.id}`);

    if (!imgElement || !mediaBox || !counterBox) return;

    const images = await fetchImagesForFolder(apartment.driveFolder);
    mediaBox.classList.remove('loading');
    imgElement.src = images[0].thumbnail;
    imgElement.style.display = 'block';
    counterBox.innerText = `📷 1/${images.length}`;
    counterBox.style.display = 'block';

    let intervalId = null;
    let localIndex = 0;

    mediaBox.addEventListener('mouseenter', () => {
        if (images.length <= 1) return;
        intervalId = setInterval(() => {
            localIndex = (localIndex + 1) % images.length;
            imgElement.src = images[localIndex].thumbnail;
            counterBox.innerText = `📷 ${localIndex + 1}/${images.length}`;
        }, 2000);
    });

    mediaBox.addEventListener('mouseleave', () => {
        if (intervalId) clearInterval(intervalId);
        localIndex = 0;
        imgElement.src = images[0].thumbnail;
        counterBox.innerText = `📷 1/${images.length}`;
    });

    let touchStartX = 0;
    mediaBox.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
    }, { passive: true });

    mediaBox.addEventListener('touchend', (e) => {
        const touchEndX = e.changedTouches[0].clientX;
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 40) {
            if (diff > 0) {
                localIndex = (localIndex + 1) % images.length;
            } else {
                localIndex = (localIndex - 1 + images.length) % images.length;
            }
            imgElement.src = images[localIndex].thumbnail;
            counterBox.innerText = `📷 ${localIndex + 1}/${images.length}`;
        }
    }, { passive: true });

    mediaBox.addEventListener('click', () => {
        openGalleryForCard(apartment.id, localIndex);
    });
}

async function openGalleryForCard(apartmentId, startIndex) {
    const apartment = apartmentsData.find(a => a.id === apartmentId);
    if (!apartment) return;

    const imagesData = await fetchImagesForFolder(apartment.driveFolder);
    activeGallery.images = imagesData.map(img => img.url);
    activeGallery.currentIndex = startIndex;

    const modal = document.getElementById('gallery-modal');
    if (!modal) return;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    updateGalleryView();
    renderGalleryThumbnails(imagesData);
}

function updateGalleryView() {
    const imgElement = document.getElementById('gallery-main-img');
    const counter = document.getElementById('gallery-counter');
    if (!imgElement || !counter) return;

    const { images, currentIndex } = activeGallery;
    imgElement.src = images[currentIndex];
    counter.innerText = `${currentIndex + 1} / ${images.length}`;

    document.querySelectorAll('.thumb-item').forEach((thumb, idx) => {
        if (idx === currentIndex) {
            thumb.classList.add('active');
            thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        } else {
            thumb.classList.remove('active');
        }
    });
}

function renderGalleryThumbnails(imagesData) {
    const footer = document.getElementById('gallery-footer');
    if (!footer) return;
    footer.innerHTML = '';

    imagesData.forEach((img, idx) => {
        const thumb = document.createElement('div');
        thumb.className = `thumb-item ${idx === activeGallery.currentIndex ? 'active' : ''}`;
        thumb.innerHTML = `<img src="${img.thumbnail}" alt="thumb">`;
        thumb.addEventListener('click', () => {
            resetZoomScope();
            activeGallery.currentIndex = idx;
            updateGalleryView();
        });
        footer.appendChild(thumb);
    });
}

function closeGalleryScope() {
    const modal = document.getElementById('gallery-modal');
    if (!modal) return;
    modal.classList.remove('active');
    document.body.style.overflow = 'unset';
    resetZoomScope();
}

function nextImageScope() {
    if (activeGallery.images.length === 0) return;
    resetZoomScope();
    activeGallery.currentIndex = (activeGallery.currentIndex + 1) % activeGallery.images.length;
    updateGalleryView();
}

function prevImageScope() {
    if (activeGallery.images.length === 0) return;
    resetZoomScope();
    activeGallery.currentIndex = (activeGallery.currentIndex - 1 + activeGallery.images.length) % activeGallery.images.length;
    updateGalleryView();
}

function resetZoomScope() {
    const wrapper = document.getElementById('main-img-wrapper');
    const btnZoom = document.getElementById('btn-zoom');
    if (wrapper) wrapper.classList.remove('zoomed');
    if (btnZoom) btnZoom.innerText = '🔍 1x';
}

document.getElementById('gallery-next')?.addEventListener('click', nextImageScope);
document.getElementById('gallery-prev')?.addEventListener('click', prevImageScope);
document.getElementById('btn-close-gallery')?.addEventListener('click', closeGalleryScope);

document.getElementById('btn-zoom')?.addEventListener('click', () => {
    const wrapper = document.getElementById('main-img-wrapper');
    const btnZoom = document.getElementById('btn-zoom');
    if (!wrapper || !btnZoom) return;

    const isZoomed = wrapper.classList.toggle('zoomed');
    btnZoom.innerText = isZoomed ? '🔍 2x' : '🔍 1x';
});

document.getElementById('btn-fullscreen')?.addEventListener('click', () => {
    const modal = document.getElementById('gallery-modal');
    if (!modal) return;
    if (!document.fullscreenElement) {
        modal.requestFullscreen().catch(() => {});
    } else {
        document.exitFullscreen();
    }
});

window.addEventListener('keydown', (e) => {
    const modal = document.getElementById('gallery-modal');
    if (!modal || !modal.classList.contains('active')) return;

    if (e.key === 'Escape') closeGalleryScope();
    if (e.key === 'ArrowRight') nextImageScope();
    if (e.key === 'ArrowLeft') prevImageScope();
});

window.addEventListener('DOMContentLoaded', renderApartments);
