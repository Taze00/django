
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
    rankingGrid: document.getElementById('ranking-grid'),
    fadeElements: document.querySelectorAll('.fade-in'),
    threeBgContainer: document.getElementById('three-bg')
};

// ===== DATA STRUCTURES =====
const galleryItems = [
    {
        id: 1,
        image: '/static/css/images/gallery/alex1.jpeg',
        title: 'Geburtstagsfeier',
        category: 'clubs'
    },
    {
        id: 2,
        image: '/static/css/images/gallery/alex2.png',
        title: 'Weiße Socken zu den Schuhen',
        category: 'clubs'
    },
    {
        id: 3,
        type: 'video',
        source: '/static/css/images/gallery/alex10.mp4',
        title: 'Klassischer Handschlag',
        category: 'clubs'
    },
    {
        id: 4,
        image: '/static/css/images/gallery/alex3.jpeg',
        title: 'Potsdam Oktoberfest',
        category: 'clubs'
    },
    {
        id: 5,
        image: '/static/css/images/gallery/alex4.jpeg',
        title: 'Baumblüte',
        category: 'people'
    },
    {
        id: 6,
        image: '/static/css/images/gallery/alex5.jpeg',
        title: 'Abend mit Freunden',
        category: 'architecture'
    },
    {
        id: 7,
        image: '/static/css/images/gallery/alex6.JPG',
        title: 'Ready machen für Berlin',
        category: 'clubs'
    },
    {
        id: 8,
        type: 'video',
        source: '/static/css/images/gallery/alex11.mp4',
        title: 'World Club Dome abkühlen',
        category: 'clubs'
    },
    {
        id: 9,
        image: '/static/css/images/gallery/alex7.jpeg',
        title: 'SMS Festival',
        category: 'people'
    },
    {
        id: 10,
        image: '/static/css/images/gallery/alex8.jpeg',
        title: 'Malle',
        category: 'architecture'
    },
    {
        id: 11,
        type: 'video',
        source: '/static/css/images/gallery/alex12.mp4',
        title: 'Aftern nach Geburtstag',
        category: 'clubs'
    },
    {
        id: 12,
        image: '/static/css/images/gallery/alex9.jpeg',
        title: 'World Club Dome',
        category: 'architecture'
    },
    {
        id: 13,
        image: '/static/css/images/gallery/alex13.jpeg',
        title: 'Berlin Bar',
        category: 'architecture'
    },
    {
        id: 14,
        image: '/static/css/images/gallery/alex14.jpg',
        title: 'Aftern nach Geburtstag',
        category: 'clubs'
    },
    {
        id: 15,
        image: '/static/css/images/gallery/alex15.jpeg',
        title: 'Aftern nach Geburtstag',
        category: 'clubs'
    },
    {
        id: 16,
        image: '/static/css/images/gallery/alex16.jpeg',
        title: 'Berlin Moment',
        category: 'clubs'
    },
    {
        id: 17,
        image: '/static/css/images/gallery/alex11.jpeg',
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

        if (item.type === 'video') {
            const video = document.createElement('video');
            video.src = item.source;
            video.muted = true;
            video.loop = true;
            video.playsInline = true;
            video.style.width = '100%';
            video.style.height = '100%';
            video.style.objectFit = 'cover';
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
            img.style.width = '100%';
            img.style.height = '100%';
            img.style.objectFit = 'cover';
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


// ===== CLUB CARDS FUNCTIONS =====
function createClubCards() {
    if (!elements.rankingGrid) return;
    
    elements.rankingGrid.innerHTML = '';
    
    // Prüfe ob Mobile
    const isMobile = window.innerWidth <= 768;
    
    clubData.forEach(club => {
        const colDiv = document.createElement('div');
        colDiv.className = 'col-lg-4 col-md-6 col-sm-12';
        
        const clubCard = document.createElement('div');
        clubCard.className = 'club-card fade-in';
        
        if (isMobile) {
            // Mobile Struktur
            const avgRating = Math.round((club.ratings.atmosphere + club.ratings.sound + club.ratings.lineup) / 3);
            
            clubCard.innerHTML = `
                <div class="club-card-header">
                    <div class="club-thumbnail">
                        <img src="${club.image}" alt="${club.name}">
                    </div>
                    <div class="club-list-info">
                        <h3>${club.name}</h3>
                        <div class="club-quick-rating">
                            <span class="stars">${getStarsFromRating(avgRating)}</span>
                            <span>${avgRating}%</span>
                        </div>
                    </div>
                    <div class="club-expand-icon">
                        <i class="fas fa-chevron-down"></i>
                    </div>
                </div>
                <div class="club-details-mobile">
                    <div class="club-details-image">
                        <img src="${club.image}" alt="${club.name}">
                        ${club.badge ? `<div class="club-badge-mobile">${club.badge}</div>` : ''}
                    </div>
                    <p class="club-desc-mobile">${club.description}</p>
                    <div class="club-ratings-mobile">
                        <div class="rating-item-mobile">
                            <div class="rating-header-mobile">
                                <span class="rating-title-mobile">Atmosphäre</span>
                                <span class="rating-value-mobile">${club.ratings.atmosphere}%</span>
                            </div>
                            <div class="rating-bar-mobile">
                                <div class="rating-fill-mobile atmosphere" style="width: 0%" data-width="${club.ratings.atmosphere}%"></div>
                            </div>
                        </div>
                        <div class="rating-item-mobile">
                            <div class="rating-header-mobile">
                                <span class="rating-title-mobile">Sound</span>
                                <span class="rating-value-mobile">${club.ratings.sound}%</span>
                            </div>
                            <div class="rating-bar-mobile">
                                <div class="rating-fill-mobile sound" style="width: 0%" data-width="${club.ratings.sound}%"></div>
                            </div>
                        </div>
                        <div class="rating-item-mobile">
                            <div class="rating-header-mobile">
                                <span class="rating-title-mobile">Lineup</span>
                                <span class="rating-value-mobile">${club.ratings.lineup}%</span>
                            </div>
                            <div class="rating-bar-mobile">
                                <div class="rating-fill-mobile lineup" style="width: 0%" data-width="${club.ratings.lineup}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Event Listener für Mobile hinzufügen
            setTimeout(() => {
                const header = clubCard.querySelector('.club-card-header');
                if (header) {
                    header.addEventListener('click', () => {
                        toggleMobileClubDetails(clubCard);
                    });
                }
            }, 100);
        } else {
            // Desktop Struktur
            clubCard.innerHTML = `
                <div class="club-image">
                    <img src="${club.image}" alt="${club.name}" loading="lazy">
                    <div class="club-badge">${club.badge}</div>
                </div>
                <div class="club-content">
                    <h3 class="club-name">${club.name}</h3>
                    <p class="club-desc">${club.description}</p>
                    
                    <div class="rating-container">
                        <div class="rating-header">
                            <span class="rating-title">Atmosphäre</span>
                            <span class="rating-value">${club.ratings.atmosphere}%</span>
                        </div>
                        <div class="rating-bar">
                            <div class="rating-fill atmosphere-fill" data-width="${club.ratings.atmosphere}%"></div>
                        </div>
                    </div>
                    
                    <div class="rating-container">
                        <div class="rating-header">
                            <span class="rating-title">Sound</span>
                            <span class="rating-value">${club.ratings.sound}%</span>
                        </div>
                        <div class="rating-bar">
                            <div class="rating-fill sound-fill" data-width="${club.ratings.sound}%"></div>
                        </div>
                    </div>
                    
                    <div class="rating-container">
                        <div class="rating-header">
                            <span class="rating-title">Lineup</span>
                            <span class="rating-value">${club.ratings.lineup}%</span>
                        </div>
                        <div class="rating-bar">
                            <div class="rating-fill lineup-fill" data-width="${club.ratings.lineup}%"></div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        colDiv.appendChild(clubCard);
        elements.rankingGrid.appendChild(colDiv);
    });
    
    setTimeout(() => {
        document.querySelectorAll('.club-card').forEach(card => {
            card.classList.add('active');
        });
    }, 300);
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

// ===== RATING BARS ANIMATION =====
function animateRatingBars() {
    if (!document.querySelector('.club-card')) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const ratingFills = entry.target.querySelectorAll('.rating-fill');
                
                ratingFills.forEach(fill => {
                    const width = fill.getAttribute('data-width');
                    setTimeout(() => {
                        fill.style.width = width;
                    }, 200);
                });
                
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });
    
    document.querySelectorAll('.club-card').forEach(card => {
        observer.observe(card);
    });
}

// ===== SMOOTH SCROLLING =====
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop,
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

// ===== MOBILE TINDER-STYLE GALLERY =====
class TinderGallery {
    constructor() {
        this.currentIndex = 0;
        this.items = galleryItems;
        this.swipedCards = [];
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
        this.currentCard = null;
        
        if (window.innerWidth <= 768) {
            this.init();
        }
    }

    init() {
        this.createTinderGallery();
        this.attachEventListeners();
    }

    createTinderGallery() {
        const gallerySection = document.querySelector('.gallery-container');
        if (!gallerySection) return;

        // Erstelle Tinder Container
        const tinderContainer = document.createElement('div');
        tinderContainer.className = 'tinder-gallery-mobile';
        tinderContainer.innerHTML = `
            <div class="tinder-card-stack" id="tinder-card-stack"></div>
            <div class="swipe-indicator left"><i class="fas fa-times"></i></div>
            <div class="swipe-indicator right"><i class="fas fa-heart"></i></div>
            <div class="tinder-end-screen" id="tinder-end-screen">
                <i class="fas fa-check-circle"></i>
                <h3>Alle Bilder gesehen!</h3>
                <p>Du hast alle Erinnerungen durchgeschaut</p>
                <button class="tinder-restart-btn" onclick="window.tinderGallery.restart()">
                    Nochmal
                </button>
            </div>
        `;

        // Füge nach dem Gallery Grid ein
        const galleryGrid = document.getElementById('gallery-grid');
        if (galleryGrid && galleryGrid.parentNode) {
            galleryGrid.parentNode.insertBefore(tinderContainer, galleryGrid);
        }

        // Erstelle Karten
        this.createCards();

        // Erstelle Action Buttons direkt in der gallery-container
        const actions = document.createElement('div');
        actions.className = 'tinder-actions';
        actions.innerHTML = `
            <button class="tinder-action-btn undo" onclick="window.tinderGallery.undo()" title="Rückgängig">
                <i class="fas fa-undo"></i>
            </button>
            <button class="tinder-action-btn nope" onclick="window.tinderGallery.swipeLeft()" title="Skip">
                <i class="fas fa-times"></i>
            </button>
            <button class="tinder-action-btn like" onclick="window.tinderGallery.swipeRight()" title="Weiter">
                <i class="fas fa-heart"></i>
            </button>
        `;
        gallerySection.appendChild(actions);
    }

    createCards() {
        const stack = document.getElementById('tinder-card-stack');
        if (!stack) return;

        stack.innerHTML = '';

        this.items.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'tinder-card';
            if (index === 0) {
                card.classList.add('is-first-card');
            }
            card.dataset.index = index;

            const isVideo = item.type === 'video';
            const mediaHtml = isVideo
                ? `<video src="${item.source || item.image}" autoplay muted loop playsinline></video>`
                : `<img src="${item.image || item.source}" alt="${item.title}" loading="eager" decoding="async">`;

            card.innerHTML = `
                ${mediaHtml}
                <div class="tinder-card-info">
                    <div class="tinder-card-counter">${index + 1} / ${this.items.length}</div>
                </div>
            `;

            stack.appendChild(card);
        });

        this.currentCard = stack.querySelector('.tinder-card:first-child');
        this.preloadNextCards();
    }

    preloadNextCards() {
        // Preload alle verbleibenden Bilder
        const startIndex = this.swipedCards.length;

        for (let idx = startIndex; idx < this.items.length; idx++) {
            const item = this.items[idx];
            if (item.type !== 'video') {
                const img = new Image();
                img.src = item.image || item.source;
            }
        }
    }

    attachEventListeners() {
        const stack = document.getElementById('tinder-card-stack');
        if (!stack) return;

        // Touch Events
        stack.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: false });
        stack.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        stack.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: false });

        // Mouse Events (für Testing)
        stack.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        document.addEventListener('mouseup', (e) => this.handleMouseUp(e));
    }

    handleTouchStart(e) {
        if (e.target.closest('.tinder-action-btn')) return;
        
        const touch = e.touches[0];
        this.startDrag(touch.clientX, touch.clientY);
        e.preventDefault();
    }

    handleTouchMove(e) {
        if (!this.isDragging) return;
        
        const touch = e.touches[0];
        this.drag(touch.clientX, touch.clientY);
        e.preventDefault();
    }

    handleTouchEnd(e) {
        if (!this.isDragging) return;
        this.endDrag();
    }

    handleMouseDown(e) {
        if (e.target.closest('.tinder-action-btn')) return;
        this.startDrag(e.clientX, e.clientY);
    }

    handleMouseMove(e) {
        if (!this.isDragging) return;
        this.drag(e.clientX, e.clientY);
    }

    handleMouseUp(e) {
        if (!this.isDragging) return;
        this.endDrag();
    }

    startDrag(x, y) {
        this.isDragging = true;
        this.startX = x;
        this.startY = y;
        this.currentCard = document.querySelector('.tinder-card:first-child');
        if (this.currentCard) {
            this.currentCard.style.transition = 'none';
        }
    }

    drag(x, y) {
        if (!this.currentCard) return;

        this.currentX = x;
        this.currentY = y;
        
        const deltaX = x - this.startX;
        const deltaY = y - this.startY;
        const rotation = deltaX * 0.1;

        this.currentCard.style.transform = `translate(${deltaX}px, ${deltaY}px) rotate(${rotation}deg)`;

        // Zeige Swipe Indikatoren
        const leftIndicator = document.querySelector('.swipe-indicator.left');
        const rightIndicator = document.querySelector('.swipe-indicator.right');

        if (Math.abs(deltaX) > 50) {
            if (deltaX < 0) {
                leftIndicator.classList.add('show');
                rightIndicator.classList.remove('show');
            } else {
                rightIndicator.classList.add('show');
                leftIndicator.classList.remove('show');
            }
        } else {
            leftIndicator.classList.remove('show');
            rightIndicator.classList.remove('show');
        }
    }

    endDrag() {
        if (!this.currentCard) return;

        this.isDragging = false;
        const deltaX = this.currentX - this.startX;

        // Swipe Threshold
        if (Math.abs(deltaX) > 100) {
            if (deltaX < 0) {
                this.animateSwipe('left');
            } else {
                this.animateSwipe('right');
            }
        } else {
            // Zurück zur Mitte
            this.currentCard.style.transition = 'transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)';
            this.currentCard.style.transform = '';
        }

        // Verstecke Indikatoren
        document.querySelectorAll('.swipe-indicator').forEach(ind => {
            ind.classList.remove('show');
        });
    }

    animateSwipe(direction) {
        if (!this.currentCard) return;

        this.currentCard.classList.add(`swiped-${direction}`);
        
        // Speichere geswiped Card
        this.swipedCards.push({
            index: parseInt(this.currentCard.dataset.index),
            direction: direction,
            element: this.currentCard
        });

        setTimeout(() => {
            if (this.currentCard && this.currentCard.parentNode) {
                this.currentCard.remove();
            }

            this.currentIndex++;
            this.currentCard = document.querySelector('.tinder-card:first-child');

            // Preload nächste Karten
            this.preloadNextCards();

            // Prüfe ob alle Karten geswiped wurden
            if (!this.currentCard) {
                this.showEndScreen();
            }
        }, 500);
    }

    swipeLeft() {
        this.currentCard = document.querySelector('.tinder-card:first-child');
        if (!this.currentCard) return;

        this.currentCard.style.transition = 'transform 0.5s ease, opacity 0.5s ease';
        this.animateSwipe('left');
    }

    swipeRight() {
        this.currentCard = document.querySelector('.tinder-card:first-child');
        if (!this.currentCard) return;

        this.currentCard.style.transition = 'transform 0.5s ease, opacity 0.5s ease';
        this.animateSwipe('right');
    }

    undo() {
        if (this.swipedCards.length === 0) return;

        const lastCard = this.swipedCards.pop();
        const stack = document.getElementById('tinder-card-stack');
        
        if (stack) {
            // Erstelle Karte neu
            const card = this.createSingleCard(lastCard.index);
            stack.insertBefore(card, stack.firstChild);
            
            // Animation
            setTimeout(() => {
                card.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
                card.classList.remove(`swiped-${lastCard.direction}`);
            }, 10);

            this.currentIndex--;
            this.currentCard = card;
        }
    }

    createSingleCard(index) {
        const item = this.items[index];
        const card = document.createElement('div');
        card.className = 'tinder-card';
        card.dataset.index = index;

        const isVideo = item.type === 'video';
        const mediaHtml = isVideo
            ? `<video src="${item.source || item.image}" autoplay muted loop playsinline></video>`
            : `<img src="${item.image || item.source}" alt="${item.title}">`;

        card.innerHTML = mediaHtml;

        return card;
    }

    showEndScreen() {
        const endScreen = document.getElementById('tinder-end-screen');
        if (endScreen) {
            endScreen.classList.add('show');
        }
    }

    restart() {
        this.currentIndex = 0;
        this.swipedCards = [];
        
        const endScreen = document.getElementById('tinder-end-screen');
        if (endScreen) {
            endScreen.classList.remove('show');
        }

        this.createCards();
        this.currentCard = document.querySelector('.tinder-card:first-child');
    }
}

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', function() {
    initVersionManagement();
    enhanceLogo();
    initScrollEvents();
    initSmoothScrolling();
    initEnhancedScrollAnimations();

    createGallery();
    setupCarouselNavigation();
    createClubCards();

    // NEU: Tinder Gallery für Mobile
    setTimeout(() => {
        initTinderGallery();
    }, 1000);

    setTimeout(() => {
        window.galleryModal = new ImprovedGallery();
    }, 600);

    setTimeout(() => {
        animateRatingBars();
    }, 1000);
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
window.createClubCards = createClubCards;
window.toggleDetails = toggleDetails;
window.galleryItems = galleryItems;

// Track Tinder Gallery initialization
let tinderGalleryInitialized = false;

// Initialisiere Tinder Gallery auf Mobile
function initTinderGallery() {
    if (window.innerWidth <= 768) {
        window.tinderGallery = new TinderGallery();
        tinderGalleryInitialized = true;
    }
}

// Helper Function für Mobile Club Cards
function getStarsFromRating(rating) {
    const fullStars = Math.floor(rating / 20);
    const halfStar = (rating % 20) >= 10;
    const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
    
    return '★'.repeat(fullStars) + 
           (halfStar ? '☆' : '') + 
           '☆'.repeat(emptyStars);
}

function toggleMobileClubDetails(card) {
    const isExpanded = card.classList.contains('expanded');
    
    // Schließe alle anderen Cards
    document.querySelectorAll('.club-card.expanded').forEach(otherCard => {
        if (otherCard !== card) {
            otherCard.classList.remove('expanded');
        }
    });
    
    // Toggle aktuelle Card
    card.classList.toggle('expanded');
    
    // Animiere die Rating-Bars wenn geöffnet
    if (!isExpanded) {
        setTimeout(() => {
            animateMobileRatingBars(card);
        }, 200);
        
        // Smooth scroll zur Card
        setTimeout(() => {
            card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }
}

function animateMobileRatingBars(card) {
    const fills = card.querySelectorAll('.rating-fill-mobile');
    fills.forEach(fill => {
        const width = fill.getAttribute('data-width');
        fill.style.width = width;
    });
}

// Track current layout state
// ===== ENHANCED SCROLL ANIMATIONS =====
function initEnhancedScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.fade-in').forEach(element => {
        observer.observe(element);
    });

    // Gallery items with enhanced animation
    document.querySelectorAll('.gallery-item').forEach((item, index) => {
        const itemObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, index * 50);
                    itemObserver.unobserve(entry.target);
                }
            });
        }, observerOptions);

        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        itemObserver.observe(item);
    });
}

let currentLayout = window.innerWidth <= 768 ? 'mobile' : 'desktop';

window.addEventListener('resize', () => {
    const newLayout = window.innerWidth <= 768 ? 'mobile' : 'desktop';
    
    if (currentLayout !== newLayout) {
        currentLayout = newLayout;
        
        // Club Cards neu erstellen
        createClubCards();
        setTimeout(() => {
            animateRatingBars();
        }, 500);
        
        // Tinder Gallery initialisieren wenn auf Mobile gewechselt wird
        if (newLayout === 'mobile' && !tinderGalleryInitialized) {
            initTinderGallery();
        }
    }
});

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
