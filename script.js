// Hero: hide the <img> if hero.jpg isn't there yet so the gradient fallback shows.
const hero = document.querySelector('.hero-img');
if (hero) {
  const hideHero = () => { hero.style.display = 'none'; };
  hero.addEventListener('error', hideHero);
  if (hero.complete && hero.naturalWidth === 0) hideHero();
}

// Gallery: mark tiles whose photo is missing so they render as placeholders.
const shots = [...document.querySelectorAll('.shot')];
shots.forEach((shot) => {
  const img = shot.querySelector('img');
  const markMissing = () => shot.classList.add('missing');
  img.addEventListener('error', markMissing);
  if (img.complete && img.naturalWidth === 0) markMissing();
});

// Lightbox
const box = document.querySelector('.lightbox');
const boxImg = box.querySelector('.lb-img');
let current = -1;

const available = () => shots.filter((s) => !s.classList.contains('missing'));

function open(shot) {
  const list = available();
  current = list.indexOf(shot);
  if (current < 0) return;
  show();
  box.hidden = false;
  document.body.style.overflow = 'hidden';
  box.querySelector('.lb-close').focus();
}

function show() {
  const img = available()[current].querySelector('img');
  boxImg.src = img.currentSrc || img.src;
  boxImg.alt = img.alt;
}

function step(dir) {
  const n = available().length;
  current = (current + dir + n) % n;
  show();
}

function close() {
  box.hidden = true;
  document.body.style.overflow = '';
  available()[current]?.focus();
}

shots.forEach((shot) => shot.addEventListener('click', () => open(shot)));
box.querySelector('.lb-close').addEventListener('click', close);
box.querySelector('.lb-prev').addEventListener('click', () => step(-1));
box.querySelector('.lb-next').addEventListener('click', () => step(1));
box.addEventListener('click', (e) => { if (e.target === box) close(); });

document.addEventListener('keydown', (e) => {
  if (box.hidden) return;
  if (e.key === 'Escape') close();
  if (e.key === 'ArrowRight') step(1);
  if (e.key === 'ArrowLeft') step(-1);
});

// Swipe on touch screens
let startX = null;
box.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; }, { passive: true });
box.addEventListener('touchend', (e) => {
  if (startX === null) return;
  const dx = e.changedTouches[0].clientX - startX;
  if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
  startX = null;
});

