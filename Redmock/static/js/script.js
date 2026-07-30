/* =========================================================================
   Examly — interactions
   ========================================================================= */

document.addEventListener('DOMContentLoaded', () => {

  /* ---------------- AOS ---------------- */
  if (window.AOS) {
    AOS.init({
      duration: 800,
      easing: 'ease-out-cubic',
      once: true,
      offset: 60,
    });
  }

  /* ---------------- GSAP setup ---------------- */
  if (window.gsap && window.ScrollTrigger) {
    gsap.registerPlugin(ScrollTrigger);

    // Hero copy entrance
    gsap.from('.eyebrow', { opacity: 0, y: 16, duration: 0.7, ease: 'power2.out' });
    gsap.from('.hero-title', { opacity: 0, y: 26, duration: 0.9, delay: 0.1, ease: 'power2.out' });
    gsap.from('.hero-desc', { opacity: 0, y: 22, duration: 0.9, delay: 0.22, ease: 'power2.out' });
    gsap.from('.hero-actions', { opacity: 0, y: 18, duration: 0.9, delay: 0.34, ease: 'power2.out' });
    gsap.from('.hero-stats', { opacity: 0, y: 18, duration: 0.9, delay: 0.44, ease: 'power2.out' });

    // Parallax glows on scroll
    gsap.to('.hero-glow-a', {
      y: 120,
      scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 1 }
    });
    gsap.to('.hero-glow-b', {
      y: -80,
      scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: 1 }
    });
  }

  /* ---------------- Sticky navbar state ---------------- */
  const navbar = document.getElementById('navbar');
  const onScroll = () => {
    if (window.scrollY > 30) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------------- Mobile nav toggle ---------------- */
  const navToggle = document.getElementById('navToggle');
  const navLinks = document.getElementById('navLinks');
  navToggle.addEventListener('click', () => {
    navLinks.classList.toggle('open');
  });
  navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => navLinks.classList.remove('open'));
  });

  /* ---------------- Mouse-follow 3D tilt on hero panel ---------------- */
  const stage = document.querySelector('.hero-stage');
  const tilt = document.getElementById('stageTilt');

  if (stage && tilt && window.matchMedia('(pointer: fine)').matches) {
    let rect = stage.getBoundingClientRect();
    window.addEventListener('resize', () => { rect = stage.getBoundingClientRect(); });

    stage.addEventListener('mousemove', (e) => {
      rect = stage.getBoundingClientRect();
      const px = (e.clientX - rect.left) / rect.width - 0.5;  // -0.5 .. 0.5
      const py = (e.clientY - rect.top) / rect.height - 0.5;
      const rotY = px * 18;
      const rotX = -py * 18;
      tilt.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg)`;
    });

    stage.addEventListener('mouseleave', () => {
      tilt.style.transform = 'rotateX(0deg) rotateY(0deg)';
    });
  }

  /* ---------------- Animated counters ---------------- */
  const counters = document.querySelectorAll('.stat-num');
  const animateCounter = (el) => {
    const target = parseFloat(el.dataset.count);
    const suffix = el.dataset.suffix || (Number.isInteger(target) && target >= 1000 ? '+' : '');
    const duration = 1600;
    const start = performance.now();

    const step = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const value = target * eased;
      el.textContent = (Number.isInteger(target) ? Math.round(value) : value.toFixed(1)) + suffix;
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  if ('IntersectionObserver' in window) {
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.6 });
    counters.forEach(c => counterObserver.observe(c));
  }

  /* ---------------- Smooth scroll for in-page anchors ---------------- */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const id = this.getAttribute('href');
      if (id.length > 1) {
        const target = document.querySelector(id);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });



  /* ---------------- Ambient particle background (Canvas) ---------------- */
  const canvas = document.getElementById('bg-particles');
  const ctx = canvas.getContext('2d');
  let particles = [];
  let w, h;

  const palette = ['#48cae4', '#00b4d8', '#0096c7', '#90e0ef'];

  function resizeCanvas() {
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
  }

  function createParticles() {
    const count = Math.min(70, Math.floor((w * h) / 22000));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * w,
      y: Math.random() * h,
      r: Math.random() * 1.8 + 0.6,
      speedY: Math.random() * 0.35 + 0.08,
      drift: Math.random() * 0.6 - 0.3,
      color: palette[Math.floor(Math.random() * palette.length)],
      alpha: Math.random() * 0.5 + 0.15,
    }));
  }

  function tick() {
    ctx.clearRect(0, 0, w, h);
    particles.forEach(p => {
      p.y -= p.speedY;
      p.x += p.drift;
      if (p.y < -10) { p.y = h + 10; p.x = Math.random() * w; }
      if (p.x < -10) p.x = w + 10;
      if (p.x > w + 10) p.x = -10;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.alpha;
      ctx.fill();
    });
    ctx.globalAlpha = 1;
    requestAnimationFrame(tick);
  }

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (canvas && !reduceMotion) {
    resizeCanvas();
    createParticles();
    tick();
    window.addEventListener('resize', () => {
      resizeCanvas();
      createParticles();
    });
  }

  /* ---------------- Dynamic Copyright Year ---------------- */
  const yearEl = document.getElementById('currentYear');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

});
