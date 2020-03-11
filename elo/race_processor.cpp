#include "elo/race_processor.h"

#include <algorithm>
#include <cassert>
#include <cstdint>
#include <iostream>

namespace elo {

namespace {

constexpr int kStartRating = 1500;

double GetEloWinProbability(int ra, int rb) { return 1.0 / (1 + pow(10., (rb - ra) / 400.)); }

template <typename T>
auto GetLastInsertedIt(std::list<T>& list) {
  auto it = list.end();
  return --it;
}

double GetRaceTypeMultiplier(tristats::RaceType race_type) {
  switch (race_type) {
    case tristats::RaceType::Supersprint:
      return 1.;
    case tristats::RaceType::Sprint:
      return 2.;
    case tristats::RaceType::Olympic:
      return 4.;
    case tristats::RaceType::Half:
      return 8;
    case tristats::RaceType::Full:
      return 16.;
  }
}

double GetContestantMultiplier(const Contestant& contestant) {
  // rating == 1500 -> 31
  // rating >= 3000 -> 1
  return std::max(1., 61. - contestant.rating / 50.);
}

}  // namespace

RaceProcessor::RaceProcessor(const std::vector<UserHistory>& user_histories) {
  for (const auto& user_history : user_histories) {
    user_histories_.push_back(user_history);
    profile_to_it_.emplace(user_history.athlete.profile, GetLastInsertedIt(user_histories_));
    auto& rating_changes = user_history.rating_changes;
    if (!rating_changes.empty()) {
      last_processed_date_ = max(last_processed_date_, rating_changes.back().race_info.date);
    }
  }
}

void RaceProcessor::Process(const tristats::Race& race) {
  if (race.info.date < last_processed_date_) {
    std::cerr << "invalid race date: " << race.info.date << " < " << last_processed_date_
              << std::endl;
    return;
  }

  last_processed_date_ = race.info.date;
  auto profile_to_contestant = CalculateRatingChanges(race);
  for (const auto& result : race.results) {
    if (profile_to_contestant.count(result.athlete.profile) == 0) {
      std::cerr << "no rating change for profile: " << result.athlete.profile << std::endl;
      assert(false);
    }

    const auto& contestant = profile_to_contestant[result.athlete.profile];
    auto map_it = profile_to_it_.find(result.athlete.profile);
    if (map_it == profile_to_it_.end()) {
      user_histories_.push_back(UserHistory{kStartRating, result.athlete, {}});
      auto it = user_histories_.end();
      --it;
      map_it = profile_to_it_.emplace(result.athlete.profile, it).first;
    }
    auto& it = map_it->second;
    it->rating += contestant.delta;
    it->rating_changes.push_back({race.info, contestant});
  }
}

std::unordered_map<std::string, Contestant> RaceProcessor::CalculateRatingChanges(
    const tristats::Race& race) {
  std::unordered_map<std::string, Contestant> profile_to_contestant;

  std::unordered_map<std::string, std::vector<Contestant>> division_to_contestants;

  auto race_type_multiplier = GetRaceTypeMultiplier(race.info.type);

  for (const auto& race_result : race.results) {
    const auto& athlete = race_result.athlete;
    const auto& profile = athlete.profile;
    auto rating = GetCurrentRating(profile);
    auto race_number = GetCompetitionCount(profile) + 1;

    division_to_contestants[athlete.division].emplace_back(
        profile, athlete.division, race_number, rating, race_result.timing.finish,
        /*group_size =*/0, /*rank =*/0., /*seed =*/0., /*delta =*/0);
  }

  for (auto& [division, contestants] : division_to_contestants) {
    auto group_size = static_cast<int>(contestants.size());
    auto finish_diff = contestants.back().finish - contestants.front().finish;
    for (auto& contestant : contestants) {
      double seed = 1.;
      for (const auto& other_contestant : contestants) {
        if (contestant.profile == other_contestant.profile) {
          continue;
        }
        seed += GetEloWinProbability(other_contestant.rating, contestant.rating);
      }

      contestant.group_size = group_size;
      contestant.rank = 1.;
      if (finish_diff > 0) {
        contestant.rank +=
            1. * (group_size - 1) * (contestant.finish - contestants.front().finish) / finish_diff;
      }

      contestant.seed = seed;

      auto rel_rank = group_size > 1 ? (contestant.seed - contestant.rank) / (group_size - 1) : 0.;
      contestant.delta = std::round(GetContestantMultiplier(contestant) * race_type_multiplier * rel_rank);
      profile_to_contestant[contestant.profile] = contestant;
    }
  }

  return profile_to_contestant;
}

int RaceProcessor::GetCurrentRating(const std::string& profile) {
  auto map_it = profile_to_it_.find(profile);
  if (map_it == profile_to_it_.end()) {
    return kStartRating;
  }
  return map_it->second->rating;
}

int RaceProcessor::GetCompetitionCount(const std::string& profile) {
  auto map_it = profile_to_it_.find(profile);
  if (map_it == profile_to_it_.end()) {
    return 0;
  }
  return static_cast<int>(map_it->second->rating_changes.size());
}

// int RaceProcessor::GetRatingToRank(const std::vector<Contestant>& contestants,
//                                    const Contestant& contestant, double rank) {
//   int left = 1;
//   int right = 10000;
//   while (right - left > 1) {
//     int mid = (left + right) / 2;
//     auto seed = GetSeed(contestants, contestant, mid);
//     if (seed < rank) {
//       right = mid;
//     } else {
//       left = mid;
//     }
//   }
//   return left;
// }

// double RaceProcessor::GetSeed(const std::vector<Contestant>& contestants,
//                               const Contestant& contestant, int rating) {
//   double seed = 0.;
//   for (const auto& other_contestant : contestants) {
//     if (other_contestant.profile == contestant.profile) {
//       continue;
//     }
//     seed += GetEloWinProbability(other_contestant.rating, rating);
//   }
//   return seed;
// }

// void RaceProcessor::ValidateDeltas(const std::vector<Contestant>& contestants) {
//   for (int i = 0; i < contestants.size(); ++i) {
//     for (int j = i + 1; j < contestants.size(); ++j) {
//       if (contestants[i].rating > contestants[j].rating) {
//         if (contestants[i].rating + contestants[i].delta <
//             contestants[j].rating + contestants[j].delta) {
//           std::cerr << "first invariant failed\ni: " << contestants[i] << "\nj: " <<
//           contestants[j]
//                     << std::endl;
//           assert(false);
//         }
//       }
//       if (contestants[i].rating < contestants[j].rating) {
//         if (contestants[i].delta < contestants[j].delta) {
//           std::cerr << "second invariant failed\ni: " << contestants[i] << "\nj: " <<
//           contestants[j]
//                     << std::endl;
//           assert(false);
//         }
//       }
//     }
//   }
// }

}  // namespace elo
