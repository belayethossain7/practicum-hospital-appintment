/* ============================================================
   HealthStack Hospital Admin  admin_custom.js
   Handles: sidebar, submenu, user dropdown, delete modal, toasts
   ============================================================ */
(function () {
    'use strict';

    function ready(fn) {
        if (document.readyState !== 'loading') { fn(); }
        else { document.addEventListener('DOMContentLoaded', fn); }
    }

    ready(function () {

        /*  Sidebar open / close  */
        var body    = document.body;
        var toggler = document.getElementById('haToggler');
        var overlay = document.getElementById('haOverlay');

        function openSidebar() {
            body.classList.add('ha-sb-open');
            if (toggler) toggler.setAttribute('aria-expanded', 'true');
        }
        function closeSidebar() {
            body.classList.remove('ha-sb-open');
            if (toggler) toggler.setAttribute('aria-expanded', 'false');
        }
        function toggleSidebar() {
            if (body.classList.contains('ha-sb-open')) { closeSidebar(); }
            else { openSidebar(); }
        }

        if (toggler)  toggler.addEventListener('click', toggleSidebar);
        if (overlay)  overlay.addEventListener('click', closeSidebar);

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') { closeSidebar(); }
        });
        window.addEventListener('resize', function () {
            if (window.innerWidth >= 992) { closeSidebar(); }
        });

        /*  Sidebar submenu accordion  */
        var sidebarToggles = document.querySelectorAll('.ha-sidebar-toggle');
        sidebarToggles.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var item   = btn.closest('.ha-sidebar-item');
                if (!item) return;
                var isOpen = item.classList.contains('is-open');

                /* close every other open item */
                document.querySelectorAll('.ha-sidebar-item.is-open').forEach(function (el) {
                    el.classList.remove('is-open');
                    var b = el.querySelector('.ha-sidebar-toggle');
                    if (b) b.setAttribute('aria-expanded', 'false');
                });

                if (!isOpen) {
                    item.classList.add('is-open');
                    btn.setAttribute('aria-expanded', 'true');
                }
            });
        });

        /*  User dropdown  */
        var userBtn  = document.getElementById('haUserBtn');
        var userMenu = document.getElementById('haUserMenu');

        if (userBtn && userMenu) {
            userBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                var open = userMenu.classList.toggle('is-open');
                userBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
            });

            /* Close when clicking outside */
            document.addEventListener('click', function () {
                userMenu.classList.remove('is-open');
                userBtn.setAttribute('aria-expanded', 'false');
            });

            /* Prevent menu click from bubbling to document */
            userMenu.addEventListener('click', function (e) {
                e.stopPropagation();
            });

            /* Keyboard: Escape closes dropdown */
            document.addEventListener('keydown', function (e) {
                if (e.key === 'Escape') {
                    userMenu.classList.remove('is-open');
                    userBtn.setAttribute('aria-expanded', 'false');
                }
            });
        }

        /*  Delete confirmation modal  */
        var deleteModal = document.getElementById('haDeleteModal');
        if (deleteModal && window.jQuery) {
            window.jQuery(deleteModal).on('show.bs.modal', function (event) {
                var trigger  = event.relatedTarget;
                if (!trigger) return;
                var form     = deleteModal.querySelector('#haDeleteForm');
                var nameEl   = deleteModal.querySelector('[data-ha-delete-target]');
                var hintEl   = deleteModal.querySelector('[data-ha-delete-hint]');
                if (form)   form.action       = trigger.getAttribute('data-ha-delete-url')  || '#';
                if (nameEl) nameEl.textContent = trigger.getAttribute('data-ha-delete-name') || 'this record';
                if (hintEl) hintEl.textContent = trigger.getAttribute('data-ha-delete-hint') || 'This action cannot be undone.';
            });
        }

        /*  Toast notifications  */
        if (window.jQuery && window.jQuery.fn.toast) {
            window.jQuery('.toast.notification').toast({ delay: 4000 }).toast('show');
        }

    });
}());
