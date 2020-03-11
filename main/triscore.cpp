#include <rapidjson/document.h>
#include <rapidjson/prettywriter.h>
#include <rapidjson/stringbuffer.h>
#include <rapidjson/writer.h>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <unordered_set>
#include <sstream>
#include <string>
#include <vector>

#include "base/filesystem.h"
#include "elo/race_processor.h"

namespace {

template <typename Value>
std::string JsonToCompactString(const Value& v) {
  using namespace rapidjson;
  StringBuffer buffer;
  Writer<StringBuffer> writer(buffer);
  v.Accept(writer);
  return buffer.GetString();
}

template <typename Value>
std::string JsonToStyledString(const Value& v) {
  using namespace rapidjson;
  StringBuffer buffer;
  PrettyWriter<StringBuffer> writer(buffer);
  v.Accept(writer);
  return buffer.GetString();
}

std::string ReadFile(const std::string& file) {
  std::ifstream istr(file);
  std::stringstream stream;
  std::string line;
  while (istr >> line) {
    stream << line;
  }
  return stream.str();
}

rapidjson::Document JsonFromFile(const std::string& file) {
  rapidjson::Document document;
  auto data = ReadFile(file);
  document.Parse(data.data());
  return document;
}

fs::path GetRaceFile(fs::path results_dir, const tristats::RaceInfo& race_info) {
  return results_dir / race_info.url.substr(1) / (race_info.date + ".json");
}

int GLOBAL_ID = 0;

size_t ParseIndex(const std::string& str) {
  size_t start_pos = str.find('_') + 1;
  size_t end_pos = str.find('.');
  auto index_str = str.substr(start_pos, end_pos - start_pos);
  return std::atoi(index_str.data());
}

}  // namespace

std::string GetString(const rapidjson::Value& value) { return value.GetString(); }

std::string GetStringOrEmpty(const rapidjson::Value& value) {
  return value.IsString() ? value.GetString() : "";
}

int StringDurationToSeconds(const std::string& duration) {
  std::vector<int> intervals;
  size_t last_pos = 0;
  while (true) {
    auto pos = duration.find(':', last_pos);
    auto r = duration.substr(last_pos, pos - last_pos);
    intervals.push_back(std::atoi(r.data()));
    last_pos = pos + 1;
    if (pos == std::string::npos) {
      break;
    }
  }
  std::reverse(intervals.begin(), intervals.end());

  int total = 0;
  int multiplier = 1;
  for (auto interval : intervals) {
    total += interval * multiplier;
    multiplier *= 60;
  }
  return total;
}

// template <typename T>
// std::string ToString(const T& t) {
//   std::ostringstream os;
//   os << t;
//   return os.str();
// }

// void ProcessRace(const RaceInfo& race_info) {
//   auto race_file = GetRaceFile(race_info);
//   // std::cerr << "race file: " << race_file << std::endl;
//   if (!fs::exists(race_file)) {
//     std::cerr << "race file not found: " << race_file << std::endl;
//     return;
//   }
//   auto race_json = JsonFromFile(race_file);

//   for (const auto& result : race_json.GetArray()) {
//     auto racer = GetString(result["Racer"]);
//     auto profile = GetStringOrEmpty(result["ProfileUrl"]);
//     // auto trilife_id = result["TrilifeId"].GetInt();
//     if (!profile) {
//       std::cerr << "no profile for racer: " << racer << std::endl;
//       continue;
//     }
//     std::cout << "profile: " << *profile << std::endl;
//   }
// }

std::vector<tristats::RaceResult> ParseRaceResults(const rapidjson::Document& race_json) {
  std::vector<tristats::RaceResult> race_results;
  std::unordered_set<std::string> profiles;
  for (const auto& result_json : race_json.GetArray()) {
    tristats::RaceResult race_result;

    auto profile = GetStringOrEmpty(result_json["ProfileUrl"]);
    if (profile.empty()) {
      profile = "profile_" + std::to_string(GLOBAL_ID++);
      // auto racer = result_json["Racer"].GetString();
      // std::cerr << "no profile for racer: " << racer << std::endl;
    }
    // std::cout << "profile: " << profile << std::endl;
    if (!profiles.insert(profile).second) {
      std::cerr << "skip duplicated profile: " << profile << std::endl;
      continue;
    }

    race_result.athlete = {
        result_json["TrilifeId"].GetInt(), profile, result_json["Division"].GetString(),
        GetStringOrEmpty(result_json["Country"]), result_json["Sex"].GetString()};
    race_result.rank = {result_json["Rank"].GetInt(), result_json["DivisionRank"].GetInt()};
    race_result.timing = {
        // StringDurationToSeconds(result_json["Swim"].GetString()),
        //                     StringDurationToSeconds(result_json["T1"].GetString()),
        //                     StringDurationToSeconds(result_json["Bike"].GetString()),
        //                     StringDurationToSeconds(result_json["T2"].GetString()),
        //                     StringDurationToSeconds(result_json["Run"].GetString()),
        0, 0, 0, 0, 0, StringDurationToSeconds(result_json["Finish"].GetString())};
    race_results.push_back(race_result);
  }
  return race_results;
}

void DumpUserHistoriesDescByRating(const fs::path& file,
                                   std::vector<elo::UserHistory> user_histories,
                                   bool pretty = false) {
  std::sort(user_histories.begin(), user_histories.end(),
            [](const auto& lhs, const auto& rhs) { return lhs.rating > rhs.rating; });

  rapidjson::Document rating_json(rapidjson::kObjectType);
  auto& allocator = rating_json.GetAllocator();

  auto AddMember = [&](rapidjson::Value& value, const std::string& name, auto&& t) {
    value.AddMember(rapidjson::StringRef(name.c_str()), t, allocator);
  };

  auto AddStringMember = [&](rapidjson::Value& value, const std::string& name,
                             const std::string& str) {
    AddMember(value, name, rapidjson::StringRef(str.c_str()));
  };

  rapidjson::Value users_json(rapidjson::kArrayType);
  std::string last_date;

  for (const auto& user_history : user_histories) {
    rapidjson::Value rating_changes_json(rapidjson::kArrayType);
    int total_races = 0;
    for (const auto& rating_change : user_history.rating_changes) {
      // std::cout << rating_change.date << " " << rating_change.change << std::endl;
      rapidjson::Value rating_change_json(rapidjson::kObjectType);
      AddStringMember(rating_change_json, "date", rating_change.race_info.date);
      AddStringMember(rating_change_json, "race", rating_change.race_info.name);
      std::string type_str = ToString(rating_change.race_info.type);
      AddStringMember(rating_change_json, "type", type_str);

      const auto& contestant = rating_change.contestant;

      AddMember(rating_change_json, "rating", contestant.rating);
      AddStringMember(rating_change_json, "division", contestant.division);
      AddMember(rating_change_json, "race_number", contestant.race_number);
      AddMember(rating_change_json, "finish", contestant.finish);
      AddMember(rating_change_json, "group_size", contestant.group_size);
      AddMember(rating_change_json, "rank", contestant.rank);
      AddMember(rating_change_json, "seed", contestant.seed);
      AddMember(rating_change_json, "delta", contestant.delta);

      rating_changes_json.PushBack(rating_change_json, allocator);
      last_date = std::max(last_date, rating_change.race_info.date);
      ++total_races;
    }

    rapidjson::Value user_json(rapidjson::kObjectType);
    AddStringMember(user_json, "profile", user_history.athlete.profile);
    AddStringMember(user_json, "country", user_history.athlete.country);
    AddStringMember(user_json, "sex", user_history.athlete.sex);
    AddMember(user_json, "rating", user_history.rating);
    AddMember(user_json, "races", total_races);
    AddMember(user_json, "changes", rating_changes_json);
    users_json.PushBack(user_json, allocator);
  }

  rating_json.AddMember("users", users_json, allocator);  // TODO: rename to athletes
  rating_json.AddMember("last_date", rapidjson::StringRef(last_date.c_str()), allocator);

  {
    if (pretty) {
      std::ofstream rating_file(file.string());
      rating_file << JsonToStyledString(rating_json);
    } else {
      std::ofstream rating_file(file.string());
      rating_file << JsonToCompactString(rating_json);
    }
  }
}

tristats::Athlete ParseAthlete(const rapidjson::Value& value) {
  tristats::Athlete athlete;
  athlete.id = value["id"].GetInt();
  athlete.profile = value["profile"].GetString();
  athlete.division = value["division"].GetString();
  athlete.country = value["country"].GetString();
  athlete.sex = value["sex"].GetString();
  return athlete;
}

elo::RatingChange ParseRatingChange(const rapidjson::Value& rating_change_json) {
  auto type_opt = tristats::FromString(rating_change_json["type"].GetString());
  assert(type_opt.has_value());

  tristats::RaceInfo race_info{rating_change_json["race"].GetString(),
                               rating_change_json["date"].GetString(),
                               /*url =*/"", *type_opt};
  std::string profile;

  elo::Contestant contestant{/*profile =*/"",
                             rating_change_json["division"].GetString(),
                             rating_change_json["race_number"].GetInt(),
                             rating_change_json["rating"].GetInt(),
                             rating_change_json["finish"].GetInt(),
                             rating_change_json["group_size"].GetInt(),
                             rating_change_json["rank"].GetDouble(),
                             rating_change_json["seed"].GetDouble(),
                             rating_change_json["delta"].GetInt()};
  return elo::RatingChange{race_info, contestant};
}

std::vector<elo::RatingChange> ParseRatingChanges(const rapidjson::Value& rating_changes_json) {
  std::vector<elo::RatingChange> rating_changes;
  for (const auto& rating_change_json : rating_changes_json.GetArray()) {
    rating_changes.push_back(ParseRatingChange(rating_change_json));
  }
  return rating_changes;
}

std::vector<elo::UserHistory> LoadFile(const fs::path& file) {
  std::vector<elo::UserHistory> user_histories;
  if (!fs::exists(file)) {
    return user_histories;
  }

  std::cerr << "read users cache file: " << file << std::endl;
  auto data = ReadFile(file.string());
  rapidjson::Document json;
  std::cerr << "parse users cache json" << std::endl;
  json.Parse(data.data(), data.length());

  for (const auto& user_history_json : json["users"].GetArray()) {
    elo::UserHistory user_history;
    user_history.rating = user_history_json["rating"].GetInt();
    user_history.athlete = ParseAthlete(user_history_json["athlete"]);
    user_history.rating_changes = ParseRatingChanges(user_history_json["changes"]);
    user_histories.push_back(user_history);
  }
  return user_histories;
}

std::optional<tristats::RaceType> GetRaceType(const std::string& event_name) {
  auto last_sep_pos = event_name.rfind('/');
  if (last_sep_pos == std::string::npos) {
    return std::nullopt;
  }
  auto type_str = event_name.substr(last_sep_pos + 1);
  return tristats::FromString(type_str);
}

int main(int argc, char** argv) {
  if (argc < 3) {
    std::cerr << "Usage: " << argv[0] << " [races-file] [results-dir]" << std::endl;
    return 0;
  }

  auto races_file = fs::canonical(fs::path{argv[1]});
  auto results_dir = fs::canonical(fs::path{argv[2]});
  auto rating_start_file = argc > 3 ? fs::canonical(fs::path{argv[3]}) : fs::path{};

  auto races_json = JsonFromFile(races_file);
  std::vector<tristats::RaceInfo> race_infos;
  for (const auto& race : races_json.GetArray()) {
    auto race_name = race["RaceName"].GetString();
    auto event_name = race["EventUrl"].GetString();
    auto race_type_opt = GetRaceType(event_name);
    if (!race_type_opt) {
      std::cerr << "unknown race type race name: " << race_name << " event name: " << event_name
                << std::endl;
      continue;
    }

    auto date = std::string(race["Date"].GetString()).substr(0, 10);
    auto url = race["RaceUrl"].GetString();
    race_infos.push_back({race_name, date, url, *race_type_opt});
  }

  std::sort(race_infos.begin(), race_infos.end(),
            [](const auto& lhs, const auto& rhs) { return lhs.date < rhs.date; });

  auto start_user_histories = LoadFile(rating_start_file);
  elo::RaceProcessor race_processor(start_user_histories);

  size_t limit = 10000;
  size_t start_index = fs::exists(rating_start_file) ? ParseIndex(rating_start_file.string()) : 0;
  size_t end_index = std::min(start_index + limit, race_infos.size());
  for (size_t i = start_index; i < end_index; ++i) {
    auto& race_info = race_infos[i];
    auto race_file = GetRaceFile(results_dir, race_info);
    if (!fs::exists(race_file)) {
      std::cerr << "race file not found: " << race_file << std::endl;
      continue;
    }

    auto race_json = JsonFromFile(race_file);
    auto race_results = ParseRaceResults(race_json);

    std::cerr << std::setw(4) << i + 1 << "/" << end_index << ": " << race_info.date << " "
              << race_info.name << " type: " << race_info.type << " count: " << race_results.size()
              << "\n";

    tristats::Race race{std::move(race_info), std::move(race_results)};
    race_processor.Process(race);

    // if ((i + 1) % 1000 == 0) {
      // fs::path tmp_rating_file{"rating_" + std::to_string(i + 1) + ".json"};
      // std::cerr << "dump " << tmp_rating_file << std::endl;
      // DumpUserHistoriesDescByRating(tmp_rating_file, race_processor.GetUserHistories());
    // }

    // std::cin.ignore();
  }


  fs::path rating_file{"rating.json"};
  DumpUserHistoriesDescByRating(rating_file, race_processor.GetUserHistories(), false);

  // fs::path rating_file{"styled_rating.json"};
  // DumpUserHistoriesDescByRating(rating_file, race_processor.GetUserHistories(), true);

  return 0;
}
