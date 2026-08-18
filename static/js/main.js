
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

    // Nach createGallery: die Galeriekacheln entstehen erst dort,
    // vorher gaebe es nichts zu beobachten.
    initReveals();
    initMetazeilen();

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

// ===== FILMSEKTION: "UEBERRASCH MICH" =====
// Waehlt einen zufaelligen Film aus dem Empfehlungsregal und faehrt ihn
// an: das Regal scrollt ihn in die Mitte, die Seite scrollt zu ihm,
// wenn er nicht ohnehin im Bild ist, und er leuchtet kurz auf.
//
// Kein Modal und kein Seitenwechsel - der Film steht schon da, es geht
// nur darum, ihn zu zeigen. Vorher wurde stattdessen eine Kopie der
// Kachel in einen eigenen Kasten ueber dem Regal gehaengt; damit stand
// derselbe Film zweimal auf der Seite, und das Regal, aus dem er kam,
// blieb unberuehrt.
//
// Der Stimmungsfilter stand hier ebenfalls: vier Chips, die die fuenf
// kuratierten Filme nach Stimmung aussortierten. Bei fuenf Filmen
// filterte er von fuenf auf ein oder zwei - eine Bedienung, die weniger
// zeigte als das Nichtstun. Mit dem Umbau auf vier Bloecke ist er weg.
(function initUeberrasch() {
    const knopf = document.querySelector('[data-ueberrasch]');
    if (!knopf) return;

    const regal = document.querySelector('[data-regal="empfehlungen"]');
    if (!regal) return;

    const spur = regal.querySelector('[data-regal-spur]');
    const kacheln = Array.from(regal.querySelectorAll('[data-eintrag]'));
    if (!spur || !kacheln.length) return;

    // Erst jetzt sichtbar: ohne JavaScript haette der Knopf nichts zu
    // tun, und ein Knopf, der nichts tut, ist schlimmer als keiner.
    knopf.hidden = false;

    // Bewusst als Funktion und nicht als Konstante hier oben:
    // BEWEGUNG_REDUZIERT steht weiter unten in dieser Datei, und diese
    // IIFE laeuft sofort - ein Zugriff von hier aus liefe in die
    // temporale Totzone und wuerde alles danach mitreissen.
    const weich = () =>
        window.matchMedia('(prefers-reduced-motion: reduce)').matches
            ? 'auto'
            : 'smooth';

    let leuchtet = null;   // haengt gerade im Licht
    let zuletzt = null;    // zuletzt gezogen, auch wenn das Licht aus ist
    let aufraeumen = null;

    function anfahren(kachel) {
        // Waagerecht: die Kachel in die Mitte der Spur. Nur die Spur
        // bewegt sich, nicht die Seite - sie traegt data-lenis-prevent.
        const ziel = kachel.offsetLeft - (spur.clientWidth - kachel.offsetWidth) / 2;
        spur.scrollTo({
            left: Math.max(0, ziel),
            behavior: weich()
        });

        // Senkrecht nur, wenn das Regal nicht ohnehin im Bild steht.
        // Sonst ruckte die Seite bei jedem Klick, obwohl schon alles zu
        // sehen ist.
        const kasten = regal.getBoundingClientRect();
        const drin = kasten.top >= 80 && kasten.bottom <= window.innerHeight;
        if (!drin) {
            // Laeuft Lenis, muss der Sprung durch Lenis gehen - sonst
            // sind es zwei Animationen auf derselben Position.
            if (window.lenis) {
                window.lenis.scrollTo(regal, { offset: KOPF_VERSATZ });
            } else {
                window.scrollTo({
                    top: regal.getBoundingClientRect().top + window.scrollY + KOPF_VERSATZ,
                    behavior: weich()
                });
            }
        }
    }

    function hervorheben(kachel) {
        // Ein vorheriger Treffer leuchtet sonst weiter, waehrend der
        // naechste schon anfaengt.
        if (aufraeumen) clearTimeout(aufraeumen);
        if (leuchtet) leuchtet.classList.remove('is-ueberrascht');

        // Neu anstossen: dieselbe Klasse ein zweites Mal zu setzen
        // startet die Animation nicht neu. Ein erzwungener Umbruch
        // dazwischen tut es.
        void kachel.offsetWidth;
        kachel.classList.add('is-ueberrascht');

        leuchtet = kachel;
        zuletzt = kachel;
        aufraeumen = setTimeout(() => {
            kachel.classList.remove('is-ueberrascht');
            leuchtet = null;
        }, 2600);
    }

    knopf.addEventListener('click', () => {
        // Nicht zweimal hintereinander derselbe Film - bei 40 Kacheln
        // faellt eine Wiederholung sofort auf und sieht kaputt aus.
        let auswahl = kacheln;
        if (kacheln.length > 1 && zuletzt) {
            auswahl = kacheln.filter(k => k !== zuletzt);
        }

        const treffer = auswahl[Math.floor(Math.random() * auswahl.length)];
        anfahren(treffer);
        hervorheben(treffer);
    });
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


// ===== HERO-PARALLAXE =====
// Drei Ebenen, drei Geschwindigkeiten - von hinten nach vorn immer
// schneller:
//
//   Foto + Sterne  Faktor  0.025  langsamst
//   Text           Faktor  0.012  mittel
//   Stadt          Faktor  0      schnellst, laeuft mit der Seite
//
// Der Faktor ist die Verschiebung nach UNTEN je gescrollten Pixel, er
// arbeitet also gegen das Scrollen: die Ebene bewegt sich mit
// (1 - Faktor) der Seitengeschwindigkeit. Ein groesserer Faktor heisst
// darum langsamer, nicht schneller - 0.025 laeuft mit 97.5%, 0.012 mit
// 98.8%, die vorderste Ebene bei 0 mit 100%.
//
// Warum die Werte so klein sind - kleiner als die 0.14/0.06/-0.10, die
// hier bis August 2026 standen:
//
// .hero-foto und .hero-stadt zeigen DASSELBE Foto und liegen im
// Ruhezustand pixelgenau uebereinander (siehe CSS, "Die zwei Ebenen aus
// einer Datei"). Beim Scrollen loest die Parallaxe diese Deckung auf -
// das ist gewollt, genau daher kommt die Tiefe. Aber der Abstand
// waechst mit der Differenz der Faktoren mal der Scrollstrecke, und
// sobald er gross genug wird, liest man ihn nicht mehr als Tiefe,
// sondern als zwei Skylines nebeneinander. Bei 0.025 gegen 0 sind es
// nach 400px Scrollen 10px Versatz. Wer hier dreht, dreht am
// Doppelbild - sehr dezent bleiben.
//
// Die Werte waren einmal doppelt so hoch. Sie mussten runter, als der
// Schleier auf .hero-foto von 0.70 auf 0.15 fiel: solange die hintere
// Ebene fast schwarz war, verdeckte die Dunkelheit das Auseinander-
// laufen: bei 20px Versatz stand ueber der hellen Dachlinie eine
// zweite, dunklere - besonders am rechten Bildrand. Sichtbar wurde der
// Fehler also nicht durch die Parallaxe, sondern durch das hellere
// Foto. Wer den Schleier wieder anzieht, darf die Faktoren mit
// anziehen.
//
// Keine Ebene reisst dabei eine Luecke auf, deshalb braucht es die
// frueheren Fuellflaechen (.hero-boden) nicht mehr: die vorderste Ebene
// steht mit Faktor 0 still zum Hero, und die hinterste wandert nach
// unten, ihr oberer Rand bleibt bei 0.05 immer oberhalb des Viewports.
// Sichtbar wuerde er erst ab Faktor 1.
//
// Verschoben wird ueber die eigenstaendige translate-Eigenschaft, nicht
// ueber transform: .hero-content traegt das translateY der
// fade-in-Klasse und der Scroll-Pfeil sein translateX. Eine Zuweisung
// an transform wuerde das ueberschreiben - translate legt sich davor,
// ohne es anzufassen.
//
// Namenszug und Metazeile werden einzeln verschoben statt gemeinsam
// ueber einen Wrapper: sie liegen auf verschiedenen z-index-Ebenen,
// weil die freigestellte Stadt zwischen ihnen steht (siehe CSS, "Die
// Ebenen des Hero"). Der gemeinsame Faktor haelt sie trotzdem als eine
// Ebene zusammen.
function starteHeroParallaxe() {
    if (BEWEGUNG_REDUZIERT) return;

    // Auf schmalen Fenstern nicht: dort liefert das native Scrollen
    // beim Nachlaufen zu wenige Ereignisse, die Ebenen ruckeln mehr,
    // als der Effekt bei der Fenstergroesse hergibt.
    if (window.matchMedia('(max-width: 600px)').matches) return;

    const hero = document.querySelector('.hero');
    if (!hero) return;

    // Je Faktor die Elemente, die sich damit bewegen. Die vorderste
    // Ebene .hero-stadt steht hier nicht: ihr Faktor ist 0, sie laeuft
    // also mit der Seite und braucht kein translate. Sie ist trotzdem
    // die schnellste der drei.
    const ebenen = [
        [0.025, hero.querySelectorAll('.hero-foto, .hero-bg')],
        [0.012, hero.querySelectorAll('.hero-content, .hero-meta-zeile')]
    ].filter(([, knoten]) => knoten.length);
    if (!ebenen.length) return;

    let angefordert = false;

    function zeichnen() {
        angefordert = false;
        // Auf die Hoehe des Hero geklemmt statt abgebrochen: darueber
        // hinaus ist er ohnehin aus dem Bild, und der Wert bleibt am
        // Rand richtig. Ein blosses `return` wuerde die Ebenen auf dem
        // letzten gezeichneten Stand einfrieren - bei einem grossen
        // Sprung also mitten in der Bewegung.
        const y = Math.min(window.scrollY || window.pageYOffset || 0,
                           hero.offsetHeight);

        for (const [faktor, knoten] of ebenen) {
            const versatz = `0 ${(y * faktor).toFixed(2)}px`;
            for (const el of knoten) el.style.translate = versatz;
        }
    }

    window.addEventListener('scroll', () => {
        if (angefordert) return;
        angefordert = true;
        requestAnimationFrame(zeichnen);
    }, { passive: true });

    zeichnen();
}

starteHeroParallaxe();


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
        ['.gallery-grid', '.gallery-item'],
        ['.films-filter', ':scope > *'],
        ['.rezensionen', ':scope > *'],
        ['.kanalliste', ':scope > *']
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
        '.films-claim',
        '.regal',
        '.films-quelle',
        '.films-attribution',
        '.impressumtext',
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

    // Skills: eine Gruppe nach der anderen, Marke kurz vor ihrem Band.
    // Ueber GRUPPEN liefe der Zaehler in jeder Gruppe wieder bei 0 los,
    // dann kaemen alle drei Marken gleichzeitig und der Eindruck von
    // drei Bereichen ginge verloren. Deshalb ein eigener Grundverzug.
    //
    // Frueher standen hier Chips und wurden einzeln gestaffelt. Es sind
    // jetzt Laufbaender - ein Band als Ganzes, sonst faehrt die Zeile in
    // Stuecken ein, waehrend sie schon laeuft.
    const SKILL_GRUPPE_MS = 220;
    const SKILL_BAND_MS = 90;
    document.querySelectorAll('.skills-gruppe').forEach((gruppe, gi) => {
        const grundverzug = gi * SKILL_GRUPPE_MS;

        const marke = gruppe.querySelector('.skills-marke');
        if (marke) {
            marke.style.setProperty('--reveal-verzug', `${grundverzug}ms`);
            ziele.push(marke);
        }

        const band = gruppe.querySelector('.skills-band');
        if (band) {
            band.style.setProperty('--reveal-verzug', `${grundverzug + SKILL_BAND_MS}ms`);
            ziele.push(band);
        }
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


// ===== ANSPRINGEN WIE EINE NEONROEHRE =====
// Die Sektions-Metazeilen und das Neonschild der Filmsektion zucken
// beim Sichtbarwerden zwei-, dreimal in der Helligkeit und stehen dann
// ruhig. Einmalig, nicht dauerhaft - deshalb wird jedes Element nach
// dem ersten Mal nicht mehr beobachtet.
//
// Ein eigener Beobachter statt der Reveal-Mechanik: die Zeile soll
// anspringen, wenn sie selbst im Bild ist, nicht wenn ihr Behaelter es
// ist.
//
// Die Hero-Metazeilen kommen nur dazu, wenn kein Intro laeuft - beim
// zweiten Aufruf in derselben Sitzung. Laeuft eins, wuerden sie hinter
// dem Vorhang anspringen; dann haengt das Anspringen im CSS an der
// Intro-Staffelung (.is-eingefahren) statt an dieser Klasse.
function initMetazeilen() {
    if (BEWEGUNG_REDUZIERT) return;
    if (typeof IntersectionObserver !== 'function') return;

    // Nur noch die Metazeilen. Das Neonschild der Filmsektion hing hier
    // mit drin und ist einer normalen Ueberschrift gewichen - eine
    // Ueberschrift, die anspringt wie eine Roehre, waere ein Effekt
    // ohne Anlass.
    const wahl = document.documentElement.classList.contains('intro-laeuft')
        ? '.sektion-meta'
        : '.sektion-meta, .hero-meta-zeile';

    const zeilen = document.querySelectorAll(wahl);
    if (!zeilen.length) return;

    const beobachter = new IntersectionObserver(eintraege => {
        eintraege.forEach(eintrag => {
            if (!eintrag.isIntersecting) return;
            eintrag.target.classList.add('is-angesprungen');
            beobachter.unobserve(eintrag.target);
        });
    }, { threshold: 0.6 });

    zeilen.forEach(zeile => beobachter.observe(zeile));
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
// Eigenes Auswahlelement (Knopf plus Liste) als Ersatz fuer <select>.
// Ein natives Auswahlfeld laesst nur den zugeklappten Knopf gestalten;
// die aufgeklappte Liste zeichnet das Betriebssystem, weiss mit blauer
// Markierung mitten in einer dunklen Seite. Dagegen hilft kein CSS.
//
// Gibt { wert, aufWechsel } zurueck. Die Auswahl meldet sich ueber
// einen Rueckruf statt ueber ein 'change'-Ereignis - es ist kein
// Formularfeld, und ein nachgebautes change waere eine Behauptung.
//
// Tastatur: Pfeil hoch/runter bewegt die Vorauswahl, Pos1/Ende
// springen an die Enden, Enter und Leertaste uebernehmen, Escape
// bricht ab. Der Fokus liegt waehrenddessen auf der Liste, die
// Vorauswahl wandert ueber aria-activedescendant - so muss nicht jede
// Option einzeln fokussierbar sein.
function initAuswahl(wurzel) {
    if (!wurzel) return null;

    const knopf = wurzel.querySelector('[data-auswahl-knopf]');
    const liste = wurzel.querySelector('[data-auswahl-liste]');
    const optionen = Array.from(liste.querySelectorAll('[role="option"]'));
    const anzeige = knopf.querySelector('.auswahl-wert');
    if (!knopf || !liste || !optionen.length) return null;

    let wert = (optionen.find(o => o.getAttribute('aria-selected') === 'true')
                || optionen[0]).dataset.wert;
    let vorwahl = 0;
    let rueckruf = null;

    function istOffen() {
        return !liste.hidden;
    }

    function zeigeVorwahl(i) {
        vorwahl = Math.max(0, Math.min(optionen.length - 1, i));
        optionen.forEach((o, n) => o.classList.toggle('is-vorgewaehlt', n === vorwahl));
        liste.setAttribute('aria-activedescendant', optionen[vorwahl].id);
        // Bei vielen Eintraegen laege die Vorauswahl sonst ausserhalb.
        optionen[vorwahl].scrollIntoView({ block: 'nearest' });
    }

    function oeffne() {
        if (istOffen()) return;
        liste.hidden = false;
        knopf.setAttribute('aria-expanded', 'true');
        zeigeVorwahl(optionen.findIndex(o => o.dataset.wert === wert));
        liste.focus();
    }

    // zurueckZumKnopf steuert, ob der Fokus zurueckspringt: beim
    // Schliessen per Tastatur oder Klick auf eine Option ja, beim Klick
    // irgendwohin ausserhalb nicht - dort will man dahin, wohin man
    // geklickt hat.
    function schliesse(zurueckZumKnopf) {
        if (!istOffen()) return;
        liste.hidden = true;
        knopf.setAttribute('aria-expanded', 'false');
        liste.removeAttribute('aria-activedescendant');
        optionen.forEach(o => o.classList.remove('is-vorgewaehlt'));
        if (zurueckZumKnopf) knopf.focus();
    }

    function waehle(i) {
        const option = optionen[i];
        if (!option) return;
        const neu = option.dataset.wert;
        optionen.forEach(o => o.setAttribute('aria-selected', String(o === option)));
        anzeige.textContent = option.textContent.trim();
        const geaendert = neu !== wert;
        wert = neu;
        if (geaendert && rueckruf) rueckruf(wert);
    }

    knopf.addEventListener('click', () => {
        istOffen() ? schliesse(true) : oeffne();
    });

    // Aufklappen direkt aus dem Knopf heraus, ohne Umweg ueber den Klick.
    knopf.addEventListener('keydown', e => {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp' || e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            oeffne();
        }
    });

    liste.addEventListener('keydown', e => {
        switch (e.key) {
            case 'ArrowDown': e.preventDefault(); zeigeVorwahl(vorwahl + 1); break;
            case 'ArrowUp':   e.preventDefault(); zeigeVorwahl(vorwahl - 1); break;
            case 'Home':      e.preventDefault(); zeigeVorwahl(0); break;
            case 'End':       e.preventDefault(); zeigeVorwahl(optionen.length - 1); break;
            case 'Enter':
            case ' ':
                e.preventDefault();
                waehle(vorwahl);
                schliesse(true);
                break;
            case 'Escape':
                e.preventDefault();
                schliesse(true);
                break;
            case 'Tab':
                // Nicht abfangen: Tab soll weiterfuehren, nur zu darf es.
                schliesse(false);
                break;
        }
    });

    optionen.forEach((option, i) => {
        option.addEventListener('click', () => {
            waehle(i);
            schliesse(true);
        });
        option.addEventListener('mousemove', () => zeigeVorwahl(i));
    });

    document.addEventListener('pointerdown', e => {
        if (!wurzel.contains(e.target)) schliesse(false);
    });

    return {
        get wert() { return wert; },
        aufWechsel(fn) { rueckruf = fn; }
    };
}


(function initFilmraster() {
    const raster = document.querySelector('[data-filmraster]');
    if (!raster) return;

    const steuerung = document.querySelector('[data-filmsteuerung]');
    const sortierung = initAuswahl(steuerung.querySelector('[data-auswahl]'));
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

    sortierung.aufWechsel(neuerWert => {
        sortiere(neuerWert);
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
    sortiere(sortierung.wert);
    wende_an();
})();


// ===== SEITE /filme/: REZENSIONEN KUERZEN =====
// Die Texte stehen ungekuerzt im Markup. Gekuerzt wird erst hier - ohne
// JavaScript soll alles lesbar bleiben, statt hinter einem
// "Weiterlesen" zu verschwinden, das dann niemand aufklappen kann.
//
// Gekuerzt wird nur, was tatsaechlich ueber vier Zeilen geht: gemessen
// wird mit gesetzter Klasse, ein Einzeiler bekommt so keinen Knopf fuer
// nichts.
(function initRezensionen() {
    const texte = Array.from(document.querySelectorAll('[data-rezension-text]'));
    if (!texte.length) return;

    // Toleranz gegen Rundung: ein Text, der die vier Zeilen um ein paar
    // Bruchteile ueberragt, ist keiner zum Aufklappen.
    const TOLERANZ = 8;

    function baue() {
        texte.forEach((text, i) => {
            text.classList.add('is-gekuerzt');

            if (text.scrollHeight <= text.clientHeight + TOLERANZ) {
                text.classList.remove('is-gekuerzt');
                return;
            }

            if (!text.id) text.id = `rezension-text-${i + 1}`;

            const knopf = document.createElement('button');
            knopf.type = 'button';
            knopf.className = 'rezension-mehr';
            knopf.textContent = 'Weiterlesen';
            knopf.setAttribute('aria-expanded', 'false');
            knopf.setAttribute('aria-controls', text.id);

            knopf.addEventListener('click', () => {
                const offen = !text.classList.toggle('is-gekuerzt');
                knopf.setAttribute('aria-expanded', String(offen));
                knopf.textContent = offen ? 'Weniger' : 'Weiterlesen';
            });

            text.insertAdjacentElement('afterend', knopf);
        });
    }

    // Erst messen, wenn die Schrift steht. Vorher rechnet der Browser mit
    // der Ersatzschrift - die Zeilen brechen anders, und ein Text kann
    // damit vier Zeilen ueberschreiten, den er mit IBM Plex gar nicht
    // fuellt (oder umgekehrt).
    if (document.fonts && document.fonts.ready) {
        document.fonts.ready.then(baue);
    } else {
        baue();
    }
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
        // Die Staffelung des Heros steht vollstaendig im CSS (Marke,
        // Buchstaben der Treppe, Metazeile). Hier faellt nur noch der
        // Startschuss ueber .is-eingefahren.
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
