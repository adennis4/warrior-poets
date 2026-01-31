// Utility functions for testing (CommonJS version of nav.js functions)

/**
 * Format number with commas and decimals
 */
function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined || num === 'n/a ' || num === 'n/a') {
    return '—';
  }
  return Number(num).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

/**
 * Format number with +/- sign
 */
function formatDelta(num, decimals = 0) {
  if (num === null || num === undefined || num === 'n/a ' || num === 'n/a') {
    return '—';
  }
  const formatted = formatNumber(Math.abs(num), decimals);
  if (num > 0) return `+${formatted}`;
  if (num < 0) return `-${formatted}`;
  return formatted;
}

/**
 * Get CSS class for positive/negative values
 */
function getValueClass(num) {
  if (num === null || num === undefined) return '';
  if (num > 0) return 'positive';
  if (num < 0) return 'negative';
  return '';
}

/**
 * Check if member is inactive
 */
function isInactive(memberName) {
  const inactive = ['Heath', 'Jerome', 'Woock', 'Marty'];
  return inactive.includes(memberName);
}

/**
 * Format rank with ordinal suffix (1st, 2nd, 3rd, etc.)
 */
function formatRank(rank) {
  if (rank === null || rank === undefined || rank === '-') return '—';
  const num = parseInt(rank);
  if (isNaN(num)) return '—';
  const suffixes = ['th', 'st', 'nd', 'rd'];
  const v = num % 100;
  return num + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
}

/**
 * Calculate sidebet payout based on rank (1-14)
 * 1st = +65, 2nd = +55, ... 7th = +5, 8th = -5, ... 14th = -65
 * Formula: 75 - (rank * 10)
 */
function calculateSidebetPayout(rank) {
  if (rank < 1 || rank > 14) return null;
  return 75 - (rank * 10);
}

/**
 * Rank members by their weekly points and return sidebet payouts
 */
function calculateWeeklySidebets(weeklyPoints, week) {
  const members = Object.keys(weeklyPoints);

  // Get scores for this week and sort descending
  const scores = members
    .map(name => ({ name, points: weeklyPoints[name][week] || 0 }))
    .sort((a, b) => b.points - a.points);

  // Assign sidebets based on rank
  const sidebets = {};
  scores.forEach((member, index) => {
    const rank = index + 1;
    sidebets[member.name] = calculateSidebetPayout(rank);
  });

  return sidebets;
}

/**
 * Calculate total points for a member across all weeks
 */
function calculateTotalPoints(memberWeeklyPoints) {
  return Object.values(memberWeeklyPoints).reduce((sum, pts) => sum + (pts || 0), 0);
}

/**
 * Calculate total sidebets for a member across all weeks
 */
function calculateTotalSidebets(memberWeeklySidebets) {
  return Object.values(memberWeeklySidebets).reduce((sum, sb) => sum + (sb || 0), 0);
}

/**
 * Count how many times a member finished last (got -65)
 */
function calculateLowManCount(memberWeeklySidebets) {
  return Object.values(memberWeeklySidebets).filter(sb => sb === -65).length;
}

module.exports = {
  formatNumber,
  formatDelta,
  getValueClass,
  isInactive,
  formatRank,
  calculateSidebetPayout,
  calculateWeeklySidebets,
  calculateTotalPoints,
  calculateTotalSidebets,
  calculateLowManCount
};
