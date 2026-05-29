// PRAVAAH - Main JS

document.addEventListener('DOMContentLoaded', function () {

  // Sidebar Toggle
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarClose = document.getElementById('sidebarClose');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  function openSidebar() {
    if (sidebar) sidebar.classList.add('open');
    if (sidebarOverlay) sidebarOverlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  if (sidebarToggle) sidebarToggle.addEventListener('click', openSidebar);
  if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar);
  if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeSidebar);

  // Live Clock
  const timeEl = document.getElementById('navbarTime');
  if (timeEl) {
    function updateTime() {
      const now = new Date();
      timeEl.textContent = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    }
    updateTime();
    setInterval(updateTime, 1000);
  }

  // Auto-dismiss alerts
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 5000);
  });

  // Photo preview on upload
  const photoInput = document.getElementById('id_photo');
  if (photoInput) {
    photoInput.addEventListener('change', function () {
      const file = this.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
          let preview = document.getElementById('photoPreview');
          if (!preview) {
            preview = document.createElement('img');
            preview.id = 'photoPreview';
            preview.style.cssText = 'width:80px;height:80px;border-radius:50%;object-fit:cover;margin-top:8px;border:3px solid #4361ee;';
            photoInput.parentNode.insertBefore(preview, photoInput.nextSibling);
          }
          preview.src = e.target.result;
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Add active class to nav items
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.landing-nav .nav-link');
  navLinks.forEach(link => {
    if (link.getAttribute('href') && link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // Admission pages: documents and course summary
  const documentRowsContainer = document.getElementById('documentRows');
  const addDocumentButton = document.getElementById('addDocumentRow');
  if (documentRowsContainer) {
    const updateRowLabels = () => {
      const rows = Array.from(documentRowsContainer.querySelectorAll('[data-document-row]'));
      rows.forEach((row, index) => {
        const rowNumber = row.querySelector('.document-row-number');
        if (rowNumber) {
          rowNumber.textContent = `Document ${index + 1}`;
        }
      });

      rows.forEach((row) => {
        const removeButtons = row.querySelectorAll('.remove-document-row');
        removeButtons.forEach((button) => {
          button.disabled = rows.length === 1;
          button.onclick = () => {
            if (rows.length > 1) {
              row.remove();
              updateRowLabels();
            }
          };
        });
      });
    };

    const createDocumentRow = () => {
      const rows = Array.from(documentRowsContainer.querySelectorAll('[data-document-row]'));
      const templateRow = rows[rows.length - 1];
      if (!templateRow) {
        return;
      }

      const clone = templateRow.cloneNode(true);
      const nextIndex = rows.length + 1;
      clone.setAttribute('data-row-index', String(nextIndex));

      const typeField = clone.querySelector('select[name^="document_type_"]');
      const fileField = clone.querySelector('input[type="file"][name^="document_file_"]');
      const hint = clone.querySelector('.file-name-hint');

      if (typeField) {
        typeField.name = `document_type_${nextIndex}`;
        typeField.value = '';
      }
      if (fileField) {
        fileField.name = `document_file_${nextIndex}`;
        fileField.value = '';
      }
      if (hint) {
        hint.textContent = 'No file selected';
      }

      documentRowsContainer.appendChild(clone);
      updateRowLabels();
    };

    documentRowsContainer.addEventListener('change', (event) => {
      const target = event.target;
      if (target && target.matches('input[type="file"]')) {
        const hint = target.closest('[data-document-row]')?.querySelector('.file-name-hint');
        if (hint) {
          hint.textContent = target.files && target.files.length ? target.files[0].name : 'No file selected';
        }
      }
    });

    if (addDocumentButton) {
      addDocumentButton.addEventListener('click', createDocumentRow);
    }

    updateRowLabels();
  }

  const courseSelect = document.querySelector('#courseSelectionForm select[name="course"]');
  const courseDataElement = document.getElementById('course-catalog-data');
  if (courseSelect && courseDataElement) {
    let courseCatalog = {};
    try {
      courseCatalog = JSON.parse(courseDataElement.textContent || '{}');
    } catch (error) {
      courseCatalog = {};
    }

    const setCourseSummary = (courseKey) => {
      const summary = courseCatalog[courseKey] || null;
      const titleEl = document.getElementById('courseSummaryTitle');
      const durationBadge = document.getElementById('courseSummaryDuration');
      const feesEls = [document.getElementById('courseSummaryFees'), document.getElementById('courseSummaryFeesCard')];
      const durationEls = [document.getElementById('courseSummaryDurationText'), document.getElementById('courseSummaryDurationCard')];
      const descriptionEl = document.getElementById('courseSummaryDescription');
      const highlightTargets = [document.getElementById('courseSummaryHighlights'), document.getElementById('courseSummaryHighlightsCard')];

      if (!summary) {
        if (titleEl) titleEl.textContent = 'Choose a course';
        if (durationBadge) durationBadge.textContent = 'Duration';
        feesEls.forEach((element) => { if (element) element.textContent = 'Select a course'; });
        durationEls.forEach((element) => { if (element) element.textContent = '---'; });
        if (descriptionEl) descriptionEl.textContent = 'Course details will appear here once you choose a program.';
        highlightTargets.forEach((element) => { if (element) element.innerHTML = ''; });
        return;
      }

      if (titleEl) titleEl.textContent = courseKey;
      if (durationBadge) durationBadge.textContent = summary.duration || 'Duration';
      feesEls.forEach((element) => { if (element) element.textContent = summary.fees || 'To be announced'; });
      durationEls.forEach((element) => { if (element) element.textContent = summary.duration || '---'; });
      if (descriptionEl) descriptionEl.textContent = summary.description || '';
      highlightTargets.forEach((element) => {
        if (!element) return;
        element.innerHTML = '';
        (summary.highlights || []).forEach((item) => {
          const badge = document.createElement('span');
          badge.className = 'course-summary-pill';
          badge.textContent = item;
          element.appendChild(badge);
        });
      });
    };

    courseSelect.addEventListener('change', () => setCourseSummary(courseSelect.value));
    setCourseSummary(courseSelect.value);
  }

});