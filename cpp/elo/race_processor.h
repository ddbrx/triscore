#pragma once
#include <list>
#include <sstream>
#include <string>
#include <unordered_map>

#include "tristats/data.h"

namespace elo {

struct Contestant {
  Contestant() = default;
  Contestant(std::string profile, std::string division, int rating, tristats::Timing timing,
             int group_size, double rank, double seed, int delta)
      : profile{std::move(profile)},
        division{std::move(division)},
        rating{rating},
        timing{std::move(timing)},
        group_size{group_size},
        rank{rank},
        seed{seed},
        delta{delta} {}

  std::string profile;
  std::string division;
  int rating;
  tristats::Timing timing;
  int group_size;
  double rank;
  double seed;
  int delta;
};

inline std::ostream& operator<<(std::ostream& os, const Contestant& contestant) {
  return os << "{"
            << " profile: " << contestant.profile << " rating: " << contestant.rating
            << " timing: " << contestant.timing << " group_size: " << contestant.group_size
            << " rank: " << contestant.rank << " seed: " << contestant.seed
            << " delta: " << contestant.delta << " }";
}

struct RatingChange {
  RatingChange(tristats::RaceInfo race_info, Contestant contestant)
      : race_info{std::move(race_info)}, contestant{std::move(contestant)} {}

  tristats::RaceInfo race_info;
  Contestant contestant;
};

struct AthleteHistory {
  int rating;
  tristats::Athlete athlete;
  std::vector<RatingChange> races;
};

class RaceProcessor {
 public:
  RaceProcessor() = default;
  RaceProcessor(const std::vector<AthleteHistory>& athlete_histories);

  void Process(const tristats::Race& race);

  std::vector<AthleteHistory> GetUserHistories() {
    return std::vector<AthleteHistory>{athlete_histories_.begin(), athlete_histories_.end()};
  }

 private:
  std::unordered_map<std::string, Contestant> CalculateRatingChanges(const tristats::Race& race);

  int GetCurrentRating(const std::string& profile);

  // int GetRatingToRank(const std::vector<Contestant>& contestants, const Contestant& contestant,
  //                     double rank);
  // double GetSeed(const std::vector<Contestant>& contestants, const Contestant& contestant,
  //                int rating);
  // void ValidateDeltas(const std::vector<Contestant>& contestants);

  std::string last_processed_date_;
  std::list<AthleteHistory> athlete_histories_;
  std::unordered_map<std::string, std::list<AthleteHistory>::iterator> profile_to_it_;
};

}  // namespace elo
