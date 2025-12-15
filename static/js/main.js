// ===== MAIN CONFIGURATION =====
const CONFIG = {
    SITE_VERSION: '20250514-2',
    PARTICLES_COUNT: 800,
    ANIMATION_SPEED: {
        ROTATION_X: 0.0003,
        ROTATION_Y: 0.0005
    }
};

// ===== DOM ELEMENTS =====
const elements = {
    header: document.getElementById('header'),
    menuToggle: document.querySelector('.menu-toggle'),
    navLinks: document.querySelector('.nav-links'),
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
        image: '/static/css/images/gallery/alex6.jpeg',
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

const topListsData = {
    anime: [
        {
            rank: 1,
            title: 'Attack on Titan',
            rating: '★★★★★',
            description: 'Die Menschheit lebt hinter riesigen Mauern, um sich vor menschenfressenden Titanen zu schützen. Was als einfache Survival-Story beginnt, entwickelt sich zu einer komplexen Erzählung über Krieg, Rassismus und den Kreislauf der Gewalt. Jede Staffel übertrifft die vorherige.',
            platform: 'Crunchyroll',
            episodes: '87 Episoden'
        },
        {
            rank: 2,
            title: 'Hunter x Hunter',
            rating: '★★★★★',
            description: 'Gon Freecss begibt sich auf die Suche nach seinem Vater und wird dabei zum Hunter. Die Serie brilliert durch komplexe Charaktere, ein ausgeklügeltes Nen-System und Kämpfe, die mehr auf Strategie als auf rohe Kraft setzen. Der Chimera Ant Arc gilt als einer der besten Anime-Arcs aller Zeiten.',
            platform: 'Prime',
            episodes: '148 Episoden'
        },
        {
            rank: 3,
            title: 'Death Note',
            rating: '★★★★☆',
            description: 'Light Yagami findet ein Notizbuch, mit dem er jeden töten kann, dessen Namen er hineinschreibt. Der daraus entstehende Kampf zwischen Light und dem Detektiv L ist ein brillantes Katz-und-Maus-Spiel voller Wendungen und moralischer Fragen über Gerechtigkeit.',
            platform: 'Netflix',
            episodes: '37 Episoden'
        },
        {
            rank: 4,
            title: '7 Deadly Sins',
            rating: '★★★☆☆',
            description: 'Die Seven Deadly Sins sind gefallene Helden, die ein zerschlagenes Königreich retten wollen. Die Dynamik der Charaktere und die überraschenden Wendungen sorgen für ein mitreißendes Abenteuer, das süchtig macht.',
            platform: 'Netflix',
            episodes: '100 Episoden'
        },
        {
            rank: 5,
            title: 'Demon Slayer',
            rating: '★★★☆☆',
            description: 'Tanjiro Kamado wird zum Dämonenjäger, um seine in einen Dämon verwandelte Schwester zu retten. Ufotable\'s Animation setzt neue Maßstäbe, besonders in Kampfszenen. Die emotionale Geschichte und liebenswerten Charaktere machen es zu einem modernen Klassiker.',
            platform: 'Netflix',
            episodes: '44 Episoden'
        }
    ],
    movies: [
        {
            rank: 1,
            title: 'The Sixth Sense',
            rating: '★★★★★',
            description: 'Dr. Crowe ist ein angesehener Kinderpsychologe, der einem verstörten Jungen helfen soll. The Sixth Sense ist ein atmosphärisch dichter Psychothriller über Verlust, Schuld und das Unbewusste. Noch nie hat mich ein Plottwist am Ende so heftig getroffen. Mit großem Abstand mein Lieblingsfilm!',
            platform: 'Prime',
            year: '1999'
        },
        {
            rank: 2,
            title: 'The Green Mile',
            rating: '★★★★★',
            description: 'Paul Edgecomb arbeitet als Aufseher im Todestrakt, doch ein neuer Häftling stellt alles infrage, was er je für wahr hielt. The Green Mile ist ein zutiefst bewegendes Drama über Mitgefühl, Gerechtigkeit und das Übernatürliche.',
            platform: 'Prime',
            year: '1999'
        },
        {
            rank: 3,
            title: 'Shutter Island',
            rating: '★★★★★',
            description: 'Teddy Daniels ist US-Marshal und ermittelt auf einer abgelegenen Inselklinik, doch nichts ist, wie es scheint. Shutter Island ist ein packender Psychothriller über Trauma, Wahrnehmung und Wahnsinn. Das verstörende Ende entfaltet eine Wucht, die einen noch lange danach nicht loslässt.',
            platform: 'Netflix',
            year: '2010'
        },
        {
            rank: 4,
            title: 'Interstellar',
            rating: '★★★★☆',
            description: 'Cooper ist Pilot und Vater, seine Mission: das Überleben der Menschheit jenseits der Sterne. Interstellar ist ein visuell überwältigendes Sci-Fi-Epos über Zeit, Raum und die Kraft der Liebe. Hans Zimmers Score und die emotionale Tiefe machen das Finale zu einem der eindrucksvollsten der Filmgeschichte.',
            platform: 'Netflix',
            year: '2014'
        },
        {
            rank: 5,
            title: 'Joker',
            rating: '★★★★☆',
            description: 'Arthur Fleck ist ein Außenseiter in einer kalten, zerrissenen Gesellschaft. Joker ist ein düsteres Charakterporträt über Wahnsinn, Isolation und Identität. Mit einer verstörenden Intensität und Joaquin Phoenix in Höchstform hinterlässt dieser Film ein Gefühl, das lange nachwirkt.',
            platform: 'Prime',
            year: '2019'
        }
    ],
    series: [
        {
            rank: 1,
            title: 'Prison Break',
            rating: '★★★★★',
            description: 'Ein Ingenieur entwickelt einen ausgeklügelten Plan, um seinen Bruder aus dem Gefängnis zu befreien. Clevere Wendungen und psychologische Spannung in einem der besten Gefängnis-Thriller aller Zeiten.',
            platform: 'Prime',
            episodes: '90 Episoden'
        },
        {
            rank: 2,
            title: 'Haus des Geldes',
            rating: '★★★★☆',
            description: 'Ein geheimnisvoller Mastermind plant den spektakulärsten Bankraub Spaniens. Heist-Thriller mit emotionaler Tiefe und gesellschaftskritischen Untertönen, der weltweit zum Phänomen wurde.',
            platform: 'Netflix',
            episodes: '48 Episoden'
        },
        {
            rank: 3,
            title: 'From',
            rating: '★★★☆☆',
            description: 'Eine Familie strandet in einer mysteriösen Stadt, aus der niemand entkommen kann. Mystery-Horror mit psychologischen Elementen, der Spannung bis zur letzten Minute garantiert.',
            platform: 'Prime',
            episodes: '40 Episoden'
        },
        {
            rank: 4,
            title: 'The Watcher',
            rating: '★★★☆☆',
            description: 'Eine Familie zieht in ihr Traumhaus und wird von anonymen, bedrohlichen Briefen terrorisiert. Psychothriller über Paranoia und die dunklen Geheimnisse der Nachbarschaft.',
            platform: 'Netflix',
            episodes: '7 Episoden'
        },
        {
            rank: 5,
            title: 'Discounter',
            rating: '★★★☆☆',
            description: 'Das chaotische Leben in einem deutschen Discounter zwischen Sonderangeboten und sozialen Abgründen. Schwarze Komödie, die den Einzelhandel-Wahnsinn mit viel Humor entlarvt.',
            platform: 'Prime',
            episodes: '40 Episoden'
        }
    ]
};

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

// ===== MOBILE MENU =====
function initMobileMenu() {
    if (elements.menuToggle && elements.navLinks) {
        elements.menuToggle.addEventListener('click', () => {
            elements.navLinks.classList.toggle('active');
            
            const icon = elements.menuToggle.querySelector('i');
            if (elements.navLinks.classList.contains('active')) {
                icon.className = 'fas fa-times';
            } else {
                icon.className = 'fas fa-bars';
            }
        });
    }
}

// ===== SCROLL EVENTS =====
function initScrollEvents() {
    window.addEventListener('scroll', () => {
        // Header style on scroll
        if (elements.header) {
            if (window.scrollY > 100) {
                elements.header.classList.add('scrolled');
            } else {
                elements.header.classList.remove('scrolled');
            }
        }
        
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
    
    galleryItems.forEach((item, index) => {
        const galleryItem = document.createElement('div');
        galleryItem.className = 'gallery-item fade-in';
        
        const itemType = item.type || 'image';
        const itemSource = item.source || item.image;
        
        if (itemType === 'video') {
            const video = document.createElement('video');
            video.autoplay = true;
            video.muted = true;
            video.loop = true;
            video.playsInline = true;
            video.src = itemSource;
            
            galleryItem.appendChild(video);
            
            const overlay = document.createElement('div');
            overlay.className = 'gallery-overlay';
            overlay.innerHTML = `<h3 class="gallery-title">${item.title}</h3>`;
            galleryItem.appendChild(overlay);
        } else {
            galleryItem.innerHTML = `
                <img src="${itemSource}" alt="${item.title}" loading="lazy">
                <div class="gallery-overlay">
                    <h3 class="gallery-title">${item.title}</h3>
                </div>
            `;
        }
        
        elements.galleryGrid.appendChild(galleryItem);
    });
    
    setTimeout(() => {
        document.querySelectorAll('.gallery-item').forEach(item => {
            item.classList.add('active');
        });
    }, 300);
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

// ===== TOP LISTS FUNCTIONS =====
function createTopLists() {
    const categories = ['anime', 'movies', 'series'];
    const categoryTitles = ['Top 5 Anime', 'Top 5 Filme', 'Top 5 Serien'];
    const categoryIcons = ['fas fa-torii-gate', 'fas fa-film', 'fas fa-tv'];
    
    categories.forEach((category, categoryIndex) => {
        const listCategory = document.querySelector(`.list-category:nth-child(${categoryIndex + 1})`);
        if (!listCategory) return;
        
        const topList = listCategory.querySelector('.top-list');
        if (!topList) return;
        
        topList.innerHTML = '';
        
        topListsData[category].forEach(item => {
            const listItem = document.createElement('div');
            listItem.className = 'list-item';
            listItem.setAttribute('data-rank', item.rank);
            listItem.onclick = () => toggleDetails(listItem);
            
            const detailsInfo = category === 'movies' 
                ? `<span><i class="fas fa-play-circle"></i> ${item.platform}</span>
                   <span><i class="fas fa-calendar"></i> ${item.year}</span>`
                : `<span><i class="fas fa-play-circle"></i> ${item.platform}</span>
                   <span><i class="fas fa-tv"></i> ${item.episodes}</span>`;
            
            listItem.innerHTML = `
                <div class="item-main">
                    <div class="rank-number">${item.rank}</div>
                    <div class="item-content">
                        <h4>${item.title}</h4>
                        <div class="rating">
                            <span class="stars">${item.rating}</span>
                        </div>
                    </div>
                </div>
                <div class="item-details">
                    <p>${item.description}</p>
                    <div class="details-info">
                        ${detailsInfo}
                    </div>
                </div>
            `;
            
            topList.appendChild(listItem);
        });
    });
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
                
                // Close mobile menu if open
                if (elements.navLinks && elements.navLinks.classList.contains('active')) {
                    elements.navLinks.classList.remove('active');
                    const icon = elements.menuToggle.querySelector('i');
                    icon.className = 'fas fa-bars';
                }
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
            video.autoplay = false;
            video.muted = false;
            video.loop = true;
            video.src = item.source || item.image;
            video.volume = 0.2;
            video.setAttribute('playsinline', '');
            
            video.addEventListener('click', (e) => e.stopPropagation());
            
            this.modal.querySelector('.improved-modal-content').insertBefore(video, this.modalCounter);
        } else {
            this.modalMedia.style.display = 'block';
            this.modalMedia.src = item.image || item.source;
            this.modalMedia.alt = item.title;
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
                <button class="btn" onclick="window.tinderGallery.restart()">
                    <i class="fas fa-redo"></i> Nochmal
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

        // Erstelle Action Buttons
        const actions = document.createElement('div');
        actions.className = 'tinder-actions';
        actions.innerHTML = `
            <button class="tinder-action-btn undo" onclick="window.tinderGallery.undo()">
                <i class="fas fa-undo"></i>
            </button>
            <button class="tinder-action-btn nope" onclick="window.tinderGallery.swipeLeft()">
                <i class="fas fa-times"></i>
            </button>
            <button class="tinder-action-btn like" onclick="window.tinderGallery.swipeRight()">
                <i class="fas fa-heart"></i>
            </button>
        `;
        tinderContainer.appendChild(actions);
    }

    createCards() {
        const stack = document.getElementById('tinder-card-stack');
        if (!stack) return;

        stack.innerHTML = '';

        this.items.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'tinder-card';
            card.dataset.index = index;

            const isVideo = item.type === 'video';
            const mediaHtml = isVideo
                ? `<video src="${item.source || item.image}" autoplay muted loop playsinline></video>`
                : `<img src="${item.image || item.source}" alt="${item.title}">`;

            card.innerHTML = mediaHtml;

            stack.appendChild(card);
        });

        this.currentCard = stack.querySelector('.tinder-card:first-child');
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
            this.currentCard.style.transition = 'transform 0.3s ease';
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
    initMobileMenu();
    initScrollEvents();
    initSmoothScrolling();
    initEnhancedScrollAnimations();

    createGallery();
    createClubCards();
    createTopLists();

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