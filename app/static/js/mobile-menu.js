document.addEventListener('DOMContentLoaded', function() {
  const mobileNav = document.querySelector('.mobile-nav');
  const overlay = document.querySelector('.overlay');
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');

  let touchStartX = 0;
  let touchStartY = 0;
  let touchEndX = 0;
  let touchEndY = 0;
  const swipeThreshold = 50; // минимальное расстояние для свайпа
  const allowedStartArea = window.innerWidth * 0.3; // правая 30% ширины экрана

  function openMobileMenu() {
    mobileNav.classList.add('active');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeMobileMenu() {
    mobileNav.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  document.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
  }, {passive: true});

  document.addEventListener('touchmove', function(e) {
    const currentX = e.changedTouches[0].screenX;
    const currentY = e.changedTouches[0].screenY;
    const deltaX = touchStartX - currentX;
    const deltaY = Math.abs(touchStartY - currentY);

    // Если свайп начался в правой части и идёт влево, блокируем прокрутку страницы и открываем меню
    if (touchStartX > window.innerWidth - allowedStartArea && deltaX > 0 && deltaX > deltaY) {
      e.preventDefault(); // блокируем скролл страницы
    }

    // Если меню открыто и свайп вправо (закрытие), блокируем переход браузера "назад"
    if (mobileNav.classList.contains('active') && currentX - touchStartX > swipeThreshold && deltaX < 0 && deltaY < 30) {
      e.preventDefault(); // блокируем дефолтное поведение (например, свайп назад)
    }
  }, {passive: false});

  document.addEventListener('touchend', function(e) {
    touchEndX = e.changedTouches[0].screenX;
    const deltaX = touchStartX - touchEndX;
    const deltaY = Math.abs(touchStartY - e.changedTouches[0].screenY);

    // Открытие меню свайпом влево с правой части экрана
    if (touchStartX > window.innerWidth - allowedStartArea && deltaX > swipeThreshold && !mobileNav.classList.contains('active')) {
      openMobileMenu();
    }

    // Закрытие меню свайпом вправо
    if (mobileNav.classList.contains('active') && (touchEndX - touchStartX) > swipeThreshold && deltaY < 30) {
      closeMobileMenu();
    }
  }, {passive: true});

  // Обработчики кнопок и оверлея
  mobileMenuBtn.addEventListener('click', openMobileMenu);
  overlay.addEventListener('click', closeMobileMenu);
  const mobileNavClose = document.querySelector('.mobile-nav-close');
  mobileNavClose.addEventListener('click', closeMobileMenu);
  document.querySelectorAll('.mobile-nav .nav-link').forEach(link => {
    link.addEventListener('click', closeMobileMenu);
  });
});
