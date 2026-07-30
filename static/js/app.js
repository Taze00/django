/* ==========================================================================
   app.js — Einstiegspunkt für das Redesign der Startseite
   Ersetzt schrittweise main.js.
   ========================================================================== */

/**
 * Lichtspot im Hero, der träge dem Mauszeiger folgt.
 *
 * Die Position landet als --hero-spot-x/y auf der Section, gerendert wird
 * ausschließlich per CSS (radial-gradient). Zwischen Cursor und Spot liegt
 * eine Lerp-Glättung, damit der Spot nachzieht statt zu kleben.
 *
 * Nichts passiert bei: fehlendem Hero, Touch-Gerät (kein Hover) oder
 * prefers-reduced-motion. Dann greifen die Defaults aus base.css und der
 * Spot steht mittig.
 */
function initHeroSpotlight() {
    const hero = document.querySelector('.hero');
    if (!hero) return;

    const canHover = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    const wantsMotion = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!canHover || !wantsMotion) return;

    const SMOOTHING = 0.08;   // je kleiner, desto träger
    const EPSILON = 0.05;     // ab hier gilt der Spot als angekommen (in %)

    // Startwerte = Defaults aus base.css, damit der erste Frame nicht springt.
    let targetX = 50;
    let targetY = 42;
    let currentX = targetX;
    let currentY = targetY;
    let frame = null;

    function render() {
        currentX += (targetX - currentX) * SMOOTHING;
        currentY += (targetY - currentY) * SMOOTHING;

        hero.style.setProperty('--hero-spot-x', currentX.toFixed(2) + '%');
        hero.style.setProperty('--hero-spot-y', currentY.toFixed(2) + '%');

        // Stillstand: Schleife anhalten, bis die Maus sie neu weckt.
        if (Math.abs(targetX - currentX) < EPSILON && Math.abs(targetY - currentY) < EPSILON) {
            frame = null;
            return;
        }
        frame = requestAnimationFrame(render);
    }

    function wake() {
        if (frame === null) frame = requestAnimationFrame(render);
    }

    hero.addEventListener('pointermove', (event) => {
        if (event.pointerType !== 'mouse') return;

        const bounds = hero.getBoundingClientRect();
        targetX = ((event.clientX - bounds.left) / bounds.width) * 100;
        targetY = ((event.clientY - bounds.top) / bounds.height) * 100;
        wake();
    });

    // Verlässt der Zeiger den Hero, zieht der Spot sanft zur Mitte zurück.
    hero.addEventListener('pointerleave', () => {
        targetX = 50;
        targetY = 42;
        wake();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initHeroSpotlight();
});
