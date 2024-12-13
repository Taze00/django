// -------------------------------------------------------------------------------------------------
const words = ["WEBDESIGN", "DEVELOPER", "STUDENT"];
let wordIndex = 0;
let charIndex = 0;
let isDeleting = false;

const speed = 150; // Geschwindigkeit des Schreibens
const pause = 2000; // Pause, bevor ein neues Wort erscheint

const animatedText = document.getElementById("animated-text");

function typeEffect() {
    const currentWord = words[wordIndex];
    const visibleText = isDeleting 
        ? currentWord.substring(0, charIndex--) 
        : currentWord.substring(0, charIndex++);

    animatedText.textContent = visibleText;

    // Geschwindigkeit anpassen beim Löschen
    const typingSpeed = isDeleting ? speed / 2 : speed;

    if (!isDeleting && charIndex === currentWord.length) {
        // Vollständig geschrieben, Pause starten
        setTimeout(() => (isDeleting = true), pause);
    } else if (isDeleting && charIndex === 0) {
        // Vollständig gelöscht, zum nächsten Wort wechseln
        isDeleting = false;
        wordIndex = (wordIndex + 1) % words.length;
    }

    setTimeout(typeEffect, typingSpeed);
}

// Animation starten
typeEffect();

// -------------------------------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    // WebGL Visualizer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio);

    // Dynamische Größe des Containers verwenden
    const visualizerContainer = document.querySelector('.visualizer-container');
    if (visualizerContainer) {
        renderer.setSize(visualizerContainer.offsetWidth, visualizerContainer.offsetHeight);
        document.getElementById('visualizer').appendChild(renderer.domElement);
    } else {
        console.error('Visualizer container not found!');
        return;
    }

    // Geometrie und Shader-Material für den Glow-Effekt
    const geometry = new THREE.SphereGeometry(3, 64, 64);

    // Punkte-Material mit Glow
    const material = new THREE.ShaderMaterial({
        uniforms: {
            glowColor: { value: new THREE.Color(0xffffff) },
            viewVector: { value: camera.position },
        },
        vertexShader: `
            varying vec3 vNormal;
            varying vec3 vPositionNormal;
            void main() {
                vNormal = normalize(normalMatrix * normal);
                vPositionNormal = normalize((modelViewMatrix * vec4(position, 1.0)).xyz);
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform vec3 glowColor;
            varying vec3 vNormal;
            varying vec3 vPositionNormal;
            void main() {
                float intensity = pow(0.9 - dot(vNormal, vPositionNormal), 3.0);
                gl_FragColor = vec4(glowColor, 1.0) * intensity;
            }
        `,
        transparent: true,
        blending: THREE.AdditiveBlending,
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);

    camera.position.z = 10;
    const initialPositions = geometry.attributes.position.array.slice();

    // Audio Setup
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    const frequencyData = new Uint8Array(analyser.frequencyBinCount);

    const audio = new Audio('/static/js/test.mp3');
    audio.crossOrigin = 'anonymous';
    audio.loop = true;

    const source = audioContext.createMediaElementSource(audio);
    source.connect(analyser);
    analyser.connect(audioContext.destination);

    // Toggle Audio Button
    const toggleAudio = document.getElementById('toggle-audio');
    if (toggleAudio) {
        toggleAudio.addEventListener('change', (event) => {
            if (event.target.checked) {
                // Start or resume audio
                audioContext.resume().then(() => {
                    audio.play();
                }).catch(err => {
                    console.error('Error resuming audio context:', err);
                });
            } else {
                // Pause audio
                audio.pause();
            }
        });
    } else {
        console.error('Audio toggle element not found!');
    }

    // Animation Loop
    function animate() {
        requestAnimationFrame(animate);

        analyser.getByteFrequencyData(frequencyData);

        const positions = geometry.attributes.position.array;
        for (let i = 0; i < positions.length; i += 3) {
            const x = initialPositions[i];
            const y = initialPositions[i + 1];
            const z = initialPositions[i + 2];

            const frequency = frequencyData[i % frequencyData.length] / 255;
            const strength = frequency * 3;

            positions[i] = x + (x / 3) * strength * 0.5;
            positions[i + 1] = y + (y / 3) * strength * 0.5;
            positions[i + 2] = z + (z / 3) * strength * 0.5;

            positions[i] += (x - positions[i]) * 0.01;
            positions[i + 1] += (y - positions[i + 1]) * 0.01;
            positions[i + 2] += (z - positions[i + 2]) * 0.01;
        }

        geometry.attributes.position.needsUpdate = true;

        points.rotation.x += 0.005;
        points.rotation.y += 0.005;

        renderer.render(scene, camera);
    }

    animate();
});

// -------------------------------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    const toggleInput = document.getElementById('toggle-audio');
    const toggleText = document.querySelector('.toggle-text');

    if (toggleInput && toggleText) {
        toggleInput.addEventListener('change', () => {
            if (toggleInput.checked) {
                // Wenn aktiviert
                toggleText.classList.add('glow');
            } else {
                // Wenn deaktiviert
                toggleText.classList.remove('glow');
            }
        });
    } else {
        console.error('Toggle input or text not found!');
    }
});
