// Hauptfunktionen für die Geburtstagsseite
document.addEventListener('DOMContentLoaded', function() {
    // Konfetti-Effekt initialisieren
    initConfetti();
    
    // Timeline-Animation initialisieren
    initTimelineAnimation();
});

// Konfetti-Effekt
function initConfetti() {
    // Konfetti-Container
    const confettiContainer = document.getElementById('confetti-container');
    
    // Farbpalette für Konfetti
    const colors = ['#ff65a3', '#ff9cc8', '#ffcee4', '#f2a6c7', '#ff8ba7'];
    
    // 50 Konfetti-Elemente erstellen
    for (let i = 0; i < 50; i++) {
        createConfetti();
    }
    
    // Funktion zum Erstellen eines Konfetti-Elements
    function createConfetti() {
        const confetti = document.createElement('div');
        confetti.classList.add('confetti');
        
        // Zufällige Position, Größe, Farbe und Animation
        const size = Math.random() * 10 + 5;
        const color = colors[Math.floor(Math.random() * colors.length)];
        const left = Math.random() * 100; // Prozent
        const animationDuration = Math.random() * 3 + 2; // 2-5 Sekunden
        const animationDelay = Math.random() * 5; // 0-5 Sekunden Verzögerung
        
        // Stil für das Konfetti-Element setzen
        confetti.style.width = `${size}px`;
        confetti.style.height = `${size}px`;
        confetti.style.backgroundColor = color;
        confetti.style.left = `${left}%`;
        confetti.style.animationDuration = `${animationDuration}s`;
        confetti.style.animationDelay = `${animationDelay}s`;
        
        // Manche Konfetti-Elemente rund, manche quadratisch
        if (Math.random() > 0.5) {
            confetti.style.borderRadius = '50%';
        }
        
        confettiContainer.appendChild(confetti);
        
        // Nach der Animation neu erstellen für kontinuierlichen Effekt
        setTimeout(() => {
            confetti.remove();
            createConfetti();
        }, (animationDuration + animationDelay) * 1000);
    }
    
    // Zusätzlicher Konfetti-Effekt beim Klicken auf die Seite
    document.body.addEventListener('click', function(event) {
        // 10 Konfetti an der Klickposition erzeugen
        for (let i = 0; i < 10; i++) {
            const confetti = document.createElement('div');
            confetti.classList.add('confetti');
            
            const size = Math.random() * 10 + 5;
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            confetti.style.width = `${size}px`;
            confetti.style.height = `${size}px`;
            confetti.style.backgroundColor = color;
            confetti.style.left = `${event.clientX}px`;
            confetti.style.top = `${event.clientY}px`;
            confetti.style.position = 'fixed';
            
            if (Math.random() > 0.5) {
                confetti.style.borderRadius = '50%';
            }
            
            // Randomisierte Animation für Explosionseffekt
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * 100 + 50;
            const duration = Math.random() * 1 + 1;
            
            confetti.style.transform = 'translate(-50%, -50%)';
            confetti.style.animation = 'none';
            
            confettiContainer.appendChild(confetti);
            
            // Animation starten nach einem kurzen Timeout
            setTimeout(() => {
                confetti.style.transition = `all ${duration}s ease-out`;
                confetti.style.transform = `translate(${Math.cos(angle) * distance}px, ${Math.sin(angle) * distance}px) rotate(${Math.random() * 360}deg)`;
                confetti.style.opacity = '0';
            }, 10);
            
            // Element entfernen, wenn die Animation beendet ist
            setTimeout(() => {
                confetti.remove();
            }, duration * 1000);
        }
    });
}

// Timeline-Animation
function initTimelineAnimation() {
    // Alle Timeline-Elemente auswählen
    const timelineItems = document.querySelectorAll('.timeline-item');
    
    // IntersectionObserver für Scroll-Animation
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.2  // Element wird sichtbar, wenn 20% im Viewport
    });
    
    // Anfänglichen Stil für alle Timeline-Elemente setzen und Observer hinzufügen
    timelineItems.forEach((item, index) => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(50px)';
        item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        item.style.transitionDelay = `${index * 0.1}s`;
        
        observer.observe(item);
    });
    
    // Galerie-Bilder vergrößern bei Klick
    const galleryImages = document.querySelectorAll('.gallery-img');
    galleryImages.forEach(img => {
        img.addEventListener('click', function() {
            // Modal erstellen für Bild-Vorschau
            const modal = document.createElement('div');
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            modal.style.display = 'flex';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';
            modal.style.zIndex = '1000';
            modal.style.cursor = 'pointer';
            
            // Bild in Modal einfügen
            const modalImg = document.createElement('img');
            modalImg.src = this.src;
            modalImg.style.maxWidth = '90%';
            modalImg.style.maxHeight = '90%';
            modalImg.style.borderRadius = '10px';
            modalImg.style.boxShadow = '0 5px 20px rgba(0, 0, 0, 0.3)';
            
            modal.appendChild(modalImg);
            document.body.appendChild(modal);
            
            // Beim Klicken Modal schließen
            modal.addEventListener('click', function() {
                this.remove();
            });
        });
    });
    
    /* 
    // Optional: Automatisches Scrollen zum aktuellen Tag
    const today = document.querySelector('.special-item');
    if (today) {
        setTimeout(() => {
            today.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }, 1500);
    }
    */
}

// Herzanimation bei Hover auf den heutigen Tag
document.addEventListener('DOMContentLoaded', function() {
    const heartElement = document.querySelector('.heart-animation');
    if (heartElement) {
        heartElement.addEventListener('mouseenter', function() {
            this.style.animation = 'none';
            setTimeout(() => {
                this.style.animation = 'heartbeat 1.5s infinite';
            }, 10);
        });
    }

    // Quiz-Funktionalität
document.addEventListener('DOMContentLoaded', function() {
    initQuiz();
});

function initQuiz() {
    // Variablen
    let currentQuestion = 1;
    let totalQuestions = document.querySelectorAll('.quiz-question').length;
    let score = 0;
    
    // Alle Optionen auswählen
    const quizOptions = document.querySelectorAll('.quiz-option');
    const progressBar = document.querySelector('.progress-bar');
    const restartButton = document.querySelector('.restart-quiz');
    
    // Event-Listener für alle Optionen
    quizOptions.forEach(option => {
        option.addEventListener('click', handleOptionClick);
    });
    
    // Event-Listener für Neustart-Button
    if (restartButton) {
        restartButton.addEventListener('click', restartQuiz);
    }
    
    // Funktion für Klick auf eine Option
    function handleOptionClick() {
        // Alle Optionen für diese Frage deaktivieren
        const currentQuestionElement = document.querySelector(`.quiz-question[data-question="${currentQuestion}"]`);
        const options = currentQuestionElement.querySelectorAll('.quiz-option');
        
        options.forEach(opt => {
            opt.classList.add('disabled');
        });
        
        // Richtige/falsche Antwort markieren
        const isCorrect = this.getAttribute('data-correct') === 'true';
        if (isCorrect) {
            this.classList.add('correct');
            score++;
            
            // Konfetti-Explosion als Belohnung
            createConfettiExplosion(10);
        } else {
            this.classList.add('incorrect');
            
            // Die richtige Antwort hervorheben
            options.forEach(opt => {
                if (opt.getAttribute('data-correct') === 'true') {
                    opt.classList.add('correct');
                }
            });
        }
        
        // Kurze Verzögerung vor dem Weitergehen zur nächsten Frage
        setTimeout(() => {
            // Fortschrittsbalken aktualisieren
            progressBar.style.width = `${(currentQuestion / totalQuestions) * 100}%`;
            
            // Zur nächsten Frage gehen oder Quiz beenden
            if (currentQuestion < totalQuestions) {
                // Aktuelle Frage ausblenden
                currentQuestionElement.style.display = 'none';
                
                // Nächste Frage einblenden
                currentQuestion++;
                const nextQuestion = document.querySelector(`.quiz-question[data-question="${currentQuestion}"]`);
                nextQuestion.style.display = 'block';
            } else {
                // Quiz beenden und Ergebnis anzeigen
                showResult();
            }
        }, 1000);
    }
    
    // Funktion zum Anzeigen des Ergebnisses
    function showResult() {
        // Alle Fragen ausblenden
        document.querySelectorAll('.quiz-question').forEach(question => {
            question.style.display = 'none';
        });
        
        // Ergebnis anzeigen
        const resultElement = document.querySelector('.quiz-result');
        resultElement.style.display = 'block';
        
        // Punktzahl eintragen
        const scoreElement = document.querySelector('.score-number');
        scoreElement.textContent = score;
        
        // Nachricht basierend auf der Punktzahl
        const messageElement = document.querySelector('.result-message');
        let message = '';
        
        if (score === totalQuestions) {
            message = 'Wow! Du kennst uns perfekt! ❤️';
            createConfettiExplosion(50); // Extra Konfetti für perfekte Punktzahl
        } else if (score >= totalQuestions * 0.8) {
            message = 'Fast perfekt! Du kennst uns wirklich gut!';
        } else if (score >= totalQuestions * 0.6) {
            message = 'Gut gemacht! Du kennst uns ziemlich gut.';
        } else if (score >= totalQuestions * 0.4) {
            message = 'Nicht schlecht! Aber da geht noch mehr.';
        } else {
            message = 'Oh! Vielleicht sollten wir mehr Zeit miteinander verbringen?';
        }
        
        messageElement.textContent = message;
    }
    
    // Funktion zum Neustarten des Quiz
    function restartQuiz() {
        // Punktzahl zurücksetzen
        score = 0;
        currentQuestion = 1;
        
        // Fortschrittsbalken zurücksetzen
        progressBar.style.width = `${(1 / totalQuestions) * 100}%`;
        
        // Ergebnis ausblenden
        document.querySelector('.quiz-result').style.display = 'none';
        
        // Erste Frage anzeigen
        document.querySelectorAll('.quiz-question').forEach((question, index) => {
            question.style.display = index === 0 ? 'block' : 'none';
            
            // Alle Optionen zurücksetzen
            const options = question.querySelectorAll('.quiz-option');
            options.forEach(opt => {
                opt.classList.remove('correct', 'incorrect', 'disabled');
            });
        });
    }
    
    // Konfetti-Explosion für richtige Antworten
    function createConfettiExplosion(count) {
        const confettiContainer = document.getElementById('confetti-container');
        const colors = ['#ff65a3', '#ff9cc8', '#ffcee4', '#f2a6c7', '#ff8ba7'];
        
        for (let i = 0; i < count; i++) {
            const confetti = document.createElement('div');
            confetti.classList.add('confetti');
            
            const size = Math.random() * 10 + 5;
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            confetti.style.width = `${size}px`;
            confetti.style.height = `${size}px`;
            confetti.style.backgroundColor = color;
            confetti.style.left = `${Math.random() * 100}%`;
            confetti.style.top = `${Math.random() * 30 + 50}%`;
            confetti.style.position = 'fixed';
            
            if (Math.random() > 0.5) {
                confetti.style.borderRadius = '50%';
            }
            
            // Randomisierte Animation
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * 100 + 50;
            const duration = Math.random() * 1 + 1;
            
            confetti.style.transform = 'translate(-50%, -50%)';
            confetti.style.animation = 'none';
            
            confettiContainer.appendChild(confetti);
            
            setTimeout(() => {
                confetti.style.transition = `all ${duration}s ease-out`;
                confetti.style.transform = `translate(${Math.cos(angle) * distance}px, ${Math.sin(angle) * distance}px) rotate(${Math.random() * 360}deg)`;
                confetti.style.opacity = '0';
            }, 10);
            
            setTimeout(() => {
                confetti.remove();
            }, duration * 1000);
        }
    }
}
});

// Quiz-Funktionalität
document.addEventListener('DOMContentLoaded', function() {
    // Variablen
    let currentQuestion = 1;
    let totalQuestions = document.querySelectorAll('.quiz-question').length;
    let score = 0;
    
    // Alle Optionen auswählen
    const quizOptions = document.querySelectorAll('.quiz-option');
    const progressBar = document.querySelector('.progress-bar');
    const restartButton = document.querySelector('.restart-quiz');
    
    // Event-Listener für alle Optionen
    quizOptions.forEach(option => {
        option.addEventListener('click', handleOptionClick);
    });
    
    // Event-Listener für Neustart-Button
    if (restartButton) {
        restartButton.addEventListener('click', restartQuiz);
    }
    
    // Funktion für Klick auf eine Option
    function handleOptionClick() {
        // Alle Optionen für diese Frage deaktivieren
        const currentQuestionElement = document.querySelector(`.quiz-question[data-question="${currentQuestion}"]`);
        const options = currentQuestionElement.querySelectorAll('.quiz-option');
        
        options.forEach(opt => {
            opt.classList.add('disabled');
        });
        
        // Richtige/falsche Antwort markieren
        const isCorrect = this.getAttribute('data-correct') === 'true';
        if (isCorrect) {
            this.classList.add('correct');
            score++;
            
            // Konfetti-Explosion als Belohnung
            createConfettiExplosion(10);
        } else {
            this.classList.add('incorrect');
            
            // Die richtige Antwort hervorheben
            options.forEach(opt => {
                if (opt.getAttribute('data-correct') === 'true') {
                    opt.classList.add('correct');
                }
            });
        }
        
        // Kurze Verzögerung vor dem Weitergehen zur nächsten Frage
        setTimeout(() => {
            goToNextQuestion();
        }, 1500);
    }
    
    // Zur nächsten Frage gehen
    function goToNextQuestion() {
        // Aktuelle Frage ausblenden
        const currentQuestionElement = document.querySelector(`.quiz-question[data-question="${currentQuestion}"]`);
        currentQuestionElement.style.display = 'none';
        
        // Fortschrittsbalken aktualisieren
        currentQuestion++;
        updateProgressBar();
        
        // Prüfen, ob wir am Ende des Quiz sind
        if (currentQuestion <= totalQuestions) {
            // Nächste Frage anzeigen
            const nextQuestionElement = document.querySelector(`.quiz-question[data-question="${currentQuestion}"]`);
            nextQuestionElement.style.display = 'block';
        } else {
            // Quiz beenden und Ergebnis anzeigen
            showResult();
        }
    }
    
    // Fortschrittsbalken aktualisieren
    function updateProgressBar() {
        const progressPercentage = ((currentQuestion - 1) / totalQuestions) * 100;
        progressBar.style.width = `${progressPercentage}%`;
    }
    
    // Ergebnis anzeigen
    function showResult() {
        const resultElement = document.querySelector('.quiz-result');
        const scoreElement = document.querySelector('.score-number');
        const messageElement = document.querySelector('.result-message');
        
        resultElement.style.display = 'block';
        scoreElement.textContent = score;
        
        // Nachricht basierend auf Punktzahl
        let message = '';
        if (score === totalQuestions) {
            message = 'Perfekt! Du kennst mich wirklich sehr gut! 💜';
            createConfettiExplosion(50); // Große Konfetti-Explosion für perfektes Ergebnis
        } else if (score >= totalQuestions * 0.8) {
            message = 'Sehr gut! Du weißt wirklich viel über uns! 😊';
        } else if (score >= totalQuestions * 0.6) {
            message = 'Gut gemacht! Wir lernen uns immer besser kennen. 😊';
        } else if (score >= totalQuestions * 0.4) {
            message = 'Nicht schlecht, aber wir haben noch mehr zu entdecken! 💫';
        } else {
            message = 'Wir haben noch viel gemeinsam zu erleben - und das ist das Schöne daran! 😊';
        }
        
        messageElement.textContent = message;
    }
    
    // Quiz neu starten
    function restartQuiz() {
        // Alles zurücksetzen
        currentQuestion = 1;
        score = 0;
        
        // Alle Fragen und Optionen zurücksetzen
        document.querySelectorAll('.quiz-question').forEach((question, index) => {
            question.style.display = index === 0 ? 'block' : 'none';
        });
        
        document.querySelectorAll('.quiz-option').forEach(option => {
            option.classList.remove('correct', 'incorrect', 'disabled');
        });
        
        // Ergebnis ausblenden
        document.querySelector('.quiz-result').style.display = 'none';
        
        // Fortschrittsbalken zurücksetzen
        progressBar.style.width = '0%';
    }
    
    // Konfetti-Explosion für richtige Antworten
    function createConfettiExplosion(count) {
        const confettiContainer = document.getElementById('confetti-container');
        const colors = ['#ff65a3', '#ff9cc8', '#ffcee4', '#f2a6c7', '#ff8ba7'];
        
        for (let i = 0; i < count; i++) {
            const confetti = document.createElement('div');
            confetti.classList.add('confetti');
            
            const size = Math.random() * 10 + 5;
            const color = colors[Math.floor(Math.random() * colors.length)];
            
            confetti.style.width = `${size}px`;
            confetti.style.height = `${size}px`;
            confetti.style.backgroundColor = color;
            confetti.style.left = `${Math.random() * 100}%`;
            confetti.style.top = `${Math.random() * 30 + 50}%`;
            confetti.style.position = 'fixed';
            
            if (Math.random() > 0.5) {
                confetti.style.borderRadius = '50%';
            }
            
            // Randomisierte Animation
            const angle = Math.random() * Math.PI * 2;
            const distance = Math.random() * 100 + 50;
            const duration = Math.random() * 1 + 1;
            
            confetti.style.transform = 'translate(-50%, -50%)';
            confetti.style.animation = 'none';
            
            confettiContainer.appendChild(confetti);
            
            // Animation starten
            setTimeout(() => {
                confetti.style.transition = `all ${duration}s ease-out`;
                confetti.style.transform = `translate(${Math.cos(angle) * distance}px, ${Math.sin(angle) * distance}px) rotate(${Math.random() * 360}deg)`;
                confetti.style.opacity = '0';
            }, 10);
            
            // Element entfernen
            setTimeout(() => {
                confetti.remove();
            }, duration * 1000);
        }
    }
});

// Video functionality mit Lautstärkeregelung
document.addEventListener('DOMContentLoaded', function() {
    // Video-Element mit niedriger Lautstärke initialisieren
    const videoElement = document.getElementById('birthday-video');
    if (videoElement) {
        // Lautstärke auf 20% setzen (0.2)
        videoElement.volume = 0.2;
        
        // Lautstärke auch beim Neuladen des Videos zurücksetzen
        videoElement.addEventListener('loadeddata', function() {
            this.volume = 0.2;
        });
        
        // Konfetti-Effekt beim Abspielen des Videos
        videoElement.addEventListener('play', function() {
            if (typeof createConfettiExplosion === 'function') {
                createConfettiExplosion(15);
            }
        });
    }
    
    // Download-Funktionalität
    const downloadBtn = document.querySelector('.download-video-btn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            // Video-Quelle abrufen
            const videoSource = videoElement.querySelector('source').src;
            
            // Temporären Download-Link erstellen
            const downloadLink = document.createElement('a');
            downloadLink.href = videoSource;
            downloadLink.download = 'schubi-geburtstag-video.mp4';
            
            // Link zum Body hinzufügen, klicken und entfernen
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);
            
            // Visuelle Rückmeldung
            const originalText = downloadBtn.innerHTML;
            downloadBtn.innerHTML = '<i class="fas fa-check"></i> Download gestartet!';
            downloadBtn.style.backgroundColor = '#00c853';
            
            // Konfetti-Effekt beim Download
            if (typeof createConfettiExplosion === 'function') {
                createConfettiExplosion(30);
            }
            
            // Button nach 2 Sekunden zurücksetzen
            setTimeout(() => {
                downloadBtn.innerHTML = originalText;
                downloadBtn.style.backgroundColor = '#ff65a3';
            }, 2000);
        });
    }
});