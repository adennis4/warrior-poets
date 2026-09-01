/**
 * @jest-environment jsdom
 */

/**
 * Regression tests for SortableTable's rank-tier bar (js/tables.js).
 *
 * js/nav.js and js/tables.js are plain browser-global scripts (they attach
 * WP/SortableTable/createTable onto `window`, not module.exports), so we
 * load them with `require` purely for their side effects: jest-environment-jsdom
 * exposes `window`/`document` as real globals that these files can see and
 * assign onto directly, the same way they would from a <script> tag.
 */
require('../js/nav.js');
require('../js/tables.js');

describe('SortableTable rank-tier bar', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="container"></div>';
  });

  function buildTestTable() {
    const data = [
      { name: 'A', total: 100 },
      { name: 'B', total: 90 },
      { name: 'C', total: 80 },
      { name: 'D', total: 70 }
    ];
    return window.createTable('container', {
      tableId: 'testTable',
      defaultSort: 'total',
      defaultOrder: 'desc',
      showRankTier: true,
      columns: [
        { key: 'rank', label: 'Rank', type: 'dynamicRank', sortable: false },
        { key: 'name', label: 'Name', type: 'member' },
        { key: 'total', label: 'Total', type: 'number' }
      ],
      data
    });
  }

  test('assigns top tier to the top half on initial (descending) render', () => {
    buildTestTable();
    const rows = document.querySelectorAll('#testTable tbody tr');
    expect(rows[0].className).toContain('rank-tier-top');
    expect(rows[1].className).toContain('rank-tier-top');
    expect(rows[2].className).toContain('rank-tier-bottom');
    expect(rows[3].className).toContain('rank-tier-bottom');
  });

  test('keeps tier bars correct after toggling the same column to ascending', () => {
    buildTestTable();
    // First click on the already-default-sorted "total" column toggles desc -> asc.
    document.querySelector('#testTable th[data-sort="total"]').click();

    const rows = document.querySelectorAll('#testTable tbody tr');
    const names = Array.from(rows).map(r => r.querySelector('.member-name').textContent.trim());

    // Ascending: D(70) < C(80) < B(90) < A(100), so DOM order is D, C, B, A.
    expect(names).toEqual(['D', 'C', 'B', 'A']);

    const aIndex = names.indexOf('A');
    const dIndex = names.indexOf('D');

    // A is the best (rank 1 - highest total) and must stay top-tier even
    // though it is now LAST in DOM order under ascending sort; D is the
    // worst (rank 4) and must stay bottom-tier even though it is now FIRST
    // in DOM order. A buggy implementation that tiers by raw array index
    // instead of the order-aware rank would invert this.
    expect(rows[aIndex].className).toContain('rank-tier-top');
    expect(rows[aIndex].className).not.toContain('rank-tier-bottom');
    expect(rows[dIndex].className).toContain('rank-tier-bottom');
    expect(rows[dIndex].className).not.toContain('rank-tier-top');
  });

  test('rank number and tier bar agree after toggling to ascending', () => {
    buildTestTable();
    document.querySelector('#testTable th[data-sort="total"]').click();

    const rows = document.querySelectorAll('#testTable tbody tr');
    Array.from(rows).forEach(row => {
      const rankCell = row.querySelector('td.dynamic-rank');
      const rank = parseInt(rankCell.textContent.trim(), 10);
      const isTopTier = row.className.includes('rank-tier-top');
      const isBottomTier = row.className.includes('rank-tier-bottom');
      // With 4 rows and getRankTier's top/bottom-half split, rank 1-2 should
      // be top tier and rank 3-4 should be bottom tier, regardless of DOM
      // position - the displayed rank number and the tier bar must never
      // disagree about who is actually winning.
      if (rank <= 2) {
        expect(isTopTier).toBe(true);
        expect(isBottomTier).toBe(false);
      } else {
        expect(isBottomTier).toBe(true);
        expect(isTopTier).toBe(false);
      }
    });
  });
});

describe('SortableTable rank-movement arrow', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="container"></div>';
  });

  function buildTableWithMovement() {
    const data = [
      { name: 'A', total: 100, movement: 'up' },
      { name: 'B', total: 90, movement: 'down' },
      { name: 'C', total: 80, movement: 'same' },
      { name: 'D', total: 70, movement: null }
    ];
    return window.createTable('container', {
      tableId: 'movementTable',
      defaultSort: 'total',
      defaultOrder: 'desc',
      columns: [
        { key: 'rank', label: 'Rank', type: 'dynamicRank', sortable: false, movementKey: 'movement' },
        { key: 'name', label: 'Name', type: 'member' },
        { key: 'total', label: 'Total', type: 'number' }
      ],
      data
    });
  }

  function movementFor(name) {
    const rows = Array.from(document.querySelectorAll('#movementTable tbody tr'));
    const row = rows.find(r => r.querySelector('.member-name').textContent.trim() === name);
    const arrow = row.querySelector('td.dynamic-rank .rank-arrow');
    return arrow ? [...arrow.classList].find(c => c.startsWith('rank-arrow-') && c !== 'rank-arrow') : null;
  }

  test('movement arrow survives the initial default-sort render', () => {
    buildTableWithMovement();
    // init() calls sortBy() immediately for the default sort - this is exactly
    // where the arrow used to get clobbered by a bare rankCell.textContent write.
    expect(movementFor('A')).toBe('rank-arrow-up');
    expect(movementFor('B')).toBe('rank-arrow-down');
    expect(movementFor('C')).toBe('rank-arrow-same');
    expect(movementFor('D')).toBe(null);
  });

  test('movement arrow survives a user-triggered sort', () => {
    buildTableWithMovement();
    document.querySelector('#movementTable th[data-sort="name"]').click();
    expect(movementFor('A')).toBe('rank-arrow-up');
    expect(movementFor('B')).toBe('rank-arrow-down');
    expect(movementFor('C')).toBe('rank-arrow-same');
  });

  test('movement arrows stay attached to the correct member across repeated re-sorts', () => {
    // This is the exact condition that exposed the stale-rowObj bug: sortBy()
    // re-runs storeOriginalData() at its own end, which used to zip DOM rows
    // to rowData by positional index - correct for the first sort, wrong for
    // every sort after that once row order had already changed once.
    buildTableWithMovement();
    document.querySelector('#movementTable th[data-sort="name"]').click(); // 1st sort
    document.querySelector('#movementTable th[data-sort="total"]').click(); // 2nd sort
    document.querySelector('#movementTable th[data-sort="name"]').click(); // 3rd sort
    document.querySelector('#movementTable th[data-sort="total"]').click(); // 4th sort

    expect(movementFor('A')).toBe('rank-arrow-up');
    expect(movementFor('B')).toBe('rank-arrow-down');
    expect(movementFor('C')).toBe('rank-arrow-same');
    expect(movementFor('D')).toBe(null);
  });
});

describe('SortableTable rank-tier bar with a string showRankTier field', () => {
  beforeEach(() => {
    document.body.innerHTML = '<div id="container"></div>';
  });

  function buildStaticRankTable() {
    // Mirrors how index.html's real Points Standings table is configured:
    // showRankTier reads a static field ('pointsRank'), not the post-sort
    // array position, since its rank column uses type 'rank', not 'dynamicRank'.
    const data = [
      { name: 'A', pointsRank: 1, points: 40 },
      { name: 'B', pointsRank: 2, points: 55 },
      { name: 'C', pointsRank: 3, points: 30 },
      { name: 'D', pointsRank: 4, points: 62 }
    ];
    return window.createTable('container', {
      tableId: 'staticRankTable',
      defaultSort: 'pointsRank',
      defaultOrder: 'asc',
      showRankTier: 'pointsRank',
      columns: [
        { key: 'pointsRank', label: 'Rank', type: 'rank' },
        { key: 'name', label: 'Name', type: 'member' },
        { key: 'points', label: 'Points', type: 'number' }
      ],
      data
    });
  }

  test('tier reflects the static field, not DOM position, even after sorting by an unrelated column', () => {
    buildStaticRankTable();
    // Sort by points (unrelated to pointsRank) so DOM order no longer matches pointsRank order.
    document.querySelector('#staticRankTable th[data-sort="points"]').click();

    const rows = Array.from(document.querySelectorAll('#staticRankTable tbody tr'));
    const byName = name => rows.find(r => r.querySelector('.member-name').textContent.trim() === name);

    // pointsRank 1-2 (A, B) must stay top-tier; 3-4 (C, D) must stay bottom-tier,
    // regardless of where "points"-sort now places them in the DOM.
    expect(byName('A').className).toContain('rank-tier-top');
    expect(byName('B').className).toContain('rank-tier-top');
    expect(byName('C').className).toContain('rank-tier-bottom');
    expect(byName('D').className).toContain('rank-tier-bottom');
  });
});
