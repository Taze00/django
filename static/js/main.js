// Initialize Three.js Background
function initThreeBackground() {
    if (!threeBgContainer) return;
    
    // Create scene, camera, and renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ 
        alpha: true, 
        antialias: true 
    });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    threeBgContainer.appendChild(renderer.domElement);
    
    // Camera position
    camera.position.z = 30;
    
    // Create particles - reduced by 33%
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 1000; // Reduced from 1500 (33% less)
    
    const posArray = new Float32Array(particlesCount * 3);
    
    // Generate random positions
    for (let i = 0; i < particlesCount * 3; i += 3) {
        posArray[i] = (Math.random() - 0.5) * 100;     // x
        posArray[i+1] = (Math.random() - 0.5) * 100;   // y
        posArray[i+2] = (Math.random() - 0.5) * 100;   // z
    }
    
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    
    // Create a canvas for circular particle texture
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const size = 64;
    canvas.width = size;
    canvas.height = size;
    
    // Draw a white circle
    ctx.beginPath();
    ctx.arc(size/2, size/2, size/2, 0, Math.PI * 2);
    ctx.fillStyle = 'white';
    ctx.fill();
    
    // Create texture from canvas
    const texture = new THREE.Texture(canvas);
    texture.needsUpdate = true;
    
    // Simple material with fixed gray color and circular texture
    const particlesMaterial = new THREE.PointsMaterial({
        color: 0xcccccc,           // Fixed gray color
        size: 0.2,                 // Particle size
        map: texture,              // Circular texture
        transparent: true,
        opacity: 0.5,
        alphaTest: 0.1,            // Helps with rendering transparency
        sizeAttenuation: true,     // Particles get smaller with distance
        depthWrite: false          // Prevents depth fighting issues
    });
    
    // Create the particle system
    const particlesMesh = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particlesMesh);
    
    // Animation
    const animate = () => {
        requestAnimationFrame(animate);
        
        particlesMesh.rotation.x += 0.0003;
        particlesMesh.rotation.y += 0.0005;
        
        renderer.render(scene, camera);
    };
    
    // Handle window resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    
    animate();
}
const header = document.getElementById('header');
const menuToggle = document.querySelector('.menu-toggle');
const navLinks = document.querySelector('.nav-links');
const galleryGrid = document.getElementById('gallery-grid');
const filterBtns = document.querySelectorAll('.filter-btn');
const rankingGrid = document.getElementById('ranking-grid');
const modal = document.querySelector('.modal');
const modalImg = document.querySelector('.modal-img');
const modalCaption = document.querySelector('.modal-caption');
const modalClose = document.querySelector('.modal-close');
const fadeElements = document.querySelectorAll('.fade-in');
const threeBgContainer = document.getElementById('three-bg');

// Logo Enhancement - Split name into spans with different styling
document.addEventListener('DOMContentLoaded', function() {
    const logoElement = document.querySelector('.logo');
    if (logoElement && logoElement.innerHTML === 'Alex Volkmann') {
        logoElement.innerHTML = '<span class="first-name">Alex</span> <span class="last-name">Volkmann</span>';
    }
});

// Gallery data
const galleryItems = [
    {
        id: 1,
        image: '/static/css/images/gallery/alex1.jpeg',
        title: 'Geburstagfeier',
        category: 'clubs'
    },
    {
        id: 2,
        image: '/static/css/images/gallery/alex2.png',
        title: 'Weiße Socken zu den Schuhen',
        category: 'clubs'
    },
    {
        id: 10,
        type: 'video', // Typ: Video
        source: '/static/css/images/gallery/alex10.mp4',
        title: 'Klassicher Handschlag',
        category: 'clubs'
    },
    {
        id: 3,
        image: '/static/css/images/gallery/alex3.jpeg',
        title: 'Potsdam Oktoberfest',
        category: 'clubs'
    },
    {
        id: 4,
        image: '/static/css/images/gallery/alex4.jpeg',
        title: 'Baumblüte',
        category: 'people'
    },
    {
        id: 5,
        image: '/static/css/images/gallery/alex5.jpeg',
        title: 'Abend mit Freunden',
        category: 'architecture'
    },
    {
        id: 6,
        image: '/static/css/images/gallery/alex6.jpeg',
        title: 'Ready machen für Berlin',
        category: 'clubs'
    },
    {
        id: 11,
        type: 'video', // Typ: Video
        source: '/static/css/images/gallery/alex11.mp4',
        title: 'World Club Dome abkühlen',
        category: 'clubs'
    },
    {
        id: 7,
        image: '/static/css/images/gallery/alex7.jpeg',
        title: 'SMS Festival',
        category: 'people'
    },
    {
        id: 8,
        image: '/static/css/images/gallery/alex8.jpeg',
        title: 'Malle',
        category: 'architecture'
    },
    {
        id: 12,
        type: 'video', // Typ: Video
        source: '/static/css/images/gallery/alex12.mp4',
        title: 'Aftern nach Geburstag',
        category: 'clubs'
    },
    {
        id: 9,
        image: '/static/css/images/gallery/alex9.jpeg',
        title: 'World Club Dome',
        category: 'architecture'
    }
];

// Club ranking data
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
        description: 'Geiler Club mit einer einzigartige Atmosphäre.',
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

// Club Cards Funktion, die in deinem Code fehlt
function createClubCards() {
    if (!rankingGrid) return;
    
    rankingGrid.innerHTML = '';
    
    clubData.forEach(club => {
        const colDiv = document.createElement('div');
        colDiv.className = 'col-lg-4 col-md-6 col-sm-12';
        
        const clubCard = document.createElement('div');
        clubCard.className = 'club-card fade-in';
        
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
        
        colDiv.appendChild(clubCard);
        rankingGrid.appendChild(colDiv);
    });
    
    // Aktiviere Fade-In für Club-Karten
    setTimeout(() => {
        document.querySelectorAll('.club-card').forEach(card => {
            card.classList.add('active');
        });
    }, 300);
}


// NEUE FUNKTION ZUM ERSETZEN - direkt an die Stelle kopieren, wo initThreeBackground definiert ist
function initThreeBackground() {
    // Sicherstellen, dass der Container existiert
    const threeBgContainer = document.getElementById('three-bg');
    if (!threeBgContainer) return;
    
    // Zuerst alle vorhandenen Renderer/Canvas entfernen
    while (threeBgContainer.firstChild) {
        threeBgContainer.removeChild(threeBgContainer.firstChild);
    }
    
    console.log("Initialisiere neue graue, runde Partikel");
    
    // Szene, Kamera und Renderer erstellen
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ 
        alpha: true, 
        antialias: true 
    });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    threeBgContainer.appendChild(renderer.domElement);
    
    // Kameraposition
    camera.position.z = 30;
    
    // Partikel erstellen - weiter reduziert
    const particlesCount = 800; // Weiter reduziert von 1000 auf 800
    const particlesGeometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particlesCount * 3);
    
    // Zufällige Positionen
    for (let i = 0; i < particlesCount * 3; i += 3) {
        positions[i] = (Math.random() - 0.5) * 100;     // x
        positions[i+1] = (Math.random() - 0.5) * 100;   // y
        positions[i+2] = (Math.random() - 0.5) * 100;   // z
    }
    
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    // Canvas für runde Partikel erstellen
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = 128;
    canvas.height = 128;
    
    // Weißen Kreis zeichnen
    context.beginPath();
    context.arc(64, 64, 64, 0, Math.PI * 2, false);
    context.fillStyle = 'white';
    context.fill();
    
    const circleTexture = new THREE.Texture(canvas);
    circleTexture.needsUpdate = true;
    
    // Material mit FIXIERTER GRAUER FARBE
    const particlesMaterial = new THREE.PointsMaterial({
        color: 0xcccccc,
        size: 0.2,         // Größe von 0.3 auf 0.2 reduziert
        map: circleTexture,
        transparent: true,
        opacity: 0.6,
        depthWrite: false,
        sizeAttenuation: true
    });
    
    // Partikelsystem erstellen
    const particleSystem = new THREE.Points(particlesGeometry, particlesMaterial);
    scene.add(particleSystem);
    
    // Animation
    function animate() {
        requestAnimationFrame(animate);
        
        particleSystem.rotation.x += 0.0003;
        particleSystem.rotation.y += 0.0005;
        
        renderer.render(scene, camera);
    }
    
    // Fenstergrößenänderung behandeln
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    
    animate();
    return true; // Erfolgreiche Initialisierung
}
// Verbesserte Partikel-Animation mit mehr Partikeln
function createParticles() {
    if (!particlesContainer) return;
    
    // Lösche vorhandene Partikel
    particlesContainer.innerHTML = '';
    
    // Erstelle 40 Partikel statt der ursprünglichen 25
    const particleCount = 40;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // Zufällige Größe zwischen 2 und 10 Pixel
        const size = Math.random() * 8 + 2;
        particle.style.width = `${size}px`;
        particle.style.height = `${size}px`;
        
        // Zufällige Position
        const posX = Math.random() * 100;
        const posY = Math.random() * 100;
        particle.style.left = `${posX}%`;
        particle.style.top = `${posY}%`;
        
        // Zufällige Opazität zwischen 0.1 und 0.4
        const opacity = Math.random() * 0.3 + 0.1;
        particle.style.opacity = opacity;
        
        // Zufällige Animation-Dauer zwischen 15 und 40 Sekunden
        const duration = Math.random() * 25 + 15;
        particle.style.animationDuration = `${duration}s`;
        
        // Zufällige Animation-Verzögerung, damit alle Partikel sofort beginnen sich zu bewegen
        // aber nicht synchron sind
        const delay = Math.random() * -40; // Negative Verzögerung sorgt dafür, dass die Animation sofort startet
        particle.style.animationDelay = `${delay}s`;
        
        // Füge das Partikel zum Container hinzu
        particlesContainer.appendChild(particle);
    }
}

// Mobile Menu Toggle
if (menuToggle) {
    menuToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        
        if (navLinks.classList.contains('active')) {
            menuToggle.innerHTML = '<i class="fas fa-times"></i>';
        } else {
            menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
        }
    });
}

// Scroll Events
window.addEventListener('scroll', () => {
    // Header style on scroll
    if (window.scrollY > 100) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
    
    // Fade in elements
    fadeElements.forEach(el => {
        const elementTop = el.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        
        if (elementTop < windowHeight - 50) {
            el.classList.add('active');
        }
    });
});

function createGallery() {
    if (!galleryGrid) return;
    
    galleryGrid.innerHTML = '';
    
    galleryItems.forEach(item => {
        const colDiv = document.createElement('div');
        colDiv.className = 'col-lg-4 col-md-6 col-sm-12';
        
        const galleryItem = document.createElement('div');
        galleryItem.className = `gallery-item fade-in`;
        
        // Überprüfe, ob item.type existiert, falls nicht, wird es als 'image' behandelt
        const itemType = item.type || 'image';
        const itemSource = item.source || item.image; // Unterstützung für beide Formate
        
        // Unterschiedlicher Inhalt je nach Typ (Bild oder Video)
        if (itemType === 'video') {
            // Erstelle Video-Element mit JavaScript für mehr Kontrolle
            const video = document.createElement('video');
            video.autoplay = true;
            video.muted = true;
            video.loop = true;
            video.playsInline = true;
            video.src = itemSource;
            
            // Video-Element zur Galerie-Item hinzufügen
            galleryItem.appendChild(video);
            
            // Overlay mit Titel hinzufügen
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
        
        galleryItem.addEventListener('click', () => {
            if (itemType === 'video') {
                // Video im Modal anzeigen
                modalImg.style.display = 'none'; // Bild ausblenden
                
                // Falls ein vorheriges Video existiert, entfernen
                const existingVideo = document.querySelector('.modal-video');
                if (existingVideo) existingVideo.remove();
                
                // Neues Video erstellen
                const video = document.createElement('video');
                video.controls = true;
                video.autoplay = true;
                video.muted = false;
                video.loop = true;
                video.src = itemSource;
                video.className = 'modal-video';
                
                // Lautstärke auf 15% setzen (0.15 von 1.0)
                video.volume = 0.15;
                
                // Einfügen vor der Bildunterschrift
                const modalContent = document.querySelector('.modal-content');
                modalContent.insertBefore(video, modalCaption);
                
                modalCaption.textContent = item.title;
                modal.style.display = 'flex';
            } else {
                // Bild im Modal anzeigen
                const existingVideo = document.querySelector('.modal-video');
                if (existingVideo) existingVideo.remove();
                
                // Sicherstellen, dass das Bild nicht verzerrt wird
                modalImg.style.display = 'block';
                modalImg.style.width = 'auto';
                modalImg.style.height = 'auto';
                modalImg.src = itemSource;
                
                modalCaption.textContent = item.title;
                modal.style.display = 'flex';
            }
        });
        
        colDiv.appendChild(galleryItem);
        galleryGrid.appendChild(colDiv);
    });
    
    setTimeout(() => {
        document.querySelectorAll('.gallery-item').forEach(item => {
            item.classList.add('active');
        });
    }, 300);
}


// Animate Rating Bars when visible
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


// Modal Functions
if (modalClose) {
    modalClose.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Smooth scrolling
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
            if (navLinks.classList.contains('active')) {
                navLinks.classList.remove('active');
                menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        }
    });
});

// Initialize
window.addEventListener('load', () => {
    // Initialisiere Three.js Hintergrund
    initThreeBackground();
    
    // Aktiviere initiale Fade-Elemente
    fadeElements.forEach(el => {
        const elementTop = el.getBoundingClientRect().top;
        const windowHeight = window.innerHeight;
        
        if (elementTop < windowHeight) {
            el.classList.add('active');
        }
    });
    
    // Erstelle Galerie und Club-Karten
    createGallery();
    createClubCards();
    animateRatingBars();
});


// Diesen Code in Ihre main.js-Datei einfügen (am Anfang oder Ende der Datei)
document.addEventListener('DOMContentLoaded', function() {
  // Aktuelle Version - ändern Sie diesen Wert, wenn Sie Updates erzwingen möchten
  const SITE_VERSION = '20250514-2';
  
  // Funktion zum Hinzufügen von Versionsnummern zu allen Medien
  function updateMediaSources() {
    // Alle Bilder auf der Seite
    document.querySelectorAll('img').forEach(img => {
      // Überprüfen, ob bereits ein Versionsparameter vorhanden ist
      if (img.src && !img.src.includes('?v=') && !img.src.includes('data:image')) {
        // URL-Objekt erstellen, um Parameter hinzuzufügen oder zu aktualisieren
        try {
          const imgUrl = new URL(img.src);
          imgUrl.searchParams.set('v', SITE_VERSION);
          img.src = imgUrl.toString();
        } catch (e) {
          // Falls eine ungültige URL vorliegt, direkten String-Ansatz verwenden
          img.src = img.src + (img.src.includes('?') ? '&' : '?') + 'v=' + SITE_VERSION;
        }
      }
    });
    
    // Alle Videos auf der Seite
    document.querySelectorAll('video').forEach(video => {
      if (video.src && !video.src.includes('?v=')) {
        try {
          const videoUrl = new URL(video.src);
          videoUrl.searchParams.set('v', SITE_VERSION);
          video.src = videoUrl.toString();
        } catch (e) {
          // Falls eine ungültige URL vorliegt, direkten String-Ansatz verwenden
          video.src = video.src + (video.src.includes('?') ? '&' : '?') + 'v=' + SITE_VERSION;
        }
      }
    });
    
    // Hintergrundbild-URLs in CSS aktualisieren (falls vorhanden)
    document.querySelectorAll('[style*="background-image"]').forEach(el => {
      const style = el.getAttribute('style');
      if (style && style.includes('url(') && !style.includes('?v=')) {
        const newStyle = style.replace(/url\(['"]?([^'"]+?)['"]?\)/g, 
          (match, url) => `url(${url}${url.includes('?') ? '&' : '?'}v=${SITE_VERSION})`);
        el.setAttribute('style', newStyle);
      }
    });
  }
  
  // Prüfen, ob ein Force-Reload nötig ist
  const lastVersion = localStorage.getItem('site_version');
  if (lastVersion !== SITE_VERSION) {
    // Neue Version in localStorage speichern
    localStorage.setItem('site_version', SITE_VERSION);
    
    // Seite neu laden, wenn zuvor schon eine Version gespeichert war
    if (lastVersion) {
      console.log('Neue Version verfügbar. Lade Seite neu...');
      // Hard reload erzwingen (kein Cache)
      window.location.reload(true);
    }
  }
  
  // Media-Quellen aktualisieren, selbst wenn kein Reload erforderlich war
  updateMediaSources();
  
  // Anpassung der Galerie- und Club-Karten-Funktionen, um Medien zu aktualisieren
  if (typeof createGallery === 'function') {
    const originalCreateGallery = createGallery;
    window.createGallery = function() {
      originalCreateGallery();
      updateMediaSources();
    };
  }
  
  if (typeof createClubCards === 'function') {
    const originalCreateClubCards = createClubCards;
    window.createClubCards = function() {
      originalCreateClubCards();
      updateMediaSources();
    };
  }
});

// Finale Version der Galerie-Navigation mit Video-Thumbnails
// Ersetzen Sie den vorherigen Code mit diesem Code in Ihrer main.js

// Verbesserte, stabilere Galerie-Navigation
// Ersetzen Sie den vorherigen Code in Ihrer main.js

// Stabilisierte Galerie-Navigation mit fixer Größe und zuverlässigen Pfeilen
function enhanceGalleryModal() {
  // Modal und zugehörige Elemente
  const modal = document.querySelector('.modal');
  const modalImg = document.querySelector('.modal-img');
  const modalCaption = document.querySelector('.modal-caption');
  const modalContent = document.querySelector('.modal-content');
  const modalClose = document.querySelector('.modal-close');
  
  if (!modal || !modalImg || !modalContent) {
    console.error('Modal-Elemente nicht gefunden');
    return;
  }
  
  // Bildunterschrift ausblenden
  if (modalCaption) {
    modalCaption.style.display = 'none';
  }
  
  // Variablen für die Navigation
  let currentIndex = 0;
  
  // Prüfen, ob Mobilgerät
  const isMobile = window.innerWidth <= 768;
  
  // Bestehende Navigation entfernen, falls vorhanden
  function clearExistingNavigation() {
    const existingNav = document.querySelector('.modal-nav');
    if (existingNav) existingNav.remove();
    
    // Auch alle anderen dynamischen Elemente entfernen
    const existingVideoContainer = document.querySelector('.modal-video-container');
    if (existingVideoContainer) existingVideoContainer.remove();
    
    const existingVideo = document.querySelector('.modal-video');
    if (existingVideo) existingVideo.remove();
  }
  
  // Modales Fenster und Layout neugestalten für konsistente Größe
  function setupModalLayout() {
    // Konsistentes Styling für das Modal
    modal.style.padding = isMobile ? '1rem' : '2rem';
    modal.style.overscrollBehavior = 'contain';
    modal.style.touchAction = 'pan-y pinch-zoom';
    
    // Konsistente Größe für modalContent
    modalContent.style.position = 'relative';
    modalContent.style.maxWidth = '90%';
    modalContent.style.height = isMobile ? '75vh' : '85vh';
    modalContent.style.display = 'flex';
    modalContent.style.flexDirection = 'column';
    modalContent.style.justifyContent = 'center'; // Vertikale Zentrierung
    modalContent.style.alignItems = 'center';
    modalContent.style.background = 'transparent';
    modalContent.style.border = 'none';
    modalContent.style.overflowY = 'hidden';
    
    // Fix für Größe und Position des Schließen-Buttons
    if (modalClose) {
      modalClose.style.position = 'absolute';
      modalClose.style.top = isMobile ? '-60px' : '-50px';
      modalClose.style.right = isMobile ? '0' : '0';
      modalClose.style.fontSize = isMobile ? '3rem' : '2.5rem';
      modalClose.style.color = 'white';
      modalClose.style.cursor = 'pointer';
      modalClose.style.zIndex = '2001';
    }
    
    // Standard-Styling für das Hauptbild
    modalImg.style.maxWidth = '100%';
    modalImg.style.maxHeight = isMobile ? '65vh' : '75vh';
    modalImg.style.width = 'auto';
    modalImg.style.height = 'auto';
    modalImg.style.objectFit = 'contain';
    modalImg.style.display = 'block';
    modalImg.style.borderRadius = '8px';
    modalImg.style.boxShadow = '0 15px 40px rgba(0, 0, 0, 0.6)';
  }
  
  // Navigations-Elemente erstellen
  // Verbesserte Galerie-Navigation ohne Pfeile auf Mobilgeräten
// Nur einen kleinen Teil des Codes aktualisieren - suchen Sie diese Funktion in Ihrem bestehenden Code

// Navigations-Elemente erstellen - mit mobiler Anpassung
function createNavigationControls() {
  // Bestehende Navigation entfernen falls vorhanden
  clearExistingNavigation();
  
  // Container für Navigationselemente
  const navContainer = document.createElement('div');
  navContainer.className = 'modal-nav';
  navContainer.style.position = 'absolute';
  
  if (isMobile) {
    // Für mobile Geräte - nur Zähler anzeigen, keine Pfeile
    navContainer.style.bottom = '-50px';
    navContainer.style.left = '0';
    navContainer.style.width = '100%';
    navContainer.style.height = '40px';
    navContainer.style.display = 'flex';
    navContainer.style.justifyContent = 'center'; // Zähler zentrieren
    navContainer.style.alignItems = 'center';
    navContainer.style.zIndex = '2001';
    
    // Zähler für die Bilder (x von y)
    const counter = document.createElement('div');
    counter.className = 'modal-counter';
    counter.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
    counter.style.color = 'white';
    counter.style.padding = '5px 15px';
    counter.style.borderRadius = '20px';
    counter.style.fontSize = '12px';
    counter.style.fontWeight = '500';
    
    // Nur den Zähler zum Container hinzufügen für Mobile
    navContainer.appendChild(counter);
    
    // Container zum Modal hinzufügen
    modalContent.appendChild(navContainer);
    
    // Swipe-Hinweis hinzufügen (optional)
    const swipeHint = document.createElement('div');
    swipeHint.className = 'swipe-hint';
    swipeHint.textContent = 'Zum Wechseln wischen';
    swipeHint.style.position = 'absolute';
    swipeHint.style.bottom = '-30px';
    swipeHint.style.width = '100%';
    swipeHint.style.textAlign = 'center';
    swipeHint.style.color = 'rgba(255, 255, 255, 0.6)';
    swipeHint.style.fontSize = '10px';
    swipeHint.style.fontWeight = '400';
    swipeHint.style.opacity = '1';
    swipeHint.style.transition = 'opacity 1s';
    
    // Swipe-Hinweis nach ein paar Sekunden ausblenden
    modalContent.appendChild(swipeHint);
    setTimeout(() => {
      swipeHint.style.opacity = '0';
    }, 2500);
    
    // Zähler aktualisieren
    updateCounter(counter);
    
    return {counter};
  } else {
    // Desktop-Version mit Pfeilen bleibt unverändert
    navContainer.style.bottom = '20px';
    navContainer.style.left = '0';
    navContainer.style.width = '100%';
    navContainer.style.height = '50px';
    navContainer.style.display = 'flex';
    navContainer.style.justifyContent = 'space-between';
    navContainer.style.alignItems = 'center';
    navContainer.style.zIndex = '2001';
    navContainer.style.pointerEvents = 'none';
    
    // Vorheriges Bild Button
    const prevButton = document.createElement('div');
    prevButton.className = 'modal-nav-prev';
    prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>';
    prevButton.style.width = '50px';
    prevButton.style.height = '50px';
    prevButton.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    prevButton.style.color = 'white';
    prevButton.style.display = 'flex';
    prevButton.style.justifyContent = 'center';
    prevButton.style.alignItems = 'center';
    prevButton.style.borderRadius = '50%';
    prevButton.style.cursor = 'pointer';
    prevButton.style.marginLeft = '20px';
    prevButton.style.pointerEvents = 'auto';
    prevButton.style.transition = 'none';
    prevButton.style.fontSize = '20px';
    prevButton.style.outline = 'none';
    prevButton.style.webkitTapHighlightColor = 'transparent';
    prevButton.style.userSelect = 'none';
    prevButton.style.border = 'none';
    
    // Nächstes Bild Button
    const nextButton = document.createElement('div');
    nextButton.className = 'modal-nav-next';
    nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>';
    nextButton.style.width = '50px';
    nextButton.style.height = '50px';
    nextButton.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    nextButton.style.color = 'white';
    nextButton.style.display = 'flex';
    nextButton.style.justifyContent = 'center';
    nextButton.style.alignItems = 'center';
    nextButton.style.borderRadius = '50%';
    nextButton.style.cursor = 'pointer';
    nextButton.style.marginRight = '20px';
    nextButton.style.pointerEvents = 'auto';
    nextButton.style.transition = 'none';
    nextButton.style.fontSize = '20px';
    nextButton.style.outline = 'none';
    nextButton.style.webkitTapHighlightColor = 'transparent';
    nextButton.style.userSelect = 'none';
    nextButton.style.border = 'none';
    
    // Zähler für die Bilder (x von y)
    const counter = document.createElement('div');
    counter.className = 'modal-counter';
    counter.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
    counter.style.color = 'white';
    counter.style.padding = '5px 15px';
    counter.style.borderRadius = '20px';
    counter.style.fontSize = '14px';
    counter.style.fontWeight = '500';
    counter.style.pointerEvents = 'none';
    
    // Navigation-Elemente zum Container hinzufügen
    navContainer.appendChild(prevButton);
    navContainer.appendChild(counter);
    navContainer.appendChild(nextButton);
    
    // Container zum Modal hinzufügen
    modalContent.appendChild(navContainer);
    
    // Definitiv funktionierende Event-Listener für die Navigation
    const handlePrevClick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      showPreviousMedia();
    };
    
    const handleNextClick = (e) => {
      e.preventDefault();
      e.stopPropagation();
      showNextMedia();
    };
    
    // Event-Listener hinzufügen - wichtig: direkte Funktionen verwenden, keine anonymen
    prevButton.addEventListener('click', handlePrevClick);
    nextButton.addEventListener('click', handleNextClick);
    
    // Alle Touch-Events verhindern Standard-Verhalten
    prevButton.addEventListener('touchstart', (e) => e.preventDefault(), {passive: false});
    nextButton.addEventListener('touchstart', (e) => e.preventDefault(), {passive: false});
    prevButton.addEventListener('mousedown', (e) => e.preventDefault());
    nextButton.addEventListener('mousedown', (e) => e.preventDefault());
    
    // Zähler aktualisieren
    updateCounter(counter);
    
    return {prevButton, nextButton, counter};
  }
}
  
  // Zähler aktualisieren
  function updateCounter(counterElement) {
    if (!counterElement) return;
    
    const totalItems = window.galleryItems ? window.galleryItems.length : 0;
    if (totalItems > 0) {
      counterElement.textContent = `${currentIndex + 1} / ${totalItems}`;
    }
  }
  
  // Video-Thumbnails aus dem ersten Frame des Videos erzeugen
  function createVideoThumbnail(videoSrc, callback) {
    const tempVideo = document.createElement('video');
    
    tempVideo.addEventListener('loadeddata', function() {
      // Wenn das Video geladen ist, gehen wir zum ersten Frame
      tempVideo.currentTime = 0.5; // 0.5 Sekunden, um einen besseren Thumbnail zu bekommen
    });
    
    tempVideo.addEventListener('seeked', function() {
      // Wenn wir zum Frame gesprungen sind, erstellen wir ein Canvas
      const canvas = document.createElement('canvas');
      canvas.width = tempVideo.videoWidth;
      canvas.height = tempVideo.videoHeight;
      
      // Frame auf Canvas zeichnen
      const ctx = canvas.getContext('2d');
      ctx.drawImage(tempVideo, 0, 0, canvas.width, canvas.height);
      
      // Thumbnail als Daten-URL zurückgeben
      const thumbnailUrl = canvas.toDataURL('image/jpeg');
      callback(thumbnailUrl);
      
      // Video entfernen
      tempVideo.remove();
    });
    
    // Für den Fall, dass Fehler auftreten
    tempVideo.addEventListener('error', function() {
      console.error('Fehler beim Laden des Videos:', videoSrc);
      callback(''); // Leere URL zurückgeben, was zu einem Fehler-Image führen sollte
    });
    
    // Video-Quelle setzen und laden
    tempVideo.src = videoSrc;
    tempVideo.load();
    tempVideo.style.display = 'none';
    document.body.appendChild(tempVideo);
  }
  
  // Medien anzeigen basierend auf Index - Hauptfunktion
  function showMedia(index) {
    // Sicherstellen, dass galleryItems verfügbar ist
    if (!window.galleryItems || !window.galleryItems.length) return;
    
    // Sicherstellen, dass der Index gültig ist
    if (index < 0) index = window.galleryItems.length - 1;
    if (index >= window.galleryItems.length) index = 0;
    
    // Aktuellen Index aktualisieren
    currentIndex = index;
    
    // Zunächst alle bestehenden Medien entfernen
    clearExistingNavigation();
    
    // Aktuelles Item aus der Galerie
    const item = window.galleryItems[index];
    
    // Navigationselemente erstellen
    const navElements = createNavigationControls();
    
    // Prüfen, ob es sich um ein Video oder Bild handelt
    const itemType = item.type || 'image';
    const itemSource = item.source || item.image;
    
    if (itemType === 'video') {
      // Bild ausblenden
      modalImg.style.display = 'none';
      
      // Video-Container erstellen mit fester Größe
      const videoContainer = document.createElement('div');
      videoContainer.className = 'modal-video-container';
      videoContainer.style.position = 'relative';
      videoContainer.style.width = '100%'; 
      videoContainer.style.maxWidth = isMobile ? '90%' : '90%';
      videoContainer.style.height = isMobile ? '65vh' : '75vh';
      videoContainer.style.display = 'flex';
      videoContainer.style.justifyContent = 'center'; // Horizontale Zentrierung
      videoContainer.style.alignItems = 'center'; // Vertikale Zentrierung
      
      // Thumbnail erstellen und anzeigen
      const thumbnail = document.createElement('div');
      thumbnail.className = 'video-thumbnail';
      thumbnail.style.position = 'relative';
      thumbnail.style.width = '100%';
      thumbnail.style.height = '100%';
      thumbnail.style.display = 'flex';
      thumbnail.style.justifyContent = 'center';
      thumbnail.style.alignItems = 'center';
      thumbnail.style.backgroundColor = '#000';
      thumbnail.style.borderRadius = '8px';
      thumbnail.style.overflow = 'hidden';
      thumbnail.style.cursor = 'pointer';
      
      // Thumbnail-Bild
      const thumbnailImg = document.createElement('img');
      thumbnailImg.style.maxWidth = '100%';
      thumbnailImg.style.maxHeight = '100%';
      thumbnailImg.style.width = 'auto';
      thumbnailImg.style.height = 'auto';
      thumbnailImg.style.objectFit = 'contain';
      thumbnailImg.style.display = 'block';
      
      // Vorübergehendes Platzhalterbild, bis das eigentliche Thumbnail geladen ist
      thumbnailImg.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200"><rect width="300" height="200" fill="%23333"/></svg>';
      
      // Play-Button über dem Thumbnail
      const playButton = document.createElement('div');
      playButton.className = 'video-play-button';
      playButton.innerHTML = '<i class="fas fa-play"></i>';
      playButton.style.position = 'absolute';
      playButton.style.top = '50%';
      playButton.style.left = '50%';
      playButton.style.transform = 'translate(-50%, -50%)';
      playButton.style.width = isMobile ? '50px' : '70px';
      playButton.style.height = isMobile ? '50px' : '70px';
      playButton.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
      playButton.style.borderRadius = '50%';
      playButton.style.display = 'flex';
      playButton.style.justifyContent = 'center';
      playButton.style.alignItems = 'center';
      playButton.style.color = 'white';
      playButton.style.fontSize = isMobile ? '20px' : '30px';
      playButton.style.cursor = 'pointer';
      playButton.style.zIndex = '1';
      
      // Thumbnail zum Container hinzufügen
      thumbnail.appendChild(thumbnailImg);
      thumbnail.appendChild(playButton);
      videoContainer.appendChild(thumbnail);
      
      // Thumbnail generieren
      createVideoThumbnail(itemSource, (thumbnailUrl) => {
        if (thumbnailUrl) {
          thumbnailImg.src = thumbnailUrl;
        }
      });
      
      // Klick-Handler für das Abspielen des Videos
      const handleThumbnailClick = (e) => {
        e.preventDefault();
        e.stopPropagation();
        
        // Thumbnail entfernen
        thumbnail.remove();
        
        // Video erstellen
        const video = document.createElement('video');
        video.controls = true;
        video.autoplay = false;
        video.muted = false;
        video.loop = true;
        video.src = itemSource;
        video.className = 'modal-video';
        video.volume = 0.15;
        
        // Vollbildmodus verhindern
        video.setAttribute('playsinline', 'playsinline');
        video.setAttribute('webkit-playsinline', 'webkit-playsinline');
        
        // Video-Styling
        video.style.maxWidth = '100%';
        video.style.maxHeight = '100%';
        video.style.width = 'auto';
        video.style.height = 'auto';
        video.style.objectFit = 'contain';
        video.style.display = 'block';
        video.style.borderRadius = '8px';
        video.style.boxShadow = '0 15px 40px rgba(0, 0, 0, 0.6)';
        
        // Video zum Container hinzufügen
        videoContainer.appendChild(video);
        
        // Video abspielen
        video.play().catch(err => console.error('Fehler beim Abspielen des Videos:', err));
        
        // Verhindere, dass das Modal beim Klick auf das Video geschlossen wird
        video.addEventListener('click', e => e.stopPropagation());
      };
      
      // Event-Listener für Klick auf Thumbnail
      thumbnail.addEventListener('click', handleThumbnailClick);
      
      // Video-Container zum Modal hinzufügen
      modalContent.insertBefore(videoContainer, navElements ? navElements.prevButton.parentNode : null);
    } else {
      // Bei Bildern: Alle Video-Elemente entfernen
      const existingVideoContainer = document.querySelector('.modal-video-container');
      if (existingVideoContainer) existingVideoContainer.remove();
      
      const existingVideo = document.querySelector('.modal-video');
      if (existingVideo) existingVideo.remove();
      
      // Bild anzeigen
      modalImg.style.display = 'block';
      modalImg.src = itemSource;
    }
    
    // Zähler aktualisieren
    if (navElements && navElements.counter) {
      updateCounter(navElements.counter);
    }
  }
  
  // Navigation zu vorherigem Medium
  function showPreviousMedia() {
    showMedia(currentIndex - 1);
  }
  
  // Navigation zu nächstem Medium
  function showNextMedia() {
    showMedia(currentIndex + 1);
  }
  
  // Verarbeitet die Tastatureingabe für die Navigation
  function handleKeyNavigation(event) {
    if (!modal.style.display || modal.style.display === 'none') return;
    
    if (event.key === 'ArrowLeft') {
      showPreviousMedia();
    } else if (event.key === 'ArrowRight') {
      showNextMedia();
    } else if (event.key === 'Escape') {
      modal.style.display = 'none';
    }
  }
  
  // Touch-Events für Swipe-Funktionalität
  let touchStartX = 0;
  let touchStartY = 0;
  
  function handleTouchStart(event) {
    touchStartX = event.changedTouches[0].screenX;
    touchStartY = event.changedTouches[0].screenY;
  }
  
  function handleTouchEnd(event) {
    const touchEndX = event.changedTouches[0].screenX;
    const touchEndY = event.changedTouches[0].screenY;
    
    // Berechne die horizontale und vertikale Distanz
    const deltaX = touchEndX - touchStartX;
    const deltaY = Math.abs(touchEndY - touchStartY);
    
    // Nur horizontale Swipes mit genügend Distanz berücksichtigen
    // und wenn die vertikale Bewegung nicht zu groß ist
    if (Math.abs(deltaX) > window.innerWidth * 0.15 && deltaY < 50) {
      if (deltaX > 0) {
        // Nach rechts - vorheriges Bild
        showPreviousMedia();
      } else {
        // Nach links - nächstes Bild
        showNextMedia();
      }
    }
  }
  
  // Setzt das Modal in einen einheitlichen Startzustand
  function resetModal() {
    // Modal-Layout optimieren
    setupModalLayout();
    
    // Klick auf das Modal außerhalb des Inhalts schließt es
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.style.display = 'none';
      }
    });
    
    // Verhindern der Standardaktion beim Klicken auf das Bild
    modalImg.addEventListener('click', (e) => {
      e.stopPropagation();
    });
    
    // Touch-Events für Swipe-Funktionalität
    modal.addEventListener('touchstart', handleTouchStart, {passive: true});
    modal.addEventListener('touchend', handleTouchEnd, {passive: true});
    
    // Tastaturnavigation hinzufügen
    document.addEventListener('keydown', handleKeyNavigation);
  }
  
  // Initialisiert das Modal mit dem Bild/Video
  function initModalWithMedia(index) {
    // Sicherstellen, dass das Modal zurückgesetzt wird
    resetModal();
    
    // Zeige das entsprechende Medium
    showMedia(index);
    
    // Modal anzeigen
    modal.style.display = 'flex';
    
    // Auf Mobilgeräten das Hintergrund-Scrollen verhindern
    if (isMobile) {
      document.body.classList.add('modal-open');
    }
  }
  
  // Modifizieren der Galerie-Items, um das neue Modal zu verwenden
  function modifyGalleryItems() {
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    galleryItems.forEach((item, index) => {
      // Bestehenden Event-Listener entfernen und neu erstellen
      const newItem = item.cloneNode(true);
      item.parentNode.replaceChild(newItem, item);
      
      // Neuen Klick-Event-Listener hinzufügen
      newItem.addEventListener('click', () => {
        initModalWithMedia(index);
      });
    });
  }
  
  // Wenn Modal geschlossen wird, Scrollen wieder aktivieren
  if (modalClose) {
    modalClose.addEventListener('click', () => {
      modal.style.display = 'none';
      document.body.classList.remove('modal-open');
    });
  }
  
  // CSS hinzufügen für Modal-Open-Klasse und Verbesserungen
  const style = document.createElement('style');
  style.textContent = `
    body.modal-open {
      overflow: hidden;
      position: fixed;
      width: 100%;
      height: 100%;
    }
    
    .modal-nav-prev:focus, 
    .modal-nav-next:focus,
    .modal-nav-prev:hover, 
    .modal-nav-next:hover,
    .modal-nav-prev:active, 
    .modal-nav-next:active {
      outline: none !important;
      box-shadow: none !important;
      border: none !important;
      background-color: rgba(0, 0, 0, 0.7) !important;
    }
  `;
  document.head.appendChild(style);
  
  // Ursprüngliche createGallery-Funktion überschreiben
  if (typeof window.createGallery === 'function') {
    const originalCreateGallery = window.createGallery;
    window.createGallery = function() {
      originalCreateGallery();
      setTimeout(modifyGalleryItems, 100);
    };
  }
  
  // Bei vorhandener Galerie sofort anwenden
  if (document.querySelectorAll('.gallery-item').length > 0) {
    setTimeout(modifyGalleryItems, 300);
  }
  
  // Größenanpassung des Fensters behandeln
  window.addEventListener('resize', () => {
    // Aktualisiere die isMobile-Erkennung
    const wasMobile = isMobile;
    const newIsMobile = window.innerWidth <= 768;
    
    // Nur wenn sich der Mobilstatus ändert oder Modal geöffnet ist
    if (wasMobile !== newIsMobile && modal.style.display === 'flex') {
      // Layout neu einrichten und aktuellen Index neu laden
      setupModalLayout();
      showMedia(currentIndex);
    }
  });
}

// Galerie-Modal-Enhancement nach dem Laden der Seite initialisieren
document.addEventListener('DOMContentLoaded', function() {
  // Stellen Sie sicher, dass die galleryItems-Variable global verfügbar ist
  window.galleryItems = galleryItems;
  
  // Verzögerung, um sicherzustellen, dass alle DOM-Elemente geladen sind
  setTimeout(enhanceGalleryModal, 500);
});