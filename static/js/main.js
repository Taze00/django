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
        id: 13,
        source: '/static/css/images/gallery/alex11.jpeg',
        title: 'Nach dem Lokschuppen',
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


// Galerie-Modal-Enhancement nach dem Laden der Seite initialisieren
document.addEventListener('DOMContentLoaded', function() {
  // Stellen Sie sicher, dass die galleryItems-Variable global verfügbar ist
  window.galleryItems = galleryItems;
  
  // Verzögerung, um sicherzustellen, dass alle DOM-Elemente geladen sind
  setTimeout(enhanceGalleryModal, 500);
});

// GallerySwipeModal - Eine vollständig neu geschriebene Galerie-Popup-Implementierung
// mit optimierter Performance und Touch-Unterstützung

class GallerySwipeModal {
  constructor() {
    // DOM-Elemente
    this.modal = document.querySelector('.modal');
    this.modalContent = document.querySelector('.modal-content');
    this.modalImg = document.querySelector('.modal-img');
    this.modalCaption = document.querySelector('.modal-caption');
    this.modalClose = document.querySelector('.modal-close');
    
    // Zustandsvariablen
    this.currentIndex = 0;
    this.items = window.galleryItems || [];
    this.isAnimating = false;
    this.isMobile = window.innerWidth <= 768;
    this.touchStartX = 0;
    this.touchStartY = 0;
    this.touchEndX = 0;
    this.touchEndY = 0;
    this.swipeThreshold = this.isMobile ? 50 : 100;
    this.isVideoPlaying = false;
    this.videoInstance = null;
    this.navElements = null;
    
    // Element-Container
    this.mediaContainer = null;
    
    // Initialisierung
    this.init();
  }
  
  // Initialisierung der Galerie
  init() {
    if (!this.modal) {
      console.error('Modal-Element nicht gefunden');
      return;
    }
    
    // Event-Listener für Schließen-Button
    if (this.modalClose) {
      this.modalClose.addEventListener('click', this.close.bind(this));
    }
    
    // Klick außerhalb des Inhalts schließt das Modal
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) {
        this.close();
      }
    });
    
    // Touch-Events für Swipe-Funktionalität
    this.modal.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
    this.modal.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
    this.modal.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    
    // Tastaturnavigation
    document.addEventListener('keydown', this.handleKeyboard.bind(this));
    
    // Fenstergrößenänderung
    window.addEventListener('resize', this.handleResize.bind(this));
    
    // Benutzerinterface vorbereiten
    this.setupUI();
    
    // Galerie-Elemente modifizieren, um auf diese Klasse zu verweisen
    this.modifyGalleryItems();
  }
  
  // UI-Einrichtung mit verbesserten Styling-Methoden
  setupUI() {
    // Styling-Elemente
    this.addStyles(`
      body.modal-open {
        overflow: hidden !important;
        position: fixed !important;
        width: 100% !important;
        height: 100% !important;
      }
      
      .gallery-modal {
        --transition-speed: 300ms;
        --swipe-color: rgba(255, 255, 255, 0.1);
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.95);
        z-index: 2000;
        overflow: hidden;
        touch-action: none;
      }
      
      .gallery-modal.open {
        display: flex;
        justify-content: center;
        align-items: center;
      }
      
      .modal-content {
        position: relative;
        width: 90%;
        height: 85vh;
        max-width: 1400px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        overflow: hidden;
      }
      
      .media-container {
        position: relative;
        width: 100%;
        height: 75vh;
        display: flex;
        justify-content: center;
        align-items: center;
        transition: transform var(--transition-speed) ease-out;
      }
      
      .media-item {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        opacity: 0;
        transform: translateX(100%);
        transition: opacity var(--transition-speed) ease, transform var(--transition-speed) ease;
      }
      
      .media-item.previous {
        transform: translateX(-100%);
        opacity: 0;
      }
      
      .media-item.current {
        transform: translateX(0);
        opacity: 1;
        z-index: 10;
      }
      
      .media-item.next {
        transform: translateX(100%);
        opacity: 0;
      }
      
      .media-content {
        max-width: 100%;
        max-height: 100%;
        width: auto;
        height: auto;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6);
      }
      
      .video-container {
        position: relative;
        max-width: 100%;
        max-height: 100%;
        width: auto;
        height: auto;
        display: flex;
        justify-content: center;
        align-items: center;
      }
      
      .video-thumbnail {
        position: relative;
        cursor: pointer;
      }
      
      .video-play-button {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 70px;
        height: 70px;
        background-color: rgba(0, 0, 0, 0.7);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 30px;
        transition: background-color 0.2s;
      }
      
      .video-play-button:hover {
        background-color: rgba(0, 0, 0, 0.8);
      }
      
      .navigation-controls {
        position: absolute;
        bottom: 20px;
        left: 0;
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 20;
        padding: 0 20px;
      }
      
      .nav-button {
        width: 50px;
        height: 50px;
        background-color: rgba(0, 0, 0, 0.7);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 20px;
        cursor: pointer;
        transition: background-color 0.2s;
        border: none;
        outline: none;
      }
      
      .nav-button:hover {
        background-color: rgba(0, 0, 0, 0.9);
      }
      
      .counter-indicator {
        background-color: rgba(0, 0, 0, 0.7);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 500;
      }
      
      .swipe-indicator {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: var(--swipe-color);
        opacity: 0;
        transition: opacity 150ms ease;
        pointer-events: none;
      }
      
      .swipe-indicator.left {
        background: linear-gradient(to right, var(--swipe-color), transparent);
      }
      
      .swipe-indicator.right {
        background: linear-gradient(to left, var(--swipe-color), transparent);
      }
      
      .swipe-hint {
        position: absolute;
        bottom: 60px;
        left: 0;
        width: 100%;
        text-align: center;
        color: rgba(255, 255, 255, 0.6);
        font-size: 12px;
        opacity: 1;
        transition: opacity 1.5s;
      }
      
      .close-button {
        position: absolute;
        top: -50px;
        right: 0;
        color: white;
        font-size: 2.5rem;
        cursor: pointer;
        z-index: 30;
      }
      
      @media (max-width: 768px) {
        .modal-content {
          height: 80vh;
        }
        
        .media-container {
          height: 70vh;
        }
        
        .nav-button {
          width: 40px;
          height: 40px;
          font-size: 16px;
        }
        
        .video-play-button {
          width: 50px;
          height: 50px;
          font-size: 24px;
        }
        
        .close-button {
          top: -40px;
          font-size: 2rem;
        }
        
        .counter-indicator {
          font-size: 12px;
          padding: 4px 12px;
        }
      }
    `);
    
    // Klasse zum Modal hinzufügen für verbesserte Selektoren
    if (this.modal) {
      this.modal.classList.add('gallery-modal');
    }
  }
  
  // Hinzufügen von CSS-Styles
  addStyles(css) {
    const styleElement = document.createElement('style');
    styleElement.textContent = css;
    document.head.appendChild(styleElement);
  }
  
  // Modifizieren der Galerie-Elemente
  modifyGalleryItems() {
    // Alle Galerie-Elemente finden
    const galleryItems = document.querySelectorAll('.gallery-item');
    
    // Für jedes Element den Event-Listener neu setzen
    galleryItems.forEach((item, index) => {
      // Clone erstellen, um alte Event-Listener zu entfernen
      const newItem = item.cloneNode(true);
      item.parentNode.replaceChild(newItem, item);
      
      // Neuen Event-Listener hinzufügen
      newItem.addEventListener('click', () => {
        this.open(index);
      });
    });
  }
  
  // Erstellen des Medien-Containers
  createMediaContainer() {
    if (this.mediaContainer) {
      // Container zurücksetzen
      this.mediaContainer.innerHTML = '';
    } else {
      // Neuen Container erstellen
      this.mediaContainer = document.createElement('div');
      this.mediaContainer.className = 'media-container';
      this.modalContent.appendChild(this.mediaContainer);
    }
    
    // Swipe-Indikator hinzufügen
    const swipeIndicator = document.createElement('div');
    swipeIndicator.className = 'swipe-indicator';
    this.mediaContainer.appendChild(swipeIndicator);
    this.swipeIndicator = swipeIndicator;
    
    return this.mediaContainer;
  }
  
  // Erstellen der Navigations-Elemente
  createNavigationControls() {
    // Bestehende Navigation entfernen
    const existingNav = document.querySelector('.navigation-controls');
    if (existingNav) {
      existingNav.remove();
    }
    
    // Container für Navigation
    const navContainer = document.createElement('div');
    navContainer.className = 'navigation-controls';
    
    // Vorheriges Bild Button
    const prevButton = document.createElement('button');
    prevButton.className = 'nav-button prev-button';
    prevButton.innerHTML = '<i class="fas fa-chevron-left"></i>';
    prevButton.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.showPrevious();
    });
    
    // Zähler für die Position
    const counter = document.createElement('div');
    counter.className = 'counter-indicator';
    
    // Nächstes Bild Button
    const nextButton = document.createElement('button');
    nextButton.className = 'nav-button next-button';
    nextButton.innerHTML = '<i class="fas fa-chevron-right"></i>';
    nextButton.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.showNext();
    });
    
    // Bei mobilen Geräten Swipe-Hinweis anzeigen
    if (this.isMobile) {
      const swipeHint = document.createElement('div');
      swipeHint.className = 'swipe-hint';
      swipeHint.textContent = 'Wischen zum Navigieren';
      this.modalContent.appendChild(swipeHint);
      
      // Nach einigen Sekunden ausblenden
      setTimeout(() => {
        swipeHint.style.opacity = '0';
      }, 2000);
    }
    
    // Elemente zum Container hinzufügen
    navContainer.appendChild(prevButton);
    navContainer.appendChild(counter);
    navContainer.appendChild(nextButton);
    
    // Container zum Modal hinzufügen
    this.modalContent.appendChild(navContainer);
    
    this.navElements = {
      prevButton,
      nextButton,
      counter
    };
    
    return this.navElements;
  }
  
  // Schließen-Button neu erstellen
  createCloseButton() {
    // Bestehenden Button entfernen
    if (this.modalClose) {
      this.modalClose.remove();
    }
    
    // Neuen Button erstellen
    const closeButton = document.createElement('div');
    closeButton.className = 'close-button';
    closeButton.innerHTML = '&times;';
    closeButton.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.close();
    });
    
    // Button zum Modal hinzufügen
    this.modalContent.appendChild(closeButton);
    this.modalClose = closeButton;
    
    return closeButton;
  }
  
  // Zähler aktualisieren
  updateCounter() {
    if (!this.navElements || !this.navElements.counter) return;
    
    const totalItems = this.items.length;
    if (totalItems > 0) {
      this.navElements.counter.textContent = `${this.currentIndex + 1} / ${totalItems}`;
    }
  }
  
  // Modal öffnen mit bestimmtem Index
  open(index) {
    if (this.isAnimating) return;
    
    // Aktuellen Index setzen
    this.currentIndex = this.validateIndex(index);
    
    // Modal anzeigen
    this.modal.classList.add('open');
    
    // Body-Klasse für Scrolling-Verhinderung
    document.body.classList.add('modal-open');
    
    // UI-Elemente erstellen
    this.createMediaContainer();
    this.createNavigationControls();
    this.createCloseButton();
    
    // Medien laden
    this.loadMedia(this.currentIndex);
    
    // Zähler aktualisieren
    this.updateCounter();
  }
  
  // Modal schließen
  close() {
    // Videos stoppen
    this.stopAllVideos();
    
    // Modal schließen
    this.modal.classList.remove('open');
    
    // Body-Klasse entfernen
    document.body.classList.remove('modal-open');
    
    // Zurücksetzen
    this.isAnimating = false;
  }
  
  // Alle Videos stoppen
  stopAllVideos() {
    const videos = this.modal.querySelectorAll('video');
    videos.forEach(video => {
      video.pause();
      video.currentTime = 0;
    });
    this.isVideoPlaying = false;
    this.videoInstance = null;
  }
  
  // Index validieren
  validateIndex(index) {
    if (index < 0) return this.items.length - 1;
    if (index >= this.items.length) return 0;
    return index;
  }
  
  // Vorheriges Medium anzeigen
  showPrevious() {
    if (this.isAnimating) return;
    this.navigate(-1);
  }
  
  // Nächstes Medium anzeigen
  showNext() {
    if (this.isAnimating) return;
    this.navigate(1);
  }
  
  // Navigation in eine Richtung
  navigate(direction) {
    if (this.isAnimating) return;
    this.isAnimating = true;
    
    // Videos stoppen
    this.stopAllVideos();
    
    // Neuen Index berechnen
    const newIndex = this.validateIndex(this.currentIndex + direction);
    
    // Animation der Richtung
    const currentItem = this.mediaContainer.querySelector('.media-item.current');
    if (currentItem) {
      if (direction > 0) {
        currentItem.classList.remove('current');
        currentItem.classList.add('previous');
      } else {
        currentItem.classList.remove('current');
        currentItem.classList.add('next');
      }
    }
    
    // Neues Medium laden
    this.loadMedia(newIndex);
    
    // Nach Animation zurücksetzen
    setTimeout(() => {
      this.isAnimating = false;
      
      // Alte Items entfernen, die nicht mehr sichtbar sind
      const oldItems = this.mediaContainer.querySelectorAll('.media-item:not(.current)');
      oldItems.forEach(item => item.remove());
      
    }, 300); // Übereinstimmend mit CSS-Transition
    
    // Index aktualisieren
    this.currentIndex = newIndex;
    
    // Zähler aktualisieren
    this.updateCounter();
  }
  
  // Medium laden
  loadMedia(index) {
    if (!this.items[index]) return;
    
    const item = this.items[index];
    const mediaType = item.type || 'image';
    const mediaSource = item.source || item.image;
    
    // Medien-Item erstellen
    const mediaItem = document.createElement('div');
    mediaItem.className = 'media-item current';
    
    if (mediaType === 'video') {
      // Video-Container erstellen
      const videoContainer = document.createElement('div');
      videoContainer.className = 'video-container';
      
      // Thumbnail erstellen
      const thumbnail = document.createElement('div');
      thumbnail.className = 'video-thumbnail';
      
      // Thumbnail-Bild
      const thumbnailImg = document.createElement('img');
      thumbnailImg.className = 'media-content';
      thumbnailImg.src = this.getVideoThumbnailPlaceholder();
      
      // Play-Button
      const playButton = document.createElement('div');
      playButton.className = 'video-play-button';
      playButton.innerHTML = '<i class="fas fa-play"></i>';
      
      // Zusammenfügen
      thumbnail.appendChild(thumbnailImg);
      thumbnail.appendChild(playButton);
      videoContainer.appendChild(thumbnail);
      
      // Klick-Handler zum Abspielen des Videos
      thumbnail.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.playVideo(mediaSource, videoContainer);
      });
      
      // Video-Thumbnail generieren
      this.generateVideoThumbnail(mediaSource, (thumbnailUrl) => {
        if (thumbnailUrl) {
          thumbnailImg.src = thumbnailUrl;
        }
      });
      
      mediaItem.appendChild(videoContainer);
    } else {
      // Bild erstellen
      const img = document.createElement('img');
      img.className = 'media-content';
      img.src = mediaSource;
      img.alt = item.title || '';
      
      // Verhindern, dass Klick auf das Bild das Modal schließt
      img.addEventListener('click', (e) => {
        e.stopPropagation();
      });
      
      mediaItem.appendChild(img);
    }
    
    // Zum Container hinzufügen
    this.mediaContainer.appendChild(mediaItem);
  }
  
  // Video abspielen
  playVideo(source, container) {
    // Thumbnail entfernen
    const thumbnail = container.querySelector('.video-thumbnail');
    if (thumbnail) {
      thumbnail.remove();
    }
    
    // Video erstellen
    const video = document.createElement('video');
    video.className = 'media-content';
    video.controls = true;
    video.autoplay = true;
    video.muted = false;
    video.loop = true;
    video.src = source;
    video.volume = 0.15;
    
    // Attribute für mobiles Abspielen
    video.setAttribute('playsinline', '');
    video.setAttribute('webkit-playsinline', '');
    
    // Verhindern, dass Klick auf das Video das Modal schließt
    video.addEventListener('click', (e) => {
      e.stopPropagation();
    });
    
    // Video zum Container hinzufügen
    container.appendChild(video);
    
    // Video-Status setzen
    this.isVideoPlaying = true;
    this.videoInstance = video;
    
    // Video abspielen
    video.play().catch(err => {
      console.error('Video konnte nicht abgespielt werden:', err);
    });
  }
  
  // Placeholder für Video-Thumbnail
  getVideoThumbnailPlaceholder() {
    return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200"><rect width="300" height="200" fill="%23333"/><text x="150" y="100" font-family="Arial" font-size="14" fill="%23fff" text-anchor="middle">Video wird geladen...</text></svg>';
  }
  
  // Video-Thumbnail generieren
  generateVideoThumbnail(videoSrc, callback) {
    const tempVideo = document.createElement('video');
    
    // Thumbnail erzeugen, sobald das Video geladen ist
    tempVideo.addEventListener('loadeddata', () => {
      // Zum optimalen Frame springen (z.B. 0.5 Sekunden)
      tempVideo.currentTime = 0.5;
    });
    
    // Wenn zum Frame gesprungen wurde, Canvas erstellen
    tempVideo.addEventListener('seeked', () => {
      const canvas = document.createElement('canvas');
      canvas.width = tempVideo.videoWidth;
      canvas.height = tempVideo.videoHeight;
      
      // Frame zeichnen
      const ctx = canvas.getContext('2d');
      ctx.drawImage(tempVideo, 0, 0, canvas.width, canvas.height);
      
      // URL des Thumbnails zurückgeben
      const thumbnailUrl = canvas.toDataURL('image/jpeg');
      callback(thumbnailUrl);
      
      // Aufräumen
      tempVideo.remove();
    });
    
    // Fehlerbehandlung
    tempVideo.addEventListener('error', () => {
      console.error('Fehler beim Laden des Videos:', videoSrc);
      callback('');
    });
    
    // Video laden
    tempVideo.crossOrigin = 'anonymous';
    tempVideo.src = videoSrc;
    tempVideo.load();
    tempVideo.style.display = 'none';
    document.body.appendChild(tempVideo);
  }
  
  // Touch-Start-Ereignis
  handleTouchStart(event) {
    // Touch-Startposition speichern
    this.touchStartX = event.touches[0].clientX;
    this.touchStartY = event.touches[0].clientY;
    this.touchMoved = false;
  }
  
  // Touch-Move-Ereignis mit visueller Rückmeldung
  handleTouchMove(event) {
    if (!this.touchStartX) return;
    
    // Wenn ein Video abgespielt wird, keine Swipe-Gesten
    if (this.isVideoPlaying) return;
    
    // Aktuelle Position
    const touchX = event.touches[0].clientX;
    const touchY = event.touches[0].clientY;
    
    // Differenz berechnen
    const diffX = touchX - this.touchStartX;
    const diffY = Math.abs(touchY - this.touchStartY);
    
    // Nur horizontale Bewegungen verarbeiten, wenn die vertikale Bewegung nicht zu groß ist
    if (Math.abs(diffX) > 10 && diffY < 50) {
      // Verhindern des Scrollens
      event.preventDefault();
      
      // Visuelle Rückmeldung
      if (this.swipeIndicator) {
        // Transparenz basierend auf der Swipe-Distanz
        const opacity = Math.min(Math.abs(diffX) / 200, 0.5);
        this.swipeIndicator.style.opacity = opacity;
        
        // Links/Rechts-Indikator
        if (diffX > 0) {
          this.swipeIndicator.classList.add('right');
          this.swipeIndicator.classList.remove('left');
        } else {
          this.swipeIndicator.classList.add('left');
          this.swipeIndicator.classList.remove('right');
        }
      }
      
      this.touchMoved = true;
    }
  }
  
  // Touch-End-Ereignis
  handleTouchEnd(event) {
    if (!this.touchStartX || !this.touchMoved) return;
    
    // Wenn ein Video abgespielt wird, keine Swipe-Gesten
    if (this.isVideoPlaying) return;
    
    // Endposition
    const touchEndX = event.changedTouches[0].clientX;
    const touchEndY = event.changedTouches[0].clientY;
    
    // Differenz berechnen
    const diffX = touchEndX - this.touchStartX;
    const diffY = Math.abs(touchEndY - this.touchStartY);
    
    // Visuellen Indikator zurücksetzen
    if (this.swipeIndicator) {
      this.swipeIndicator.style.opacity = 0;
      this.swipeIndicator.classList.remove('left', 'right');
    }
    
    // Nur horizontale Bewegungen, wenn die vertikale Bewegung nicht zu groß ist
    if (Math.abs(diffX) > this.swipeThreshold && diffY < 50) {
      if (diffX > 0) {
        // Nach rechts - vorheriges Bild
        this.showPrevious();
      } else {
        // Nach links - nächstes Bild
        this.showNext();
      }
    }
    
    // Zurücksetzen
    this.touchStartX = 0;
    this.touchStartY = 0;
    this.touchMoved = false;
  }
  
  // Keyboard-Navigation
  handleKeyboard(event) {
    // Nur reagieren, wenn das Modal geöffnet ist
    if (!this.modal.classList.contains('open')) return;
    
    switch (event.key) {
      case 'ArrowLeft':
        this.showPrevious();
        break;
      case 'ArrowRight':
        this.showNext();
        break;
      case 'Escape':
        this.close();
        break;
    }
  }
  
  // Fenstergrößenänderung
  handleResize() {
    // Mobilen Status aktualisieren
    this.isMobile = window.innerWidth <= 768;
    
    // Swipe-Schwellenwert anpassen
    this.swipeThreshold = this.isMobile ? 50 : 100;
  }
}

// Initialisierung nach dem Laden der Seite
document.addEventListener('DOMContentLoaded', () => {
  // Bestehende Funktion sichern
  const originalCreateGallery = window.createGallery;
  
  // Neue Galerie-Funktion
  window.createGallery = function() {
    // Originale Funktion aufrufen
    if (typeof originalCreateGallery === 'function') {
      originalCreateGallery();
    }
    
    // Nach kurzer Verzögerung neue Galerie initialisieren
    setTimeout(() => {
      // Neue Galerie-Instanz erstellen
      window.galleryModal = new GallerySwipeModal();
    }, 500);
  };
  
  // Falls die Seite bereits geladen ist
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    // Galerie direkt initialisieren
    window.galleryModal = new GallerySwipeModal();
  }
});

//-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


// ===== IMPROVED GALLERY JAVASCRIPT =====

// Gallery Data - Deine bestehenden Daten
const improvedGalleryItems = [
    {
        id: 1,
        image: '/static/css/images/gallery/alex1.jpeg',
        title: 'Geburtstagsfeier',
        type: 'image'
    },
    {
        id: 2,
        image: '/static/css/images/gallery/alex2.png',
        title: 'Weiße Socken zu den Schuhen',
        type: 'image'
    },
    {
        id: 3,
        source: '/static/css/images/gallery/alex10.mp4',
        title: 'Klassischer Handschlag',
        type: 'video'
    },
    {
        id: 4,
        image: '/static/css/images/gallery/alex3.jpeg',
        title: 'Potsdam Oktoberfest',
        type: 'image'
    },
    {
        id: 5,
        image: '/static/css/images/gallery/alex4.jpeg',
        title: 'Baumblüte',
        type: 'image'
    },
    {
        id: 6,
        image: '/static/css/images/gallery/alex5.jpeg',
        title: 'Abend mit Freunden',
        type: 'image'
    },
    {
        id: 7,
        image: '/static/css/images/gallery/alex6.jpeg',
        title: 'Ready machen für Berlin',
        type: 'image'
    },
    {
        id: 8,
        source: '/static/css/images/gallery/alex11.mp4',
        title: 'World Club Dome abkühlen',
        type: 'video'
    },
    {
        id: 9,
        image: '/static/css/images/gallery/alex7.jpeg',
        title: 'SMS Festival',
        type: 'image'
    },
    {
        id: 10,
        image: '/static/css/images/gallery/alex8.jpeg',
        title: 'Malle',
        type: 'image'
    },
    {
        id: 11,
        source: '/static/css/images/gallery/alex12.mp4',
        title: 'Aftern nach Geburtstag',
        type: 'video'
    },
    {
        id: 12,
        image: '/static/css/images/gallery/alex9.jpeg',
        title: 'World Club Dome',
        type: 'image'
    }
];

class ImprovedGallery {
    constructor() {
        this.currentIndex = 0;
        this.items = improvedGalleryItems;
        this.modal = document.getElementById('improved-modal');
        this.modalMedia = document.getElementById('improved-modal-media');
        this.modalClose = document.getElementById('improved-modal-close');
        this.modalPrev = document.getElementById('improved-modal-prev');
        this.modalNext = document.getElementById('improved-modal-next');
        this.modalCounter = document.getElementById('improved-modal-counter');
        this.galleryGrid = document.getElementById('gallery-grid');
        
        // Touch-Variablen
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.isSwiping = false;
        this.swipeThreshold = 50;
        
        // Check if elements exist
        if (!this.modal || !this.galleryGrid) {
            console.error('Required gallery elements not found');
            return;
        }
        
        this.init();
    }

    init() {
        this.createGallery();
        this.bindEvents();
    }

    createGallery() {
        // Clear existing content
        this.galleryGrid.innerHTML = '';
        
        this.items.forEach((item, index) => {
            const galleryItem = document.createElement('div');
            galleryItem.className = 'gallery-item fade-in';
            galleryItem.addEventListener('click', () => this.openModal(index));

            if (item.type === 'video') {
                // Video Thumbnail erstellen
                const videoContainer = document.createElement('div');
                videoContainer.className = 'video-thumbnail-container';
                
                const video = document.createElement('video');
                video.src = item.source;
                video.muted = true;
                video.preload = 'metadata';
                video.addEventListener('loadedmetadata', () => {
                    // Set video to first frame
                    video.currentTime = 0.1;
                });
                
                const playButton = document.createElement('button');
                playButton.className = 'video-play-button';
                playButton.innerHTML = '<i class="fas fa-play"></i>';
                playButton.setAttribute('aria-label', 'Video abspielen');
                
                const indicator = document.createElement('div');
                indicator.className = 'video-indicator';
                indicator.innerHTML = '<i class="fas fa-video"></i> Video';
                
                videoContainer.appendChild(video);
                videoContainer.appendChild(playButton);
                videoContainer.appendChild(indicator);
                galleryItem.appendChild(videoContainer);
            } else {
                // Bild erstellen
                const img = document.createElement('img');
                img.src = item.image;
                img.alt = item.title;
                img.loading = 'lazy';
                
                // Error handling für Bilder
                img.addEventListener('error', () => {
                    console.error(`Failed to load image: ${item.image}`);
                    img.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect width="300" height="300" fill="%23333"/><text x="150" y="150" font-family="Arial" font-size="14" fill="%23fff" text-anchor="middle">Bild nicht verfügbar</text></svg>';
                });
                
                galleryItem.appendChild(img);
            }

            // Overlay hinzufügen
            const overlay = document.createElement('div');
            overlay.className = 'gallery-overlay';
            const title = document.createElement('h3');
            title.className = 'gallery-title';
            title.textContent = item.title;
            overlay.appendChild(title);
            galleryItem.appendChild(overlay);

            this.galleryGrid.appendChild(galleryItem);
        });

        // Trigger fade-in animation
        setTimeout(() => {
            document.querySelectorAll('.gallery-item').forEach(item => {
                item.classList.add('active');
            });
        }, 100);
    }

    bindEvents() {
        // Modal schließen
        if (this.modalClose) {
            this.modalClose.addEventListener('click', () => this.closeModal());
        }
        
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });

        // Navigation
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

        // Tastatur-Navigation
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

        // Touch-Events für Swipe
        this.modal.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        this.modal.addEventListener('touchmove', (e) => this.handleTouchMove(e), { passive: false });
        this.modal.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
    }

    openModal(index) {
        this.currentIndex = index;
        
        // Prevent pull-to-refresh and browser navigation
        this.preventOverscroll();
        
        this.showMedia();
        this.modal.classList.add('active');
        document.body.classList.add('improved-modal-open');
        
        // Swipe-Hinweis auf Mobile anzeigen
        if (window.innerWidth <= 768) {
            this.showSwipeHint();
        }
    }

    closeModal() {
        this.modal.classList.remove('active');
        document.body.classList.remove('improved-modal-open');
        
        // Re-enable overscroll
        this.restoreOverscroll();
        
        // Alle Videos stoppen
        const videos = this.modal.querySelectorAll('video');
        videos.forEach(video => {
            video.pause();
            video.currentTime = 0;
        });
        
        // Swipe hint entfernen falls vorhanden
        const swipeHint = this.modal.querySelector('.swipe-hint');
        if (swipeHint) {
            swipeHint.remove();
        }
    }

    showMedia() {
        const item = this.items[this.currentIndex];
        if (!item) return;
        
        this.updateCounter();

        // Altes Video entfernen
        const existingVideo = this.modal.querySelector('video:not(#improved-modal-media)');
        if (existingVideo) {
            existingVideo.remove();
        }

        if (item.type === 'video') {
            // Bild verstecken
            this.modalMedia.style.display = 'none';
            
            // Video erstellen
            const video = document.createElement('video');
            video.className = 'improved-modal-media';
            video.controls = true;
            video.autoplay = false;
            video.muted = false;
            video.loop = true;
            video.src = item.source;
            video.volume = 0.2;
            video.setAttribute('playsinline', '');
            video.setAttribute('webkit-playsinline', '');
            
            // Video verhindern das Modal zu schließen
            video.addEventListener('click', (e) => e.stopPropagation());
            
            // Error handling für Videos
            video.addEventListener('error', () => {
                console.error(`Failed to load video: ${item.source}`);
                // Fallback: zeige einen Fehler-Platzhalter
                video.style.display = 'none';
                this.modalMedia.style.display = 'block';
                this.modalMedia.src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300"><rect width="400" height="300" fill="%23333"/><text x="200" y="150" font-family="Arial" font-size="16" fill="%23fff" text-anchor="middle">Video nicht verfügbar</text></svg>';
                this.modalMedia.alt = 'Video nicht verfügbar';
            });
            
            // Video zur Modal hinzufügen
            this.modal.querySelector('.improved-modal-content').insertBefore(video, this.modalCounter);
        } else {
            // Video verstecken, Bild anzeigen
            this.modalMedia.style.display = 'block';
            this.modalMedia.src = item.image;
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
        // Überprüfen ob bereits ein Hinweis existiert
        if (this.modal.querySelector('.swipe-hint')) return;
        
        const hint = document.createElement('div');
        hint.className = 'swipe-hint';
        hint.textContent = '← Wischen zum Navigieren →';
        this.modal.querySelector('.improved-modal-content').appendChild(hint);
        
        // Hinweis nach 3 Sekunden entfernen
        setTimeout(() => {
            if (hint.parentNode) {
                hint.remove();
            }
        }, 3000);
    }

    // Touch-Events für Swipe-Funktionalität
    handleTouchStart(e) {
        // Verhindere Standard-Browser-Verhalten
        if (e.target.closest('.improved-modal-content')) {
            this.touchStartX = e.touches[0].clientX;
            this.touchStartY = e.touches[0].clientY;
            this.isSwiping = false;
        }
    }

    handleTouchMove(e) {
        if (!this.touchStartX || !this.touchStartY) return;

        this.touchEndX = e.touches[0].clientX;
        this.touchEndY = e.touches[0].clientY;

        const diffX = this.touchStartX - this.touchEndX;
        const diffY = this.touchStartY - this.touchEndY;

        // Nur horizontale Swipes verarbeiten und Browser-Navigation verhindern
        if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > 10) {
            e.preventDefault(); // Scrollen und Browser-Navigation verhindern
            e.stopPropagation(); // Event-Bubbling stoppen
            this.isSwiping = true;
            this.modal.classList.add('swiping');
        }
    }

    handleTouchEnd(e) {
        if (!this.isSwiping) {
            // Reset touch coordinates
            this.touchStartX = 0;
            this.touchStartY = 0;
            return;
        }

        const diffX = this.touchStartX - this.touchEndX;
        
        this.modal.classList.remove('swiping');

        if (Math.abs(diffX) > this.swipeThreshold) {
            if (diffX > 0) {
                this.nextItem(); // Nach links wischen = nächstes Bild
            } else {
                this.previousItem(); // Nach rechts wischen = vorheriges Bild
            }
        }

        // Reset
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.isSwiping = false;
    }

    // Prevent overscroll behavior
    preventOverscroll() {
        // Store current body position to restore later
        this.bodyScrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Prevent pull-to-refresh and overscroll
        document.body.style.position = 'fixed';
        document.body.style.top = `-${this.bodyScrollTop}px`;
        document.body.style.width = '100%';
        
        // Prevent touchmove on document level when modal is open
        this.preventTouchMove = (e) => {
            // Allow touch events only within modal content
            if (!e.target.closest('.improved-modal-content')) {
                e.preventDefault();
            }
        };
        
        document.addEventListener('touchmove', this.preventTouchMove, { passive: false });
    }

    // Restore overscroll behavior
    restoreOverscroll() {
        // Remove event listener
        if (this.preventTouchMove) {
            document.removeEventListener('touchmove', this.preventTouchMove);
        }
        
        // Restore body position
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        
        // Restore scroll position
        if (this.bodyScrollTop !== undefined) {
            window.scrollTo(0, this.bodyScrollTop);
        }
    }
}

// Globale Variable für die Galerie-Instanz
let improvedGalleryInstance = null;

// Funktion zum Initialisieren der verbesserten Galerie
function initImprovedGallery() {
    // Alte Galerie-Funktionalität deaktivieren falls vorhanden
    const oldModal = document.getElementById('galleryModal');
    if (oldModal) {
        oldModal.style.display = 'none';
    }
    
    // Neue Galerie initialisieren
    if (!improvedGalleryInstance) {
        improvedGalleryInstance = new ImprovedGallery();
    }
}

// Event-Listener für DOM-Bereitschaft
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initImprovedGallery);
} else {
    // DOM ist bereits geladen
    initImprovedGallery();
}

// Bestehende createGallery-Funktion überschreiben falls vorhanden
if (typeof window.createGallery === 'function') {
    const originalCreateGallery = window.createGallery;
    window.createGallery = function() {
        // Nach kurzer Verzögerung neue Galerie initialisieren
        setTimeout(() => {
            initImprovedGallery();
        }, 100);
    };
}