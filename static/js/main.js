
// ===== MAIN CONFIGURATION =====
const CONFIG = {
    SITE_VERSION: '20250515-2',
    PARTICLES_COUNT: 800,
    ANIMATION_SPEED: {
        ROTATION_X: 0.0003,
        ROTATION_Y: 0.0005
    }
};

// ===== DOM ELEMENTS =====
const elements = {
    galleryGrid: document.getElementById('gallery-grid'),
    clubListe: document.getElementById('clubliste'),
    fadeElements: document.querySelectorAll('.fade-in'),
    threeBgContainer: document.getElementById('three-bg')
};

// ===== DATA STRUCTURES =====
const galleryItems = [
    {
        id: 1,
        image: '/static/css/images/gallery/alex1.jpeg',
        breite: 1170,
        hoehe: 874,
        title: 'Geburtstagsfeier',
        category: 'clubs'
    },
    {
        id: 2,
        image: '/static/css/images/gallery/alex2.png',
        breite: 1196,
        hoehe: 1312,
        title: 'Weiße Socken zu den Schuhen',
        category: 'clubs'
    },
    {
        id: 3,
        type: 'video',
        source: '/static/css/images/gallery/alex10.mp4',
        breite: 480,
        hoehe: 848,
        title: 'Klassischer Handschlag',
        category: 'clubs'
    },
    {
        id: 4,
        image: '/static/css/images/gallery/alex3.jpeg',
        breite: 1200,
        hoehe: 1600,
        title: 'Potsdam Oktoberfest',
        category: 'clubs'
    },
    {
        id: 5,
        image: '/static/css/images/gallery/alex4.jpeg',
        breite: 1152,
        hoehe: 1154,
        title: 'Baumblüte',
        category: 'people'
    },
    {
        id: 6,
        image: '/static/css/images/gallery/alex5.jpeg',
        breite: 900,
        hoehe: 1600,
        title: 'Abend mit Freunden',
        category: 'architecture'
    },
    {
        id: 7,
        image: '/static/css/images/gallery/alex6.JPG',
        breite: 1152,
        hoehe: 1343,
        title: 'Ready machen für Berlin',
        category: 'clubs'
    },
    {
        id: 8,
        type: 'video',
        source: '/static/css/images/gallery/alex11.mp4',
        breite: 480,
        hoehe: 848,
        title: 'World Club Dome abkühlen',
        category: 'clubs'
    },
    {
        id: 9,
        image: '/static/css/images/gallery/alex7.jpeg',
        breite: 777,
        hoehe: 1420,
        title: 'SMS Festival',
        category: 'people'
    },
    {
        id: 10,
        image: '/static/css/images/gallery/alex8.jpeg',
        breite: 1200,
        hoehe: 1600,
        title: 'Malle',
        category: 'architecture'
    },
    {
        id: 11,
        type: 'video',
        source: '/static/css/images/gallery/alex12.mp4',
        breite: 480,
        hoehe: 848,
        title: 'Aftern nach Geburtstag',
        category: 'clubs'
    },
    {
        id: 12,
        image: '/static/css/images/gallery/alex9.jpeg',
        breite: 1152,
        hoehe: 2048,
        title: 'World Club Dome',
        category: 'architecture'
    },
    {
        id: 13,
        image: '/static/css/images/gallery/alex13.jpeg',
        breite: 1152,
        hoehe: 2048,
        title: 'Berlin Bar',
        category: 'architecture'
    },
    {
        id: 14,
        image: '/static/css/images/gallery/alex14.jpg',
        breite: 1510,
        hoehe: 1366,
        title: 'Aftern nach Geburtstag',
        category: 'clubs'
    },
    {
        id: 15,
        image: '/static/css/images/gallery/alex15.jpeg',
        breite: 1152,
        hoehe: 2048,
        title: 'Aftern nach Geburtstag',
        category: 'clubs'
    },
    {
        id: 16,
        image: '/static/css/images/gallery/alex16.jpeg',
        breite: 1536,
        hoehe: 2048,
        title: 'Berlin Moment',
        category: 'clubs'
    },
    {
        id: 17,
        image: '/static/css/images/gallery/alex11.jpeg',
        breite: 900,
        hoehe: 1600,
        title: 'Berlin Nacht',
        category: 'clubs'
    }

];

const clubData = [
    {
        id: 1,
        name: 'Lokschuppen',
        image: '/static/css/images/clubs/lokschuppen.png',
        description: 'Der Lokschuppen Berlin ist ein bekannter Techno-Club im Herzen Berlins.',
        ratings: {
            atmosphere: 95,
            sound: 92,
            lineup: 89
        },
        badge: '★★★★★'
    },
    {
        id: 2,
        name: 'Club Ost',
        image: '/static/css/images/clubs/ost.png',
        description: 'Erlebe das Beste aus Techno, EDM und Berliner Nachtleben im Club OST.',
        ratings: {
            atmosphere: 89,
            sound: 98,
            lineup: 86
        },
        badge: '★★★★★'
    },
    {
        id: 3,
        name: 'Tresor',
        image: '/static/css/images/clubs/tresor.png',
        description: 'Legendärer Untergrund-Techno-Club in einem ehemaligen Kraftwerk.',
        ratings: {
            atmosphere: 85,
            sound: 89,
            lineup: 76
        },
        badge: '★★★★☆'
    },
    {
        id: 4,
        name: 'Ritter Butzke',
        image: '/static/css/images/clubs/butzke.png',
        description: 'Geiler Club mit einer einzigartigen Atmosphäre.',
        ratings: {
            atmosphere: 98,
            sound: 83,
            lineup: 83
        },
        badge: '★★★☆☆'
    },
    {
        id: 5,
        name: 'Wilde Renate',
        image: '/static/css/images/clubs/renate.png',
        description: 'Mehrere Floors in einer alten Wohnung mit Labyrinth im Keller.',
        ratings: {
            atmosphere: 91,
            sound: 80,
            lineup: 73
        },
        badge: '★★★☆☆'
    },
    {
        id: 6,
        name: 'MBIA',
        image: '/static/css/images/clubs/mbia.png',
        description: 'Bekannter Fetisch-Club mit Techno-Musik und Pool.',
        ratings: {
            atmosphere: 87,
            sound: 83,
            lineup: 70
        },
        badge: '★★★☆☆'
    }
];


// ===== THREE.JS BACKGROUND =====
function initThreeBackground() {
    if (!elements.threeBgContainer) return;
    
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ 
        alpha: true, 
        antialias: true 
    });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    elements.threeBgContainer.appendChild(renderer.domElement);
    
    camera.position.z = 30;
    
    // Create particles
    const particlesGeometry = new THREE.BufferGeometry();
    const posArray = new Float32Array(CONFIG.PARTICLES_COUNT * 3);
    
    for (let i = 0; i < CONFIG.PARTICLES_COUNT * 3; i += 3) {
        posArray[i] = (Math.random() - 0.5) * 100;
        posArray[i + 1] = (Math.random() - 0.5) * 100;
        posArray[i + 2] = (Math.random() - 0.5) * 100;
    }
    
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const size = 64;
    canvas.width = size;
    canvas.height = size;
    
    ctx.beginPath();
    ctx.arc(size/2, size/2, size/2, 0, Math.PI * 2);
    ctx.fillStyle = 'white';
    ctx.fill();
    
    const texture = new THREE.Texture(canvas);
    texture.needsUpdate = true;
    
    const particlesMaterial = new THREE.PointsMaterial({
        color: 0xcccccc,
        size: 0.2,
        map: texture,
        transparent: true,
        opacity: 0.5,
        alphaTest: 0.1,
        sizeAttenuation: true,
        depthWrite: false
    });
    
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particlesMesh);
    
    const animate = () => {
        requestAnimationFrame(animate);
        
        particlesMesh.rotation.x += CONFIG.ANIMATION_SPEED.ROTATION_X;
        particlesMesh.rotation.y += CONFIG.ANIMATION_SPEED.ROTATION_Y;
        
        renderer.render(scene, camera);
    };
    
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    
    animate();
}

// ===== LOGO ENHANCEMENT =====
function enhanceLogo() {
    const logoElement = document.querySelector('.logo');
    if (logoElement && logoElement.innerHTML === 'Alex Volkmann') {
        logoElement.innerHTML = '<span class="first-name">Alex</span> <span class="last-name">Volkmann</span>';
    }
}

// ===== SCROLL EVENTS =====
function initScrollEvents() {
    window.addEventListener('scroll', () => {
        // Fade in elements
        elements.fadeElements.forEach(el => {
            const elementTop = el.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;

            if (elementTop < windowHeight - 50) {
                el.classList.add('active');
            }
        });
    });
}

// ===== GALLERY FUNCTIONS =====
function createGallery() {
    if (!elements.galleryGrid) return;

    elements.galleryGrid.innerHTML = '';
    galleryItems.forEach((item) => {
        const galleryItem = document.createElement('div');
        galleryItem.className = 'gallery-item';

        // breite/hoehe als Attribut, nicht als Stil: daraus leitet der
        // Browser das Seitenverhaeltnis ab und haelt den Platz frei,
        // bevor die Datei da ist. Ohne das faenden die Masonry-Spalten
        // erst nach dem Laden ihre Hoehe - und wuerden dabei springen.
        if (item.type === 'video') {
            const video = document.createElement('video');
            video.src = item.source;
            video.muted = true;
            video.loop = true;
            video.playsInline = true;
            video.width = item.breite;
            video.height = item.hoehe;
            galleryItem.appendChild(video);

            video.addEventListener('canplay', () => video.play().catch(() => {}), { once: true });

            const playIcon = document.createElement('div');
            playIcon.className = 'gallery-video-icon';
            playIcon.innerHTML = '<i class="fas fa-play"></i>';
            galleryItem.appendChild(playIcon);
        } else {
            const img = document.createElement('img');
            img.src = item.image;
            img.alt = item.title || 'Gallery image';
            img.loading = 'lazy';
            img.decoding = 'async';
            img.width = item.breite;
            img.height = item.hoehe;
            galleryItem.appendChild(img);
        }

        elements.galleryGrid.appendChild(galleryItem);
    });

    const carouselNav = document.getElementById('carousel-nav');
    if (carouselNav) {
        carouselNav.style.display = 'none';
    }
}

function setupCarouselNavigation() {
    // Not needed for simple grid gallery
}


// ===== CLUBLISTE =====
// Die Clubs standen als Karten mit Foto, Sternebadge und drei farbigen
// Fortschrittsbalken. Drei Balken je Karte, sechs Karten - achtzehn
// Balken, die alle ungefaehr gleich weit ausschlugen und deshalb nichts
// unterschieden. Die Rangfolge, um die es geht, war daraus nicht
// ablesbar: die Karten standen in Eingabereihenfolge im Raster.
//
// Jetzt eine nummerierte Liste, sortiert nach der Gesamtzahl. Das Foto
// und die drei Einzelwerte kommen beim Darueberfahren dazu - auf
// Zeigegeraeten per Hover, sonst per Antippen.
function createClubListe() {
    const liste = elements.clubListe;
    if (!liste) return;

    // Die Gesamtzahl ist der gerundete Schnitt der drei Einzelwerte -
    // sie steht nirgends in den Daten, sonst koennten beide auseinander
    // laufen.
    const rang = clubData
        .map(club => ({
            club,
            gesamt: Math.round(
                (club.ratings.atmosphere + club.ratings.sound + club.ratings.lineup) / 3
            )
        }))
        .sort((a, b) => b.gesamt - a.gesamt);

    liste.innerHTML = '';

    rang.forEach((eintrag, i) => {
        const { club, gesamt } = eintrag;
        const nummer = String(i + 1).padStart(2, '0');

        const zeile = document.createElement('li');
        zeile.className = 'clubliste-zeile';

        // Ein <button>, damit die Details auch mit der Tastatur
        // erreichbar sind - auf einem Zeigegeraet kommen sie sonst nur
        // beim Darueberfahren.
        zeile.innerHTML = `
            <button type="button" class="clubliste-knopf" aria-expanded="false">
                <span class="clubliste-nr">${nummer}</span>
                <span class="clubliste-bild">
                    <img src="${club.image}" alt="" width="52" height="32" loading="lazy">
                </span>
                <span class="clubliste-name">${club.name}</span>
                <span class="clubliste-werte" aria-hidden="true">ATM ${club.ratings.atmosphere} &middot; SND ${club.ratings.sound} &middot; LNP ${club.ratings.lineup}</span>
                <span class="visually-hidden">Atmosphäre ${club.ratings.atmosphere}, Sound ${club.ratings.sound}, Lineup ${club.ratings.lineup}</span>
                <span class="clubliste-gesamt">${gesamt}</span>
            </button>
        `;

        const knopf = zeile.querySelector('.clubliste-knopf');
        knopf.addEventListener('click', () => oeffneClubZeile(zeile));

        liste.appendChild(zeile);
    });
}

// Immer nur eine Zeile offen: sechs aufgeklappte Zeilen sind wieder die
// Kartenwand, die die Liste ersetzt hat.
function oeffneClubZeile(zeile) {
    const offen = zeile.classList.contains('is-offen');

    document.querySelectorAll('.clubliste-zeile.is-offen').forEach(andere => {
        if (andere === zeile) return;
        andere.classList.remove('is-offen');
        andere.querySelector('.clubliste-knopf').setAttribute('aria-expanded', 'false');
    });

    zeile.classList.toggle('is-offen', !offen);
    zeile.querySelector('.clubliste-knopf').setAttribute('aria-expanded', String(!offen));
}

// ===== TOP LISTS TOGGLE FUNCTION =====
function toggleDetails(element) {
    const details = element.querySelector('.item-details');
    const allDetails = document.querySelectorAll('.item-details');
    
    // Close all other details
    allDetails.forEach(detail => {
        if (detail !== details && detail.classList.contains('show')) {
            detail.classList.remove('show');
        }
    });
    
    // Toggle current detail
    details.classList.toggle('show');
}

// ===== SMOOTH SCROLLING =====
// Ankersprünge. Laeuft Lenis, muss der Sprung durch Lenis gehen -
// window.scrollTo() waere eine zweite Animation auf derselben Position.
// Der Versatz haelt das Ziel unter dem fixierten Kopf frei.
const KOPF_VERSATZ = -88;

function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;

            const targetElement = document.querySelector(targetId);
            if (!targetElement) return;

            e.preventDefault();

            if (window.lenis) {
                window.lenis.scrollTo(targetElement, { offset: KOPF_VERSATZ });
            } else {
                window.scrollTo({
                    top: targetElement.offsetTop + KOPF_VERSATZ,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// ===== VERSION MANAGEMENT =====
function initVersionManagement() {
    const lastVersion = localStorage.getItem('site_version');
    if (lastVersion !== CONFIG.SITE_VERSION) {
        localStorage.setItem('site_version', CONFIG.SITE_VERSION);
        if (lastVersion) {
            console.log('Neue Version verfügbar. Lade Seite neu...');
            window.location.reload(true);
        }
    }
    
    updateMediaSources();
}

function updateMediaSources() {
    // Update all images
    document.querySelectorAll('img').forEach(img => {
        if (img.src && !img.src.includes('?v=') && !img.src.includes('data:image')) {
            try {
                const imgUrl = new URL(img.src);
                imgUrl.searchParams.set('v', CONFIG.SITE_VERSION);
                img.src = imgUrl.toString();
            } catch (e) {
                img.src = img.src + (img.src.includes('?') ? '&' : '?') + 'v=' + CONFIG.SITE_VERSION;
            }
        }
    });
    
    // Update all videos
    document.querySelectorAll('video').forEach(video => {
        if (video.src && !video.src.includes('?v=')) {
            try {
                const videoUrl = new URL(video.src);
                videoUrl.searchParams.set('v', CONFIG.SITE_VERSION);
                video.src = videoUrl.toString();
            } catch (e) {
                video.src = video.src + (video.src.includes('?') ? '&' : '?') + 'v=' + CONFIG.SITE_VERSION;
            }
        }
    });
}

// ===== IMPROVED GALLERY CLASS =====
class ImprovedGallery {
    constructor() {
        this.currentIndex = 0;
        this.items = galleryItems;
        this.modal = document.getElementById('improved-modal');
        this.modalMedia = document.getElementById('improved-modal-media');
        this.modalClose = document.getElementById('improved-modal-close');
        this.modalPrev = document.getElementById('improved-modal-prev');
        this.modalNext = document.getElementById('improved-modal-next');
        this.modalCounter = document.getElementById('improved-modal-counter');

        // Touch variables
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.isSwiping = false;
        this.swipeThreshold = 50;

        // Scroll position tracking
        this.savedScrollPosition = 0;
        
        if (this.modal && elements.galleryGrid) {
            this.init();
        }
    }

    init() {
        this.bindEvents();
        this.attachGalleryListeners();
    }

    bindEvents() {
        if (this.modalClose) {
            this.modalClose.addEventListener('click', () => this.closeModal());
        }
        
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });

        if (this.modalPrev) {
            this.modalPrev.addEventListener('click', (e) => {
                e.stopPropagation();
                this.previousItem();
            });
        }
        
        if (this.modalNext) {
            this.modalNext.addEventListener('click', (e) => {
                e.stopPropagation();
                this.nextItem();
            });
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (!this.modal.classList.contains('active')) return;
            
            switch (e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousItem();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextItem();
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.closeModal();
                    break;
            }
        });

        // Touch events
        this.modal.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        this.modal.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        this.modal.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
    }

    attachGalleryListeners() {
        setTimeout(() => {
            const galleryItems = document.querySelectorAll('.gallery-item');
            galleryItems.forEach((item, index) => {
                item.addEventListener('click', () => this.openModal(index));
            });
        }, 500);
    }

    openModal(index) {
        this.currentIndex = index;
        this.showMedia();

        // Save scroll position before opening modal
        this.savedScrollPosition = window.scrollY;
        document.body.style.setProperty('--scroll-y', `${this.savedScrollPosition}px`);

        this.modal.classList.add('active');
        document.body.classList.add('improved-modal-open');

        if (window.innerWidth <= 768) {
            this.showSwipeHint();
        }
    }

    closeModal() {
        this.modal.classList.remove('active');
        document.body.classList.remove('improved-modal-open');

        // Stop all videos
        const videos = this.modal.querySelectorAll('video');
        videos.forEach(video => {
            video.pause();
            video.currentTime = 0;
        });

        // Restore scroll position
        window.scrollTo(0, this.savedScrollPosition);
    }

    showMedia() {
        const item = this.items[this.currentIndex];
        if (!item) return;
        
        this.updateCounter();

        // Remove existing video
        const existingVideo = this.modal.querySelector('video:not(#improved-modal-media)');
        if (existingVideo) {
            existingVideo.remove();
        }

        if (item.type === 'video') {
            this.modalMedia.style.display = 'none';

            const video = document.createElement('video');
            video.className = 'improved-modal-media';
            video.controls = true;
            video.loop = true;
            video.src = item.source || item.image;
            video.volume = 0.2;
            video.setAttribute('playsinline', '');

            video.addEventListener('click', (e) => e.stopPropagation());

            this.modal.querySelector('.improved-modal-content').insertBefore(video, this.modalCounter);

            video.load();
            video.play().catch(() => {});
        } else {
            this.modalMedia.style.display = 'block';
            this.modalMedia.src = item.image || item.source;
            this.modalMedia.alt = item.title;

            // Spezial-Positioning für alex6.jpg - nach unten verschieben
            if (item.image && item.image.includes('alex6')) {
                this.modalMedia.style.objectPosition = 'center bottom';
            } else {
                this.modalMedia.style.objectPosition = 'center center';
            }
        }
    }

    updateCounter() {
        if (this.modalCounter) {
            this.modalCounter.textContent = `${this.currentIndex + 1} / ${this.items.length}`;
        }
    }

    previousItem() {
        this.currentIndex = this.currentIndex > 0 ? this.currentIndex - 1 : this.items.length - 1;
        this.showMedia();
    }

    nextItem() {
        this.currentIndex = this.currentIndex < this.items.length - 1 ? this.currentIndex + 1 : 0;
        this.showMedia();
    }

    showSwipeHint() {
        if (this.modal.querySelector('.swipe-hint')) return;
        
        const hint = document.createElement('div');
        hint.className = 'swipe-hint';
        hint.textContent = '← Wischen zum Navigieren →';
        this.modal.querySelector('.improved-modal-content').appendChild(hint);
        
        setTimeout(() => {
            if (hint.parentNode) {
                hint.remove();
            }
        }, 3000);
    }

    handleTouchStart(e) {
        if (e.target.closest('.improved-modal-content')) {
            this.touchStartX = e.touches[0].clientX;
            this.touchStartY = e.touches[0].clientY;
            this.isSwiping = false;
        }
    }

    handleTouchMove(e) {
        if (!this.touchStartX || !this.touchStartY) return;

        const touchEndX = e.touches[0].clientX;
        const touchEndY = e.touches[0].clientY;
        const diffX = this.touchStartX - touchEndX;
        const diffY = this.touchStartY - touchEndY;

        if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 10) {
            e.preventDefault();
            e.stopPropagation();
            this.isSwiping = true;
            this.modal.classList.add('swiping');
        }
    }

    handleTouchEnd(e) {
        if (!this.isSwiping) {
            this.touchStartX = 0;
            this.touchStartY = 0;
            return;
        }

        const touchEndX = e.changedTouches[0].clientX;
        const diffX = this.touchStartX - touchEndX;
        
        this.modal.classList.remove('swiping');

        if (Math.abs(diffX) > this.swipeThreshold) {
            if (diffX > 0) {
                this.nextItem();
            } else {
                this.previousItem();
            }
        }

        this.touchStartX = 0;
        this.touchStartY = 0;
        this.isSwiping = false;
    }
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initVersionManagement();
    enhanceLogo();
    initScrollEvents();
    initSmoothScrolling();

    createGallery();
    setupCarouselNavigation();
    createClubListe();

    // Nach createGallery/createClubListe: Galeriekacheln und Clubzeilen
    // entstehen erst dort, vorher gaebe es nichts zu beobachten.
    initReveals();

    setTimeout(() => {
        window.galleryModal = new ImprovedGallery();
    }, 600);
});

// Initialize when page loads
window.addEventListener('load', () => {
    // Initialize Three.js background
    initThreeBackground();
    
    // Activate initial fade elements
    elements.fadeElements.forEach(el => {
        const elementTop = el.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        
        if (elementTop < windowHeight) {
            el.classList.add('active');
        }
    });
});

// Make functions globally available
window.createGallery = createGallery;
window.createClubListe = createClubListe;
window.toggleDetails = toggleDetails;
window.galleryItems = galleryItems;

// ===== REGAL =====
// Ein Initializer fuer alle Regale auf der Seite. Findet sie ueber
// [data-regal] - jedes neue Regal im Markup ist damit automatisch
// bedienbar, ohne dass hier etwas dazukommt.
//
// Ohne JS bleibt die Spur ein normaler Scroll-Container: Wischen und
// Trackpad funktionieren weiter, nur die Pfeile fehlen (sie sind per
// CSS unsichtbar, bis is-scrollbar gesetzt ist).
(function initRegale() {
    const regale = document.querySelectorAll('[data-regal]');
    if (!regale.length) return;

    // Toleranz gegen Subpixel-Rundung: ohne die wird das Ende bei
    // fraktionalen Breiten nie ganz erreicht und der Pfeil bleibt stehen.
    const RAND = 2;

    regale.forEach(regal => {
        const viewport = regal.querySelector('[data-regal-viewport]');
        const spur = regal.querySelector('[data-regal-spur]');
        if (!viewport || !spur) return;

        const zurueck = regal.querySelector('[data-regal-prev]');
        const weiter = regal.querySelector('[data-regal-next]');

        function zustand() {
            // Wie weit rechts kann ueberhaupt gescrollt werden.
            const maximum = spur.scrollWidth - spur.clientWidth;
            const scrollbar = maximum > RAND;

            viewport.classList.toggle('is-scrollbar', scrollbar);
            viewport.classList.toggle('is-am-anfang', spur.scrollLeft <= RAND);
            // Passt alles rein, gilt das Regal auch als "am Ende" - dann
            // faellt der Verlauf am rechten Rand weg.
            viewport.classList.toggle(
                'is-am-ende', !scrollbar || spur.scrollLeft >= maximum - RAND
            );

            // Die Pfeile sind unsichtbar, sollen aber auch nicht in der
            // Tab-Reihenfolge liegen, solange sie nichts tun.
            const amAnfang = viewport.classList.contains('is-am-anfang');
            const amEnde = viewport.classList.contains('is-am-ende');
            if (zurueck) zurueck.tabIndex = scrollbar && !amAnfang ? 0 : -1;
            if (weiter) weiter.tabIndex = scrollbar && !amEnde ? 0 : -1;
        }

        // Eine Seite = sichtbare Breite minus eine Kachel, damit beim
        // Blaettern ein Rest stehen bleibt und der Zusammenhang haelt.
        function seite() {
            const slot = spur.querySelector('.regal-slot');
            const kachel = slot ? slot.getBoundingClientRect().width : 200;
            return Math.max(spur.clientWidth - kachel, kachel);
        }

        function blaettern(richtung) {
            spur.scrollBy({ left: richtung * seite(), behavior: 'smooth' });
        }

        if (zurueck) zurueck.addEventListener('click', () => blaettern(-1));
        if (weiter) weiter.addEventListener('click', () => blaettern(1));

        spur.addEventListener('scroll', zustand, { passive: true });

        // Tastatur: die Spur ist fokussierbar, Pfeiltasten scrollen.
        spur.addEventListener('keydown', ereignis => {
            const tasten = {
                ArrowRight: () => blaettern(1),
                ArrowLeft: () => blaettern(-1),
                Home: () => spur.scrollTo({ left: 0, behavior: 'smooth' }),
                End: () => spur.scrollTo({ left: spur.scrollWidth, behavior: 'smooth' })
            };

            const aktion = tasten[ereignis.key];
            if (!aktion) return;

            ereignis.preventDefault();
            aktion();
        });

        // Breitenaenderung (Fenster, spaet geladene Poster) kann aus einem
        // scrollbaren Regal ein volles machen und umgekehrt.
        if (typeof ResizeObserver === 'function') {
            new ResizeObserver(zustand).observe(spur);
        } else {
            window.addEventListener('resize', zustand);
        }

        // Werden Slots ein- oder ausgeblendet, aendert sich scrollWidth,
        // ohne dass die Spur selbst ihre Masse aendert - der
        // ResizeObserver schweigt dann. Der Filter meldet sich deshalb
        // hier selbst zurueck.
        regal.addEventListener('regal:aktualisieren', zustand);

        zustand();
    });
})();

// ===== FILMSEKTION: STIMMUNGSFILTER =====
// Die Gattungen sind jetzt eigene Regale - gefiltert wird nur noch nach
// Stimmung, und zwar ausschliesslich im Filme-Regal. Serien und Anime
// bleiben unberuehrt stehen.
(function initStimmungsfilter() {
    const sektion = document.getElementById('filme');
    if (!sektion) return;

    const filmRegal = sektion.querySelector('[data-regal="filme"]');
    if (!filmRegal) return;

    const karten = Array.from(filmRegal.querySelectorAll('[data-eintrag]'));
    if (!karten.length) return;

    const spur = filmRegal.querySelector('[data-regal-spur]');
    const chips = Array.from(sektion.querySelectorAll('[data-stimmung]'));
    const leer = sektion.querySelector('[data-empty]');
    const spotlight = sektion.querySelector('[data-spotlight]');
    const shuffleBtn = sektion.querySelector('[data-shuffle]');

    let aktiveStimmung = 'alle';

    function anwenden() {
        let sichtbar = 0;

        karten.forEach(karte => {
            const zeigen =
                aktiveStimmung === 'alle' ||
                karte.dataset.stimmung === aktiveStimmung;

            // Der Slot traegt die Breite - die Karte selbst zu verstecken
            // wuerde eine leere Luecke in der Spur hinterlassen.
            const slot = karte.closest('.regal-slot') || karte;
            slot.hidden = !zeigen;
            if (zeigen) sichtbar++;
        });

        if (leer) leer.hidden = sichtbar > 0;
        if (spotlight) spotlight.hidden = true;

        // Nach dem Filtern kann die Spur weiter rechts stehen, als es
        // jetzt noch Inhalt gibt - dann waere das Regal scheinbar leer.
        if (spur) spur.scrollLeft = 0;

        // Weniger Kacheln koennen heissen: passt jetzt ohne Scrollen.
        // Pfeile und Verlauf muessen das erfahren.
        filmRegal.dispatchEvent(new CustomEvent('regal:aktualisieren'));
    }

    function markiere(wert) {
        chips.forEach(chip => {
            const aktiv = chip.dataset.stimmung === wert;
            chip.classList.toggle('is-active', aktiv);
            chip.setAttribute('aria-pressed', String(aktiv));
        });
    }

    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            aktiveStimmung = chip.dataset.stimmung;
            markiere(aktiveStimmung);
            anwenden();
        });
    });

    // Zufall nur aus den gerade sichtbaren Filmen.
    if (shuffleBtn && spotlight) {
        shuffleBtn.addEventListener('click', () => {
            const auswahl = karten.filter(k => {
                const slot = k.closest('.regal-slot') || k;
                return !slot.hidden;
            });
            if (!auswahl.length) return;

            const treffer = auswahl[Math.floor(Math.random() * auswahl.length)];
            spotlight.replaceChildren();

            const kopie = treffer.cloneNode(true);
            kopie.hidden = false;
            kopie.classList.add('kachel--spotlight');
            spotlight.appendChild(kopie);
            spotlight.hidden = false;
        });
    }

    anwenden();
})();


// ===== SEITENKOPF: NAVIGATION =====
// Drei Aufgaben: Hintergrund ab dem Scrollen, Burger unter 768px und
// Hervorhebung des Abschnitts, in dem man gerade steht.
//
// Bewusst ohne Framework-Markup - die Nav haengt nur an data-Attributen
// im Template und an den bereits vorhandenen Sektions-IDs.
(function initSeitenkopf() {
    const kopf = document.querySelector('[data-kopf]');
    if (!kopf) return;

    const nav = kopf.querySelector('[data-nav]');
    const burger = kopf.querySelector('[data-burger]');
    const links = Array.from(kopf.querySelectorAll('[data-nav-link]'));

    // --- Hintergrund ---------------------------------------------------
    // Ueber dem Hero transparent, danach dunkel. 40px, damit schon die
    // erste Mausraddrehung umschaltet.
    const SCHWELLE = 40;

    function kopfZustand() {
        kopf.classList.toggle('is-gescrollt', window.scrollY > SCHWELLE);
    }

    window.addEventListener('scroll', kopfZustand, { passive: true });
    kopfZustand();

    // --- Burger --------------------------------------------------------
    function menue(offen) {
        if (!nav || !burger) return;
        nav.classList.toggle('is-offen', offen);
        // Der Balken deckt mit, solange das Panel offen steht.
        kopf.classList.toggle('is-menue-offen', offen);
        burger.setAttribute('aria-expanded', String(offen));
        burger.setAttribute('aria-label', offen ? 'Menü schließen' : 'Menü öffnen');
    }

    if (burger && nav) {
        burger.addEventListener('click', () => {
            menue(!nav.classList.contains('is-offen'));
        });

        // Nach dem Sprung soll das Panel nicht offen ueber dem Ziel stehen.
        links.forEach(link => link.addEventListener('click', () => menue(false)));

        document.addEventListener('keydown', ereignis => {
            if (ereignis.key === 'Escape') menue(false);
        });
    }

    // --- Aktiver Abschnitt ---------------------------------------------
    const ziele = links
        .map(link => {
            const id = link.getAttribute('href');
            return { link, sektion: id && id.startsWith('#') ? document.querySelector(id) : null };
        })
        .filter(ziel => ziel.sektion);

    if (!ziele.length || typeof IntersectionObserver !== 'function') return;

    // Aktiv ist der Abschnitt, der gerade den groessten Teil des
    // Viewports fuellt - nicht der, der ein schmales Band beruehrt.
    //
    // Ein Band scheitert an zwei Stellen: Nach einem Ankersprung liegt
    // die Zielsektion wegen scroll-margin-top bei 88px, waehrend die
    // Vorgaengersektion mit ein paar Pixeln noch ins Band ragt und
    // faelschlich aktiv bleibt. Und der Footer ist so kurz, dass er am
    // Seitenende gar nicht erst bis ins Band hochreicht.
    //
    // Der sichtbare Anteil hat beide Faelle von selbst richtig.
    const anteil = new Map();

    function markiere() {
        let treffer = null;
        let groesster = 0;

        // Dokumentreihenfolge entscheidet bei Gleichstand.
        ziele.forEach(ziel => {
            const hoehe = anteil.get(ziel.sektion) || 0;
            if (hoehe > groesster) {
                groesster = hoehe;
                treffer = ziel;
            }
        });

        ziele.forEach(ziel => {
            const aktiv = ziel === treffer;
            ziel.link.classList.toggle('is-aktiv', aktiv);
            if (aktiv) {
                ziel.link.setAttribute('aria-current', 'true');
            } else {
                ziel.link.removeAttribute('aria-current');
            }
        });
    }

    // Der Kopf verdeckt die obersten 72px - die zaehlen nicht als sichtbar.
    // Viele Schwellen, damit auch Abschnitte, die laenger sind als der
    // Viewport, beim Scrollen regelmaessig neu melden.
    const beobachter = new IntersectionObserver(eintraege => {
        eintraege.forEach(eintrag => {
            anteil.set(eintrag.target, eintrag.isIntersecting ? eintrag.intersectionRect.height : 0);
        });
        markiere();
    }, {
        rootMargin: '-72px 0px 0px 0px',
        threshold: Array.from({ length: 21 }, (unused, i) => i / 20)
    });

    ziele.forEach(ziel => beobachter.observe(ziel.sektion));
})();


// ===== BEWEGUNGSSCHICHT =====
// Traegheits-Scroll, Scroll-Reveals und Koernung.
//
// Eine gemeinsame Abfrage fuer alle vier: wer Bewegung reduziert haben
// will, bekommt die Seite statisch - aber vollstaendig sichtbar.
const BEWEGUNG_REDUZIERT = window.matchMedia('(prefers-reduced-motion: reduce)').matches;


// ===== TRAEGHEITS-SCROLL (LENIS) =====
// Startet nicht mehr von selbst: laeuft ein Ladebildschirm, wuerde sonst
// waehrenddessen gescrollt. Aufgerufen wird das entweder sofort (kein
// Intro) oder wenn der Vorhang weg ist - siehe ganz unten.
function starteTraegheitsScroll() {
    if (window.lenis) return;              // schon gestartet
    if (BEWEGUNG_REDUZIERT) return;
    if (typeof window.Lenis !== 'function') return;

    // Kurz gehalten: das Nachlaufen soll spuerbar sein, aber nicht
    // bremsen. Lenis' Standard (1.2s) fuehlt sich auf einer 9500px
    // langen Seite zaeh an.
    const lenis = new window.Lenis({
        duration: 0.8,
        easing: t => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        smoothWheel: true,
        // Auf Touch bleibt das native Scrollen - Lenis dort fuehlt sich
        // gegenueber der Systemphysik falsch an.
        smoothTouch: false
    });

    function takt(zeit) {
        lenis.raf(zeit);
        requestAnimationFrame(takt);
    }
    requestAnimationFrame(takt);

    window.lenis = lenis;
}


// ===== SCROLL-REVEALS =====
// Ein Beobachter fuer die ganze Seite. Elemente starten 24px tiefer und
// unsichtbar und fahren beim Sichtbarwerden auf ihre Endposition.
//
// Gruppen (Kacheln, Karten, Listenpunkte) bekommen 80ms Versatz pro
// Element, damit sie nacheinander erscheinen. Jedes Element genau einmal -
// danach wird es nicht mehr beobachtet.
function initReveals() {
    // Bewegung reduziert: nichts verstecken, nichts animieren. Ohne das
    // frueh zurueckzugeben, bliebe die Seite auf opacity 0 stehen.
    if (BEWEGUNG_REDUZIERT) return;

    const VERSATZ_MS = 80;
    // Deckel gegen absurde Wartezeiten: bei 17 Galeriekacheln waere das
    // letzte Element sonst erst nach 1,3s da.
    const VERSATZ_MAX = 8;

    // Reihen, deren Kinder nacheinander erscheinen.
    const GRUPPEN = [
        ['.projects-grid', '.project-card'],
        ['.clubliste', ':scope > *'],
        ['.gallery-grid', '.gallery-item'],
        ['.films-filter', ':scope > *'],
        ['.social-links', ':scope > *']
    ];

    // Einzelstuecke - erscheinen als Block, ohne Versatz.
    //
    // Regale bewusst als Ganzes: ihre Kacheln liegen zum Teil rechts
    // ausserhalb des Viewports, einzeln beobachtet wuerden die erst beim
    // seitlichen Scrollen auftauchen.
    const EINZELN = [
        // .hero-content fehlt hier bewusst: den fahrt das Intro ein
        // (siehe unten). Zwei Mechaniken auf denselben Elementen wuerden
        // sich gegenseitig ueberschreiben.
        '.sektion-kopf',
        '.about-text',
        '.about-image',
        '.berlin-marke',
        '.films-claim',
        '.regal',
        '.films-quelle',
        '.films-attribution',
        '.footer-content'
    ];

    const ziele = [];

    GRUPPEN.forEach(([behaelterWahl, kindWahl]) => {
        document.querySelectorAll(behaelterWahl).forEach(behaelter => {
            behaelter.querySelectorAll(kindWahl).forEach((kind, i) => {
                kind.style.setProperty('--reveal-verzug', `${Math.min(i, VERSATZ_MAX) * VERSATZ_MS}ms`);
                ziele.push(kind);
            });
        });
    });

    EINZELN.forEach(wahl => {
        document.querySelectorAll(wahl).forEach(el => ziele.push(el));
    });

    if (!ziele.length) return;

    const beobachter = new IntersectionObserver(eintraege => {
        eintraege.forEach(eintrag => {
            if (!eintrag.isIntersecting) return;
            // `active` fuer das alte .fade-in-CSS, das andere Seiten
            // (impressum.html) weiter nutzen.
            eintrag.target.classList.add('is-sichtbar', 'active');
            beobachter.unobserve(eintrag.target);
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -80px 0px' });

    ziele.forEach(el => {
        // Erst jetzt verstecken. Waere das Attribut schon im Markup,
        // bliebe die Seite ohne JS dauerhaft leer.
        el.setAttribute('data-reveal', '');
        beobachter.observe(el);
    });
}


// ===== KACHEL-TEXT AUF TOUCH =====
// Auf Desktop faehrt der Text per :hover ueber das Poster. Auf Touch
// gibt es kein Hover - dort schaltet ein Tipp auf die Kachel um.
//
// Der Knopf steckt im Markup (kachel-poster.html) und ist per CSS nur
// sichtbar, wo (hover: none) gilt. Hier haengt nur das Verhalten dran.
(function initKachelText() {
    const schalter = document.querySelectorAll('[data-kachel-schalter]');
    if (!schalter.length) return;

    function schliesse(ausser) {
        document.querySelectorAll('.kachel.is-offen').forEach(kachel => {
            if (kachel === ausser) return;
            kachel.classList.remove('is-offen');
            const knopf = kachel.querySelector('[data-kachel-schalter]');
            if (knopf) knopf.setAttribute('aria-expanded', 'false');
        });
    }

    schalter.forEach(knopf => {
        knopf.addEventListener('click', () => {
            const kachel = knopf.closest('.kachel');
            if (!kachel) return;

            const offen = !kachel.classList.contains('is-offen');
            // Immer nur eine Kachel offen - zwei gleichzeitig lesen sich
            // in einer scrollenden Reihe wie ein Fehler.
            schliesse(kachel);
            kachel.classList.toggle('is-offen', offen);
            knopf.setAttribute('aria-expanded', String(offen));
        });
    });

    document.addEventListener('keydown', ereignis => {
        if (ereignis.key === 'Escape') schliesse(null);
    });
})();


// ===== FILMSUCHE =====
// "Hab ich den gesehen?" - der Index kommt einmal vom Server, gesucht
// wird danach vollstaendig hier. Kein Abruf je Tastendruck, damit auch
// kein Ladezustand und keine Verzoegerung.
(function initFilmsuche() {
    const block = document.querySelector('[data-filmsuche]');
    if (!block) return;

    const feld = block.querySelector('[data-filmsuche-feld]');
    const liste = block.querySelector('[data-filmsuche-treffer]');
    const leerHinweis = block.querySelector('[data-filmsuche-leer]');
    const leerenKnopf = block.querySelector('[data-filmsuche-leeren]');

    const HOECHSTENS = 5;
    const BOXD = 'https://boxd.it/';

    let index = [];
    let treffer = [];
    let auswahl = -1;

    // Dieselbe Normalisierung wie serverseitig in films/models.py:
    // klein, ohne Akzente. Sonst faende "amelie" den Eintrag "Amélie"
    // nur auf einer der beiden Seiten.
    function normalisiere(text) {
        return String(text || '')
            .normalize('NFKD')
            .replace(/[̀-ͯ]/g, '')
            .toLowerCase()
            .trim();
    }

    function sterne(wertung) {
        const voll = Math.floor(wertung);
        const halb = wertung % 1 >= 0.5;
        return '★'.repeat(voll) + (halb ? '½' : '');
    }

    // --- Suche ----------------------------------------------------------
    function suche(eingabe) {
        const frage = normalisiere(eingabe);
        if (!frage) return [];

        // Treffer am Wortanfang zuerst - wer "pul" tippt, meint eher
        // "Pulp Fiction" als "Ford v Ferrari: Pulling Ahead".
        const beginnt = [];
        const enthaelt = [];

        for (const film of index) {
            const stelle = film.n.indexOf(frage);
            if (stelle === 0) beginnt.push(film);
            else if (stelle > 0) enthaelt.push(film);
            if (beginnt.length >= HOECHSTENS) break;
        }

        return beginnt.concat(enthaelt).slice(0, HOECHSTENS);
    }

    // --- Anzeige --------------------------------------------------------
    function zeichne() {
        liste.replaceChildren();
        auswahl = -1;

        treffer.forEach((film, i) => {
            const li = document.createElement('li');
            li.id = `filmsuche-treffer-${i}`;
            li.setAttribute('role', 'option');
            li.setAttribute('aria-selected', 'false');

            const a = document.createElement('a');
            a.href = BOXD + film.u;
            a.target = '_blank';
            a.rel = 'noopener noreferrer';

            const titel = document.createElement('span');
            titel.className = 'filmsuche-titel';
            titel.textContent = film.t;
            a.appendChild(titel);

            if (film.j) {
                const jahr = document.createElement('span');
                jahr.className = 'filmsuche-jahr';
                jahr.textContent = film.j;
                a.appendChild(jahr);
            }

            // Drei Faelle. `w` fehlt heisst unbewertet, `l` heisst Watchlist.
            if (film.l) {
                const status = document.createElement('span');
                status.className = 'filmsuche-status';
                status.textContent = 'Steht auf meiner Liste';
                a.appendChild(status);
            } else if (typeof film.w === 'number') {
                const wertung = document.createElement('span');
                wertung.className = 'filmsuche-wertung';
                wertung.textContent = sterne(film.w);
                wertung.title = `${film.w} von 5`;
                a.appendChild(wertung);
            } else {
                const status = document.createElement('span');
                status.className = 'filmsuche-status';
                status.textContent = 'Gesehen, nicht bewertet';
                a.appendChild(status);
            }

            li.appendChild(a);
            liste.appendChild(li);
        });

        feld.setAttribute('aria-expanded', String(treffer.length > 0));
        leerenKnopf.hidden = !feld.value;
    }

    function markiere(neu) {
        const eintraege = Array.from(liste.children);
        if (!eintraege.length) return;

        // Umlaufend: von unten weiter landet man wieder oben.
        auswahl = (neu + eintraege.length) % eintraege.length;

        eintraege.forEach((li, i) => {
            const aktiv = i === auswahl;
            li.classList.toggle('is-aktiv', aktiv);
            li.setAttribute('aria-selected', String(aktiv));
        });
        feld.setAttribute('aria-activedescendant', eintraege[auswahl].id);
    }

    function leere() {
        feld.value = '';
        treffer = [];
        zeichne();
        leerHinweis.hidden = true;
        feld.removeAttribute('aria-activedescendant');
    }

    // --- Ereignisse -----------------------------------------------------
    feld.addEventListener('input', () => {
        treffer = suche(feld.value);
        zeichne();

        // "Noch nicht gesehen" nur, wenn wirklich etwas getippt wurde und
        // nichts passt - nicht schon beim leeren Feld.
        const nichts = feld.value.trim().length > 0 && treffer.length === 0;
        leerHinweis.hidden = !nichts;
        if (nichts) leerHinweis.textContent = 'Noch nicht gesehen';
    });

    feld.addEventListener('keydown', ereignis => {
        if (ereignis.key === 'Escape') {
            ereignis.preventDefault();
            leere();
            return;
        }

        if (ereignis.key === 'ArrowDown') {
            ereignis.preventDefault();
            markiere(auswahl + 1);
        } else if (ereignis.key === 'ArrowUp') {
            ereignis.preventDefault();
            markiere(auswahl - 1);
        } else if (ereignis.key === 'Enter' && auswahl >= 0) {
            const link = liste.children[auswahl].querySelector('a');
            if (link) link.click();
        }
    });

    leerenKnopf.addEventListener('click', () => {
        leere();
        feld.focus();
    });

    // Klick daneben schliesst die Liste, ohne das Feld zu leeren.
    document.addEventListener('click', ereignis => {
        if (!block.contains(ereignis.target)) {
            liste.replaceChildren();
            feld.setAttribute('aria-expanded', 'false');
        }
    });

    // --- Index holen ----------------------------------------------------
    // Erst wenn er da ist, wird das Feld sichtbar. Ein Suchfeld, das noch
    // nichts finden kann, waere irrefuehrender als gar keines.
    fetch('/api/filme/index.json')
        .then(antwort => (antwort.ok ? antwort.json() : Promise.reject(antwort.status)))
        .then(daten => {
            index = daten;
            block.hidden = false;
        })
        .catch(() => {
            // Bleibt versteckt. Die Sektion funktioniert ohne die Suche.
        });
})();


// ===== WERTUNGSVERTEILUNG =====
// Balken wachsen beim Sichtbarwerden von 0 auf ihre Hoehe. Gleiche
// Mechanik wie die Club-Balken: die Zielhoehe steht im Markup, hier wird
// sie nur gesetzt, animiert wird per CSS-Transition.
(function initVerteilung() {
    const grafik = document.querySelector('[data-verteilung]');
    if (!grafik) return;

    const balken = grafik.querySelectorAll('.verteilung-balken');
    if (!balken.length) return;

    function setze() {
        balken.forEach(b => {
            b.style.height = b.dataset.hoehe || '0%';
        });
    }

    // Bewegung reduziert: sofort auf Endhoehe, ohne Beobachter.
    if (BEWEGUNG_REDUZIERT) {
        setze();
        return;
    }

    const beobachter = new IntersectionObserver(eintraege => {
        eintraege.forEach(eintrag => {
            if (!eintrag.isIntersecting) return;
            // Kurz warten, damit die Bewegung nach dem Reveal der Sektion
            // einsetzt und nicht mit ihm zusammenfaellt.
            setTimeout(setze, 200);
            beobachter.unobserve(eintrag.target);
        });
    }, { threshold: 0.25 });

    beobachter.observe(grafik);
})();


// ===== SEITE /filme/: SORTIEREN, FILTERN, POSTER NACHLADEN =====
// Alle Filme stehen bereits im Markup. Sortiert und gefiltert wird
// deshalb hier, ohne Serverrunde - bei gut zweihundert Kacheln ist das
// schneller als jede Anfrage und funktioniert ohne Nachladen.
(function initFilmraster() {
    const raster = document.querySelector('[data-filmraster]');
    if (!raster) return;

    const steuerung = document.querySelector('[data-filmsteuerung]');
    const sortierung = steuerung.querySelector('[data-sortierung]');
    const chips = Array.from(steuerung.querySelectorAll('[data-filter]'));
    const zaehler = steuerung.querySelector('[data-zaehler]');
    const leerHinweis = document.querySelector('[data-raster-leer]');

    const kacheln = Array.from(raster.children);

    // Nachladegrenze: nicht alle Kacheln auf einmal zeigen. 216 Stueck
    // ergaben auf Mobil eine Seite von ueber 34000px - unbrauchbar zum
    // Ueberfliegen und teuer im Aufbau.
    const ERSTE_MENGE = 40;
    const NACHSCHUB = 40;
    let gezeigt = ERSTE_MENGE;

    // Werte einmal auslesen statt bei jeder Sortierung neu aus dem DOM.
    const daten = kacheln.map(el => ({
        el,
        wertung: el.dataset.wertung ? parseFloat(el.dataset.wertung) : null,
        jahr: el.dataset.jahr ? parseInt(el.dataset.jahr, 10) : null,
        gesehen: el.dataset.gesehen || '',
        titel: el.dataset.titel || ''
    }));

    // --- Sortieren ------------------------------------------------------
    // Ohne Wert immer ans Ende, egal in welche Richtung sortiert wird -
    // ein fehlendes Jahr ist keine Null.
    function vergleiche(a, b, feld) {
        if (feld === 'titel') return a.titel.localeCompare(b.titel, 'de');

        const wertA = a[feld];
        const wertB = b[feld];
        const leerA = wertA === null || wertA === '';
        const leerB = wertB === null || wertB === '';

        if (leerA && leerB) return a.titel.localeCompare(b.titel, 'de');
        if (leerA) return 1;
        if (leerB) return -1;
        if (wertA === wertB) return a.titel.localeCompare(b.titel, 'de');

        return wertA < wertB ? 1 : -1;
    }

    function sortiere(feld) {
        const reihenfolge = daten.slice().sort((a, b) => vergleiche(a, b, feld));
        // Ein DocumentFragment statt 216 einzelner Einfuegungen.
        const stapel = document.createDocumentFragment();
        reihenfolge.forEach(d => stapel.appendChild(d.el));
        raster.appendChild(stapel);
    }

    // --- Filtern --------------------------------------------------------
    const FILTER = {
        alle: () => true,
        ab4: d => d.wertung !== null && d.wertung >= 4,
        ab3: d => d.wertung !== null && d.wertung >= 3 && d.wertung < 4,
        unter3: d => d.wertung !== null && d.wertung < 3,
        ohne: d => d.wertung === null
    };

    let aktiverFilter = 'alle';

    function wende_an() {
        const pruefe = FILTER[aktiverFilter] || FILTER.alle;
        let passend = 0;
        let sichtbar = 0;

        daten.forEach(d => {
            const trifft = pruefe(d);
            // Erst der Filter, dann die Nachladegrenze: die Grenze zaehlt
            // nur die Kacheln, die zur Auswahl gehoeren.
            const zeigen = trifft && passend < gezeigt;
            if (trifft) passend++;
            d.el.hidden = !zeigen;
            if (zeigen) sichtbar++;
        });

        zaehler.textContent = passend === daten.length
            ? `${sichtbar} von ${daten.length} Filmen`
            : `${sichtbar} von ${passend} (Auswahl aus ${daten.length})`;

        leerHinweis.hidden = passend > 0;

        // Der Fuehler steht unter der letzten sichtbaren Kachel und
        // loest den Nachschub aus, sobald er in Sichtweite kommt.
        const fehltNoch = passend > sichtbar;
        fuehler.hidden = !fehltNoch;
        if (fehltNoch) {
            nachschubBeobachter.observe(fuehler);
        } else {
            nachschubBeobachter.unobserve(fuehler);
        }

        // Neu sichtbare Kacheln brauchen ihr Poster.
        beobachteOffene();
    }

    // Ein leeres Element am Ende der Liste. Kommt es in Sichtweite,
    // wird nachgelegt - kein Knopf, kein Scroll-Listener.
    const fuehler = document.createElement('div');
    fuehler.className = 'filmraster-fuehler';
    fuehler.hidden = true;
    raster.after(fuehler);

    const nachschubBeobachter = new IntersectionObserver(eintraege => {
        eintraege.forEach(eintrag => {
            if (!eintrag.isIntersecting) return;
            gezeigt += NACHSCHUB;
            wende_an();
        });
    }, { rootMargin: '400px 0px' });

    sortierung.addEventListener('change', () => {
        sortiere(sortierung.value);
        beobachteOffene();
    });

    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            aktiverFilter = chip.dataset.filter;
            // Neue Auswahl faengt wieder bei der ersten Menge an.
            gezeigt = ERSTE_MENGE;
            chips.forEach(c => {
                const aktiv = c === chip;
                c.classList.toggle('is-active', aktiv);
                c.setAttribute('aria-pressed', String(aktiv));
            });
            wende_an();
        });
    });

    // --- Poster nachladen ------------------------------------------------
    // Erst wenn eine Kachel in Sichtweite kommt. Die IDs werden kurz
    // gesammelt und gebuendelt angefragt - beim Scrollen durch ein Raster
    // waeren es sonst zweihundert Einzelanfragen.
    const offen = new Set();
    let sammlung = [];
    let zeitgeber = null;

    function fordere_an() {
        if (!sammlung.length) return;
        const ids = sammlung.splice(0, 8);

        fetch(`/api/filme/poster?ids=${ids.join(',')}`)
            .then(a => (a.ok ? a.json() : Promise.reject(a.status)))
            .then(treffer => {
                Object.entries(treffer).forEach(([id, url]) => {
                    const kachel = raster.querySelector(`[data-film="${id}"]`);
                    if (!kachel) return;

                    if (url) {
                        const bild = document.createElement('img');
                        bild.src = url;
                        bild.alt = 'Plakat: ' + kachel.querySelector('.filmkachel-titel').textContent;
                        bild.loading = 'lazy';
                        bild.decoding = 'async';
                        kachel.querySelector('.filmkachel-poster').replaceChildren(bild);
                    }
                    // Kein Poster bei TMDB: der Anfangsbuchstabe bleibt stehen.
                    offen.delete(id);
                });

                // Was ueber die Buendelgrenze hinausging, kommt gleich dran.
                if (sammlung.length) zeitgeber = setTimeout(fordere_an, 150);
            })
            .catch(() => { /* Ohne Poster bleibt der Buchstabe stehen. */ });
    }

    function melde(id) {
        if (offen.has(id) || sammlung.includes(id)) return;
        sammlung.push(id);
        clearTimeout(zeitgeber);
        zeitgeber = setTimeout(fordere_an, 120);
    }

    const posterBeobachter = new IntersectionObserver(eintraege => {
        eintraege.forEach(eintrag => {
            if (!eintrag.isIntersecting) return;
            posterBeobachter.unobserve(eintrag.target);
            melde(eintrag.target.dataset.film);
        });
    }, { rootMargin: '300px 0px' });

    function beobachteOffene() {
        daten.forEach(d => {
            if (d.el.hidden) return;
            if (d.el.querySelector('.filmkachel-poster img')) return;
            posterBeobachter.observe(d.el);
        });
    }

    // --- Start ----------------------------------------------------------
    // Beim Start einmal sortieren, nicht nur filtern: sonst bliebe die
    // Reihenfolge aus der Datenbank stehen und die Auswahl im Feld waere
    // eine Behauptung.
    sortiere(sortierung.value);
    wende_an();
})();


// ===== LADEBILDSCHIRM =====
// Ablauf: Buchstaben einzeln herein, Zaehler auf 100, kurze Pause,
// Vorhang faehrt nach oben weg, Hero faehrt ein.
//
// Ob ueberhaupt etwas laeuft, hat das Inline-Skript im Kopf entschieden
// (Klasse intro-laeuft auf <html>). Hier wird nichts mehr geprueft ausser
// dem Vorhandensein des Vorhangs - sonst koennten beide Stellen zu
// unterschiedlichen Ergebnissen kommen.
(function initIntro() {
    const wurzel = document.documentElement;
    const vorhang = document.querySelector('[data-intro]');
    const laeuft = wurzel.classList.contains('intro-laeuft');

    // Kein Intro auf dieser Seite oder in dieser Sitzung: Lenis sofort,
    // Hero ohne Sonderbehandlung.
    if (!vorhang || !laeuft) {
        starteTraegheitsScroll();
        return;
    }

    const name = vorhang.querySelector('[data-intro-name]');
    const zaehler = vorhang.querySelector('[data-intro-zaehler]');
    const heroInhalt = document.querySelector('.hero-content');

    // Gesamt rund 2,4s. Der Zaehler haengt an aufbauDauer und kommt
    // damit weiterhin genau mit dem letzten Buchstaben bei 100 an.
    const VERSATZ = 55;        // Abstand zwischen zwei Buchstaben
    const BUCHSTABE_DAUER = 550;
    const PAUSE = 400;         // bei 100 stehen bleiben
    const VORHANG_DAUER = 800; // muss zur CSS-Transition passen

    let beendet = false;

    // --- Aufraeumen -----------------------------------------------------
    // Global, damit das Sicherheitsnetz im Kopf es aufrufen kann.
    // Mehrfachaufruf ist ungefaehrlich.
    window.introBeenden = function introBeenden() {
        if (beendet) return;
        beendet = true;

        clearTimeout(window.__introNetz);

        wurzel.classList.remove('intro-laeuft');
        if (vorhang.parentNode) vorhang.parentNode.removeChild(vorhang);

        try {
            sessionStorage.setItem('intro-gesehen', '1');
        } catch (e) {
            // Privater Modus: dann laeuft das Intro eben erneut.
        }

        document.dispatchEvent(new CustomEvent('intro:fertig'));
    };

    // --- Buchstaben ------------------------------------------------------
    // Sie stehen bereits einzeln im Markup, jeder von Anfang an auf
    // opacity 0. Vorher wurden sie hier aus dem Text zerlegt - dabei
    // stand der fertige Schriftzug einen Wimpernschlag lang sichtbar da,
    // bevor das Zerlegen ihn wieder unsichtbar machte.
    const buchstaben = Array.from(name.querySelectorAll('.intro-buchstabe'));
    if (!buchstaben.length) {
        // Ohne Buchstaben gibt es nichts aufzubauen - dann sofort weiter,
        // statt hinter einem leeren Vorhang zu warten.
        window.introBeenden();
        return;
    }

    const aufbauDauer = (buchstaben.length - 1) * VERSATZ + BUCHSTABE_DAUER;

    buchstaben.forEach((span, i) => {
        setTimeout(() => span.classList.add('is-da'), i * VERSATZ);
    });

    // --- Zaehler ---------------------------------------------------------
    // Laeuft ueber die Dauer des Buchstabenaufbaus, nicht in festen
    // Schritten - so kommt er zusammen mit dem letzten Buchstaben an.
    const start = performance.now();

    function zaehlen(jetzt) {
        const anteil = Math.min((jetzt - start) / aufbauDauer, 1);
        zaehler.textContent = String(Math.round(anteil * 100)).padStart(2, '0');
        if (anteil < 1) requestAnimationFrame(zaehlen);
    }
    requestAnimationFrame(zaehlen);

    // --- Vorhang und Hero -------------------------------------------------
    setTimeout(() => {
        // Die Staffelung des Heros steht vollstaendig im CSS (Namenszug,
        // Buchstaben, Strich, Metazeilen, Buttons). Hier faellt nur noch
        // der Startschuss ueber .is-eingefahren.
        vorhang.classList.add('is-faehrt-weg');

        // Kurz nach dem Anfahren des Vorhangs, damit der Hero hinter der
        // Kante hervorkommt statt erst danach.
        setTimeout(() => {
            if (heroInhalt) heroInhalt.classList.add('is-eingefahren');
        }, 150);

        setTimeout(() => {
            window.introBeenden();
        }, VORHANG_DAUER);
    }, aufbauDauer + PAUSE);

    // Lenis erst, wenn der Vorhang weg ist.
    document.addEventListener('intro:fertig', starteTraegheitsScroll, { once: true });
})();
