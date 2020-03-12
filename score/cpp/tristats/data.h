#pragma once
#include <optional>
#include <string>
#include <vector>

namespace tristats {

struct Athlete {
  std::string profile;
  std::string name;
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

struct RaceResult {
  Athlete athlete;
  Timing timing;
};

enum class RaceType : uint8_t { Supersprint, Sprint, Olympic, Half, Full };

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

inline std::ostream& operator<<(std::ostream& os, Timing timing) {
  return os << "{"
            << " swim: " << timing.swim << " t1: " << timing.t1 << " bike: " << timing.bike
            << " t2: " << timing.t2 << " run: " << timing.run << " finish: " << timing.finish
            << " }";
}

}  // namespace tristats
