/**
 * Data Validation Tests
 * Tests to ensure data integrity in the league data structure
 */

const {
  MOCK_MEMBERS,
  MOCK_WEEKLY_POINTS,
  MOCK_WEEKLY_SIDEBETS,
  MOCK_STANDINGS,
  MOCK_SIDEBET_STANDINGS,
  SIDEBET_PAYOUTS
} = require('./mockData');

const {
  calculateTotalPoints,
  calculateTotalSidebets,
  calculateLowManCount
} = require('./utils');

describe('Data Structure Validation', () => {
  const activeMembers = MOCK_MEMBERS.active;
  const weeks = ['1', '2', '3'];

  describe('Member Data Completeness', () => {
    test('should have exactly 14 active members', () => {
      expect(activeMembers.length).toBe(14);
    });

    test('all active members should have weekly points data', () => {
      activeMembers.forEach(member => {
        expect(MOCK_WEEKLY_POINTS).toHaveProperty(member);
      });
    });

    test('all active members should have weekly sidebets data', () => {
      activeMembers.forEach(member => {
        expect(MOCK_WEEKLY_SIDEBETS).toHaveProperty(member);
      });
    });

    test('all active members should have standings data', () => {
      activeMembers.forEach(member => {
        expect(MOCK_STANDINGS).toHaveProperty(member);
        expect(MOCK_STANDINGS[member]).toHaveProperty('totalPoints');
        expect(MOCK_STANDINGS[member]).toHaveProperty('pointsRank');
      });
    });

    test('all active members should have sidebet standings data', () => {
      activeMembers.forEach(member => {
        expect(MOCK_SIDEBET_STANDINGS).toHaveProperty(member);
        expect(MOCK_SIDEBET_STANDINGS[member]).toHaveProperty('total');
        expect(MOCK_SIDEBET_STANDINGS[member]).toHaveProperty('rank');
        expect(MOCK_SIDEBET_STANDINGS[member]).toHaveProperty('lowManCount');
      });
    });
  });

  describe('Weekly Points Validation', () => {
    test('all members should have data for each week', () => {
      activeMembers.forEach(member => {
        weeks.forEach(week => {
          expect(MOCK_WEEKLY_POINTS[member]).toHaveProperty(week);
          expect(typeof MOCK_WEEKLY_POINTS[member][week]).toBe('number');
        });
      });
    });

    test('weekly points should be within realistic range (50-200)', () => {
      activeMembers.forEach(member => {
        weeks.forEach(week => {
          const points = MOCK_WEEKLY_POINTS[member][week];
          expect(points).toBeGreaterThanOrEqual(50);
          expect(points).toBeLessThanOrEqual(200);
        });
      });
    });
  });

  describe('Total Points Calculation', () => {
    test('standings totalPoints should equal sum of weekly points', () => {
      activeMembers.forEach(member => {
        const calculatedTotal = calculateTotalPoints(MOCK_WEEKLY_POINTS[member]);
        const storedTotal = MOCK_STANDINGS[member].totalPoints;
        expect(calculatedTotal).toBeCloseTo(storedTotal, 2);
      });
    });
  });

  describe('Points Rank Validation', () => {
    test('points ranks should be unique integers from 1-14', () => {
      const ranks = activeMembers.map(m => MOCK_STANDINGS[m].pointsRank);
      const uniqueRanks = [...new Set(ranks)].sort((a, b) => a - b);
      expect(uniqueRanks).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]);
    });

    test('higher total points should have better (lower) rank', () => {
      const sortedByPoints = [...activeMembers].sort(
        (a, b) => MOCK_STANDINGS[b].totalPoints - MOCK_STANDINGS[a].totalPoints
      );

      sortedByPoints.forEach((member, index) => {
        expect(MOCK_STANDINGS[member].pointsRank).toBe(index + 1);
      });
    });
  });
});

describe('Sidebet Data Validation', () => {
  const activeMembers = MOCK_MEMBERS.active;
  const weeks = ['1', '2', '3'];

  describe('Weekly Sidebets Zero-Sum', () => {
    test('each week sidebets should sum to zero', () => {
      weeks.forEach(week => {
        const weekTotal = activeMembers.reduce((sum, member) => {
          return sum + (MOCK_WEEKLY_SIDEBETS[member][week] || 0);
        }, 0);
        expect(weekTotal).toBe(0);
      });
    });
  });

  describe('Weekly Sidebet Values', () => {
    test('all weekly sidebets should be valid payout values', () => {
      const validPayouts = Object.values(SIDEBET_PAYOUTS);

      activeMembers.forEach(member => {
        weeks.forEach(week => {
          const sidebet = MOCK_WEEKLY_SIDEBETS[member][week];
          expect(validPayouts).toContain(sidebet);
        });
      });
    });

    test('each week should have exactly one +65 (high man) and one -65 (low man)', () => {
      weeks.forEach(week => {
        const highManCount = activeMembers.filter(
          m => MOCK_WEEKLY_SIDEBETS[m][week] === 65
        ).length;
        const lowManCount = activeMembers.filter(
          m => MOCK_WEEKLY_SIDEBETS[m][week] === -65
        ).length;

        expect(highManCount).toBe(1);
        expect(lowManCount).toBe(1);
      });
    });

    test('each payout value should appear exactly once per week', () => {
      const validPayouts = Object.values(SIDEBET_PAYOUTS);

      weeks.forEach(week => {
        validPayouts.forEach(payout => {
          const count = activeMembers.filter(
            m => MOCK_WEEKLY_SIDEBETS[m][week] === payout
          ).length;
          expect(count).toBe(1);
        });
      });
    });
  });

  describe('Total Sidebet Calculation', () => {
    test('sidebet standings total should equal sum of weekly sidebets', () => {
      activeMembers.forEach(member => {
        const calculatedTotal = calculateTotalSidebets(MOCK_WEEKLY_SIDEBETS[member]);
        const storedTotal = MOCK_SIDEBET_STANDINGS[member].total;
        expect(calculatedTotal).toBe(storedTotal);
      });
    });

    test('sum of all sidebet totals should be zero', () => {
      const totalSum = activeMembers.reduce((sum, member) => {
        return sum + MOCK_SIDEBET_STANDINGS[member].total;
      }, 0);
      expect(totalSum).toBe(0);
    });
  });

  describe('Low Man Count Validation', () => {
    test('lowManCount should match number of -65 weeks', () => {
      activeMembers.forEach(member => {
        const calculatedCount = calculateLowManCount(MOCK_WEEKLY_SIDEBETS[member]);
        const storedCount = MOCK_SIDEBET_STANDINGS[member].lowManCount;
        expect(calculatedCount).toBe(storedCount);
      });
    });

    test('total lowManCount across all members should equal number of weeks', () => {
      const totalLowMan = activeMembers.reduce((sum, member) => {
        return sum + MOCK_SIDEBET_STANDINGS[member].lowManCount;
      }, 0);
      expect(totalLowMan).toBe(weeks.length);
    });
  });

  describe('Sidebet Rank Validation', () => {
    test('sidebet ranks should be integers from 1-14', () => {
      activeMembers.forEach(member => {
        const rank = MOCK_SIDEBET_STANDINGS[member].rank;
        expect(rank).toBeGreaterThanOrEqual(1);
        expect(rank).toBeLessThanOrEqual(14);
      });
    });
  });
});
