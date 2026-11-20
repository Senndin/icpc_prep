// Ініціалізація підказок для кнопок панелі інструментів
document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
  new bootstrap.Tooltip(el);
});

// Модальне вікно підтвердження видалення: підставляємо адресу та назву об'єкта
var deleteModal = document.getElementById('deleteModal');
if (deleteModal) {
  deleteModal.addEventListener('show.bs.modal', function (event) {
    var button = event.relatedTarget;
    deleteModal.querySelector('form').action = button.getAttribute('data-url');
    deleteModal.querySelector('.object-name').textContent = button.getAttribute('data-name');
  });
}

// Автоматичне приховування інформаційних повідомлень через 6 секунд
setTimeout(function () {
  document.querySelectorAll('.alert-dismissible.auto-hide').forEach(function (el) {
    bootstrap.Alert.getOrCreateInstance(el).close();
  });
}, 6000);
