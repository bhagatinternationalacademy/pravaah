/* =============================================================
   PRAVAAH ERP – Shared Services Dashboard
   File: dashboard/static/dashboard/js/dashboard.js
   Purpose:
   - Sidebar interactions
   - Dashboard search/filter
   - Login animations
   - Role handling
   - Notifications
   - Responsive behaviour
   ============================================================= */


/* =============================================================
   GLOBAL HELPERS
   ============================================================= */

/**
 * Safely get element by ID
 */
function getEl(id) {
    return document.getElementById(id);
}


/* =============================================================
   SIDEBAR TOGGLE
   ============================================================= */

function toggleSidebar() {

    const sidebar = getEl('erpSidebar');
    const shell = getEl('erpShell');

    if (!sidebar || !shell) return;

    sidebar.classList.toggle('collapsed');
    shell.classList.toggle('sidebar-collapsed');
}


/* =============================================================
   MODULE CARD SEARCH/FILTER
   ============================================================= */

function filterCards(searchTerm) {

    const cards = document.querySelectorAll('.module-card');
    const emptyState = getEl('searchEmpty');

    let visibleCount = 0;

    searchTerm = searchTerm.toLowerCase().trim();

    cards.forEach(card => {

        const title = card.dataset.cardTitle || '';

        if (title.includes(searchTerm)) {

            card.style.display = 'flex';
            visibleCount++;

        } else {

            card.style.display = 'none';
        }
    });

    // Empty search state
    if (emptyState) {

        if (visibleCount === 0) {
            emptyState.classList.remove('d-none');
        } else {
            emptyState.classList.add('d-none');
        }
    }
}


/* =============================================================
   CURRENT DATE & TIME
   ============================================================= */

function updateCurrentDateTime() {

    const dateContainer = getEl('currentDateTime');

    if (!dateContainer) return;

    const now = new Date();

    const formatted = now.toLocaleString('en-IN', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    dateContainer.innerHTML = `
        <i class="fa-solid fa-calendar-days me-1"></i>
        ${formatted}
    `;
}


/* =============================================================
   AUTO-HIDE ALERT MESSAGES
   ============================================================= */

function autoHideAlerts() {

    const alerts = document.querySelectorAll('.pravaah-alert');

    alerts.forEach((alert, index) => {

        setTimeout(() => {

            alert.style.opacity = '0';
            alert.style.transform = 'translateX(40px)';

            setTimeout(() => {
                alert.remove();
            }, 300);

        }, 4000 + (index * 500));
    });
}


/* =============================================================
   CARD HOVER ANIMATION
   ============================================================= */

function initializeCardAnimations() {

    const cards = document.querySelectorAll('.module-card');

    cards.forEach(card => {

        card.addEventListener('mouseenter', () => {

            card.style.transform = 'translateY(-8px)';
        });

        card.addEventListener('mouseleave', () => {

            card.style.transform = 'translateY(0px)';
        });
    });
}


/* =============================================================
   LOGIN FORM ENHANCEMENTS
   ============================================================= */

function initializeLoginForm() {

    const loginForm = getEl('loginForm');

    if (!loginForm) return;

    loginForm.addEventListener('submit', function () {

        const loginBtn = getEl('loginBtn');

        if (!loginBtn) return;

        const btnText = loginBtn.querySelector('.btn-login-text');
        const btnSpinner = loginBtn.querySelector('.btn-login-spinner');

        if (btnText) btnText.classList.add('d-none');

        if (btnSpinner) btnSpinner.classList.remove('d-none');

        loginBtn.disabled = true;
    });
}


/* =============================================================
   ACTIVE SIDEBAR LINK
   ============================================================= */

function activateSidebarLinks() {

    const currentPath = window.location.pathname;

    const navLinks = document.querySelectorAll('.sidebar-nav-item');

    navLinks.forEach(item => {

        item.classList.remove('active');

        const link = item.querySelector('a');

        if (!link) return;

        const href = link.getAttribute('href');

        if (href === currentPath) {

            item.classList.add('active');
        }
    });
}


/* =============================================================
   RESPONSIVE SIDEBAR
   ============================================================= */

function handleResponsiveSidebar() {

    const sidebar = getEl('erpSidebar');
    const shell = getEl('erpShell');

    if (!sidebar || !shell) return;

    if (window.innerWidth < 992) {

        sidebar.classList.add('collapsed');
        shell.classList.add('sidebar-collapsed');

    } else {

        sidebar.classList.remove('collapsed');
        shell.classList.remove('sidebar-collapsed');
    }
}


/* =============================================================
   DASHBOARD STATS COUNT ANIMATION
   ============================================================= */

function animateStatCounters() {

    const statValues = document.querySelectorAll('.stat-card-value');

    statValues.forEach(stat => {

        const originalText = stat.innerText;

        // Extract numeric value
        const number = parseInt(originalText.replace(/[^0-9]/g, ''));

        if (isNaN(number)) return;

        let count = 0;

        const increment = Math.ceil(number / 50);

        const timer = setInterval(() => {

            count += increment;

            if (count >= number) {

                stat.innerText = originalText;
                clearInterval(timer);

            } else {

                stat.innerText = count;
            }

        }, 25);
    });
}


/* =============================================================
   MODULE CARD CLICK EFFECT
   ============================================================= */

function initializeModuleClicks() {

    const buttons = document.querySelectorAll('.btn-open-module');

    buttons.forEach(button => {

        button.addEventListener('click', function () {

            button.innerHTML = `
                <i class="fa-solid fa-spinner fa-spin me-2"></i>
                Opening...
            `;
        });
    });
}


/* =============================================================
   ROLE BADGE COLORS
   ============================================================= */

function initializeRoleBadge() {

    const badge = getEl('roleActiveBadge');

    if (!badge) return;

    const roleInput = getEl('roleInput');

    if (!roleInput) return;

    const role = roleInput.value;

    badge.classList.remove(
        'role-admin',
        'role-trainer',
        'role-student',
        'role-user'
    );

    badge.classList.add(`role-${role}`);
}


/* =============================================================
   ESC KEY CLOSE SIDEBAR (MOBILE)
   ============================================================= */

document.addEventListener('keydown', function (event) {

    if (event.key === 'Escape') {

        const sidebar = getEl('erpSidebar');
        const shell = getEl('erpShell');

        if (!sidebar || !shell) return;

        if (window.innerWidth < 992) {

            sidebar.classList.add('collapsed');
            shell.classList.add('sidebar-collapsed');
        }
    }
});


/* =============================================================
   WINDOW RESIZE
   ============================================================= */

window.addEventListener('resize', function () {

    handleResponsiveSidebar();
});


/* =============================================================
   INITIALIZE EVERYTHING
   ============================================================= */

document.addEventListener('DOMContentLoaded', function () {

    console.log('PRAVAAH ERP Dashboard Loaded Successfully');

    updateCurrentDateTime();

    setInterval(updateCurrentDateTime, 60000);

    autoHideAlerts();

    initializeCardAnimations();

    initializeLoginForm();

    activateSidebarLinks();

    handleResponsiveSidebar();

    animateStatCounters();

    initializeModuleClicks();

    initializeRoleBadge();
});


/* =============================================================
   OPTIONAL FUTURE FEATURES
   ============================================================= */

/*

Future enhancements you can add later:

1. Dark/Light Mode Toggle
2. Real-time notifications
3. API integration
4. Chart.js analytics
5. User profile dropdown logic
6. Role-based API permissions
7. WebSocket notifications
8. Loading skeletons
9. Dashboard customization
10. Session timeout warning

*/