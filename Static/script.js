// Флаг для предотвращения множественных отправок
let isSubmitting = false;

  // Обработчик отправки данных салона
async function sendReportData(e, form) {
    e.preventDefault();
    if (isSubmitting) return;
    isSubmitting = true;

    const submitButton = e.submitter;
    const row = submitButton.closest("tr");
    const salonName = row.querySelector("td:first-child").textContent;

    // Получаем ID из формы (если есть)
    const formId = form.id;
    const reportId = formId ? formId.split('-').pop() : null;

    const card = parseFloat(form.card_sales.value) || 0;
    const sbp = parseFloat(form.sbp_sales.value) || 0;
    const ratio = (sbp > 0) ? ((card / sbp) * 100).toFixed(2) : 0;
    form.ratio.value = ratio + "%";

    const data = {
        salon_name: salonName,
        card_sales: card,
        sbp_sales: sbp
    };

    try {
        // Если у нас есть ID, используем PUT для обновления, иначе POST для создания
        const url = reportId ? `/api/reports/${reportId}` : '/api/reports/';
        const method = reportId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка сервера');
        }

        const result = await response.json();
        alert(reportId ? 'Отчет успешно обновлен' : 'Отчет успешно сохранен');
        location.reload();
    } catch (error) {
        console.error('Ошибка:', error);
        alert(error.message);
    } finally {
        isSubmitting = false;
    }
}

// После загрузки данных с сервера:
function displayOfficesReport(offices) {
    const tbody = document.querySelector("tbody");
    if (!tbody) return;

    tbody.innerHTML = offices.map(office => {
        const formId = `form-salon-${office.id}`;
        return `
            <tr>
                <td>${office.salon_name}</td>
                <td><input type="number" form="${formId}" name="card_sales" required value="${office.card_sales}"></td>
                <td><input type="number" form="${formId}" name="sbp_sales" required value="${office.sbp_sales}"></td>
                <td><output form="${formId}" name="ratio">${((office.sbp_sales > 0) ? ((office.sbp_sales / office.card_sales) * 100).toFixed(2) : 0)}%</output></td>
                <td><button type="submit" form="${formId}">${office.is_submitted ? 'Обновить' : 'Отправить'}</button></td>
            </tr>
        `;
    }).join('');

    offices.forEach(office => {
        const formId = `form-salon-${office.id}`;
        let form = document.getElementById(formId);
        if (!form) {
            form = document.createElement("form");
            form.id = formId;
            form.onsubmit = (e) => sendReportData(e, form);
            document.body.appendChild(form);
        }
    });
}

// Функция загрузки списка салонов
async function loadOfficesReport() {
    try {
        const response = await fetch('/api/reports/');
        if (!response.ok) throw new Error('Ошибка при загрузке салонов');

        const offices = await response.json();
        displayOfficesReport(offices);
    } catch (error) {
        console.error('Ошибка', error);
    }
}

// Основная функция отправки отчета
// document.getElementById('submit')?.addEventListener('click', async function(e) {
//     e.preventDefault();
//
//     if (isSubmitting) return;
//     isSubmitting = true;
//
//     const formData = {
//         salon_name: document.getElementById('salon-name')?.value || "Название салона",
//         card_sales: parseFloat(document.getElementById('card-sales')?.value) || 0,
//         sbp_sales: parseFloat(document.getElementById('sbp-sales')?.value) || 0
//     };
//
//     try {
//         const response = await fetch('/api/reports/', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify(formData)
//         });
//
//         if (!response.ok) {
//             const errorData = await response.json();
//             throw new Error(errorData.detail || 'Ошибка сервера');
//         }
//
//         const result = await response.json();
//         alert('Отчет успешно сохранен');
//         location.reload();
//     } catch (error) {
//         console.error('Ошибка:', error);
//         alert(error.message);
//     } finally {
//         isSubmitting = false;
//     }
// });

// Обработчик для кнопки добавления нового салона
document.querySelector('.offices-dialog__addbtn')?.addEventListener('click', function(e) {
    e.preventDefault();
    const hidingBlock = document.querySelector('.offices-dialog__hidding-block');
    if (hidingBlock) {
        hidingBlock.classList.toggle('active');
    }
});

// Обработчик для кнопки подтверждения добавления салона
document.addEventListener('click', function(el) {
    if (el.target.closest('.offices-dialog__addinputbtn')) {
        el.preventDefault();
        handleAddOfficeSubmit(el);
    }
});

// Функция обработки отправки формы добавления салона
async function handleAddOfficeSubmit(el) {
    if (isSubmitting) return;
    isSubmitting = true;

    const input = document.getElementById('offices-dialog__addinput');
    const hidingBlock = document.querySelector('.offices-dialog__hidding-block');

    if (!input) {
        isSubmitting = false;
        return;
    }

    const listOffices = {
        salon_name: input.value.trim(),
        card_sales: 0,
        sbp_sales: 0
    };

    if (!listOffices.salon_name) {
        alert('Название салона не может быть пустым');
        isSubmitting = false;
        return;
    }

    try {
        const response = await fetch('/api/reports/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(listOffices)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Ошибка сервера');
        }

        await loadOffices();
        input.value = '';
        if (hidingBlock) {
            hidingBlock.classList.remove('active');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert(error.message);
    } finally {
        isSubmitting = false;
    }
}


// Функция загрузки списка салонов
async function loadOffices() {
    try {
        const response = await fetch('/api/reports/');
        if (!response.ok) throw new Error('Ошибка при загрузке салонов');

        const offices = await response.json();
        displayOffices(offices);
    } catch (error) {
        console.error('Ошибка', error);
    }
}

// Функция отображения списка салонов
function displayOffices(offices) {
    const officesDialogUl = document.querySelector('.dialog__content ul');
    if (!officesDialogUl) return;

    officesDialogUl.innerHTML = offices.map(office => `
        <li>
            <span data-id="${office.id}">${office.salon_name}</span>
            <div class="offices-dialog__btns-block">
                <button class="offices-dialog__editbtn" data-id="${office.id}"><ion-icon name="create"></ion-icon></button>
                <button class="offices-dialog__delbtn" data-id="${office.id}"><ion-icon name="trash"></ion-icon></button>      
            </div>
        </li>
    `).join('');

    // Добавляем обработчики для кнопок удаления
    document.querySelectorAll('.offices-dialog__delbtn').forEach(btn => {
        btn.addEventListener('click', handleDeleteOffice);
    });
    document.querySelectorAll('.offices-dialog__editbtn').forEach(btn => {
        btn.addEventListener('click', handleEditOffice);
    });
}
// Обработчик редактирования названия салона
async function handleEditOffice(e) {
    e.preventDefault();
    if (isSubmitting) return;
    isSubmitting = true;

    const id = e.currentTarget.getAttribute('data-id');
    const li = e.currentTarget.parentElement.parentElement;

    // Скрываем текст и вставляем форму
    const span = e.currentTarget.parentElement.previousElementSibling;
    span.style.display = "none";

    li.innerHTML = `
        <form id="edit-office__form">
            <input type="text" id="edit-office__input" value="${span.textContent}">
            <div class="edit-office__btn-block">
                <button type="button" id="edit-office__btn-confirm"><ion-icon name="checkmark"></ion-icon></button>
                <button type="button" id="edit-office__btn-cancel"><ion-icon name="close"></ion-icon></button>
            </div>
        </form>
    `;

    // Получаем элементы формы
    const form = li.querySelector('#edit-office__form');
    const input = li.querySelector('#edit-office__input');
    const confirmBtn = li.querySelector('#edit-office__btn-confirm');
    const cancelBtn = li.querySelector('#edit-office__btn-cancel');

    // Ожидаем действия пользователя (аналог dialog.returnValue)
    try {
        const newValue = await new Promise((resolve, reject) => {
            confirmBtn.addEventListener('click', () => {
                const value = input.value.trim();
                if (value) {
                    resolve(value); // Подтверждение с новым значением
                } else {
                    reject(new Error("Поле не может быть пустым"));
                }
            }, { once: true });

            cancelBtn.addEventListener('click', () => {
                reject(new Error("Редактирование отменено"));
            }, { once: true });
        });

        // Если пользователь подтвердил ввод
        console.log("Новое значение:", newValue);

        // Отправляем данные на сервер (аналогично handleDeleteOffice)
        const response = await fetch(`/api/reports/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ salon_name: newValue }),
        });

        if (!response.ok) throw new Error('Ошибка при обновлении');

        // Обновляем интерфейс
        span.textContent = newValue;
        span.style.display = "inline";
        li.innerHTML = ''; // Удаляем форму (или восстанавливаем исходный HTML)
        await loadOffices();

    } catch (error) {
        // Если пользователь отменил или ошибка
        console.log(error.message);
        span.style.display = "inline"; // Показываем исходный текст
        li.innerHTML = ''; // Удаляем форму
        await loadOffices();
    } finally {
        isSubmitting = false;
    }
}

// Обработчик удаления салона
async function handleDeleteOffice(e) {
    e.preventDefault();
    const id = e.currentTarget.getAttribute('data-id');

    const dialog = window['dialog__confirm-del'];
    if (!dialog) return;

    dialog.showModal();

    const userConfirmed = await new Promise((resolve) => {
        dialog.addEventListener('close', () => {
            resolve(dialog.returnValue === "yes");
        }, { once: true });
    });

    if (!userConfirmed) {
        console.log("Действие отменено пользователем");
        return;
    }

    try {
        const response = await fetch(`/api/reports/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) throw new Error('Ошибка при удалении салона');

        await loadOffices();
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка: ' + error.message);
    }

}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    loadOffices();
    loadOfficesReport();
});