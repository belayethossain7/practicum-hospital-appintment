/* dp_theme.js — Sidebar toggle + theiaStickySidebar neutralization
   Scope: body.dp-theme only
   ------------------------------------------------------------ */
(function () {
  'use strict';

  /* -------------------------------------------------------
     PHASE 1 — Prevent theiaStickySidebar from ever running
     on dp-theme pages by removing the class it targets
     BEFORE the plugin initialises (script.js runs later).
     ------------------------------------------------------- */
  var body = document.body;
  if (!body.classList.contains('dp-theme')) return;

  /* Strip .theiaStickySidebar from sidebar columns NOW (sync, before DOMContentLoaded).
     The plugin only inits for elements that have this class. */
  var stickyCols = document.querySelectorAll('.dp-theme-sidebar-col.theiaStickySidebar');
  for (var i = 0; i < stickyCols.length; i++) {
    stickyCols[i].classList.remove('theiaStickySidebar');
    stickyCols[i].setAttribute('data-dp-sticky-disabled', '1');
  }

  document.addEventListener('DOMContentLoaded', function () {

    /* -------------------------------------------------------
       PHASE 2 — Mobile sidebar toggle
       ------------------------------------------------------- */
    var sidebar = document.querySelector('.dp-theme-sidebar-col');
    var toggle  = document.querySelector('.dp-sidebar-toggle');
    var overlay = document.querySelector('.dp-sidebar-overlay');

    function openSidebar() {
      if (!sidebar) return;
      sidebar.classList.add('dp-sidebar-open');
      if (overlay) overlay.classList.add('dp-active');
      body.style.overflow = 'hidden';
    }

    function closeSidebar() {
      if (!sidebar) return;
      sidebar.classList.remove('dp-sidebar-open');
      if (overlay) overlay.classList.remove('dp-active');
      body.style.overflow = '';
    }

    if (toggle) {
      toggle.addEventListener('click', function () {
        if (sidebar && sidebar.classList.contains('dp-sidebar-open')) {
          closeSidebar();
        } else {
          openSidebar();
        }
      });
    }

    if (overlay) {
      overlay.addEventListener('click', closeSidebar);
    }

    /* -------------------------------------------------------
       PHASE 3 — Aggressively neutralize theiaStickySidebar
       The plugin sets inline styles on scroll (position,
       height, transform, top, left, overflow, width).
       We observe and strip them continuously.
       ------------------------------------------------------- */
    function cleanStickyStyles(el) {
      var dirty = false;
      var props = ['position', 'height', 'overflow', 'padding-bottom',
                   'margin-bottom', 'transform', 'top', 'left', 'width',
                   '-webkit-transform'];
      for (var j = 0; j < props.length; j++) {
        if (el.style.getPropertyValue(props[j])) {
          el.style.removeProperty(props[j]);
          dirty = true;
        }
      }
      return dirty;
    }

    function cleanAllSticky() {
      var targets = document.querySelectorAll(
        '.dp-theme-sidebar-col, ' +
        '.dp-theme-sidebar-col .theiaStickySidebar, ' +
        '.dp-theme-sidebar-col [style*="position"]'
      );
      for (var k = 0; k < targets.length; k++) {
        cleanStickyStyles(targets[k]);
      }
    }

    /* Initial cleanup */
    cleanAllSticky();

    /* Unbind theiaStickySidebar scroll/resize handlers so they stop
       re-injecting inline styles. The plugin uses namespace 'TSS'. */
    if (typeof jQuery !== 'undefined') {
      jQuery(document).off('scroll.TSS');
      jQuery(window).off('resize.TSS');
    }

    /* Also re-strip the class if script.js somehow re-adds it */
    var sidebarCol = document.querySelector('.dp-theme-sidebar-col');
    if (sidebarCol) {
      /* If theiaStickySidebar already ran and wrapped content, unwrap it */
      var innerSticky = sidebarCol.querySelector('.theiaStickySidebar');
      if (innerSticky && innerSticky !== sidebarCol) {
        cleanStickyStyles(innerSticky);
        /* Move children back out of wrapper if the plugin wrapped them */
        if (innerSticky.parentNode === sidebarCol &&
            sidebarCol.children.length === 1 &&
            innerSticky.classList.contains('theiaStickySidebar')) {
          while (innerSticky.firstChild) {
            sidebarCol.insertBefore(innerSticky.firstChild, innerSticky);
          }
          sidebarCol.removeChild(innerSticky);
        }
      }

      /* MutationObserver — strip inline styles whenever they change */
      if (typeof MutationObserver !== 'undefined') {
        var observer = new MutationObserver(function (mutations) {
          for (var m = 0; m < mutations.length; m++) {
            var target = mutations[m].target;
            if (mutations[m].type === 'attributes' &&
                mutations[m].attributeName === 'style') {
              cleanStickyStyles(target);
            }
            /* If child nodes were added (plugin wrapper div), clean them too */
            if (mutations[m].type === 'childList') {
              cleanAllSticky();
            }
          }
        });
        observer.observe(sidebarCol, {
          attributes: true,
          attributeFilter: ['style'],
          childList: true,
          subtree: true
        });
      }

      /* Fallback: interval-based cleanup for older browsers */
      setInterval(cleanAllSticky, 500);
    }

    /* Also clean sidebar parent (.content row) inline styles */
    var contentRow = document.querySelector('.dp-theme-content > .container-fluid > .row');
    if (contentRow) {
      cleanStickyStyles(contentRow);
    }
  });
})();
