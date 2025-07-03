// Функция создания элемента перехода
function createTransitionElement(isDark) {
  const transition = document.createElement('div');
  transition.className = 'theme-transition';
  transition.style.backgroundColor = isDark ? '#141e2d' : '#ffffff';
  document.body.appendChild(transition);

  setTimeout(() => {
    transition.remove();
  }, 600);
}

// Функция применения темы
function applyTheme(isDark) {
  // Сначала создаем элемент перехода
  createTransitionElement(isDark);

  // Затем применяем тему
  document.documentElement.classList.toggle('dark', isDark);
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');

  // Сохраняем в localStorage
  localStorage.setItem('theme', isDark ? 'dark' : 'light');

  // Обновляем favicon
  const iconPath = isDark ? '/static/icon-night.png' : '/static/icon.png';
  const icon = document.querySelector('link[rel="icon"]');
  if (icon) icon.href = iconPath + '?v=' + Date.now();
}

// Инициализация темы при загрузке
(function initTheme() {
  // Определяем текущую тему
  const savedTheme = localStorage.getItem('theme');
  const preferDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = savedTheme ? savedTheme === 'dark' : preferDark;

  // Сразу применяем тему (без анимации при первой загрузке)
  document.documentElement.classList.toggle('dark', isDark);
  document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');

  // Для перехода между страницами создаем анимацию
  if (performance.navigation.type === performance.navigation.TYPE_NAVIGATE) {
    createTransitionElement(isDark);
  }
})();

// Обработчик кнопки переключения темы
document.getElementById('themeToggle')?.addEventListener('click', () => {
  const isDark = !document.documentElement.classList.contains('dark');
  applyTheme(isDark);
});

// 1. БЛОКИРУЕМ АНИМАЦИЮ ПЕРЕД ЗАГРУЗКОЙ
(function() {
  // Добавляем стиль, который отключает transition
  const antiFlicker = document.createElement("style");
  antiFlicker.textContent = `
    * {
      transition: none !important;
    }
  `;
  document.head.appendChild(antiFlicker);

  // Применяем тему сразу (до загрузки страницы)
  const savedTheme = localStorage.getItem("theme");
  const isDark = savedTheme === "dark";
  document.documentElement.classList.toggle("dark", isDark);
  document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");

  // Удаляем блокировку анимации после загрузки
  setTimeout(() => {
    document.head.removeChild(antiFlicker);
  }, 100);
})();
