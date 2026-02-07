// Sortable table functionality for Warrior Poets Fantasy Football

class SortableTable {
  constructor(tableId, options = {}) {
    this.table = document.getElementById(tableId);
    if (!this.table) return;

    this.options = {
      defaultSort: options.defaultSort || null,
      defaultOrder: options.defaultOrder || 'desc',
      ...options
    };

    this.currentSort = this.options.defaultSort;
    this.currentOrder = this.options.defaultOrder;
    this.originalData = [];

    this.init();
  }

  init() {
    // Store original row data
    const tbody = this.table.querySelector('tbody');
    if (!tbody) return;

    this.tbody = tbody;
    this.storeOriginalData();

    // Add click handlers to headers
    const headers = this.table.querySelectorAll('th[data-sort]');
    headers.forEach(header => {
      header.classList.add('sortable');
      header.addEventListener('click', () => this.sortBy(header.dataset.sort));
    });

    // Apply default sort if specified
    if (this.currentSort) {
      this.sortBy(this.currentSort, true);
    }
  }

  storeOriginalData() {
    const rows = this.tbody.querySelectorAll('tr');
    this.originalData = Array.from(rows).map(row => {
      const cells = row.querySelectorAll('td');
      const data = {};

      cells.forEach((cell, index) => {
        const header = this.table.querySelector(`th:nth-child(${index + 1})`);
        if (header && header.dataset.sort) {
          // Get numeric value if specified
          if (cell.dataset.value !== undefined) {
            data[header.dataset.sort] = parseFloat(cell.dataset.value) || 0;
          } else {
            const text = cell.textContent.trim();
            // Try to parse as number
            const num = parseFloat(text.replace(/[^0-9.-]/g, ''));
            data[header.dataset.sort] = isNaN(num) ? text : num;
          }
        }
      });

      return { element: row, data };
    });
  }

  sortBy(column, isInitial = false) {
    // Determine sort order
    if (!isInitial && this.currentSort === column) {
      this.currentOrder = this.currentOrder === 'asc' ? 'desc' : 'asc';
    } else if (!isInitial) {
      this.currentOrder = 'desc'; // Default to descending for new column
    }

    this.currentSort = column;

    // Update header classes
    const headers = this.table.querySelectorAll('th');
    headers.forEach(h => {
      h.classList.remove('sort-asc', 'sort-desc');
      if (h.dataset.sort === column) {
        h.classList.add(this.currentOrder === 'asc' ? 'sort-asc' : 'sort-desc');
      }
    });

    // Sort the data with stable sort (use name as tiebreaker)
    const sorted = [...this.originalData].sort((a, b) => {
      let valA = a.data[column];
      let valB = b.data[column];

      // Handle undefined/null
      if (valA === undefined || valA === null || valA === '—') valA = this.currentOrder === 'asc' ? Infinity : -Infinity;
      if (valB === undefined || valB === null || valB === '—') valB = this.currentOrder === 'asc' ? Infinity : -Infinity;

      // Compare
      let result;
      if (typeof valA === 'string' && typeof valB === 'string') {
        result = this.currentOrder === 'asc'
          ? valA.localeCompare(valB)
          : valB.localeCompare(valA);
      } else {
        result = this.currentOrder === 'asc' ? valA - valB : valB - valA;
      }

      // Use name as tiebreaker for stable sort
      if (result === 0 && a.data.name && b.data.name) {
        return a.data.name.localeCompare(b.data.name);
      }

      return result;
    });

    // Re-render rows
    this.tbody.innerHTML = '';
    const totalRows = sorted.length;
    sorted.forEach((item, index) => {
      this.tbody.appendChild(item.element);
      // Update dynamic rank cells - reverse if sorted ascending
      const rankCell = item.element.querySelector('td.dynamic-rank');
      if (rankCell) {
        const rank = this.currentOrder === 'desc' ? index + 1 : totalRows - index;
        rankCell.textContent = rank;
        rankCell.dataset.value = rank;
        // Update rank classes
        rankCell.classList.remove('rank-1', 'rank-2', 'rank-3');
        if (rank === 1) rankCell.classList.add('rank-1');
        if (rank === 2) rankCell.classList.add('rank-2');
        if (rank === 3) rankCell.classList.add('rank-3');
      }
    });

    // Re-store data with new row references
    this.storeOriginalData();
  }
}

// Create a table from data
function createTable(containerId, config) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const {
    columns,
    data,
    tableId,
    defaultSort,
    defaultOrder,
    onRowClick
  } = config;

  let html = `
    <div class="table-container">
      <table id="${tableId}">
        <thead>
          <tr>
            ${columns.map(col => `
              <th ${col.sortable !== false ? `data-sort="${col.key}"` : ''} ${col.align ? `style="text-align: ${col.align}"` : ''}>
                ${col.label}
              </th>
            `).join('')}
          </tr>
        </thead>
        <tbody>
          ${data.map((row, index) => `
            <tr ${onRowClick ? `onclick="${onRowClick}('${row.id || row.name || index}')"` : ''}>
              ${columns.map(col => {
                let value = row[col.key];
                let displayValue = value;
                let classes = [];
                let dataValue = '';

                // Format based on column type
                if (col.type === 'dynamicRank') {
                  classes.push('rank');
                  classes.push('numeric');
                  classes.push('dynamic-rank');
                  displayValue = index + 1;
                  dataValue = index + 1;
                  if (index === 0) classes.push('rank-1');
                  if (index === 1) classes.push('rank-2');
                  if (index === 2) classes.push('rank-3');
                } else if (col.type === 'rank') {
                  classes.push('rank');
                  classes.push('numeric');
                  if (value === null || value === undefined || value === 0) {
                    displayValue = '—';
                    dataValue = 999;
                  } else {
                    if (value === 1) classes.push('rank-1');
                    if (value === 2) classes.push('rank-2');
                    if (value === 3) classes.push('rank-3');
                    dataValue = value;
                  }
                } else if (col.type === 'number') {
                  classes.push('numeric');
                  displayValue = WP.formatNumber(value, col.decimals !== undefined ? col.decimals : 2);
                  dataValue = value || 0;
                } else if (col.type === 'delta') {
                  classes.push('numeric');
                  classes.push(WP.getValueClass(value));
                  displayValue = WP.formatDelta(value, col.decimals !== undefined ? col.decimals : 0);
                  dataValue = value || 0;
                } else if (col.type === 'member') {
                  classes.push('member-name');
                  if (WP.isInactive(value)) classes.push('inactive');
                }

                if (col.align) {
                  classes.push(`text-${col.align}`);
                }

                return `<td class="${classes.join(' ')}" ${dataValue !== '' ? `data-value="${dataValue}"` : ''}>${displayValue}</td>`;
              }).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;

  container.innerHTML = html;

  // Initialize sorting
  return new SortableTable(tableId, { defaultSort, defaultOrder });
}

// Export
window.SortableTable = SortableTable;
window.createTable = createTable;
