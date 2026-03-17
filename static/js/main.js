// ===== RANKINGS DATA =====
// HIER KANNST DU DIE POSTER URLS UND IMDB LINKS ÄNDERN
// Format für jeden Eintrag:
// { rank: 1, title: 'Filmname', year: 2023, rating: '9.2', length: '120min', description: '...', platform: 'Netflix', imdb: 'https://www.imdb.com/title/ttXXXXXX/', poster: '/static/css/images/movie/poster-name.jpg' }
//
// POSTER BILDER:
// 1. Speichere deine Bilder im Ordner: /static/css/images/movie/
// 2. Trage den Pfad ein: '/static/css/images/movie/dein-bild.jpg'
// 3. Empfohlene Größe: 336×500px (2:3 Seitenverhältnis)
//
// IMDb Link: Format ist https://www.imdb.com/title/ttXXXXXX/
// Die ttXXXXXX ist die IMDb ID (kannst du auf imdb.com finden)

const RANKINGS = {
    movies: [
        { rank: 1, title: 'The Sixth Sense', year: 1999, rating: '9.5', length: '107min', genre: 'Thriller', description: 'Unvergesslicher Twist, meisterhaft gemacht, Gänsehaut beim Schauen.', platform: 'Amazon Prime', imdb: 'https://www.imdb.com/title/tt0167404/', poster: '/static/css/images/movie/the-sixth-sense.jpeg' },
        { rank: 2, title: 'Fight Club', year: 1999, rating: '9.2', length: '139min', genre: 'Thriller', description: 'Tiefgründige Fragen aufs Leben mit David Fincher, der zum Denken anregt.', platform: 'Amazon Prime', imdb: 'https://www.imdb.com/title/tt0137523/', poster: '/static/css/images/movie/fightclub.png' },
        { rank: 3, title: 'Prisoners', year: 2013, rating: '9.1', length: '153min', genre: 'Thriller', description: 'Meisterhafte Darstellungen, unfassbar wie echte Eltern reagieren.', platform: 'Netflix', imdb: 'https://www.imdb.com/title/tt1392214/', poster: '/static/css/images/movie/prisoners.png' },
        { rank: 4, title: 'The Green Mile', year: 1999, rating: '9.0', length: '189min', genre: 'Drama', description: 'Emotional und tiefgründig, ein Film, der einen nicht mehr loslässt.', platform: 'Amazon Prime', imdb: 'https://www.imdb.com/title/tt0120689/', poster: '/static/css/images/movie/thegreenmile.png' },
        { rank: 5, title: 'Das Streben nach Glück', year: 2006, rating: '8.8', length: '117min', genre: 'Drama', description: 'Inspirierend und emotional, eine wahre Geschichte über Hoffnung und Durchhaltevermögen.', platform: 'Netflix', imdb: 'https://www.imdb.com/title/tt0454921/', poster: '/static/css/images/movie/das_streben_nach_glück.png' },
        { rank: 6, title: 'Interstellar', year: 2014, rating: '8.7', length: '169min', genre: 'Sci-Fi', description: 'Visuelle Wucht kombiniert mit emotionalem Storytelling und der besten Filmmusik.', platform: 'Amazon Prime', imdb: 'https://www.imdb.com/title/tt0816692/', poster: '/static/css/images/movie/interstellar.png' },
        { rank: 7, title: 'In Time', year: 2011, rating: '8.0', length: '109min', genre: 'Sci-Fi', description: 'Spannender Plot mit interessantem Konzept, Zeit als Währung.', platform: 'Disney+ / Prime', imdb: 'https://www.imdb.com/title/tt1637688/', poster: '/static/css/images/movie/InTime.png' },
        { rank: 8, title: 'The Prestige', year: 2006, rating: '8.5', length: '130min', genre: 'Mystery', description: 'Meisterhafter Thriller über zwei Magier und ihren obsessiven Wettkampf.', platform: 'Amazon Prime', imdb: 'https://www.imdb.com/title/tt0482571/', poster: '/static/css/images/movie/thePrestige.png', isFavorite: true },
        { rank: 9, title: 'Train Dreams', year: 2023, rating: '8.5', length: '127min', genre: 'Drama', description: 'Tiefgründig über Träume und Verlust, emotional überwältigend.', platform: 'Netflix', imdb: 'https://www.imdb.com/de/title/tt29768334/', poster: '/static/css/images/movie/traindreams.png' }
    ],
    series: [
        { rank: 1, title: 'Prison Break', year: 2005, rating: '9.4', length: '5 Staffeln', genre: 'Thriller', description: 'Durchgehend spannend, echtes Meisterwerk der Serienwelt.', platform: 'Amazon Prime', imdb: 'https://www.imdb.com/title/tt0455275/', poster: '/static/css/images/movie/prisonbreak.png' },
        { rank: 2, title: 'Haus des Geldes', year: 2017, rating: '9.1', length: '5 Staffeln', genre: 'Heist', description: 'Eine verdammt geile Idee mit unverwechselbaren Charakteren und packenden Wendungen.', platform: 'Netflix', imdb: 'https://www.imdb.com/title/tt6468322/', poster: '/static/css/images/movie/hausdesgeldes.png' },
        { rank: 3, title: 'From', year: 2022, rating: '9.0', length: '3 Staffeln', genre: 'Mystery', description: 'Mysteriös und atmosphärisch, ständig neue Fragen.', platform: 'Amazon Prime', imdb: 'https://www.imdb.com/title/tt9813792/', poster: '/static/css/images/movie/from.png' },
        { rank: 4, title: 'The Watcher', year: 2022, rating: '8.7', length: '1 Staffel', genre: 'Thriller', description: 'Ryan Murphy Thriller über Obsession und Paranoia mit einem verrückten Ende.', platform: 'Netflix', imdb: 'https://www.imdb.com/de/title/tt14852808/', poster: '/static/css/images/movie/the-watcher_cover.png' },
        { rank: 5, title: 'Solange wir lügen', year: 2024, rating: '8.5', length: '8 Episoden', genre: 'Drama', description: 'Spannend über Geheimnisse und Verrat, überraschend.', platform: 'Amazon Prime', imdb: 'https://www.imdb.com/de/title/tt3914054/', poster: '/static/css/images/movie/solangewirlügen.png' },
        { rank: 6, title: 'Discounter', year: 2022, rating: '8.0', length: '2 Staffeln', genre: 'Comedy', description: 'Mal was Anderes, echt lustig mit genau meinem Humor.', platform: 'Amazon Prime', imdb: 'https://www.imdb.com/de/title/tt16463942/', poster: '/static/css/images/movie/Discounter.png' },
        { rank: 7, title: 'Sons of Anarchy', year: 2008, rating: '8.6', length: '7 Staffeln', genre: 'Crime Drama', description: 'Düstere, fesselnde Serie über Motorrad-Gangs mit starken Charakteren.', platform: 'Disney+', imdb: 'https://www.imdb.com/title/tt1124373/', poster: '/static/css/images/movie/SonsofAnarchy.png' },
        { rank: 8, title: 'Stranger Things', year: 2016, rating: '8.4', length: '4 Staffeln', genre: 'Sci-Fi Horror', description: 'Nostalgisch, spannend und atmosphärisch mit großartigen Charakteren.', platform: 'Netflix', imdb: 'https://www.imdb.com/title/tt4574334/', poster: '/static/css/images/movie/StrangerThings.png' },
        { rank: 9, title: 'Black Mirror', year: 2011, rating: '8.8', length: '6 Staffeln', genre: 'Sci-Fi Thriller', description: 'Dystopische Episoden über Technologie und ihre Auswirkungen auf die Gesellschaft.', platform: 'Netflix', imdb: 'https://www.imdb.com/title/tt2085059/', poster: '/static/css/images/movie/BlackMirror.png' },
        { rank: 10, title: 'Das Damen Gambit', year: 2020, rating: '8.4', length: '1 Staffel', genre: 'Drama', description: 'Fesselnde Serie über eine junge Schachspielerin und ihren Aufstieg.', platform: 'Netflix', imdb: 'https://www.imdb.com/de/title/tt10048342/?ref_=nv_sr_srsg_0_tt_2_nm_0_in_0_q_Das%20Damengamb', poster: '/static/css/images/movie/DasDamengambit.png' },
        { rank: 11, title: 'Sie weiß von dir', year: 2023, rating: '8.2', length: '8 Episoden', genre: 'Thriller', description: 'Psychologischer Thriller über Obsession und gefährliche Lügen.', platform: 'Netflix', imdb: 'https://www.imdb.com/de/title/tt9698442/?ref_=nv_sr_srsg_0_tt_5_nm_3_in_0_q_Sie%20weis%20von%20dir', poster: '/static/css/images/movie/Siewiesvondir.png' },
        { rank: 12, title: 'Sherlock', year: 2010, rating: '9.1', length: '4 Staffeln', genre: 'Crime Drama', description: 'Moderner Detektiv Sherlock Holmes mit brillanten Wendungen und scharfsinnigen Fällen.', platform: 'Netflix', imdb: 'https://www.imdb.com/de/title/tt1475582/?ref_=nv_sr_srsg_3_tt_8_nm_0_in_0_q_Sherlock', poster: '/static/css/images/movie/Sherlock.png', isFavorite: true }
    ],
    anime: [
        { rank: 1, title: 'Attack on Titan', year: 2013, rating: '9.9', length: '4 Staffeln', genre: 'Action', description: 'Immer spannend, unglaubliche Plottwists, absolutes Meisterwerk.', platform: 'Crunchyroll', imdb: 'https://www.imdb.com/title/tt2560140/', poster: '/static/css/images/movie/attackontitan.png' },
        { rank: 2, title: 'Hunter x Hunter', year: 2011, rating: '9.4', length: '6 Staffeln', genre: 'Adventure', description: 'Sehr cool, macht dich wach, willst was Großes erreichen.', platform: 'Crunchyroll', imdb: 'https://www.imdb.com/title/tt2098220/', poster: '/static/css/images/movie/hunterxhunter.png' },
        { rank: 3, title: 'Death Note', year: 2006, rating: '9.0', length: '2 Staffeln', genre: 'Thriller', description: 'Hin und her mit Tricks, pure Spannung auf höchstem Niveau.', platform: 'Netflix', imdb: 'https://www.imdb.com/title/tt0877057/', poster: '/static/css/images/movie/DEATH_NOTE.png' },
        { rank: 4, title: 'Vinland Saga', year: 2019, rating: '8.9', length: '2 Staffeln', genre: 'Action', description: 'Wikinger-Epos mit beeindruckender Charakterentwicklung und dem besten Antagonisten. Fesselndes Storytelling vom Anfang bis zum Ende.', platform: 'Netflix', imdb: 'https://www.imdb.com/de/title/tt10233448/?ref_=nv_sr_srsg_0_tt_8_nm_0_in_0_q_Vinland%20Saga', poster: '/static/css/images/movie/VinlandSaga.png' },
        { rank: 5, title: '7 Deadly Sins', year: 2014, rating: '8.2', length: '5 Staffeln', genre: 'Fantasy', description: 'Ich feier die Charaktere und die Story, einfach solid durchzuschauen.', platform: 'Netflix', imdb: 'https://www.imdb.com/de/title/tt3909224/', poster: '/static/css/images/movie/7deadlysins.png' },
        { rank: 6, title: 'Demon Slayer', year: 2019, rating: '7.8', length: '4 Staffeln', genre: 'Action', description: 'Wahnsinn Animationen, emotional, unforgettable Kämpfe.', platform: 'Netflix', imdb: 'https://www.imdb.com/title/tt9335498/', poster: '/static/css/images/movie/DemonSlayer.png' },
        { rank: 7, title: 'My Hero Academia', year: 2016, rating: '7.6', length: '7 Staffeln', genre: 'Action', description: 'Viele Charaktere und die sind alle wichtig, gute Story mit guter Action.', platform: 'Crunchyroll', imdb: 'https://www.imdb.com/title/tt5626028/', poster: '/static/css/images/movie/myheroacademia.png' },
        { rank: 8, title: 'Fullmetal Alchemist: Brotherhood', year: 2009, rating: '9.1', length: '5 Staffeln', genre: 'Action', description: 'Meisterwerk über zwei Brüder und ihre Reise zur Wiedererlangung ihres Körpers.', platform: 'Netflix', imdb: 'https://www.imdb.com/de/title/tt1355642/?ref_=nv_sr_srsg_0_tt_8_nm_0_in_0_q_Fullmetal', poster: '/static/css/images/movie/FullmetalAlchimistBrotherhood.png', isFavorite: true }
    ]
};

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
    galleryItems.forEach((item, index) => {
        const galleryItem = document.createElement('div');
        galleryItem.className = 'gallery-item';

        if (item.type === 'video') {
            const video = document.createElement('video');
            video.src = item.source;
            video.autoplay = true;
            video.muted = true;
            video.loop = true;
            video.playsInline = true;
            video.style.width = '100%';
            video.style.height = '100%';
            video.style.objectFit = 'cover';
            galleryItem.appendChild(video);
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

        galleryItem.addEventListener('click', () => {
            const source = item.source || item.image;
            openImageModal(source, index);
        });
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

function openImageModal(imageSrc, index) {
    const modal = document.getElementById('improved-modal');
    const modalMedia = document.getElementById('improved-modal-media');
    const modalCounter = document.getElementById('improved-modal-counter');

    if (modal && modalMedia) {
        modalMedia.src = imageSrc;
        modal.classList.add('active');
        if (modalCounter) {
            modalCounter.textContent = `${index + 1} / ${galleryItems.length}`;
        }
    }
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

// ===== RANKINGS FUNCTIONS =====

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

// ===== RANKINGS INITIALIZATION =====
function initRankings() {
    const container = document.getElementById('rankings-container');
    const tabs = document.querySelectorAll('.rankings-tab-btn');
    const rankingCategory = document.getElementById('ranking-category');

    if (!container || tabs.length === 0) return;

    let currentCategory = 'movies';

    const categoryLabels = {
        movies: 'Film',
        series: 'Serien',
        anime: 'Anime'
    };

    // Funktion zum Konvertieren von Minuten zu h:min Format
    function formatLength(length) {
        // Wenn es schon "X Staffeln" ist, nicht konvertieren
        if (length.includes('Staffel')) {
            return length;
        }

        // Wenn es "XXXmin" ist, konvertieren
        if (length.includes('min')) {
            const minutes = parseInt(length);
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;
            return `${hours}h${mins}min`;
        }

        return length;
    }

    function renderRankings(category) {
        const items = RANKINGS[category];
        const top5 = items.slice(0, 5);
        const allRecommendations = items.slice(5);
        // Sort recommendations so favorites appear first
        const recommendations = allRecommendations.sort((a, b) => {
            if (a.isFavorite && !b.isFavorite) return -1;
            if (!a.isFavorite && b.isFavorite) return 1;
            return 0;
        });

        // Render Top 5
        container.innerHTML = top5.map(item => `
            <div class="ranking-item">
                <div class="ranking-rank">${String(item.rank).padStart(2, '0')}</div>
                <div class="ranking-poster">
                    <img src="${item.poster}" alt="${item.title}" loading="lazy">
                </div>
                <div class="ranking-content">
                    <a href="${item.imdb}" target="_blank" rel="noopener noreferrer" class="ranking-title">${item.title}</a>
                    <p class="ranking-description">${item.description}</p>
                    <div class="ranking-meta">
                        <span class="ranking-rating"><span class="star">⭐</span> ${item.rating}</span>
                        <span>${item.genre || ''}</span>
                        <span>${item.platform}</span>
                        <span>${formatLength(item.length)}</span>
                        <span>${item.year}</span>
                    </div>
                </div>
            </div>
        `).join('');

        // Render Recommendations Carousel with infinite scrolling
        const carouselTrack = document.getElementById('carousel-track');
        if (carouselTrack && recommendations.length > 0) {
            // Create card HTML function
            const createCardHTML = (item) => `
                <div class="recommendation-card${item.isFavorite ? ' favorite' : ''}">
                    <div class="recommendation-poster">
                        <img src="${item.poster}" alt="${item.title}" loading="lazy">
                        ${item.isFavorite ? '<div class="favorite-star"><i class="fas fa-star"></i></div>' : ''}
                        <div class="recommendation-overlay">
                            <a href="${item.imdb}" target="_blank" rel="noopener noreferrer" class="recommendation-link">
                                <i class="fas fa-external-link-alt"></i>
                            </a>
                        </div>
                    </div>
                    <div class="recommendation-info">
                        <h4 class="recommendation-title">${item.title}</h4>
                        <div class="recommendation-platform">
                            <i class="fas fa-play-circle"></i> ${item.platform}
                        </div>
                    </div>
                </div>
            `;

            // Render alle Karten - keine Duplikate nötig!
            const cardsHTML = recommendations.map(createCardHTML).join('');
            carouselTrack.innerHTML = cardsHTML;

            // Initialize infinite carousel with buttons
            initInfiniteCarousel(carouselTrack, recommendations, recommendations.length);
        }
    }

    function initInfiniteCarousel(track, items, itemCount) {
        const prevBtn = document.getElementById('carousel-prev-btn');
        const nextBtn = document.getElementById('carousel-next-btn');

        if (!prevBtn || !nextBtn || !track) return;

        // Remove old listeners
        prevBtn.replaceWith(prevBtn.cloneNode(true));
        nextBtn.replaceWith(nextBtn.cloneNode(true));

        const newPrevBtn = document.getElementById('carousel-prev-btn');
        const newNextBtn = document.getElementById('carousel-next-btn');

        let scrollIndex = 0; // Unlimited index - kann negativ oder > itemCount sein
        let isAnimating = false;
        let cardWidth = 160;
        let gap = 32;

        function measureCard() {
            const firstCard = track.querySelector('.recommendation-card');
            if (firstCard && firstCard.offsetWidth > 0) {
                cardWidth = firstCard.offsetWidth;
                const computedGap = window.getComputedStyle(track).gap;
                gap = parseFloat(computedGap) || 32;
            }
        }

        function updatePosition(index) {
            const offset = -(index * (cardWidth + gap));
            track.style.transform = `translateX(${offset}px)`;
        }

        function updateButtonStates() {
            // Deaktiviere buttons wenn am Anfang/Ende
            newPrevBtn.disabled = scrollIndex === 0;
            newNextBtn.disabled = scrollIndex >= itemCount - 1;
        }

        function scroll(direction) {
            if (isAnimating) return;
            isAnimating = true;

            // Einfach weiterzählen
            if (direction === 'next') {
                scrollIndex++;
            } else {
                scrollIndex--;
            }

            track.style.transition = 'transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
            updatePosition(scrollIndex);

            setTimeout(() => {
                updateButtonStates();
                isAnimating = false;
            }, 500);
        }

        newNextBtn.addEventListener('click', () => scroll('next'));
        newPrevBtn.addEventListener('click', () => scroll('prev'));

        // Measure card size after a tick to ensure DOM is ready
        setTimeout(() => {
            measureCard();
            updatePosition(scrollIndex);
            updateButtonStates();
        }, 10);
    }

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentCategory = tab.dataset.category;
            renderRankings(currentCategory);
            if (rankingCategory) {
                rankingCategory.textContent = categoryLabels[currentCategory];
            }
        });
    });

    renderRankings('movies');
    if (rankingCategory) {
        rankingCategory.textContent = categoryLabels['movies'];
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
    initRankings();

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