(function () {
  function qs(id) {
    return document.getElementById(id);
  }

  // Home page booking form should NOT refresh other sections.
  // This script only manages booking dropdown cascades + carousels.

  function init() {
    var form = document.getElementById('hsFilterForm');
    if (!form) return;

    var hospitalSelect = qs('hsHospitalSelect');
    var specializationSelect = qs('hsSpecializationSelect');
    var doctorSelect = qs('hsDoctorSelect');
    var dateInput = qs('hsDateInput');
    var slotSelect = qs('hsSlotSelect');
    var quickBookBtn = qs('hsQuickBookBtn');
    var dateHelp = qs('hsDateHelp');

    var urlParams = new URLSearchParams(window.location.search || '');

    function selectedFrom(el, key) {
      if (!el) return '';
      var fromAttr = el.getAttribute('data-selected');
      if (fromAttr) return String(fromAttr);
      if (key && urlParams.get(key)) return String(urlParams.get(key));
      return '';
    }

    var api = {
      specializations: '/home/specializations/',
      doctors: '/home/doctors/',
      availableSlots: '/home/available-slots/'
    };

    function initHospitalsCarousel() {
      var carousel = document.getElementById('hsHospitalCarousel');
      if (!carousel) return;

      var prevBtn = document.getElementById('hsHospitalPrev');
      var nextBtn = document.getElementById('hsHospitalNext');

      window.__hsHospitalCarouselEl = carousel;

      function itemWidth() {
        var active = window.__hsHospitalCarouselEl || carousel;
        var item = active.querySelector('.hs-carousel-item');
        if (!item) return 320;
        return item.getBoundingClientRect().width + 16;
      }

      function scrollByItems(direction) {
        var active = window.__hsHospitalCarouselEl || carousel;
        active.scrollBy({ left: direction * itemWidth(), behavior: 'smooth' });
      }

      if (!window.__hsHospitalControlsBound) {
        window.__hsHospitalControlsBound = true;
        if (prevBtn) prevBtn.addEventListener('click', function () { scrollByItems(-1); });
        if (nextBtn) nextBtn.addEventListener('click', function () { scrollByItems(1); });
      }

      var paused = false;
      carousel.addEventListener('mouseenter', function () { paused = true; });
      carousel.addEventListener('mouseleave', function () { paused = false; });

      if (window.__hsHospitalCarouselIntervalId) {
        window.clearInterval(window.__hsHospitalCarouselIntervalId);
      }

      window.__hsHospitalCarouselIntervalId = window.setInterval(function () {
        if (paused) return;
        var active = window.__hsHospitalCarouselEl || carousel;
        if (active.scrollWidth <= active.clientWidth + 2) return;

        var nearEnd = active.scrollLeft + active.clientWidth >= active.scrollWidth - 12;
        if (nearEnd) {
          active.scrollTo({ left: 0, behavior: 'smooth' });
          return;
        }

        scrollByItems(1);
      }, 2600);
    }

    function setSelectOptions(selectEl, options, placeholder) {
      if (!selectEl) return;
      selectEl.innerHTML = '';
      var ph = document.createElement('option');
      ph.value = '';
      ph.textContent = placeholder || 'Select';
      selectEl.appendChild(ph);
      for (var i = 0; i < options.length; i++) {
        var opt = document.createElement('option');
        opt.value = String(options[i].value);
        opt.textContent = options[i].label;
        selectEl.appendChild(opt);
      }
    }

    function setDisabled(el, disabled, placeholder) {
      if (!el) return;
      el.disabled = !!disabled;
      if (placeholder) {
        setSelectOptions(el, [], placeholder);
      }
    }

    function isPastDate(dateStr) {
      if (!dateStr) return false;
      // dateStr: YYYY-MM-DD
      var parts = dateStr.split('-');
      if (parts.length !== 3) return false;
      var d = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
      var now = new Date();
      var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      return d.getTime() < today.getTime();
    }

    function updateQuickBookEnabled() {
      if (!quickBookBtn) return;
      var ok = !!(doctorSelect && doctorSelect.value && dateInput && dateInput.value && slotSelect && slotSelect.value);
      quickBookBtn.disabled = !ok;
    }

    function validateDate() {
      if (!dateInput) return true;
      var invalid = isPastDate(dateInput.value);
      if (invalid) {
        dateInput.classList.add('hs-date-invalid');
        if (dateHelp) dateHelp.classList.remove('d-none');
      } else {
        dateInput.classList.remove('hs-date-invalid');
        if (dateHelp) dateHelp.classList.add('d-none');
      }
      return !invalid;
    }

    function loadSpecializations() {
      if (!hospitalSelect || !specializationSelect) return;
      var hid = hospitalSelect.value;
      if (!hid) {
        setDisabled(specializationSelect, true, 'Select hospital first');
        setDisabled(doctorSelect, true, 'Select specialization first');
        setDisabled(slotSelect, true, 'Select date to see slots');
        updateQuickBookEnabled();
        return;
      }

      specializationSelect.disabled = true;
      setSelectOptions(specializationSelect, [], 'Loading…');
      fetch(api.specializations + '?hospital=' + encodeURIComponent(hid), { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var items = (data && data.items) ? data.items : [];
          var opts = items.map(function (x) {
            return { value: x.specialization_id, label: x.specialization__specialization_name };
          });
          specializationSelect.disabled = false;
          setSelectOptions(specializationSelect, opts, 'Select specialization');

          var pre = selectedFrom(specializationSelect, 'specialization');
          if (pre) {
            specializationSelect.value = pre;
          }

          setDisabled(doctorSelect, true, 'Select specialization first');
          setDisabled(slotSelect, true, 'Select date to see slots');
          updateQuickBookEnabled();

          if (specializationSelect.value) {
            loadDoctors();
          }
        })
        .catch(function () {
          specializationSelect.disabled = false;
          setSelectOptions(specializationSelect, [], 'Select specialization');
        });
    }

    function loadDoctors() {
      if (!hospitalSelect || !doctorSelect) return;
      var hid = hospitalSelect.value;
      var sid = specializationSelect ? specializationSelect.value : '';
      if (!hid || !sid) {
        setDisabled(doctorSelect, true, 'Select specialization first');
        setDisabled(slotSelect, true, 'Select date to see slots');
        updateQuickBookEnabled();
        return;
      }

      doctorSelect.disabled = true;
      setSelectOptions(doctorSelect, [], 'Loading…');

      var url = api.doctors + '?hospital=' + encodeURIComponent(hid) + '&specialization=' + encodeURIComponent(sid);
      var searchEl = form.querySelector('input[name=q]');
      if (searchEl && searchEl.value) url += '&q=' + encodeURIComponent(searchEl.value);

      fetch(url, { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var items = (data && data.items) ? data.items : [];
          var opts = items.map(function (d) {
            var label = (d.name || 'Doctor') + (d.specialization ? (' — ' + d.specialization) : '');
            return { value: d.doctor_id, label: label };
          });
          doctorSelect.disabled = false;
          setSelectOptions(doctorSelect, opts, 'Select doctor');

          var pre = selectedFrom(doctorSelect, 'doctor');
          if (pre) {
            doctorSelect.value = pre;
          }

          setDisabled(slotSelect, true, 'Select date to see slots');
          updateQuickBookEnabled();

          if (doctorSelect.value && dateInput && dateInput.value) {
            loadSlots();
          }
        })
        .catch(function () {
          doctorSelect.disabled = false;
          setSelectOptions(doctorSelect, [], 'Select doctor');
        });
    }

    function loadSlots() {
      if (!doctorSelect || !dateInput || !slotSelect) return;
      var did = doctorSelect.value;
      var date = dateInput.value;
      if (!did || !date) {
        setDisabled(slotSelect, true, 'Select date to see slots');
        updateQuickBookEnabled();
        return;
      }
      if (!validateDate()) {
        setDisabled(slotSelect, true, 'Select a valid date');
        updateQuickBookEnabled();
        return;
      }

      slotSelect.disabled = true;
      setSelectOptions(slotSelect, [], 'Loading…');
      var url = api.availableSlots + '?doctor=' + encodeURIComponent(did) + '&date=' + encodeURIComponent(date);
      fetch(url, { credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var items = (data && data.items) ? data.items : [];
          var opts = items.map(function (t) {
            return { value: t, label: t };
          });
          slotSelect.disabled = false;
          if (!opts.length) {
            setSelectOptions(slotSelect, [], 'No slots available');
            slotSelect.disabled = true;
          } else {
            setSelectOptions(slotSelect, opts, 'Select time slot');
            var pre = selectedFrom(slotSelect, 'time');
            if (pre) {
              slotSelect.value = pre;
            }
          }
          updateQuickBookEnabled();
        })
        .catch(function () {
          slotSelect.disabled = false;
          setSelectOptions(slotSelect, [], 'Select time slot');
          updateQuickBookEnabled();
        });
    }

    function initSlotCarousel(root) {
      var carousel = document.getElementById('hsSlotCarousel');
      if (!carousel) return;

      var prevBtn = document.getElementById('hsSlotPrev');
      var nextBtn = document.getElementById('hsSlotNext');

      // Keep a pointer to the latest carousel element.
      window.__hsSlotCarouselEl = carousel;

      function itemWidth() {
        var active = window.__hsSlotCarouselEl || carousel;
        var item = active.querySelector('.hs-carousel-item');
        if (!item) return 320;
        var styles = window.getComputedStyle(item);
        var marginRight = parseFloat(styles.marginRight || '0') || 0;
        return item.getBoundingClientRect().width + marginRight + 16;
      }

      function scrollByItems(direction) {
        var active = window.__hsSlotCarouselEl || carousel;
        var step = itemWidth();
        active.scrollBy({ left: direction * step, behavior: 'smooth' });
      }

      if (!window.__hsSlotControlsBound) {
        window.__hsSlotControlsBound = true;

        if (prevBtn) {
          prevBtn.addEventListener('click', function () {
            scrollByItems(-1);
          });
        }

        if (nextBtn) {
          nextBtn.addEventListener('click', function () {
            scrollByItems(1);
          });
        }
      }

      var paused = false;
      carousel.addEventListener('mouseenter', function () { paused = true; });
      carousel.addEventListener('mouseleave', function () { paused = false; });

      if (window.__hsSlotCarouselIntervalId) {
        window.clearInterval(window.__hsSlotCarouselIntervalId);
      }

      window.__hsSlotCarouselIntervalId = window.setInterval(function () {
        if (paused) return;
        var active = window.__hsSlotCarouselEl || carousel;
        if (active.scrollWidth <= active.clientWidth + 2) return;

        var nearEnd = active.scrollLeft + active.clientWidth >= active.scrollWidth - 12;
        if (nearEnd) {
          active.scrollTo({ left: 0, behavior: 'smooth' });
          return;
        }

        // Move one card at a time.
        scrollByItems(1);
      }, 2600);
    }

    function initServiceCarousel() {
      var carousel = document.getElementById('hsServiceCarousel');
      if (!carousel) return;

      window.__hsServiceCarouselEl = carousel;

      function itemWidth() {
        var active = window.__hsServiceCarouselEl || carousel;
        var item = active.querySelector('.hs-carousel-item');
        if (!item) return 320;
        return item.getBoundingClientRect().width + 16;
      }

      function scrollByItems(direction) {
        var active = window.__hsServiceCarouselEl || carousel;
        active.scrollBy({ left: direction * itemWidth(), behavior: 'smooth' });
      }

      var paused = false;
      carousel.addEventListener('mouseenter', function () { paused = true; });
      carousel.addEventListener('mouseleave', function () { paused = false; });

      if (window.__hsServiceCarouselIntervalId) {
        window.clearInterval(window.__hsServiceCarouselIntervalId);
      }

      window.__hsServiceCarouselIntervalId = window.setInterval(function () {
        if (paused) return;
        var active = window.__hsServiceCarouselEl || carousel;
        if (active.scrollWidth <= active.clientWidth + 2) return;

        var nearEnd = active.scrollLeft + active.clientWidth >= active.scrollWidth - 12;
        if (nearEnd) {
          active.scrollTo({ left: 0, behavior: 'smooth' });
          return;
        }

        scrollByItems(1);
      }, 2400);
    }

    // Prevent full-page reloads from the booking form.
    form.addEventListener('submit', function (e) {
      e.preventDefault();
    });

    if (hospitalSelect) {
      hospitalSelect.addEventListener('change', function () {
        loadSpecializations();
      });
    }
    if (specializationSelect) {
      specializationSelect.addEventListener('change', function () {
        loadDoctors();
      });
    }
    if (doctorSelect) {
      doctorSelect.addEventListener('change', function () {
        loadSlots();
        updateQuickBookEnabled();
      });
    }
    if (dateInput) {
      dateInput.addEventListener('change', function () {
        validateDate();
        loadSlots();
      });
      dateInput.addEventListener('input', function () {
        validateDate();
      });
    }
    if (slotSelect) {
      slotSelect.addEventListener('change', function () {
        updateQuickBookEnabled();
      });
    }
    if (quickBookBtn) {
      quickBookBtn.addEventListener('click', function () {
        if (!doctorSelect || !doctorSelect.value) return;
        if (!dateInput || !dateInput.value) return;
        if (!slotSelect || !slotSelect.value) return;
        if (!validateDate()) return;

        var bookingUrl = '/doctor/booking/' + encodeURIComponent(doctorSelect.value) + '/';
        var params = new URLSearchParams();
        if (hospitalSelect && hospitalSelect.value) params.set('hospital', hospitalSelect.value);
        params.set('date', dateInput.value);
        params.set('time', slotSelect.value);
        window.location.href = bookingUrl + '?' + params.toString();
      });
    }

    // Preload cascades if hospital is already selected.
    if (hospitalSelect && hospitalSelect.value) {
      loadSpecializations();
    }

    initHospitalsCarousel();
    initSlotCarousel();
    initServiceCarousel();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
