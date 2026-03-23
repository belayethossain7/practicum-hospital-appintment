/* ============================================================
   Lab Dashboard — JavaScript
   Handles: sidebar toggle, test detail modal, upload modal
   ============================================================ */

// ------------ SIDEBAR TOGGLE (mobile) ------------
function toggleSidebar() {
    var sidebar = document.getElementById('labSidebar');
    var overlay = document.getElementById('sidebarOverlay');
    if (sidebar) {
        sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('show');
    }
}

// ------------ TEST DETAIL MODAL ------------
function openTestDetail(testId) {
    var modalEl = document.getElementById('testDetailModal');
    var body = document.getElementById('testDetailBody');

    // Show spinner while loading
    body.innerHTML = '<div class="text-center p-5"><div class="spinner-border text-primary" role="status"></div></div>';

    // Reuse existing Bootstrap Modal instance, or create one if first call
    var modal = bootstrap.Modal.getInstance(modalEl);
    if (!modal) {
        modal = new bootstrap.Modal(modalEl);
    }
    modal.show();

    fetch('/lab/test-detail/' + testId + '/')
        .then(function (res) { return res.json(); })
        .then(function (d) {
            var html = '';

            // Patient & Doctor info
            html += '<div class="lab-detail-section">';
            html += '  <div class="lab-detail-section-title">Patient & Doctor</div>';
            html += '  <div class="lab-detail-grid">';
            html += '    <div class="lab-detail-item">';
            html += '      <span class="lab-detail-label">Patient</span>';
            html += '      <div class="lab-detail-patient">';
            if (d.patient_image) {
                html += '        <img src="' + escHtml(d.patient_image) + '" alt="">';
            } else {
                html += '        <div class="lab-detail-patient-placeholder"><i class="fas fa-user"></i></div>';
            }
            html += '        <div><strong>' + escHtml(d.patient_name) + '</strong>';
            if (d.patient_phone) html += '<br><small class="text-muted">' + escHtml(d.patient_phone) + '</small>';
            html += '        </div>';
            html += '      </div>';
            html += '    </div>';
            html += '    <div class="lab-detail-item">';
            html += '      <span class="lab-detail-label">Doctor</span>';
            html += '      <div class="lab-detail-patient">';
            if (d.doctor_image) {
                html += '        <img src="' + escHtml(d.doctor_image) + '" alt="">';
            } else {
                html += '        <div class="lab-detail-patient-placeholder"><i class="fas fa-user-md"></i></div>';
            }
            html += '        <div><strong>' + escHtml(d.doctor_name) + '</strong>';
            if (d.doctor_department) html += '<br><small class="text-muted">' + escHtml(d.doctor_department) + '</small>';
            html += '        </div>';
            html += '      </div>';
            html += '    </div>';
            html += '  </div>';
            html += '</div>';

            // Prescription info
            html += '<div class="lab-detail-section">';
            html += '  <div class="lab-detail-section-title">Prescription</div>';
            html += '  <div class="lab-detail-grid">';
            html += '    <div class="lab-detail-item"><span class="lab-detail-label">ID</span><span class="lab-detail-value">#' + escHtml(String(d.prescription_id)) + '</span></div>';
            html += '    <div class="lab-detail-item"><span class="lab-detail-label">Date</span><span class="lab-detail-value">' + escHtml(d.prescription_date || '—') + '</span></div>';
            html += '  </div>';
            if (d.extra_info) {
                html += '  <div class="mt-2"><small class="text-muted">' + escHtml(d.extra_info) + '</small></div>';
            }
            html += '</div>';

            // Current test
            html += '<div class="lab-detail-section">';
            html += '  <div class="lab-detail-section-title">Current Test</div>';
            html += '  <div class="lab-detail-grid">';
            html += '    <div class="lab-detail-item"><span class="lab-detail-label">Name</span><span class="lab-detail-value">' + escHtml(d.test_name) + '</span></div>';
            html += '    <div class="lab-detail-item"><span class="lab-detail-label">Price</span><span class="lab-detail-value">৳' + escHtml(d.test_price) + '</span></div>';
            html += '    <div class="lab-detail-item"><span class="lab-detail-label">Status</span><span class="lab-detail-value">' + statusBadge(d.test_status) + '</span></div>';
            html += '    <div class="lab-detail-item"><span class="lab-detail-label">Payment</span><span class="lab-detail-value">' + escHtml(d.pay_status || '—') + '</span></div>';
            if (d.completed_date) {
                html += '    <div class="lab-detail-item"><span class="lab-detail-label">Completed</span><span class="lab-detail-value">' + escHtml(d.completed_date) + '</span></div>';
            }
            html += '  </div>';

            // Report
            if (d.report_file_url || d.report_text) {
                html += '  <div class="mt-3">';
                if (d.report_file_url) {
                    html += '    <a href="' + escHtml(d.report_file_url) + '" target="_blank" class="lab-report-link"><i class="fas fa-file-pdf"></i> View Report File</a><br>';
                }
                if (d.report_text) {
                    html += '    <div class="mt-2 p-3" style="background:#f8fafc;border-radius:10px;font-size:14px;white-space:pre-wrap;">' + escHtml(d.report_text) + '</div>';
                }
                html += '  </div>';
            }
            html += '</div>';

            // All tests in prescription
            if (d.all_tests && d.all_tests.length > 0) {
                html += '<div class="lab-detail-section">';
                html += '  <div class="lab-detail-section-title">All Tests in Prescription</div>';
                html += '  <table class="lab-detail-test-table">';
                html += '    <thead><tr><th>Test</th><th>Price</th><th>Payment</th><th>Status</th><th>Report</th></tr></thead>';
                html += '    <tbody>';
                d.all_tests.forEach(function (t) {
                    html += '    <tr>';
                    html += '      <td>' + escHtml(t.test_name) + '</td>';
                    html += '      <td>৳' + escHtml(t.test_price) + '</td>';
                    html += '      <td>' + escHtml(t.pay_status || '—') + '</td>';
                    html += '      <td>' + statusBadge(t.test_status) + '</td>';
                    html += '      <td>' + (t.has_report ? '<i class="fas fa-check-circle text-success"></i>' : '<i class="fas fa-minus-circle text-muted"></i>') + '</td>';
                    html += '    </tr>';
                });
                html += '    </tbody></table>';
                html += '</div>';
            }

            // Medicines
            if (d.medicines && d.medicines.length > 0) {
                html += '<div class="lab-detail-section">';
                html += '  <div class="lab-detail-section-title">Prescribed Medicines</div>';
                html += '  <table class="lab-detail-test-table">';
                html += '    <thead><tr><th>Medicine</th><th>Qty</th><th>Duration</th><th>Frequency</th><th>Instruction</th></tr></thead>';
                html += '    <tbody>';
                d.medicines.forEach(function (m) {
                    html += '    <tr>';
                    html += '      <td>' + escHtml(m.name) + '</td>';
                    html += '      <td>' + escHtml(m.quantity) + '</td>';
                    html += '      <td>' + escHtml(m.duration) + '</td>';
                    html += '      <td>' + escHtml(m.frequency) + '</td>';
                    html += '      <td>' + escHtml(m.instruction || '—') + '</td>';
                    html += '    </tr>';
                });
                html += '    </tbody></table>';
                html += '</div>';
            }

            body.innerHTML = html;
        })
        .catch(function () {
            body.innerHTML = '<div class="text-center text-danger p-4"><i class="fas fa-exclamation-triangle fa-2x mb-2"></i><br>Failed to load test details.</div>';
        });
}

// ------------ PER-ROW UPLOAD (direct file input) ------------
// Each table row has its own <form> with a hidden <input type="file">.
// Upload button calls input.click() → file picker opens directly.
// On file selection → validate → auto-submit the per-row form.
document.addEventListener('DOMContentLoaded', function () {
    var ALLOWED_EXT = ['pdf', 'png', 'jpg', 'jpeg', 'docx', 'doc', 'txt'];
    var MAX_SIZE_MB = 15;

    document.querySelectorAll('.lab-upload-file-input').forEach(function (input) {
        input.addEventListener('change', function () {
            if (!this.files || this.files.length === 0) return;

            var file = this.files[0];
            var ext = file.name.split('.').pop().toLowerCase();

            if (ALLOWED_EXT.indexOf(ext) === -1) {
                alert('Invalid file type ".' + ext + '".\nAllowed: PDF, PNG, JPG, JPEG, DOCX, DOC, TXT');
                this.value = '';
                return;
            }
            if (file.size > MAX_SIZE_MB * 1024 * 1024) {
                alert('File too large (' + (file.size / 1024 / 1024).toFixed(1) + ' MB).\nMaximum allowed: ' + MAX_SIZE_MB + ' MB');
                this.value = '';
                return;
            }

            // Disable the Upload button and show spinner
            var form = this.closest('form');
            var btn = form ? form.querySelector('button[type="button"]') : null;
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Uploading…';
            }

            // Auto-submit the per-row form
            if (form) form.submit();
        });
    });
});

// ------------ HELPERS ------------
function escHtml(str) {
    if (!str) return '';
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function statusBadge(status) {
    if (status === 'Pending') return '<span class="badge lab-badge-pending">Pending</span>';
    if (status === 'Processing') return '<span class="badge lab-badge-processing">Processing</span>';
    if (status === 'Completed') return '<span class="badge lab-badge-completed">Completed</span>';
    return '<span class="badge bg-secondary">' + escHtml(status) + '</span>';
}
