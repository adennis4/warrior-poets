// Navigation functionality for Warrior Poets Fantasy Football

// Icons as SVG strings
const icons = {
  star: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`,
  home: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>`,
  trophy: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"></path><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"></path><path d="M4 22h16"></path><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"></path><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"></path><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"></path></svg>`,
  chart: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>`,
  calendar: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`,
  users: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>`,
  chevron: `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>`,
  menu: `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>`,
  wager: `<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"></path><path d="M12 18V6"></path></svg>`
};

// Generate sidebar HTML
function generateSidebar(currentPage = '') {
  const years = [];
  for (let y = 2025; y >= 2009; y--) {
    years.push(y);
  }

  const activeMembers = ['Andrew', 'Ben', 'CP', 'Dues', 'Farber', 'JB', 'Jett', 'Lloyd', 'Pinkston', 'Rich', 'Rick', 'Rizzo', 'Stern', 'Yonk'];
  const inactiveMembers = ['Heath', 'Jerome', 'Marty', 'Woock'];

  // Determine if current page is an active or inactive member
  const currentMember = currentPage.startsWith('members/') ? currentPage.replace('members/', '') : null;
  const isActiveMember = currentMember && activeMembers.some(m => m.toLowerCase() === currentMember);
  const isInactiveMember = currentMember && inactiveMembers.some(m => m.toLowerCase() === currentMember);

  // Determine base path based on current page location
  const pathDepth = (currentPage.match(/\//g) || []).length;
  const basePath = pathDepth > 0 ? '../'.repeat(pathDepth) : './';

  return `
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-header">
        <a href="${basePath}index.html" class="sidebar-logo">
          <img src="${basePath}images/logo-64.png" alt="Warrior Poets" class="sidebar-logo-img">
          <span>Warrior Poets</span>
        </a>
      </div>
      <nav class="sidebar-nav">
        <div class="nav-section">
          <a href="${basePath}index.html" class="nav-link ${currentPage === 'index' ? 'active' : ''}">
            ${icons.star}
            Current Season
          </a>
          <a href="${basePath}all-time.html" class="nav-link ${currentPage === 'all-time' ? 'active' : ''}">
            ${icons.chart}
            All-Time Stats
          </a>
          <a href="${basePath}hall-of-fame.html" class="nav-link ${currentPage === 'hall-of-fame' ? 'active' : ''}">
            ${icons.trophy}
            Hall of Fame
          </a>
          <a href="${basePath}wagers.html" class="nav-link ${currentPage === 'wagers' ? 'active' : ''}">
            ${icons.wager}
            Wagers
          </a>
        </div>

        <div class="nav-section">
          <div class="nav-section-title nav-section-toggle" onclick="toggleNavSection(this)">
            <span>Past Seasons</span>
            <svg class="nav-toggle-icon${currentPage.startsWith('years/') ? ' rotated' : ''}" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </div>
          <div class="nav-section-content${currentPage.startsWith('years/') ? '' : ' collapsed'}">
            <div class="nav-year-grid">
              ${years.map(year => `
                <a href="${basePath}years/${year}.html" class="nav-year-link ${currentPage === `years/${year}` ? 'active' : ''}">${year}</a>
              `).join('')}
            </div>
          </div>
        </div>

        <div class="nav-section">
          <div class="nav-section-title nav-section-toggle" onclick="toggleNavSection(this)">
            <span>Active Members</span>
            <svg class="nav-toggle-icon${isActiveMember ? ' rotated' : ''}" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </div>
          <div class="nav-section-content${isActiveMember ? '' : ' collapsed'}">
            <div class="nav-member-grid">
              ${activeMembers.map(member => `
                <a href="${basePath}members/${member.toLowerCase()}.html" class="nav-member-link ${currentPage === `members/${member.toLowerCase()}` ? 'active' : ''}">${member}</a>
              `).join('')}
            </div>
          </div>
        </div>

        <div class="nav-section">
          <div class="nav-section-title nav-section-toggle" onclick="toggleNavSection(this)">
            <span>Past Members</span>
            <svg class="nav-toggle-icon${isInactiveMember ? ' rotated' : ''}" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </div>
          <div class="nav-section-content${isInactiveMember ? '' : ' collapsed'}">
            <div class="nav-member-grid">
              ${inactiveMembers.map(member => `
                <a href="${basePath}members/${member.toLowerCase()}.html" class="nav-member-link inactive ${currentPage === `members/${member.toLowerCase()}` ? 'active' : ''}">${member}</a>
              `).join('')}
            </div>
          </div>
        </div>
      </nav>
    </aside>
    <div class="sidebar-overlay" id="sidebarOverlay"></div>
    <button class="mobile-menu-btn" id="mobileMenuBtn">
      ${icons.menu}
    </button>
  `;
}

// Generate footer HTML
function generateFooter() {
  const now = new Date();
  const timestamp = now.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });

  return `
    <footer class="footer">
      Last updated: ${timestamp}
    </footer>
  `;
}

// Toggle collapsible nav sections
function toggleNavSection(element) {
  const content = element.nextElementSibling;
  const icon = element.querySelector('.nav-toggle-icon');
  content.classList.toggle('collapsed');
  icon.classList.toggle('rotated');
}

// Make toggleNavSection available globally
window.toggleNavSection = toggleNavSection;

// Initialize mobile menu functionality
function initMobileMenu() {
  const menuBtn = document.getElementById('mobileMenuBtn');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (menuBtn && sidebar && overlay) {
    menuBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('active');
    });

    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('active');
    });
  }
}

// Format number with commas and decimals
function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined || num === 'n/a ' || num === 'n/a') {
    return '—';
  }
  return Number(num).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

// Format number with +/- sign
function formatDelta(num, decimals = 0) {
  if (num === null || num === undefined || num === 'n/a ' || num === 'n/a') {
    return '—';
  }
  const formatted = formatNumber(Math.abs(num), decimals);
  if (num > 0) return `+${formatted}`;
  if (num < 0) return `-${formatted}`;
  return formatted;
}

// Get CSS class for positive/negative values
function getValueClass(num) {
  if (num === null || num === undefined) return '';
  if (num > 0) return 'positive';
  if (num < 0) return 'negative';
  return '';
}

// Check if member is inactive
function isInactive(memberName) {
  const inactive = ['Heath', 'Jerome', 'Woock', 'Marty'];
  return inactive.includes(memberName);
}

// Format rank with ordinal suffix (1st, 2nd, 3rd, etc.)
function formatRank(rank) {
  if (rank === null || rank === undefined || rank === '-') return '—';
  const num = parseInt(rank);
  if (isNaN(num)) return '—';
  const suffixes = ['th', 'st', 'nd', 'rd'];
  const v = num % 100;
  return num + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
}

// Trophy SVG for inline use
function getTrophySvg(count = 1) {
  return `<span class="trophy" title="${count} Championship${count > 1 ? 's' : ''}">${icons.trophy}${count > 1 ? `<span class="trophy-count">x${count}</span>` : ''}</span>`;
}

// Initialize page
function initPage(pageName) {
  // Insert sidebar
  const sidebarContainer = document.createElement('div');
  sidebarContainer.innerHTML = generateSidebar(pageName);
  document.body.insertBefore(sidebarContainer.firstElementChild, document.body.firstChild);

  // Insert overlay and menu button
  const overlay = sidebarContainer.querySelector('.sidebar-overlay');
  const menuBtn = sidebarContainer.querySelector('.mobile-menu-btn');
  if (overlay) document.body.appendChild(overlay);
  if (menuBtn) document.body.appendChild(menuBtn);

  // Insert footer
  const mainContent = document.querySelector('.main-content');
  if (mainContent) {
    mainContent.insertAdjacentHTML('beforeend', generateFooter());
  }

  // Initialize mobile menu
  initMobileMenu();
}

/**
 * Return which half of a ranked table a rank falls in ('top' or 'bottom'),
 * or null if the rank/total isn't valid. The top half is rounded up on odd
 * totals (e.g. rank 3 of 5 is "top").
 */
function getRankTier(rank, totalRows) {
  if (!rank || !totalRows) return null;
  return rank <= Math.ceil(totalRows / 2) ? 'top' : 'bottom';
}

/**
 * Render an inline rank-movement indicator for a 'up' | 'down' | 'same' | null
 * movement value. Returns an empty string when there's nothing to show.
 */
function formatRankMovement(movement) {
  if (movement === 'up') return ' <span class="rank-arrow rank-arrow-up">▲</span>';
  if (movement === 'down') return ' <span class="rank-arrow rank-arrow-down">▼</span>';
  if (movement === 'same') return ' <span class="rank-arrow rank-arrow-same">—</span>';
  return '';
}

/**
 * Rank every member by their cumulative total through a given week.
 * Returns { memberName: rank } where rank 1 is the highest cumulative total.
 */
function calculateCumulativeRanks(weeklyValues, throughWeek) {
  const totals = Object.keys(weeklyValues).map(name => {
    let sum = 0;
    for (let w = 1; w <= throughWeek; w++) {
      sum += weeklyValues[name][String(w)] || 0;
    }
    return { name, total: sum };
  });
  totals.sort((a, b) => b.total - a.total);
  const ranks = {};
  totals.forEach((entry, index) => {
    ranks[entry.name] = index + 1;
  });
  return ranks;
}

/**
 * Compute each member's rank movement ('up' | 'down' | 'same') between the
 * previous week and currentWeek, based on cumulative totals. Returns null
 * for every member when currentWeek is 1 or less (no prior week to compare).
 */
function computeRankMovement(weeklyValues, currentWeek) {
  const names = Object.keys(weeklyValues);
  if (!currentWeek || currentWeek < 2) {
    const none = {};
    names.forEach(name => { none[name] = null; });
    return none;
  }

  const currentRanks = calculateCumulativeRanks(weeklyValues, currentWeek);
  const previousRanks = calculateCumulativeRanks(weeklyValues, currentWeek - 1);

  const movement = {};
  names.forEach(name => {
    const cur = currentRanks[name];
    const prev = previousRanks[name];
    if (cur < prev) movement[name] = 'up';
    else if (cur > prev) movement[name] = 'down';
    else movement[name] = 'same';
  });
  return movement;
}

// Export functions for use in other modules
window.WP = {
  initPage,
  formatNumber,
  formatDelta,
  formatRank,
  getValueClass,
  isInactive,
  getTrophySvg,
  icons,
  getRankTier,
  formatRankMovement,
  calculateCumulativeRanks,
  computeRankMovement
};
