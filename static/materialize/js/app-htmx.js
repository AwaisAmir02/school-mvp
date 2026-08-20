document.body.addEventListener('htmx:afterSwap', function (event) {
  if (event.detail.target && event.detail.target.id === 'modal-root') {
    var modalEl = event.detail.target.querySelector('.modal');
    if (modalEl) {
      bootstrap.Modal.getOrCreateInstance(modalEl).show();
    }
  }
});

document.body.addEventListener('refresh-list', function () {
  var modalEl = document.querySelector('#modal-root .modal.show');
  if (modalEl) {
    bootstrap.Modal.getOrCreateInstance(modalEl).hide();
  }
});

document.body.addEventListener('hidden.bs.modal', function (event) {
  var root = document.getElementById('modal-root');
  if (root && root.contains(event.target)) {
    root.innerHTML = '';
  }
});
