document.addEventListener('DOMContentLoaded', () => {
  // Отслеживаем все клики по ссылкам
  document.querySelectorAll('a[href]').forEach(link => {
    // Пропускаем специальные ссылки
    if (
      link.target === '_blank' ||
      link.href.startsWith('javascript:') ||
      link.getAttribute('href').startsWith('#')
    ) {
      return;
    }

    link.addEventListener('click', (e) => {
      // Если клик не мышкой (например, навигация браузера), пропускаем
      if (e.clientX === 0 && e.clientY === 0) {
        return;
      }

      // Для обычных кликов: плавный скролл вверх перед переходом
      e.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });

      // Мгновенный переход после скролла
      setTimeout(() => {
        window.location.href = link.href;
      }, 300); // Ждем завершения скролла
    });
  });
});
