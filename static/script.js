const form = document.getElementById('analysisForm');
const urlInput = document.getElementById('urlInput');
const submitBtn = document.getElementById('submitBtn');
const statusContainer = document.getElementById('statusContainer');
const resultContainer = document.getElementById('resultContainer');
const errorContainer = document.getElementById('errorContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusMessage = document.getElementById('statusMessage');
const resultContent = document.getElementById('resultContent');
const errorText = document.getElementById('errorText');
const resultInfo = document.getElementById('resultInfo');
const costInfo = document.getElementById('costInfo');
const costValue = document.getElementById('costValue');
const resultActions = document.getElementById('resultActions');
const exportDocxBtn = document.getElementById('exportDocxBtn');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const instrumentsBlock = document.getElementById('instrumentsBlock');
const analysisSection = document.getElementById('analysisSection');
const btnMdToDocx = document.getElementById('btnMdToDocx');
const btnMdToDocxCustom = document.getElementById('btnMdToDocxCustom');
const btnAnalysis = document.getElementById('btnAnalysis');
const backToInstrumentsBtn = document.getElementById('backToInstrumentsBtn');
const toolModalOverlay = document.getElementById('toolModalOverlay');
const toolModalCloseBtn = document.getElementById('toolModalCloseBtn');
const toolModalMdToDocxBtn = document.getElementById('toolModalMdToDocxBtn');
const toolModalError = document.getElementById('toolModalError');
const mdFileInput = document.getElementById('mdFileInput');
const toolModalTitle = document.getElementById('toolModalTitle');
const mdDocxCustomOptions = document.getElementById('mdDocxCustomOptions');
const mdDocxPandocDefaultRow = document.getElementById('mdDocxPandocDefaultRow');
const mdDocxPandocDefault = document.getElementById('mdDocxPandocDefault');
const mdDocxPostprocessSettings = document.getElementById('mdDocxPostprocessSettings');
const mdDocxListMarkerRow = document.getElementById('mdDocxListMarkerRow');
const entryBtn = document.getElementById('entryBtn');
const loginModalOverlay = document.getElementById('loginModalOverlay');
const loginPasswordInput = document.getElementById('loginPasswordInput');
const loginError = document.getElementById('loginError');
const loginSubmitBtn = document.getElementById('loginSubmitBtn');
const loginCancelBtn = document.getElementById('loginCancelBtn');
const adminModalOverlay = document.getElementById('adminModalOverlay');
const adminNewPasswordInput = document.getElementById('adminNewPasswordInput');
const adminConfirmPasswordInput = document.getElementById('adminConfirmPasswordInput');
const adminError = document.getElementById('adminError');
const adminSaveBtn = document.getElementById('adminSaveBtn');
const adminCloseBtn = document.getElementById('adminCloseBtn');

const AUTH_STORAGE_KEY = 'analysisUnlocked';
const ADMIN_CODE = '123654+';

// При загрузке: кнопка анализа активна только если ранее был выполнен вход
if (btnAnalysis) {
    btnAnalysis.disabled = !sessionStorage.getItem(AUTH_STORAGE_KEY);
}

let currentTaskId = null;
let currentResult = null;
let statusCheckInterval = null;
let currentProgress = 0; // Текущее значение прогресса (только увеличивается)

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = urlInput.value.trim();
    if (!url) return;
    
    // Скрываем предыдущие результаты и ошибки
    resultContainer.style.display = 'none';
    resultInfo.style.display = 'none';
    errorContainer.style.display = 'none';
    costInfo.style.display = 'none';
    resultActions.style.display = 'none';
    
    // Блокируем форму
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').style.display = 'none';
    submitBtn.querySelector('.btn-loader').style.display = 'block';
    urlInput.disabled = true;
    
    // Показываем статус
    statusContainer.style.display = 'block';
    currentProgress = 0; // Сбрасываем прогресс при новом анализе
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    statusMessage.textContent = 'Запуск анализа...';
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        // Проверяем Content-Type перед парсингом JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Сервер вернул не JSON ответ');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка при запуске анализа');
        }
        
        currentTaskId = data.task_id;
        startStatusPolling();
        
    } catch (error) {
        showError(error.message);
        resetForm();
    }
});

function startStatusPolling() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        if (!currentTaskId) return;
        
        try {
            const response = await fetch(`/api/status/${currentTaskId}`);
            
            // Проверяем, что ответ успешный и это JSON
            if (!response.ok) {
                // Если ответ не OK, пытаемся получить JSON ошибки
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    // Если не JSON, значит это HTML страница ошибки
                    throw new Error(`Ошибка ${response.status}: ${response.statusText}`);
                }
                throw new Error(errorData.error || `Ошибка ${response.status}`);
            }
            
            // Проверяем Content-Type
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Сервер вернул не JSON ответ');
            }
            
            const data = await response.json();
            
            if (data.status === 'completed') {
                clearInterval(statusCheckInterval);
                
                // Убеждаемся, что результат есть
                if (!data.result) {
                    showError('Результат анализа не найден');
                    resetForm();
                    return;
                }
                
                // Приоритетно используем стоимость из статуса, затем из результата
                let finalCost = null;
                if (data.cost !== null && data.cost !== undefined) {
                    finalCost = data.cost;
                } else if (data.result.cost !== null && data.result.cost !== undefined) {
                    finalCost = data.result.cost;
                }
                
                // Устанавливаем стоимость в результат
                data.result.cost = finalCost;
                
                // Добавляем task_id в результат для экспорта
                data.result.task_id = currentTaskId;
                
                console.log('Отображение результата:', {
                    cost: finalCost,
                    hasResult: !!data.result,
                    taskId: currentTaskId
                });
                
                showResult(data.result);
                resetForm();
                // НЕ очищаем поле ввода - пользователь может использовать кнопку "Анализ другого сайта"
            } else if (data.status === 'error') {
                clearInterval(statusCheckInterval);
                showError(data.message);
                resetForm();
            } else if (data.status === 'processing') {
                updateProgress(data.progress, data.message);
            }
        } catch (error) {
            clearInterval(statusCheckInterval);
            const errorMessage = error.message || 'Ошибка при проверке статуса';
            console.error('Ошибка при проверке статуса:', error);
            showError(errorMessage);
            resetForm();
        }
    }, 2000); // Проверяем каждые 2 секунды
}

function updateProgress(progress, message) {
    // Прогресс может только увеличиваться, никогда не уменьшаться
    // Используем Math.max, чтобы гарантировать, что прогресс не откатывается назад
    const newProgress = Math.max(currentProgress, Math.min(progress, 100));
    
    // Обновляем только если прогресс действительно увеличился
    if (newProgress > currentProgress) {
        currentProgress = newProgress;
        progressFill.style.width = `${currentProgress}%`;
        progressText.textContent = `${currentProgress}%`;
    }
    
    // Сообщение обновляем всегда (может меняться независимо от прогресса)
    if (message) {
        statusMessage.textContent = message;
    }
}

function showResult(result) {
    statusContainer.style.display = 'none';
    resultContainer.style.display = 'block';
    resultInfo.style.display = 'flex';
    
    // Сохраняем результат и task_id для экспорта
    currentResult = result;
    // currentTaskId уже должен быть установлен, но убеждаемся
    if (!currentTaskId && result.task_id) {
        currentTaskId = result.task_id;
    }
    
    // Форматируем результат
    const formattedResult = formatResult(result.result);
    resultContent.textContent = formattedResult;
    
    // Отображаем стоимость анализа
    console.log('Попытка отобразить стоимость:', result.cost, typeof result.cost);
    
    const costValueNum = result.cost !== null && result.cost !== undefined && 
                        result.cost !== 'None' && result.cost !== '' && 
                        !isNaN(parseFloat(result.cost)) ? parseFloat(result.cost) : null;
    
    if (costValueNum !== null) {
        costValue.textContent = `${costValueNum.toFixed(2)} руб.`;
        costInfo.style.display = 'inline-flex';
        console.log('Стоимость отображена:', costValueNum);
    } else {
        costValue.textContent = 'Недоступно';
        costInfo.style.display = 'inline-flex';
        console.log('Стоимость недоступна');
    }
    
    // Показываем кнопки действий
    resultActions.style.display = 'flex';
    
    // Прокручиваем к результатам
    resultInfo.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function formatResult(text) {
    // Простое форматирование текста
    return text;
}

function showError(message) {
    statusContainer.style.display = 'none';
    errorContainer.style.display = 'block';
    errorText.textContent = message;
    
    // Прокручиваем к ошибке
    errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function resetForm() {
    submitBtn.disabled = false;
    submitBtn.querySelector('.btn-text').style.display = 'block';
    submitBtn.querySelector('.btn-loader').style.display = 'none';
    urlInput.disabled = false;
    currentTaskId = null;
}

// Обработчик экспорта в DOCX
exportDocxBtn.addEventListener('click', async () => {
    // Используем task_id из результата или сохраненный currentTaskId
    const taskIdForExport = currentResult?.task_id || currentTaskId;
    
    if (!taskIdForExport || !currentResult) {
        showError('Нет данных для экспорта');
        return;
    }
    
    try {
        exportDocxBtn.disabled = true;
        exportDocxBtn.querySelector('span').textContent = '⏳ Экспорт...';
        
        const response = await fetch(`/api/export/${taskIdForExport}`, {
            method: 'GET',
        });
        
        if (!response.ok) {
            // Пытаемся получить JSON ошибки
            let errorData;
            try {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    errorData = await response.json();
                } else {
                    throw new Error(`Ошибка ${response.status}: ${response.statusText}`);
                }
            } catch (e) {
                throw new Error(`Ошибка при экспорте: ${response.status} ${response.statusText}`);
            }
            throw new Error(errorData.error || 'Ошибка при экспорте');
        }
        
        // Получаем файл
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis_${currentResult.company_name || 'report'}_${new Date().toISOString().split('T')[0]}.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        exportDocxBtn.querySelector('span').textContent = '✅ Экспортировано';
        setTimeout(() => {
            exportDocxBtn.querySelector('span').textContent = '📄 Экспорт в DOCX';
            exportDocxBtn.disabled = false;
        }, 2000);
        
    } catch (error) {
        showError(`Ошибка экспорта: ${error.message}`);
        exportDocxBtn.querySelector('span').textContent = '📄 Экспорт в DOCX';
        exportDocxBtn.disabled = false;
    }
});

// Обработчик нового анализа
newAnalysisBtn.addEventListener('click', () => {
    // Скрываем результаты и ошибки
    resultContainer.style.display = 'none';
    resultInfo.style.display = 'none';
    errorContainer.style.display = 'none';
    
    // Очищаем данные
    currentTaskId = null;
    currentResult = null;
    resultContent.textContent = '';
    
    // Очищаем поле ввода и фокусируемся
    urlInput.value = '';
    urlInput.focus();
    
    // Прокручиваем к форме
    form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
});

// Закрытие результатов и ошибок (если есть кнопка закрытия)
const closeResultBtn = document.getElementById('closeResult');
if (closeResultBtn) {
    closeResultBtn.addEventListener('click', () => {
        resultContainer.style.display = 'none';
        resultInfo.style.display = 'none';
        // Очищаем поле ввода для новой итерации
        urlInput.value = '';
        urlInput.focus();
    });
}

document.getElementById('closeError').addEventListener('click', () => {
    errorContainer.style.display = 'none';
});

function setPostprocessSettingsEnabled(enabled) {
    if (!mdDocxPostprocessSettings) return;
    const inputs = mdDocxPostprocessSettings.querySelectorAll('input, select');
    inputs.forEach(el => {
        el.disabled = !enabled;
    });
}

// Открытие модалки MD→DOCX с выбором движка (pandoc / custom)
function openMdToDocxModal(engine) {
    if (!toolModalOverlay) return;
    toolModalOverlay.dataset.engine = engine || 'pandoc';
    toolModalOverlay.style.display = 'flex';
    toolModalOverlay.setAttribute('aria-hidden', 'false');
    if (toolModalError) {
        toolModalError.style.display = 'none';
        toolModalError.textContent = '';
    }
    if (toolModalTitle) {
        toolModalTitle.textContent = engine === 'custom' ? 'MD → DOCX (свой алгоритм)' : 'MD → DOCX (Pandoc)';
    }
    if (mdDocxCustomOptions) {
        mdDocxCustomOptions.style.display = 'block';
    }
    if (mdDocxPandocDefaultRow) {
        mdDocxPandocDefaultRow.style.display = engine === 'pandoc' ? 'block' : 'none';
    }
    if (mdDocxListMarkerRow) {
        mdDocxListMarkerRow.style.display = engine === 'custom' ? 'flex' : 'none';
    }
    if (engine === 'pandoc' && mdDocxPandocDefault) {
        const useDefault = mdDocxPandocDefault.checked;
        setPostprocessSettingsEnabled(!useDefault);
    } else {
        setPostprocessSettingsEnabled(true);
    }
}

if (mdDocxPandocDefault) {
    mdDocxPandocDefault.addEventListener('change', () => {
        setPostprocessSettingsEnabled(!mdDocxPandocDefault.checked);
    });
}
if (btnMdToDocx && toolModalOverlay) {
    btnMdToDocx.addEventListener('click', () => openMdToDocxModal('pandoc'));
}
if (btnMdToDocxCustom && toolModalOverlay) {
    btnMdToDocxCustom.addEventListener('click', () => openMdToDocxModal('custom'));
}

// Кнопка «Анализ корпоративного сайта» — показываем секцию анализа
if (btnAnalysis && instrumentsBlock && analysisSection) {
    btnAnalysis.addEventListener('click', () => {
        instrumentsBlock.style.display = 'none';
        analysisSection.style.display = 'block';
    });
}

// «К инструментам» — возврат на главный экран с двумя кнопками
if (backToInstrumentsBtn && instrumentsBlock && analysisSection) {
    backToInstrumentsBtn.addEventListener('click', () => {
        instrumentsBlock.style.display = 'block';
        analysisSection.style.display = 'none';
        errorContainer.style.display = 'none';
    });
}

// ——— Скрытый режим администратора: Вход и смена пароля ———
function showLoginModal() {
    if (loginModalOverlay && loginPasswordInput) {
        loginPasswordInput.value = '';
        if (loginError) { loginError.style.display = 'none'; loginError.textContent = ''; }
        loginModalOverlay.style.display = 'flex';
        loginModalOverlay.setAttribute('aria-hidden', 'false');
        loginPasswordInput.focus();
    }
}
function hideLoginModal() {
    if (loginModalOverlay) {
        loginModalOverlay.style.display = 'none';
        loginModalOverlay.setAttribute('aria-hidden', 'true');
    }
}
function showAdminModal() {
    if (adminModalOverlay && adminNewPasswordInput && adminConfirmPasswordInput) {
        adminNewPasswordInput.value = '';
        adminConfirmPasswordInput.value = '';
        if (adminError) { adminError.style.display = 'none'; adminError.textContent = ''; }
        adminModalOverlay.style.display = 'flex';
        adminModalOverlay.setAttribute('aria-hidden', 'false');
        adminNewPasswordInput.focus();
    }
}
function hideAdminModal() {
    if (adminModalOverlay) {
        adminModalOverlay.style.display = 'none';
        adminModalOverlay.setAttribute('aria-hidden', 'true');
    }
}

if (entryBtn) {
    entryBtn.addEventListener('click', () => showLoginModal());
}

if (loginSubmitBtn && loginPasswordInput) {
    async function doLogin() {
        const password = loginPasswordInput.value.trim();
        if (!password) return;
        if (password === ADMIN_CODE) {
            hideLoginModal();
            showAdminModal();
            return;
        }
        try {
            const response = await fetch('/api/auth/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password })
            });
            const data = await response.json();
            if (data.ok && !data.admin) {
                sessionStorage.setItem(AUTH_STORAGE_KEY, '1');
                if (btnAnalysis) btnAnalysis.disabled = false;
                hideLoginModal();
            } else {
                sessionStorage.removeItem(AUTH_STORAGE_KEY);
                if (btnAnalysis) btnAnalysis.disabled = true;
                if (loginError) {
                    loginError.textContent = 'Неверный пароль';
                    loginError.style.display = 'block';
                }
            }
        } catch (e) {
            sessionStorage.removeItem(AUTH_STORAGE_KEY);
            if (btnAnalysis) btnAnalysis.disabled = true;
            if (loginError) {
                loginError.textContent = 'Ошибка проверки пароля';
                loginError.style.display = 'block';
            }
        }
    }
    loginSubmitBtn.addEventListener('click', doLogin);
    loginPasswordInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') doLogin(); });
}
if (loginCancelBtn) {
    loginCancelBtn.addEventListener('click', () => hideLoginModal());
}
if (loginModalOverlay) {
    loginModalOverlay.addEventListener('click', (e) => {
        if (e.target === loginModalOverlay) hideLoginModal();
    });
}

if (adminSaveBtn && adminNewPasswordInput && adminConfirmPasswordInput) {
    adminSaveBtn.addEventListener('click', async () => {
        const newPwd = adminNewPasswordInput.value;
        const confirmPwd = adminConfirmPasswordInput.value;
        if (adminError) { adminError.style.display = 'none'; adminError.textContent = ''; }
        if (newPwd !== confirmPwd) {
            if (adminError) {
                adminError.textContent = 'Пароли не совпадают';
                adminError.style.display = 'block';
            }
            return;
        }
        if (!newPwd.trim()) {
            if (adminError) {
                adminError.textContent = 'Введите новый пароль';
                adminError.style.display = 'block';
            }
            return;
        }
        try {
            const response = await fetch('/api/auth/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ admin_key: ADMIN_CODE, new_password: newPwd.trim() })
            });
            const data = await response.json();
            if (response.ok && data.ok) {
                hideAdminModal();
            } else {
                if (adminError) {
                    adminError.textContent = (data && data.error) || 'Ошибка сохранения';
                    adminError.style.display = 'block';
                }
            }
        } catch (e) {
            if (adminError) {
                adminError.textContent = 'Ошибка сети';
                adminError.style.display = 'block';
            }
        }
    });
}
if (adminCloseBtn) {
    adminCloseBtn.addEventListener('click', () => hideAdminModal());
}
if (adminModalOverlay) {
    adminModalOverlay.addEventListener('click', (e) => {
        if (e.target === adminModalOverlay) hideAdminModal();
    });
}

if (toolModalCloseBtn && toolModalOverlay) {
    toolModalCloseBtn.addEventListener('click', () => {
        toolModalOverlay.style.display = 'none';
        toolModalOverlay.setAttribute('aria-hidden', 'true');
    });
}
if (toolModalOverlay) {
    toolModalOverlay.addEventListener('click', (e) => {
        if (e.target === toolModalOverlay) {
            toolModalOverlay.style.display = 'none';
            toolModalOverlay.setAttribute('aria-hidden', 'true');
        }
    });
}

// MD → DOCX: по клику на кнопку в модалке — выбор файла
if (toolModalMdToDocxBtn && mdFileInput) {
    toolModalMdToDocxBtn.addEventListener('click', () => {
        mdFileInput.value = '';
        mdFileInput.click();
    });
}
// Показать ошибку в модалке MD→DOCX (модалка остаётся открытой для повторной попытки)
function showToolModalError(message) {
    if (toolModalError) {
        toolModalError.textContent = message;
        toolModalError.style.display = 'block';
    } else {
        showError(message);
    }
}

function hideToolModalError() {
    if (toolModalError) {
        toolModalError.style.display = 'none';
        toolModalError.textContent = '';
    }
}

// После выбора .md — отправка на сервер и скачивание DOCX
if (mdFileInput) {
    mdFileInput.addEventListener('change', async () => {
        const file = mdFileInput.files[0];
        if (!file) return;
        const btn = toolModalMdToDocxBtn;
        const engine = (toolModalOverlay && toolModalOverlay.dataset.engine) || 'pandoc';
        hideToolModalError();
        if (btn) btn.disabled = true;
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('engine', engine);
            const spacing = {
                normal: { before: parseInt(document.getElementById('mdDocxNormalBefore')?.value || 0, 10) || 0, after: parseInt(document.getElementById('mdDocxNormalAfter')?.value || 0, 10) || 0 },
                heading1: { before: parseInt(document.getElementById('mdDocxH1Before')?.value || 12, 10) || 0, after: parseInt(document.getElementById('mdDocxH1After')?.value || 6, 10) || 0 },
                heading2: { before: parseInt(document.getElementById('mdDocxH2Before')?.value || 10, 10) || 0, after: parseInt(document.getElementById('mdDocxH2After')?.value || 4, 10) || 0 },
                heading3: { before: parseInt(document.getElementById('mdDocxH3Before')?.value || 8, 10) || 0, after: parseInt(document.getElementById('mdDocxH3After')?.value || 4, 10) || 0 },
                heading4: { before: parseInt(document.getElementById('mdDocxH4Before')?.value || 6, 10) || 0, after: parseInt(document.getElementById('mdDocxH4After')?.value || 2, 10) || 0 },
            };
            formData.append('spacing', JSON.stringify(spacing));
            const usePandocDefault = (engine === 'pandoc' && document.getElementById('mdDocxPandocDefault')?.checked);
            formData.append('use_pandoc_default', usePandocDefault ? '1' : '0');
            const options = {
                line_spacing: parseFloat(document.getElementById('mdDocxLineSpacing')?.value || 1.15),
                table_font_size: parseInt(document.getElementById('mdDocxTableFont')?.value || 9, 10) || 9,
                main_font_size: parseInt(document.getElementById('mdDocxMainFont')?.value || 11, 10) || 11,
                alternating_rows: document.getElementById('mdDocxAlternatingRows')?.checked !== false,
                list_marker: document.getElementById('mdDocxListMarker')?.value || 'default',
            };
            formData.append('options', JSON.stringify(options));
            const apiUrl = engine === 'custom' ? '/api/convert/md-to-docx' : '/api/convert/md-to-docx-pandoc';
            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData,
            });
            const contentType = response.headers.get('content-type') || '';
            if (!response.ok) {
                let msg = `Ошибка ${response.status}: ${response.statusText}`;
                if (contentType.includes('application/json')) {
                    try {
                        const err = await response.json();
                        msg = err.error || msg;
                    } catch (_) {}
                }
                showToolModalError(msg + ' Выберите файл снова или другой файл.');
                return;
            }
            // Ответ 200 с JSON — значит сервер вернул ошибку в теле
            if (contentType.includes('application/json')) {
                try {
                    const data = await response.json();
                    showToolModalError((data.error || 'Ошибка конвертации') + ' Выберите файл снова.');
                } catch (_) {
                    showToolModalError('Неожиданный ответ сервера. Выберите файл снова.');
                }
                return;
            }
            const blob = await response.blob();
            if (!blob || blob.size === 0) {
                showToolModalError('Сервер вернул пустой файл. Попробуйте другой файл или проверьте сервер.');
                return;
            }
            const name = response.headers.get('content-disposition');
            let filename = (file.name || 'document').replace(/\.[^/.]+$/, '') + '_converted.docx';
            if (name && name.includes('filename=')) {
                const m = name.match(/filename\*?=(?:UTF-8'')?([^'";\n]+)/i) || name.match(/filename=['"]?([^'";\n]+)/);
                if (m) {
                    try {
                        filename = decodeURIComponent(m[1].trim().replace(/^"(.*)"$/, '$1'));
                    } catch (_) {
                        filename = m[1].trim();
                    }
                }
            }
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.style.display = 'none';
            document.body.appendChild(a);
            requestAnimationFrame(() => {
                a.click();
                setTimeout(() => {
                    window.URL.revokeObjectURL(url);
                    if (a.parentNode) document.body.removeChild(a);
                }, 300);
            });
            hideToolModalError();
            toolModalOverlay.style.display = 'none';
            toolModalOverlay.setAttribute('aria-hidden', 'true');
        } catch (e) {
            const raw = (e.message || String(e)).trim();
            let msg;
            if (raw === 'Failed to fetch' || raw.toLowerCase().includes('failed to fetch')) {
                msg = 'Не удалось связаться с сервером. Проверьте: 1) приложение запущено (python main.py); 2) страница открыта по адресу сервера (например http://localhost:5000), а не как файл; 3) файл не слишком большой. Затем выберите файл снова.';
            } else if (raw.toLowerCase().includes('network') || raw.toLowerCase().includes('load')) {
                msg = 'Ошибка сети или сервер не отвечает. Убедитесь, что приложение запущено и откройте страницу по адресу сервера (например http://localhost:5000). Выберите файл снова.';
            } else {
                msg = 'Ошибка при конвертации: ' + raw + ' Выберите файл снова или проверьте соединение.';
            }
            showToolModalError(msg);
        } finally {
            mdFileInput.value = '';
            if (btn) btn.disabled = false;
        }
    });
}
