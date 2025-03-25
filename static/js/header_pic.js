// ------------------------------
// Typing Animation Script
// ------------------------------
const words = ["WEBDESIGN", "DEVELOPER", "STUDENT"];
let wordIndex = 0;
let charIndex = 0;
let isDeleting = false;

// Geschwindigkeits- und Pauseneinstellungen
const typingSpeed = 150; // Geschwindigkeit des Schreibens (ms)
const deletingSpeed = 75; // Geschwindigkeit des Löschens (ms)
const pauseAfterWord = 2000; // Pause nach Fertigstellen eines Wortes (ms)

// Ziel-Element für die Animation
const animatedText = document.getElementById("animated-text");

// Hauptfunktion für die Schreibanimation
function typeEffect() {
    const currentWord = words[wordIndex];

    // Sichtbarer Text: Hinzufügen oder Löschen von Zeichen
    const visibleText = isDeleting 
        ? currentWord.substring(0, charIndex--) 
        : currentWord.substring(0, charIndex++);

    animatedText.textContent = visibleText;

    // Geschwindigkeit je nach Status (Schreiben oder Löschen)
    const speed = isDeleting ? deletingSpeed : typingSpeed;

    if (!isDeleting && charIndex === currentWord.length) {
        // Wort ist komplett geschrieben, kurze Pause
        setTimeout(() => (isDeleting = true), pauseAfterWord);
    } else if (isDeleting && charIndex === 0) {
        // Wort ist vollständig gelöscht, nächstes Wort
        isDeleting = false;
        wordIndex = (wordIndex + 1) % words.length; // Zyklischer Wechsel der Wörter
    }

    // Nächsten Frame der Animation starten
    setTimeout(typeEffect, speed);
}

// Animation initial starten
if (animatedText) {
    typeEffect();
} else {
    console.error("Element mit ID 'animated-text' nicht gefunden.");
}

// ------------------------------
// Rock-Paper-Scissors Script
// ------------------------------
let gameInProgress = false; // Blockiert neue Spiele während einer Runde

function playGame(userChoice) {
    if (gameInProgress) return; // Verhindert mehrfaches Starten
    gameInProgress = true;

    const choices = ['rock', 'paper', 'scissors'];
    const difficulty = document.getElementById("difficulty").value;
    const timerElement = document.getElementById("rps-timer");
    const userResult = document.getElementById("user-choice-emoji");
    const computerResult = document.getElementById("computer-choice-emoji");
    const resultIcon = document.getElementById("result-icon");
    const opponentName = document.getElementById("opponent-name");
    const userTitle = document.querySelector("#user-result h3"); // Verweis auf "You"
    let computerChoice;
    let winnerName = "";

    // Alles initial leeren
    userResult.innerText = "";
    computerResult.innerText = "";
    resultIcon.innerText = "";
    opponentName.innerText = "";
    userTitle.classList.add("hidden"); // Versteckt "You" beim Start
    timerElement.style.color = "#FFFFFF"; // Timer bleibt weiß

    // Schwierigkeit auswerten
    if (difficulty === "leonard") {
        winnerName = "Leonard";
        // Leonard verliert oder spielt unentschieden
        if (userChoice === 'rock') computerChoice = 'scissors'; // Rock schlägt Scissors
        else if (userChoice === 'paper') computerChoice = 'rock'; // Paper schlägt Rock
        else computerChoice = 'paper'; // Scissors schlägt Paper
        if (Math.random() < 0.5) computerChoice = userChoice; // 50% Chance auf Unentschieden
    } else if (difficulty === "alex") {
        winnerName = "Alex";
        // Alex gewinnt oder spielt unentschieden
        if (userChoice === 'rock') computerChoice = 'paper'; // Paper schlägt Rock
        else if (userChoice === 'paper') computerChoice = 'scissors'; // Scissors schlägt Paper
        else computerChoice = 'rock'; // Rock schlägt Scissors
        if (Math.random() < 0.5) computerChoice = userChoice; // 50% Chance auf Unentschieden
    } else {
        winnerName = "Schubi";
        computerChoice = choices[Math.floor(Math.random() * 3)]; // Zufällige Wahl
    }

    // Timer-Countdown
    let countdown = 3;
    timerElement.innerText = `Ready... ${countdown}`;
    const timer = setInterval(() => {
        countdown--;
        if (countdown > 0) {
            timerElement.innerText = `Ready... ${countdown}`;
        } else {
            clearInterval(timer);

            // Emojis anzeigen
            const emojiMap = { rock: "✊", paper: "✋", scissors: "✌" };
            userResult.innerText = emojiMap[userChoice];
            computerResult.innerText = emojiMap[computerChoice];
            opponentName.innerText = winnerName;

            // "You" sichtbar machen
            userTitle.classList.remove("hidden");

            // Ergebnislogik
            let resultText = "";
            let resultClass = "";
            if (userChoice === computerChoice) {
                resultText = `It is a draw against ${winnerName}!`;
                resultClass = "result-draw";
                resultIcon.innerText = "⚖️";
            } else if (
                (userChoice === 'rock' && computerChoice === 'scissors') ||
                (userChoice === 'paper' && computerChoice === 'rock') ||
                (userChoice === 'scissors' && computerChoice === 'paper')
            ) {
                resultText = `You have won against ${winnerName}!`;
                resultClass = "result-win";
                resultIcon.innerText = "✅";
            } else {
                resultText = `${winnerName} has won against you!`;
                resultClass = "result-lose";
                resultIcon.innerText = "❌";
            }

            // Ergebnis anzeigen
            timerElement.innerText = resultText;
            timerElement.className = ""; // Klassen zurücksetzen
            timerElement.classList.add(resultClass);
            timerElement.style.color = "#FFFFFF"; // Sicherstellen, dass die Timer-Farbe weiß bleibt

            // Nach 2 Sekunden entsperren
            setTimeout(() => {
                gameInProgress = false;
            }, 2000);
        }
    }, 1000);
}


