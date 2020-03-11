#pragma once
#include <list>
#include <sstream>
#include <string>
#include <unordered_map>

#include "tristats/data.h"

namespace elo {

struct Contestant {
  Contestant() = default;
  Contestant(std::string profile, std::string division, int race_number, int rating, int finish,
             int group_size, double rank, double seed, int delta)
      : profile{std::move(profile)},
        division{std::move(division)},
        race_number{race_number},
        rating{rating},
        finish{finish},
        group_size{group_size},
        rank{rank},
        seed{seed},
        delta{delta} {}

  std::string profile;
  std::string division;
  int race_number;
  int rating;
  int finish;
  int group_size;
  double rank;
  double seed;
  int delta;
};

inline std::ostream& operator<<(std::ostream& os, const Contestant& contestant) {
  return os << "{"
            << " profile: " << contestant.profile << " race_number: " << contestant.race_number
            << " rating: " << contestant.rating << " finish: " << contestant.finish
            << " group_size: " << contestant.group_size << " rank: " << contestant.rank
            << " seed: " << contestant.seed << " delta: " << contestant.delta << " }";
}

struct RatingChange {
  RatingChange(tristats::RaceInfo race_info, Contestant contestant)
      : race_info{std::move(race_info)}, contestant{std::move(contestant)} {}

  tristats::RaceInfo race_info;
  Contestant contestant;
};

struct UserHistory {
  int rating;
  tristats::Athlete athlete;
  std::vector<RatingChange> rating_changes;  // TODO: rename to races
};

class RaceProcessor {
 public:
  RaceProcessor() = default;
  RaceProcessor(const std::vector<UserHistory>& user_histories);

  void Process(const tristats::Race& race);

  std::vector<UserHistory> GetUserHistories() {
    return std::vector<UserHistory>{user_histories_.begin(), user_histories_.end()};
  }

 private:
  std::unordered_map<std::string, Contestant> CalculateRatingChanges(const tristats::Race& race);

  int GetCurrentRating(const std::string& profile);
  int GetCompetitionCount(const std::string& profile);

  // int GetRatingToRank(const std::vector<Contestant>& contestants, const Contestant& contestant,
  //                     double rank);
  // double GetSeed(const std::vector<Contestant>& contestants, const Contestant& contestant,
  //                int rating);
  // void ValidateDeltas(const std::vector<Contestant>& contestants);

  std::string last_processed_date_;
  std::list<UserHistory> user_histories_;
  std::unordered_map<std::string, std::list<UserHistory>::iterator> profile_to_it_;
};

}  // namespace elo
