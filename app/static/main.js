// --- Общие вспомогательные функции ---

function checkVisibility() {
  const elements = document.querySelectorAll('.reveal');
  elements.forEach(el => {
    const rect = el.getBoundingClientRect();
    const isVisible = (rect.top <= window.innerHeight * 0.8) && (rect.bottom >= 0);
    if (isVisible) {
      el.classList.add('active');
    }
  });
}

function setupSmoothScrolling() {
  document.querySelectorAll('a[href]').forEach(link => {
    if (
      link.target === '_blank' ||
      link.href.startsWith('javascript:') ||
      link.getAttribute('href').startsWith('#')
    ) {
      return;
    }

    link.addEventListener('click', (e) => {
      if (e.clientX === 0 && e.clientY === 0) {
        return;
      }

      e.preventDefault();
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });

      setTimeout(() => {
        window.location.href = link.href;
      }, 300);
    });
  });
}

// --- Функции для динамических выпадающих списков ---
/**
 * Очищает и заполняет SelectField данными.
 * Это критически важная функция, которая была переработана для корректной работы с Select2.
 * @param {HTMLSelectElement} selectElement Элемент <select>.
 * @param {Array<Object>} data Массив объектов {id: number, name: string}.
 * @param {string} defaultOptionText Текст для опции по умолчанию (например, "Выберите...").
 * @param {string|number} [selectedValue='0'] ID значения, которое должно быть выбрано по умолчанию.
 */
function populateSelect(selectElement, data, defaultOptionText, selectedValue = '0') {
    selectElement.innerHTML = '';

    const defaultOption = document.createElement('option');
    defaultOption.value = '0';
    defaultOption.textContent = defaultOptionText;
    selectElement.appendChild(defaultOption);

    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name;
        selectElement.appendChild(option);
    });

    selectElement.value = selectedValue;

    if ($(selectElement).data('select2')) {
        $(selectElement).trigger('change');
    }
}

/**
 * Загружает населенные пункты для выбранного региона.
 * @param {string} regionId ID выбранного региона.
 * @param {string|number} [initialSettlementId='0'] ID населенного пункта, который нужно выбрать по умолчанию (для инициализации).
 * @param {function} [callback] Функция обратного вызова, выполняемая после загрузки населенных пунктов.
 */
function loadSettlements(regionId, initialSettlementId = '0', callback) {
    const settlementSelect = document.getElementById('settlement');
    const institutionSelect = document.getElementById('educational_institution');

    if (!settlementSelect || !institutionSelect) return;

    if (regionId === '0') {
        populateSelect(settlementSelect, [], 'Выберите населенный пункт');
        populateSelect(institutionSelect, [], 'Выберите учебное заведение');
        if (callback) callback();
        return;
    }

    fetch(`/get_settlements/${regionId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            populateSelect(settlementSelect, data, 'Выберите населенный пункт', initialSettlementId);
            if (initialSettlementId === '0' || data.length === 0) {
                populateSelect(institutionSelect, [], 'Выберите учебное заведение');
            }
            if (callback) callback();
        })
        .catch(error => {
            console.error('Error loading settlements:', error);
            populateSelect(settlementSelect, [], 'Ошибка загрузки');
            populateSelect(institutionSelect, [], 'Ошибка загрузки');
            if (callback) callback();
        });
}

/**
 * Загружает учебные заведения для выбранного населенного пункта.
 * @param {string} settlementId ID выбранного населенного пункта.
 * @param {string|number} [initialInstitutionId='0'] ID учебного заведения, которое нужно выбрать по умолчанию (для инициализации).
 */
function loadInstitutions(settlementId, initialInstitutionId = '0') {
    const institutionSelect = document.getElementById('educational_institution');

    if (!institutionSelect) return;

    if (settlementId === '0') {
        populateSelect(institutionSelect, [], 'Выберите учебное заведение');
        return;
    }

    fetch(`/get_educational_institutions/${settlementId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            populateSelect(institutionSelect, data, 'Выберите учебное заведение', initialInstitutionId);
        })
        .catch(error => {
            console.error('Error loading institutions:', error);
            populateSelect(institutionSelect, [], 'Ошибка загрузки');
        });
}


// --- Инициализация при загрузке DOM ---
document.addEventListener('DOMContentLoaded', function() {
    checkVisibility();
    setupSmoothScrolling();

    // Обработка мультиселектов
    document.querySelectorAll('.select2-multiple').forEach(select => {
        const $select = $(select);
        const placeholder = $select.data('placeholder') || 'Выберите...';

        // Инициализация Select2
        $select.select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: placeholder,
            closeOnSelect: false,
            allowClear: true
        });
    });


    const regionSelect = document.getElementById('region');
    const settlementSelect = document.getElementById('settlement');
    const institutionSelect = document.getElementById('educational_institution');

    const hasDynamicLocationFields = regionSelect && settlementSelect && institutionSelect;

    if (hasDynamicLocationFields) {
        $(regionSelect).select2({
            theme: 'bootstrap-5',
            width: $(regionSelect).data('width') ? $(regionSelect).data('width') : $(regionSelect).hasClass('w-100') ? '100%' : 'style',
            placeholder: 'Выберите регион',
            allowClear: true,
            language: "ru"
        });

        $(settlementSelect).select2({
            theme: 'bootstrap-5',
            width: $(settlementSelect).data('width') ? $(settlementSelect).data('width') : $(settlementSelect).hasClass('w-100') ? '100%' : 'style',
            placeholder: 'Выберите населенный пункт',
            allowClear: true,
            language: "ru"
        });

        $(institutionSelect).select2({
            theme: 'bootstrap-5',
            width: $(institutionSelect).data('width') ? $(institutionSelect).data('width') : $(institutionSelect).hasClass('w-100') ? '100%' : 'style',
            placeholder: 'Выберите учебное заведение',
            allowClear: true,
            language: "ru"
        });

        // --- Настройка обработчиков событий ---
        $(regionSelect).on('select2:select', function (e) {
            const selectedRegionId = e.params.data.id;
            loadSettlements(selectedRegionId);
        });

        $(settlementSelect).on('select2:select', function (e) {
            const selectedSettlementId = e.params.data.id;
            loadInstitutions(selectedSettlementId);
        });

        // --- Инициализация значений при первой загрузке страницы ---
        const currentRegionId = regionSelect.dataset.currentValue || '0';
        const currentSettlementId = settlementSelect.dataset.currentValue || '0';
        const currentInstitutionId = institutionSelect.dataset.currentValue || '0';

        if (currentRegionId !== '0') {
            loadSettlements(currentRegionId, currentSettlementId, () => {
                if (currentSettlementId !== '0') {
                    loadInstitutions(currentSettlementId, currentInstitutionId);
                }
            });
        } else {
            populateSelect(settlementSelect, [], 'Выберите населенный пункт');
            populateSelect(institutionSelect, [], 'Выберите учебное заведение');
        }
    }
});

// Фикс для Safari и мобильных браузеров
setTimeout(() => {
    document.querySelectorAll('.select2-container--custom-summary').forEach(container => {
        const rendered = container.querySelector('.select2-selection__rendered');
        if (rendered) {
            rendered.querySelectorAll('.select2-selection__choice, .select2-selection__placeholder').forEach(el => {
                el.remove();
            });
        }
    });
}, 1000);
