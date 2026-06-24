import { useState, useEffect } from 'react';

// Dezenter Hinweis NUR für iOS-Safari-Nutzer: iOS zeigt keinen automatischen
// Install-Prompt. Zeigt sich nicht auf Desktop/Android, nicht wenn die App
// schon installiert (standalone) läuft, und nicht nach dem Wegtippen.
export default function IosInstallHint() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const ua = window.navigator.userAgent || '';
    const isIos = /iphone|ipad|ipod/i.test(ua);
    const isStandalone =
      window.navigator.standalone === true ||
      window.matchMedia('(display-mode: standalone)').matches;
    const dismissed = localStorage.getItem('corvis_ios_hint_dismissed') === '1';
    if (isIos && !isStandalone && !dismissed) setShow(true);
  }, []);

  if (!show) return null;

  const dismiss = () => {
    localStorage.setItem('corvis_ios_hint_dismissed', '1');
    setShow(false);
  };

  return (
    <div className="ios-hint">
      <div className="ios-hint-text">
        Tippe auf <span className="ios-hint-share">Teilen</span> → „Zum Home-Bildschirm",
        um CORVIS als App zu installieren.
      </div>
      <button className="ios-hint-close" onClick={dismiss} aria-label="Hinweis schließen">×</button>
    </div>
  );
}
