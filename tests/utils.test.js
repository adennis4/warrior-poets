/**
 * Utility Function Tests
 * Tests for formatting and helper functions
 */

const {
  formatNumber,
  formatDelta,
  getValueClass,
  isInactive,
  formatRank,
  calculateTotalPoints,
  calculateTotalSidebets,
  calculateLowManCount
} = require('./utils');

describe('formatNumber', () => {
  test('formats positive numbers with default 2 decimals', () => {
    expect(formatNumber(123.456)).toBe('123.46');
    expect(formatNumber(1000)).toBe('1,000.00');
    expect(formatNumber(0)).toBe('0.00');
  });

  test('formats numbers with specified decimals', () => {
    expect(formatNumber(123.456, 1)).toBe('123.5');
    expect(formatNumber(123.456, 0)).toBe('123');
    expect(formatNumber(123.456, 3)).toBe('123.456');
  });

  test('adds commas for thousands', () => {
    expect(formatNumber(1234567.89, 2)).toBe('1,234,567.89');
  });

  test('returns dash for null/undefined', () => {
    expect(formatNumber(null)).toBe('—');
    expect(formatNumber(undefined)).toBe('—');
  });

  test('returns dash for n/a values', () => {
    expect(formatNumber('n/a')).toBe('—');
    expect(formatNumber('n/a ')).toBe('—');
  });
});

describe('formatDelta', () => {
  test('formats positive numbers with + prefix', () => {
    expect(formatDelta(65, 0)).toBe('+65');
    expect(formatDelta(25.5, 1)).toBe('+25.5');
  });

  test('formats negative numbers with - prefix', () => {
    expect(formatDelta(-65, 0)).toBe('-65');
    expect(formatDelta(-25.5, 1)).toBe('-25.5');
  });

  test('formats zero without prefix', () => {
    expect(formatDelta(0, 0)).toBe('0');
  });

  test('returns dash for null/undefined', () => {
    expect(formatDelta(null)).toBe('—');
    expect(formatDelta(undefined)).toBe('—');
  });

  test('uses default 0 decimals', () => {
    expect(formatDelta(65)).toBe('+65');
    expect(formatDelta(-65)).toBe('-65');
  });
});

describe('getValueClass', () => {
  test('returns "positive" for positive numbers', () => {
    expect(getValueClass(65)).toBe('positive');
    expect(getValueClass(0.1)).toBe('positive');
  });

  test('returns "negative" for negative numbers', () => {
    expect(getValueClass(-65)).toBe('negative');
    expect(getValueClass(-0.1)).toBe('negative');
  });

  test('returns empty string for zero', () => {
    expect(getValueClass(0)).toBe('');
  });

  test('returns empty string for null/undefined', () => {
    expect(getValueClass(null)).toBe('');
    expect(getValueClass(undefined)).toBe('');
  });
});

describe('isInactive', () => {
  test('returns true for inactive members', () => {
    expect(isInactive('Heath')).toBe(true);
    expect(isInactive('Jerome')).toBe(true);
    expect(isInactive('Woock')).toBe(true);
    expect(isInactive('Marty')).toBe(true);
  });

  test('returns false for active members', () => {
    expect(isInactive('Lloyd')).toBe(false);
    expect(isInactive('JB')).toBe(false);
    expect(isInactive('Andrew')).toBe(false);
    expect(isInactive('Yonk')).toBe(false);
  });

  test('returns false for unknown names', () => {
    expect(isInactive('Unknown')).toBe(false);
    expect(isInactive('')).toBe(false);
  });
});

describe('formatRank', () => {
  test('formats ranks with correct ordinal suffixes', () => {
    expect(formatRank(1)).toBe('1st');
    expect(formatRank(2)).toBe('2nd');
    expect(formatRank(3)).toBe('3rd');
    expect(formatRank(4)).toBe('4th');
    expect(formatRank(5)).toBe('5th');
    expect(formatRank(10)).toBe('10th');
    expect(formatRank(11)).toBe('11th');
    expect(formatRank(12)).toBe('12th');
    expect(formatRank(13)).toBe('13th');
    expect(formatRank(14)).toBe('14th');
  });

  test('handles teen numbers correctly', () => {
    expect(formatRank(11)).toBe('11th');
    expect(formatRank(12)).toBe('12th');
    expect(formatRank(13)).toBe('13th');
  });

  test('handles larger numbers', () => {
    expect(formatRank(21)).toBe('21st');
    expect(formatRank(22)).toBe('22nd');
    expect(formatRank(23)).toBe('23rd');
    expect(formatRank(24)).toBe('24th');
  });

  test('returns dash for null/undefined', () => {
    expect(formatRank(null)).toBe('—');
    expect(formatRank(undefined)).toBe('—');
    expect(formatRank('-')).toBe('—');
  });

  test('handles string numbers', () => {
    expect(formatRank('1')).toBe('1st');
    expect(formatRank('14')).toBe('14th');
  });
});

describe('calculateTotalPoints', () => {
  test('sums all weekly points', () => {
    const weeklyPoints = { '1': 100.5, '2': 150.25, '3': 125.75 };
    expect(calculateTotalPoints(weeklyPoints)).toBeCloseTo(376.5, 2);
  });

  test('handles empty object', () => {
    expect(calculateTotalPoints({})).toBe(0);
  });

  test('handles null/undefined values', () => {
    const weeklyPoints = { '1': 100, '2': null, '3': undefined };
    expect(calculateTotalPoints(weeklyPoints)).toBe(100);
  });
});

describe('calculateTotalSidebets', () => {
  test('sums all weekly sidebets correctly', () => {
    const weeklySidebets = { '1': 65, '2': -25, '3': 15 };
    expect(calculateTotalSidebets(weeklySidebets)).toBe(55);
  });

  test('handles negative totals', () => {
    const weeklySidebets = { '1': -65, '2': -55, '3': 35 };
    expect(calculateTotalSidebets(weeklySidebets)).toBe(-85);
  });

  test('handles empty object', () => {
    expect(calculateTotalSidebets({})).toBe(0);
  });
});

describe('calculateLowManCount', () => {
  test('counts -65 occurrences correctly', () => {
    const weeklySidebets = { '1': -65, '2': -65, '3': 45 };
    expect(calculateLowManCount(weeklySidebets)).toBe(2);
  });

  test('returns 0 when no -65 values', () => {
    const weeklySidebets = { '1': 65, '2': 55, '3': 45 };
    expect(calculateLowManCount(weeklySidebets)).toBe(0);
  });

  test('handles empty object', () => {
    expect(calculateLowManCount({})).toBe(0);
  });
});
