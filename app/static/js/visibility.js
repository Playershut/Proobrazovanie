// Функция для проверки видимости элементов
function checkVisibility() {
  const elements = document.querySelectorAll('.reveal');
  elements.forEach(el => {
    const rect = el.getBoundingClientRect();
    const isVisible = (rect.top <= window.innerHeight * 0.8) && (rect.bottom >= 0);
    if (isVisible) el.classList.add('active');
  });
}

// Запуск при загрузке и скролле
window.addEventListener('load', checkVisibility);
window.addEventListener('scroll', checkVisibility);
