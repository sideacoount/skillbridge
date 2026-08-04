/* ============================================================
   SkillBridge — main frontend behavior
   Dark mode, live search, toasts, animations, validations
   ============================================================ */
(function () {
  'use strict';

  const $ = (sel, ctx) => (ctx || document).querySelector(sel);
  const $$ = (sel, ctx) => Array.from((ctx || document).querySelectorAll(sel));

  /* ---------------- Theme (dark / light) ---------------- */
  const THEME_KEY = 'sb-theme';
  const root = document.documentElement;
  const themeBtn = $('#themeToggle');

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
    if (themeBtn) {
      themeBtn.innerHTML = theme === 'dark'
        ? '<i class="bi bi-sun-fill"></i>'
        : '<i class="bi bi-moon-stars-fill"></i>';
    }
  }

  function initTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(stored || (prefersDark ? 'dark' : 'light'));
  }

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
    });
  }

  /* ---------------- Navbar scroll state ---------------- */
  const nav = $('#mainNavbar');
  function onScroll() {
    if (!nav) return;
    nav.classList.toggle('sb-navbar--scrolled', window.scrollY > 24);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------------- Toasts ---------------- */
  const toastWrap = $('#toastWrap');
  if (toastWrap) {
    $$('.sb-toast', toastWrap).forEach((toast) => {
      const dismiss = () => {
        toast.classList.add('leaving');
        setTimeout(() => toast.remove(), 320);
      };
      $('.sb-toast-close', toast)?.addEventListener('click', dismiss);
      setTimeout(dismiss, 5200);
    });
  }

  window.showToast = function (message, type = 'info') {
    if (!toastWrap) return;
    const icons = { success: 'bi-check-circle-fill', error: 'bi-exclamation-triangle-fill', warning: 'bi-exclamation-circle-fill', info: 'bi-info-circle-fill' };
    const el = document.createElement('div');
    el.className = `sb-toast sb-toast--${type}`;
    el.innerHTML = `
      <div class="sb-toast-icon"><i class="bi ${icons[type] || icons.info}"></i></div>
      <div class="sb-toast-body"></div>
      <button type="button" class="sb-toast-close" aria-label="Dismiss"><i class="bi bi-x-lg"></i></button>`;
    $('.sb-toast-body', el).textContent = message;
    toastWrap.appendChild(el);
    const dismiss = () => { el.classList.add('leaving'); setTimeout(() => el.remove(), 320); };
    $('.sb-toast-close', el).addEventListener('click', dismiss);
    setTimeout(dismiss, 5200);
  };

  /* ---------------- Button ripple ---------------- */
  $$('.sb-btn').forEach((btn) => {
    btn.addEventListener('click', function (e) {
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const ripple = document.createElement('span');
      ripple.className = 'ripple';
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
      this.appendChild(ripple);
      setTimeout(() => ripple.remove(), 650);
    });
  });

  /* ---------------- Scroll reveal + counters ---------------- */
  function revealOnScroll() {
    const items = $$('.sb-reveal');
    if (!('IntersectionObserver' in window)) {
      items.forEach((el) => el.classList.add('in-view'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    items.forEach((el) => io.observe(el));
  }
  revealOnScroll();

  function animateCounters() {
    const counters = $$('[data-count]');
    if (!('IntersectionObserver' in window)) { counters.forEach(c => c.textContent = c.dataset.count); return; }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseInt(el.dataset.count, 10) || 0;
        const duration = 1200;
        const start = performance.now();
        const suffix = el.dataset.suffix || '';
        function tick(now) {
          const p = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased).toLocaleString() + suffix;
          if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
        io.unobserve(el);
      });
    }, { threshold: 0.4 });
    counters.forEach((c) => io.observe(c));
  }
  animateCounters();

  /* ---------------- Live search + filters ---------------- */
  const browse = $('#browseGrid');
  const searchInput = $('#liveSearch');
  const resultsCount = $('#sbResultsCount');
  const browseForm = $('#browseFilters');

  if (browse) {
    const filters = $$('.filter-select', browseForm || document);
    const debounce = (fn, ms) => {
      let t;
      return function () { clearTimeout(t); t = setTimeout(() => fn.apply(this, arguments), ms); };
    };

    async function runSearch() {
      if (!browse) return;
      const params = new URLSearchParams();
      if (searchInput && searchInput.value.trim()) params.set('q', searchInput.value.trim());
      if (browseForm) {
        new FormData(browseForm).forEach((v, k) => { if (v) params.set(k, v); });
      }
      const skeleton = $('.sb-skeleton-row', browse) || browse.firstElementChild;
      if (skeleton) { skeleton.classList.add('sb-skeleton'); skeleton.style.minHeight = '180px'; }
      try {
        const res = await fetch(`${window.SKILLBRIDGE.searchUrl}?${params.toString()}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const data = await res.json();
        if (resultsCount) resultsCount.textContent = data.count;
        browse.innerHTML = data.html || emptyResults();
        bindWishlist();
      } catch (err) {
        console.error('Search failed', err);
      }
    }
    const debounced = debounce(runSearch, 260);

    if (searchInput) searchInput.addEventListener('input', debounced);
    if (browseForm) {
      filters.forEach((f) => {
        const tag = f.tagName.toLowerCase();
        f.addEventListener(tag === 'select' ? 'change' : 'input', debounced);
      });
      $('#clearFilters')?.addEventListener('click', () => {
        browseForm.reset();
        debounced();
      });
    }

    function emptyResults() {
      return `
        <div class="col-12">
          <div class="sb-empty">
            <div class="sb-empty-icon"><i class="bi bi-search"></i></div>
            <h4 class="fw-bold">No services found</h4>
            <p class="mb-0">Try a different keyword or loosen your filters.</p>
          </div>
        </div>`;
    }
  }

  /* ---------------- Wishlist toggle ---------------- */
  function bindWishlist() {
    $$('[data-wishlist]').forEach((btn) => {
      if (btn.dataset.bound) return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', async (e) => {
        e.preventDefault();
        const pk = btn.dataset.wishlist;
        if (!window.SKILLBRIDGE.loggedIn) {
          window.location.href = window.SKILLBRIDGE.loginUrl;
          return;
        }
        try {
          const res = await fetch(`/services/${pk}/wishlist/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': window.SKILLBRIDGE.csrf, 'X-Requested-With': 'XMLHttpRequest' },
          });
          const data = await res.json();
          btn.classList.toggle('active', data.saved);
          const label = btn.querySelector('.wish-label');
          if (label) {
            btn.innerHTML = data.saved
              ? '<i class="bi bi-heart-fill"></i><span class="wish-label">Saved to wishlist</span>'
              : '<i class="bi bi-heart"></i><span class="wish-label">Save to wishlist</span>';
          } else {
            btn.innerHTML = data.saved ? '<i class="bi bi-heart-fill"></i>' : '<i class="bi bi-heart"></i>';
          }
          showToast(data.message, data.saved ? 'success' : 'info');
        } catch (err) { showToast('Could not update wishlist.', 'error'); }
      });
    });
  }
  bindWishlist();

  /* ---------------- Form validation ---------------- */
  const forms = $$('form[data-validate]');
  forms.forEach((form) => {
    form.addEventListener('submit', (e) => {
      const inputs = $$('input[required], select[required], textarea[required]', form);
      let firstBad = null;
      inputs.forEach((input) => {
        const valid = input.value.trim() !== '';
        input.classList.toggle('is-invalid', !valid);
        if (!valid && !firstBad) firstBad = input;
      });
      if (firstBad) {
        e.preventDefault();
        firstBad.focus();
      }
    });
    $$('input, select, textarea', form).forEach((input) => {
      input.addEventListener('input', () => input.classList.remove('is-invalid'));
    });
  });

  /* ---------------- Password strength meter ---------------- */
  const pwInput = $('#password1') || $('#id_password1');
  const pwMeter = $('#pwMeter');
  if (pwInput && pwMeter) {
    pwInput.addEventListener('input', () => {
      const v = pwInput.value;
      let score = 0;
      if (v.length >= 8) score++;
      if (v.length >= 12) score++;
      if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++;
      if (/\d/.test(v)) score++;
      if (/[^A-Za-z0-9]/.test(v)) score++;
      const strength = Math.min(4, score);
      pwMeter.dataset.strength = strength;
      $$('span', pwMeter).forEach((bar, i) => bar.classList.toggle('on', i < strength));
    });
  }

  /* ---------------- Character counters ---------------- */
  $$('[data-char-counter]').forEach((el) => {
    const max = parseInt(el.getAttribute('maxlength'), 10) || 0;
    if (!max) return;
    const wrap = el.closest('.mb-3') || el.parentElement;
    const counter = document.createElement('div');
    counter.className = 'sb-char-counter';
    counter.textContent = `0 / ${max}`;
    wrap.appendChild(counter);
    const update = () => {
      const len = el.value.length;
      counter.textContent = `${len} / ${max}`;
      counter.classList.toggle('danger', len > max * 0.9);
    };
    el.addEventListener('input', update);
    update();
  });

  /* ---------------- Image previews ---------------- */
  $$('[data-image-preview]').forEach((input) => {
    const target = document.getElementById(input.dataset.imagePreview);
    if (!target) return;
    input.addEventListener('change', () => {
      const file = input.files && input.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        target.src = e.target.result;
        target.classList.add('has-image');
        target.style.border = 'none';
      };
      reader.readAsDataURL(file);
    });
  });

  /* ---------------- Star rating input ---------------- */
  const starWrap = $('.sb-star-input');
  const ratingValue = $('#ratingValue') || $('#id_rating');
  if (starWrap && ratingValue) {
    const stars = $$('i', starWrap);
    const sync = (val) => {
      stars.forEach((s, i) => s.classList.toggle('selected', i < val));
      ratingValue.value = val;
    };
    stars.forEach((star, i) => {
      star.addEventListener('mouseenter', () => {
        stars.forEach((s, j) => s.classList.toggle('hover', j <= i));
      });
      star.addEventListener('click', () => sync(i + 1));
    });
    starWrap.addEventListener('mouseleave', () => stars.forEach((s) => s.classList.remove('hover')));
    sync(parseInt(ratingValue.value, 10) || 5);
  }

  /* ---------------- Confirm delete modals ---------------- */
  $$('[data-confirm-form]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      const msg = form.dataset.confirmMessage || 'Are you sure? This cannot be undone.';
      if (!window.confirm(msg)) e.preventDefault();
    });
  });

  /* ---------------- Dashboard sidebar (mobile) ---------------- */
  const sidebarToggle = $('#sidebarToggle');
  const sidebar = $('.sb-sidebar');
  const overlay = $('.sb-sidebar-overlay');
  if (sidebarToggle && sidebar) {
    const close = () => { sidebar.classList.remove('open'); overlay?.classList.remove('show'); };
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay?.classList.toggle('show');
    });
    overlay?.addEventListener('click', close);
  }

  /* ---------------- Mark notifications read ---------------- */
  const notifList = $('#notifList');
  if (notifList) {
    notifList.addEventListener('click', () => {
      fetch('/accounts/notifications/read/', {
        method: 'POST',
        headers: { 'X-CSRFToken': window.SKILLBRIDGE.csrf, 'X-Requested-With': 'XMLHttpRequest' },
      }).catch(() => {});
      $$('.sb-notif.unread', notifList).forEach((n) => n.classList.remove('unread'));
      $$('.sb-badge-dot').forEach((d) => d.remove());
    });
  }

  /* ---------------- Smooth anchor scrolling ---------------- */
  $$('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (id.length > 1) {
        const target = $(id);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  });

  /* ---------------- Init ---------------- */
  initTheme();
})();
