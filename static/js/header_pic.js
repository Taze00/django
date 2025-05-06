// Verbesserte Typing Animation ohne Layout-Verschiebung
document.addEventListener('DOMContentLoaded', function() {
    const words = ["WEBDESIGN", "DEVELOPER", "STUDENT", "CREATIVE", "TECHNO"];
    let wordIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    
    // Geschwindigkeits- und Pauseneinstellungen
    const typingSpeed = 120;
    const deletingSpeed = 60; 
    const pauseAfterWord = 1500;
    
    // Ziel-Element für die Animation
    const animatedText = document.getElementById("animated-text");
    
    // Wichtig: Wir stellen sicher, dass der Container sofort seine volle Größe hat
    if (animatedText) {
        // Finde das längste Wort
        const longestWord = words.reduce((a, b) => a.length > b.length ? a : b);
        
        // Erstelle ein unsichtbares Element mit dem längsten Wort,
        // um den Container zu initialisieren und Layout-Verschiebungen zu vermeiden
        const tempText = document.createElement('span');
        tempText.style.visibility = 'hidden';
        tempText.style.position = 'absolute';
        tempText.style.fontSize = '2rem';
        tempText.style.fontWeight = '600';
        tempText.textContent = longestWord;
        
        // Füge das temporäre Element neben dem eigentlichen Text ein
        animatedText.parentNode.appendChild(tempText);
        
        // Entferne es nach einer kurzen Verzögerung wieder
        setTimeout(() => {
            if (tempText.parentNode) {
                tempText.parentNode.removeChild(tempText);
            }
        }, 500);
    }
    
    // Hauptfunktion für die Schreibanimation
    function typeEffect() {
        if (!animatedText) return;
        
        const currentWord = words[wordIndex];
    
        // Text aktualisieren mit Hinzufügen oder Löschen von Zeichen
        const visibleText = isDeleting 
            ? currentWord.substring(0, charIndex--) 
            : currentWord.substring(0, charIndex++);
    
        animatedText.textContent = visibleText;
        
        // Die Textzentrierung kann Layout-Verschiebungen verursachen,
        // daher stellen wir sicher, dass der Text zentriert bleibt
        animatedText.style.textAlign = 'center';
    
        // Geschwindigkeit je nach Status
        const speed = isDeleting ? deletingSpeed : typingSpeed;
    
        if (!isDeleting && charIndex === currentWord.length) {
            // Wort ist komplett geschrieben
            setTimeout(() => (isDeleting = true), pauseAfterWord);
        } else if (isDeleting && charIndex === 0) {
            // Wort ist vollständig gelöscht
            isDeleting = false;
            wordIndex = (wordIndex + 1) % words.length;
        }
    
        // Nächsten Frame starten
        setTimeout(typeEffect, speed);
    }
    
    // Scroll-Indikator-Funktionalität
    const scrollIndicator = document.querySelector('.scroll-indicator');
    if (scrollIndicator) {
        scrollIndicator.addEventListener('click', function() {
            const aboutSection = document.querySelector('#about-me');
            if (aboutSection) {
                aboutSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
    
    // Starte die Animation mit Verzögerung
    if (animatedText) {
        setTimeout(() => {
            typeEffect();
        }, 1500);
    }
    
    // Parallax-Effekt
    window.addEventListener('scroll', function() {
        const header = document.querySelector('header');
        const scrollPosition = window.scrollY;
        
        if (header && scrollPosition < window.innerHeight) {
            const headerBackground = document.querySelector('.header-background');
            if (headerBackground) {
                headerBackground.style.transform = `translateY(${scrollPosition * 0.3}px)`;
            }
        }
    });
});