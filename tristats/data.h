#pragma once
#include <optional>
#include <string>
#include <vector>

namespace tristats {

struct Athlete {
  int id;
  std::string profile;
  // TODO: add name
  std::string division;
  std::string country;
  std::string sex;
};

struct Timing {
  int swim;
  int t1;
  int bike;
  int t2;
  int run;
  int finish;
};

struct Rank {
  int total_rank;
  int division_rank;
};

struct RaceResult {
  Athlete athlete;
  Timing timing;
  Rank rank;
};

enum class RaceType : uint8_t { Supersprint, Sprint, Olympic, Half, Full };

inline std::optional<RaceType> FromString(const std::string& type_str) {
  if (type_str == "supersprint") {
    return tristats::RaceType::Supersprint;
  } else if (type_str == "sprint") {
    return tristats::RaceType::Sprint;
  } else if (type_str == "olympic") {
    return tristats::RaceType::Olympic;
  } else if (type_str == "half") {
    return tristats::RaceType::Half;
  } else if (type_str == "full") {
    return tristats::RaceType::Full;
  }
  return std::nullopt;
}

inline std::string ToString(RaceType race_type) {
  switch (race_type) {
    case RaceType::Supersprint:
      return "supersprint";
    case RaceType::Sprint:
      return "sprint";
    case RaceType::Olympic:
      return "olympic";
    case RaceType::Half:
      return "half";
    case RaceType::Full:
      return "full";
  }
}

inline std::ostream& operator<<(std::ostream& os, RaceType race_type) {
  os << ToString(race_type);
  return os;
}

// inline std::ostream& operator<<(std::ostream& os, RaceType race_type) {
//   switch (race_type) {
//     case RaceType::Supersprint:
//       return os << "supersprint";
//     case RaceType::Sprint:
//       return os << "sprint";
//     case RaceType::Olympic:
//       return os << "olympic";
//     case RaceType::Half:
//       return os << "half";
//     case RaceType::Full:
//       return os << "full";
//   }
// }

struct RaceInfo {
  std::string name;
  std::string date;
  std::string url;
  RaceType type;
};

struct Race {
  RaceInfo info;
  std::vector<RaceResult> results;
};

}  // namespace tristats
