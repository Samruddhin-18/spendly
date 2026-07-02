// main.js — students will add JavaScript here as features are built

(function () {
    var openBtn = document.getElementById('how-it-works-btn');
    var overlay = document.getElementById('video-modal-overlay');
    var closeBtn = document.getElementById('video-modal-close');
    var iframe = document.getElementById('video-modal-iframe');

    if (!openBtn || !overlay || !closeBtn || !iframe) {
        return;
    }

    function openModal(e) {
        e.preventDefault();
        iframe.src = iframe.dataset.src + '?autoplay=1';
        overlay.classList.add('is-open');
    }

    function closeModal() {
        overlay.classList.remove('is-open');
        iframe.src = '';
    }

    openBtn.addEventListener('click', openModal);
    closeBtn.addEventListener('click', closeModal);

    overlay.addEventListener('click', function (e) {
        if (e.target === overlay) {
            closeModal();
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && overlay.classList.contains('is-open')) {
            closeModal();
        }
    });
})();
