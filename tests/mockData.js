// Mock data for testing - matches the 2026 season mock data in data.js

const MOCK_MEMBERS = {
  active: ['CP', 'Yonk', 'Farber', 'Rick', 'JB', 'Rizzo', 'Ben', 'Dues', 'Rich', 'Stern', 'Andrew', 'Pinkston', 'Lloyd', 'Jett'],
  inactive: ['Heath', 'Jerome', 'Woock', 'Marty']
};

const MOCK_WEEKLY_POINTS = {
  "CP": {"1": 142.36, "2": 101.22, "3": 159.56},
  "Yonk": {"1": 98.72, "2": 158.32, "3": 117.62},
  "Farber": {"1": 156.84, "2": 82.36, "3": 138.74},
  "Rick": {"1": 121.50, "2": 119.82, "3": 103.88},
  "JB": {"1": 134.28, "2": 112.56, "3": 167.84},
  "Rizzo": {"1": 88.46, "2": 144.90, "3": 76.28},
  "Ben": {"1": 145.92, "2": 95.68, "3": 124.18},
  "Dues": {"1": 112.64, "2": 125.44, "3": 90.16},
  "Rich": {"1": 128.18, "2": 106.94, "3": 145.92},
  "Stern": {"1": 105.30, "2": 151.28, "3": 110.34},
  "Andrew": {"1": 118.76, "2": 132.18, "3": 97.42},
  "Pinkston": {"1": 91.54, "2": 138.64, "3": 83.54},
  "Lloyd": {"1": 162.40, "2": 89.14, "3": 131.46},
  "Jett": {"1": 76.82, "2": 74.90, "3": 152.28}
};

const MOCK_WEEKLY_SIDEBETS = {
  "CP": {"1": 35, "2": -25, "3": 55},
  "Yonk": {"1": -35, "2": 65, "3": -5},
  "Farber": {"1": 55, "2": -55, "3": 25},
  "Rick": {"1": 5, "2": 5, "3": -25},
  "JB": {"1": 25, "2": -5, "3": 65},
  "Rizzo": {"1": -55, "2": 45, "3": -65},
  "Ben": {"1": 45, "2": -35, "3": 5},
  "Dues": {"1": -15, "2": 15, "3": -45},
  "Rich": {"1": 15, "2": -15, "3": 35},
  "Stern": {"1": -25, "2": 55, "3": -15},
  "Andrew": {"1": -5, "2": 25, "3": -35},
  "Pinkston": {"1": -45, "2": 35, "3": -55},
  "Lloyd": {"1": 65, "2": -45, "3": 15},
  "Jett": {"1": -65, "2": -65, "3": 45}
};

const MOCK_STANDINGS = {
  "CP": { "totalPoints": 403.14, "pointsRank": 2, "yearEndStanding": null },
  "Yonk": { "totalPoints": 374.66, "pointsRank": 6, "yearEndStanding": null },
  "Farber": { "totalPoints": 377.94, "pointsRank": 5, "yearEndStanding": null },
  "Rick": { "totalPoints": 345.20, "pointsRank": 10, "yearEndStanding": null },
  "JB": { "totalPoints": 414.68, "pointsRank": 1, "yearEndStanding": null },
  "Rizzo": { "totalPoints": 309.64, "pointsRank": 13, "yearEndStanding": null },
  "Ben": { "totalPoints": 365.78, "pointsRank": 8, "yearEndStanding": null },
  "Dues": { "totalPoints": 328.24, "pointsRank": 11, "yearEndStanding": null },
  "Rich": { "totalPoints": 381.04, "pointsRank": 4, "yearEndStanding": null },
  "Stern": { "totalPoints": 366.92, "pointsRank": 7, "yearEndStanding": null },
  "Andrew": { "totalPoints": 348.36, "pointsRank": 9, "yearEndStanding": null },
  "Pinkston": { "totalPoints": 313.72, "pointsRank": 12, "yearEndStanding": null },
  "Lloyd": { "totalPoints": 383.00, "pointsRank": 3, "yearEndStanding": null },
  "Jett": { "totalPoints": 304.00, "pointsRank": 14, "yearEndStanding": null }
};

const MOCK_SIDEBET_STANDINGS = {
  "CP": { "total": 65, "rank": 2, "lowManCount": 0 },
  "Yonk": { "total": 25, "rank": 6, "lowManCount": 0 },
  "Farber": { "total": 25, "rank": 5, "lowManCount": 0 },
  "Rick": { "total": -15, "rank": 10, "lowManCount": 0 },
  "JB": { "total": 85, "rank": 1, "lowManCount": 0 },
  "Rizzo": { "total": -75, "rank": 13, "lowManCount": 1 },
  "Ben": { "total": 15, "rank": 7, "lowManCount": 0 },
  "Dues": { "total": -45, "rank": 11, "lowManCount": 0 },
  "Rich": { "total": 35, "rank": 3, "lowManCount": 0 },
  "Stern": { "total": 15, "rank": 8, "lowManCount": 0 },
  "Andrew": { "total": -15, "rank": 9, "lowManCount": 0 },
  "Pinkston": { "total": -65, "rank": 12, "lowManCount": 0 },
  "Lloyd": { "total": 35, "rank": 4, "lowManCount": 0 },
  "Jett": { "total": -85, "rank": 14, "lowManCount": 2 }
};

// Sidebet payout structure (rank -> payout)
const SIDEBET_PAYOUTS = {
  1: 65, 2: 55, 3: 45, 4: 35, 5: 25, 6: 15, 7: 5,
  8: -5, 9: -15, 10: -25, 11: -35, 12: -45, 13: -55, 14: -65
};

module.exports = {
  MOCK_MEMBERS,
  MOCK_WEEKLY_POINTS,
  MOCK_WEEKLY_SIDEBETS,
  MOCK_STANDINGS,
  MOCK_SIDEBET_STANDINGS,
  SIDEBET_PAYOUTS
};
