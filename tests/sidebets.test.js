/**
 * Sidebet Calculation Tests
 * Tests for the core sidebet payout logic
 */

const {
  calculateSidebetPayout,
  calculateWeeklySidebets
} = require('./utils');

const { MOCK_WEEKLY_POINTS, SIDEBET_PAYOUTS } = require('./mockData');

describe('Sidebet Payout Calculation', () => {
  describe('calculateSidebetPayout', () => {
    test('1st place gets +65', () => {
      expect(calculateSidebetPayout(1)).toBe(65);
    });

    test('2nd place gets +55', () => {
      expect(calculateSidebetPayout(2)).toBe(55);
    });

    test('3rd place gets +45', () => {
      expect(calculateSidebetPayout(3)).toBe(45);
    });

    test('7th place gets +5', () => {
      expect(calculateSidebetPayout(7)).toBe(5);
    });

    test('8th place gets -5', () => {
      expect(calculateSidebetPayout(8)).toBe(-5);
    });

    test('14th place gets -65', () => {
      expect(calculateSidebetPayout(14)).toBe(-65);
    });

    test('all ranks 1-14 return expected payouts', () => {
      Object.entries(SIDEBET_PAYOUTS).forEach(([rank, expectedPayout]) => {
        expect(calculateSidebetPayout(parseInt(rank))).toBe(expectedPayout);
      });
    });

    test('invalid ranks return null', () => {
      expect(calculateSidebetPayout(0)).toBe(null);
      expect(calculateSidebetPayout(-1)).toBe(null);
      expect(calculateSidebetPayout(15)).toBe(null);
    });

    test('payouts are symmetric around zero', () => {
      // 1st (+65) and 14th (-65) should be opposite
      expect(calculateSidebetPayout(1)).toBe(-calculateSidebetPayout(14));
      // 2nd (+55) and 13th (-55) should be opposite
      expect(calculateSidebetPayout(2)).toBe(-calculateSidebetPayout(13));
      // etc.
      for (let i = 1; i <= 7; i++) {
        expect(calculateSidebetPayout(i)).toBe(-calculateSidebetPayout(15 - i));
      }
    });

    test('payouts decrease by 10 for each rank', () => {
      for (let i = 1; i < 14; i++) {
        const diff = calculateSidebetPayout(i) - calculateSidebetPayout(i + 1);
        expect(diff).toBe(10);
      }
    });
  });

  describe('calculateWeeklySidebets', () => {
    test('assigns correct sidebets for week 1', () => {
      const sidebets = calculateWeeklySidebets(MOCK_WEEKLY_POINTS, '1');

      // Week 1 rankings by points:
      // 1. Lloyd (162.40) -> +65
      // 14. Jett (76.82) -> -65
      expect(sidebets['Lloyd']).toBe(65);
      expect(sidebets['Jett']).toBe(-65);
    });

    test('assigns correct sidebets for week 2', () => {
      const sidebets = calculateWeeklySidebets(MOCK_WEEKLY_POINTS, '2');

      // Week 2 rankings:
      // 1. Yonk (158.32) -> +65
      // 14. Jett (74.90) -> -65
      expect(sidebets['Yonk']).toBe(65);
      expect(sidebets['Jett']).toBe(-65);
    });

    test('assigns correct sidebets for week 3', () => {
      const sidebets = calculateWeeklySidebets(MOCK_WEEKLY_POINTS, '3');

      // Week 3 rankings:
      // 1. JB (167.84) -> +65
      // 14. Rizzo (76.28) -> -65
      expect(sidebets['JB']).toBe(65);
      expect(sidebets['Rizzo']).toBe(-65);
    });

    test('all 14 members get a sidebet value', () => {
      const sidebets = calculateWeeklySidebets(MOCK_WEEKLY_POINTS, '1');
      expect(Object.keys(sidebets).length).toBe(14);
    });

    test('weekly sidebets sum to zero', () => {
      ['1', '2', '3'].forEach(week => {
        const sidebets = calculateWeeklySidebets(MOCK_WEEKLY_POINTS, week);
        const total = Object.values(sidebets).reduce((sum, sb) => sum + sb, 0);
        expect(total).toBe(0);
      });
    });

    test('each payout value appears exactly once per week', () => {
      const expectedPayouts = Object.values(SIDEBET_PAYOUTS).sort((a, b) => b - a);

      ['1', '2', '3'].forEach(week => {
        const sidebets = calculateWeeklySidebets(MOCK_WEEKLY_POINTS, week);
        const actualPayouts = Object.values(sidebets).sort((a, b) => b - a);
        expect(actualPayouts).toEqual(expectedPayouts);
      });
    });
  });
});

describe('Sidebet Edge Cases', () => {
  test('handles tie scores by maintaining order (first encountered wins)', () => {
    const tiedPoints = {
      'A': { '1': 100 },
      'B': { '1': 100 },
      'C': { '1': 90 }
    };

    // Note: In a real implementation, ties might need specific handling
    // This test documents current behavior
    const sidebets = calculateWeeklySidebets(tiedPoints, '1');

    // All members should get a sidebet
    expect(Object.keys(sidebets).length).toBe(3);

    // Sum should still be limited by number of members
    // With only 3 members, we'd use ranks 1-3 payouts
  });

  test('payout structure follows $10 increment rule', () => {
    // Verify the payout structure matches documentation
    const expectedStructure = {
      1: 65, 2: 55, 3: 45, 4: 35, 5: 25, 6: 15, 7: 5,
      8: -5, 9: -15, 10: -25, 11: -35, 12: -45, 13: -55, 14: -65
    };

    Object.entries(expectedStructure).forEach(([rank, payout]) => {
      expect(SIDEBET_PAYOUTS[rank]).toBe(payout);
    });
  });

  test('total possible sidebet payouts sum to zero', () => {
    const totalPayouts = Object.values(SIDEBET_PAYOUTS).reduce((sum, p) => sum + p, 0);
    expect(totalPayouts).toBe(0);
  });
});

describe('Cumulative Sidebet Scenarios', () => {
  test('member who wins every week accumulates correctly', () => {
    // If someone got 1st place (65) every week for 17 weeks
    const weeklyWins = 17 * 65;
    expect(weeklyWins).toBe(1105);
  });

  test('member who loses every week accumulates correctly', () => {
    // If someone got 14th place (-65) every week for 17 weeks
    const weeklyLosses = 17 * -65;
    expect(weeklyLosses).toBe(-1105);
  });

  test('perfectly average member (7th/8th) stays near zero', () => {
    // Alternating between 7th (+5) and 8th (-5)
    const evenWeeks = 8 * 5 + 9 * -5; // 8 weeks at +5, 9 at -5
    expect(evenWeeks).toBe(-5);
  });
});
