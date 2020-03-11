/*
 * Copyright by Mike Mirzayanov
 */
package com.codeforces.module.rating.service.rating.impl;

import com.codeforces.module.contest.party.Party;
import com.codeforces.module.contest.service.model.StandingsRow;
import com.codeforces.module.rating.model.RatingChange;
import com.codeforces.module.rating.service.rating.RatingCalculator;

import java.util.*;

/**
 * @author Mike Mirzayanov (mirzayanovmr@gmail.com)
 */
public class CodeforcesRatingCalculator2 implements RatingCalculator {
    private static final int INITIAL_RATING = 1500;

    @Override
    public int aggregateRating(List<RatingChange> ratingChanges) {
        int rating = INITIAL_RATING;

        if (ratingChanges != null) {
            for (RatingChange ratingChange : ratingChanges) {
                rating += ratingChange.getChange();
            }
        }

        return rating;
    }

    @Override
    public int getMaxRating(List<RatingChange> ratingChanges) {
        int maxRating = 0;

        if (ratingChanges != null) {
            int rating = INITIAL_RATING;
            for (RatingChange ratingChange : ratingChanges) {
                rating += ratingChange.getChange();
                maxRating = Math.max(rating, maxRating);
            }
        }

        return maxRating;
    }

    @Override
    public Map<Party, Integer> calculateRatingChanges(Map<Party, Integer> previousRatings,
                                                      List<StandingsRow> standingsRows, Set<Party> newcomers) {
        List<Contestant> contestants = new ArrayList<>(standingsRows.size());

        for (StandingsRow standingsRow : standingsRows) {
            int rank = standingsRow.getRank();
            Party party = standingsRow.getParty();
            contestants.add(new Contestant(party, rank, standingsRow.getPoints(), previousRatings.get(party)));
        }

        process(contestants);

        Map<Party, Integer> ratingChanges = new HashMap<>();
        for (Contestant contestant : contestants) {
            ratingChanges.put(contestant.party, contestant.delta);
        }

        return ratingChanges;
    }

    private static double getEloWinProbability(double ra, double rb) {
        return 1.0 / (1 + Math.pow(10, (rb - ra) / 400.0));
    }

    /**
     * @param a Participant a
     * @param b Participant b
     * @return Probability a wins b
     */
    private double getEloWinProbability(Contestant a, Contestant b) {
        return getEloWinProbability(a.rating, b.rating);
    }

    public int composeRatingsByTeamMemberRatings(int[] ratings) {
        double left = 100;
        double right = 4000;

        for (int tt = 0; tt < 20; tt++) {
            double r = (left + right) / 2.0;

            double rWinsProbability = 1.0;
            for (int rating : ratings) {
                rWinsProbability *= getEloWinProbability(r, rating);
            }

            double rating = Math.log10(1 / (rWinsProbability) - 1) * 400 + r;

            if (rating > r) {
                left = r;
            } else {
                right = r;
            }
        }

        return (int) Math.round((left + right) / 2);
    }

    private double getSeed(List<Contestant> contestants, int rating) {
        Contestant extraContestant = new Contestant(null, 0, 0, rating);

        double result = 1;
        for (Contestant other : contestants) {
            result += getEloWinProbability(other, extraContestant);
        }

        return result;
    }

    private int getRatingToRank(List<Contestant> contestants, double rank) {
        int left = 1;
        int right = 8000;

        while (right - left > 1) {
            int mid = (left + right) / 2;

            if (getSeed(contestants, mid) < rank) {
                right = mid;
            } else {
                left = mid;
            }
        }

        return left;
    }

    private void reassignRanks(List<Contestant> contestants) {
        sortByPointsDesc(contestants);

        for (Contestant contestant : contestants) {
            contestant.rank = 0;
            contestant.delta = 0;
        }

        int first = 0;
        double points = contestants.get(0).points;
        for (int i = 1; i < contestants.size(); i++) {
            if (contestants.get(i).points < points) {
                for (int j = first; j < i; j++) {
                    contestants.get(j).rank = i;
                }
                first = i;
                points = contestants.get(i).points;
            }
        }

        {
            double rank = contestants.size();
            for (int j = first; j < contestants.size(); j++) {
                contestants.get(j).rank = rank;
            }
        }
    }

    private void sortByPointsDesc(List<Contestant> contestants) {
        Collections.sort(contestants, new Comparator<Contestant>() {
            @Override
            public int compare(Contestant o1, Contestant o2) {
                return -Double.compare(o1.points, o2.points);
            }
        });
    }

    private void process(List<Contestant> contestants) {
        if (contestants.isEmpty()) {
            return;
        }

        reassignRanks(contestants);

        for (Contestant a : contestants) {
            a.seed = 1;
            for (Contestant b : contestants) {
                if (a != b) {
                    a.seed += getEloWinProbability(b, a);
                }
            }
        }

        for (Contestant contestant : contestants) {
            double midRank = Math.sqrt(contestant.rank * contestant.seed);
            contestant.needRating = getRatingToRank(contestants, midRank);
            contestant.delta = (contestant.needRating - contestant.rating) / 2;
        }

        sortByRatingDesc(contestants);

        // Total sum should not be more than zero.
        {
            int sum = 0;
            for (Contestant c : contestants) {
                sum += c.delta;
            }
            int inc = -sum / contestants.size() - 1;
            for (Contestant contestant : contestants) {
                contestant.delta += inc;
            }
        }

        // Sum of top-4*sqrt should be adjusted to zero.
        {
            int sum = 0;
            int zeroSumCount = Math.min((int) (4 * Math.round(Math.sqrt(contestants.size()))), contestants.size());
            for (int i = 0; i < zeroSumCount; i++) {
                sum += contestants.get(i).delta;
            }
            int inc = Math.min(Math.max(-sum / zeroSumCount, -10), 0);
            for (Contestant contestant : contestants) {
                contestant.delta += inc;
            }
        }

        validateDeltas(contestants);
    }

    private void validateDeltas(List<Contestant> contestants) {
        sortByPointsDesc(contestants);

        for (int i = 0; i < contestants.size(); i++) {
            for (int j = i + 1; j < contestants.size(); j++) {
                if (contestants.get(i).rating > contestants.get(j).rating) {
                    ensure(contestants.get(i).rating + contestants.get(i).delta >= contestants.get(j).rating + contestants.get(j).delta,
                            "First rating invariant failed: " + contestants.get(i).party + " vs. " + contestants.get(j).party + ".");
                }
                if (contestants.get(i).rating < contestants.get(j).rating) {
                    if (contestants.get(i).delta < contestants.get(j).delta) {
                        System.out.println(1);
                    }
                    ensure(contestants.get(i).delta >= contestants.get(j).delta,
                            "Second rating invariant failed: " + contestants.get(i).party + " vs. " + contestants.get(j).party + ".");
                }
            }
        }
    }

    private void ensure(boolean b, String message) {
        if (!b) {
            throw new RuntimeException(message);
        }
    }

    private void sortByRatingDesc(List<Contestant> contestants) {
        Collections.sort(contestants, new Comparator<Contestant>() {
            @Override
            public int compare(Contestant o1, Contestant o2) {
                return -Integer.compare(o1.rating, o2.rating);
            }
        });
    }

    private static final class Contestant {
        private Party party;
        private double rank;
        private double points;
        private int rating;
        private int needRating;
        private double seed;
        private int delta;

        private Contestant(Party party, int rank, double points, int rating) {
            this.party = party;
            this.rank = rank;
            this.points = points;
            this.rating = rating;
        }
    }
}