/* Presentation only: no credential reads, storage, requests or form submission. */
(() => {
  const initialize = () => {
    const list = document.getElementById('kc-totp-settings');
    const form = document.getElementById('kc-totp-settings-form');
    if (!list || !form) return;
    const spanish = document.documentElement.lang.startsWith('es');
    // Keycloak renders a fourth list item for manual configuration parameters.
    // Keep those native values available inside the connection step.
    if (list.children.length === 4) {
      const parameters = list.children[2];
      const details = document.createElement('details');
      details.className = 'enrollment-manual-details';
      const summary = document.createElement('summary');
      summary.textContent = spanish ? 'Parámetros de la aplicación' : 'App settings';
      details.append(summary);
      [...parameters.querySelectorAll('ul')].forEach(node => details.append(node));
      list.children[1].append(details);
      parameters.remove();
    }
    const panels = [...list.children];
    if (panels.length !== 3) return;
    const card = list.closest('.card-pf');
    const content = document.getElementById('kc-content-wrapper');
    const labels = spanish ? ['Aplicación', 'Vincular', 'Verificar'] : ['App', 'Connect', 'Verify'];
    const error = !!content.querySelector('.pf-m-danger, .alert-error');
    let step = error ? 3 : new URL(location.href).searchParams.has('mode') ? 2 : 1;
    let wizard = false;
    const title = card.querySelector('#kc-page-title');
    const originalTitle = title.textContent;
    panels[0].querySelector('p').textContent = spanish ? 'Instala una aplicación autenticadora.' : 'Install an authenticator app.';
    const manual = new URL(location.href).searchParams.get('mode') === 'manual';
    panels[1].querySelector('p').textContent = manual
      ? (spanish ? 'Introduce esta clave en tu aplicación.' : 'Enter this key in your app.')
      : (spanish ? 'Escanea el QR con tu aplicación.' : 'Scan this QR with your app.');
    panels[2].querySelector('p').textContent = spanish ? 'Introduce el código de tu aplicación.' : 'Enter the code from your app.';
    const warning = content.querySelector('.pf-m-warning, .alert-warning');
    const progress = document.createElement('nav');
    progress.className = 'enrollment-progress';
    progress.setAttribute('aria-label', spanish ? 'Pasos de configuración' : 'Setup steps');
    const buttons = labels.map((label, index) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = `${index + 1}. ${label}`;
      button.addEventListener('click', () => render(index + 1, true));
      progress.append(button);
      return button;
    });
    const navigation = document.createElement('div');
    navigation.className = 'enrollment-navigation';
    const previous = document.createElement('button');
    previous.type = 'button';
    previous.className = 'enrollment-previous';
    previous.textContent = spanish ? 'Anterior' : 'Back';
    previous.addEventListener('click', () => render(step - 1, true));
    const next = document.createElement('button');
    next.type = 'button';
    next.className = 'enrollment-next';
    next.textContent = spanish ? 'Continuar' : 'Continue';
    next.addEventListener('click', () => render(step + 1, true));
    navigation.append(previous, next);
    const heading = card.querySelector('.login-pf-header');
    heading.after(progress);
    card.append(navigation);
    panels.forEach((panel, index) => {
      panel.tabIndex = -1;
      panel.dataset.enrollmentNumber = String(index + 1);
      panel.id ||= `koodaria-enrollment-step-${index + 1}`;
      buttons[index].setAttribute('aria-controls', panel.id + (index === 2 ? ' kc-totp-settings-form' : ''));
      panel.setAttribute('aria-label', labels[index]);
    });
    function render(value = step, focus = false) {
      step = Math.max(1, Math.min(3, value));
      card.dataset.enrollmentMode = wizard ? 'steps' : 'full';
      card.dataset.enrollmentStep = String(step);
      progress.hidden = !wizard;
      navigation.hidden = !wizard;
      panels.forEach((panel, index) => { panel.hidden = wizard && index !== step - 1; });
      form.hidden = wizard && step !== 3;
      if (warning) warning.hidden = wizard;
      title.textContent = wizard ? (spanish ? 'Configura tu 2FA' : 'Set up your 2FA') : originalTitle;
      previous.hidden = step === 1;
      next.hidden = step === 3;
      buttons.forEach((button, index) => {
        if (index === step - 1) button.setAttribute('aria-current', 'step');
        else button.removeAttribute('aria-current');
      });
      if (focus) panels[step - 1].focus({ preventScroll: true });
    }
    function resize() {
      const height = Math.round(window.visualViewport?.height || innerHeight);
      const width = document.documentElement.clientWidth;
      document.documentElement.style.setProperty('--enrollment-viewport-height', `${height}px`);
      card.dataset.enrollmentDensity = height < 640 ? 'tight' : height < 780 ? 'compact' : 'comfortable';
      const nextWizard = width < 800 || height < 700;
      if (nextWizard && !wizard && form.contains(document.activeElement)) step = 3;
      wizard = nextWizard;
      render();
    }
    window.addEventListener('resize', resize, { passive: true });
    window.visualViewport?.addEventListener('resize', resize, { passive: true });
    resize();
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, { once: true });
  else initialize();
})();
