// JavaScript für die Galerie-Funktionalität
document.addEventListener('DOMContentLoaded', function() {
    // Elemente auswählen
    const filterButtons = document.querySelectorAll('.filter-btn');
    const galleryItems = document.querySelectorAll('.gallery-item');
    const loadMoreButton = document.querySelector('.load-more');
    
    // Anfangszustand: Zeige nur die ersten 12 Bilder
    const itemsToShow = 12;
    let currentlyShown = itemsToShow;
    
    // Anfangs verstecke alle Bilder über dem Limit
    galleryItems.forEach((item, index) => {
        if (index >= itemsToShow) {
            item.style.display = 'none';
        }
    });
    
    // Wenn es weniger oder genau 12 Bilder gibt, verstecke den "Load More" Button
    if (galleryItems.length <= itemsToShow) {
        loadMoreButton.style.display = 'none';
    }
    
    // "Load More" Button Funktionalität
    loadMoreButton.addEventListener('click', function() {
        // Zeige 6 weitere Bilder an
        const batchSize = 6;
        for (let i = currentlyShown; i < currentlyShown + batchSize; i++) {
            if (galleryItems[i]) {
                galleryItems[i].style.display = 'block';
                // Animation für neu geladene Bilder
                setTimeout(() => {
                    galleryItems[i].style.opacity = '1';
                    galleryItems[i].style.transform = 'translateY(0)';
                }, 50 * (i - currentlyShown));
            }
        }
        
        currentlyShown += batchSize;
        
        // Verstecke den Button, wenn alle Bilder geladen sind
        if (currentlyShown >= galleryItems.length) {
            loadMoreButton.style.display = 'none';
        }
        
        // Filtere die neu geladenen Bilder basierend auf dem aktiven Filter
        const activeFilter = document.querySelector('.filter-btn.active').getAttribute('data-filter');
        filterGallery(activeFilter);
    });
    
    // Filter-Funktionalität
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Aktiven Button markieren
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Bilder filtern basierend auf Kategorie
            const filterValue = this.getAttribute('data-filter');
            filterGallery(filterValue);
        });
    });
    
    // Funktion zum Filtern der Galerie
    function filterGallery(filter) {
        galleryItems.forEach(item => {
            // Ignoriere versteckte Elemente (über dem aktuellen "Load More" Limit)
            if (item.style.display === 'none') return;
            
            const category = item.getAttribute('data-category');
            
            if (filter === 'all' || filter === category) {
                item.classList.remove('hidden');
                setTimeout(() => {
                    item.style.opacity = '1';
                    item.style.transform = '';
                }, 50);
            } else {
                item.classList.add('hidden');
                item.style.opacity = '0';
                item.style.transform = 'scale(0.8)';
            }
        });
    }
    
    // Animation beim Scrollen für Galerieelemente
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    // Beobachte alle Galerieelemente, die sichtbar sind
    galleryItems.forEach((item, index) => {
        if (index < itemsToShow) {
            // Verzögere die Animation basierend auf dem Index
            setTimeout(() => {
                observer.observe(item);
            }, 100 * index);
        }
    });
    
    // Zusätzliche Stilregeln für Animation hinzufügen
    const style = document.createElement('style');
    style.textContent = `
        .gallery-item {
            opacity: 0;
            transform: translateY(20px);
            transition: opacity 0.6s ease, transform 0.6s ease;
        }
        
        .gallery-item.in-view {
            opacity: 1;
            transform: translateY(0);
        }
    `;
    document.head.appendChild(style);
});