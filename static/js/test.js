let isMoved = false;
let index = 0; // Globale Variable zum Verfolgen der Position beim Schreiben von Text

// Verhindere Scrollen und initiiere Tippeffekt beim Laden der Seite
window.onload = function() {
    document.body.classList.add('no-scroll');
    typeText(document.getElementById('click-me-text'), "Click me");
};

// Funktion, um Text Buchstabe für Buchstabe zu tippen
function typeText(element, textToType) {
    if (index < textToType.length) {
        element.textContent += textToType.charAt(index++);
        setTimeout(() => typeText(element, textToType), 100);
    }
}

// Funktion, um das Bild nach Links zu verschieben und den About-Me-Text anzuzeigen
function moveImageToLeft() {
    if (isMoved) return;
    
    document.getElementById('click-me-text').style.display = 'none';
    document.getElementById('logo-image').style.cssText = 'transition: transform 0.5s; transform: translateX(-50%);'; // Kombiniere mehrere Stile in einer Zeile
    document.getElementById('about-section').style.display = 'block';
    
    setTimeout(typeAboutHeader, 2500); // Warte, bevor mit dem Schreiben der Überschrift begonnen wird

    isMoved = true; // Markiere, dass das Bild verschoben wurde
    document.body.classList.remove('no-scroll');
    document.querySelector('.navbar').style.display = 'block';
}

let aboutHeaderIndex = 0;
const aboutHeaderText = "Welcome";

// Funktion, um die "About me"-Überschrift Buchstabe für Buchstabe zu tippen
function typeAboutHeader() {
    const aboutHeader = document.getElementById('about-header');
    if (aboutHeaderIndex < aboutHeaderText.length) {
        aboutHeader.textContent += aboutHeaderText.charAt(aboutHeaderIndex++);
        setTimeout(typeAboutHeader, 150);
    }
}

// Zeige den "About me"-Paragraphen
const aboutParagraph = document.getElementById('about-paragraph');
aboutParagraph.innerHTML = 'Welcome to a pixel adventure! I am <strong>Alex Volkmann</strong>, crafting code and design into unique digital experiences. Get to know me better.';

let currentImageIndex = 0; // Variable zum Verfolgen des aktuellen Bildindex

// Funktion, um das Profilbild zu ändern, wenn es angeklickt wird
function changeProfileImage() {
    const images = JSON.parse(document.getElementById('profile-picture').getAttribute('data-images'));
    currentImageIndex = (currentImageIndex + 1) % images.length;
    document.getElementById('profile-image').src = images[currentImageIndex];
}

// Event Listener für das Laden des DOM und das Klicken auf das Profilbild
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('profile-picture').addEventListener('click', changeProfileImage);
});

//----------------------------------------------------------------------------------------------------------------

//Animation Figur
//----------------------------------------------------------------------------------------------------------------
let figure = document.getElementById('pixel-figure-container');
let containerWidth = window.innerWidth;
let figureWidth = 50; // Die Breite Ihrer Figur
let speed = 200; // Geschwindigkeit, wie schnell die Figur sich bewegt (Pixel pro Sekunde)
let position = 0; // Startposition
let movingRight = true; // Startet mit der Bewegung nach rechts

function updatePosition(delta) {
  // Position aktualisieren basierend auf der Bewegungsrichtung
  position += (movingRight ? 1 : -1) * delta * speed;
  
  // Überprüfen, ob die Figur den Rand erreicht hat
  if (position > containerWidth - figureWidth) {
    position = containerWidth - figureWidth;
    movingRight = false;
    figure.classList.add('flipped'); // Klasse, um die Figur zu spiegeln
  } else if (position < 0) {
    position = 0;
    movingRight = true;
    figure.classList.remove('flipped'); // Klasse entfernen, um die Figur zurückzusetzen
  }
  
  // Position der Figur aktualisieren
  figure.style.transform = `translateX(${position}px)`;
}

// Animation Loop
function animate(timestamp) {
  // Delta Zeit seit dem letzten Frame berechnen
  if (!lastTimestamp) lastTimestamp = timestamp;
  let delta = (timestamp - lastTimestamp) / 1000; // in Sekunden
  lastTimestamp = timestamp;

  updatePosition(delta);
  requestAnimationFrame(animate);
}

// Start der Animation
let lastTimestamp;
requestAnimationFrame(animate);

// Event Listener für das Klicken auf das Logo
document.addEventListener('DOMContentLoaded', function() {
  let logo = document.getElementById('logo-image');
  if (logo) {
    logo.addEventListener('click', function() {
      figure.style.visibility = 'visible';
      requestAnimationFrame(animate);
    });
  } else {
    console.error('Das Logo-Image-Element wurde nicht gefunden.');
  }
});
//----------------------------------------------------------------------------------------------------------------

  