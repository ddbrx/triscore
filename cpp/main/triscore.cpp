#include <rapidjson/document.h>
#include <rapidjson/prettywriter.h>
#include <rapidjson/stringbuffer.h>
#include <rapidjson/writer.h>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <unordered_set>
#include <vector>

#include "base/filesystem.h"
#include "elo/race_processor.h"
#include "tristats/parser.h"

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

size_t ParseIndex(const std::string& str) {
  size_t start_pos = str.find('_') + 1;
  size_t end_pos = str.find('.');
  auto index_str = str.substr(start_pos, end_pos - start_pos);
  return std::atoi(index_str.data());
}

}  // namespace

void DumpUserHistoriesDescByRating(const fs::path& file,
                                   std::vector<elo::AthleteHistory> athlete_histories,
                                   bool pretty = false) {
  std::sort(athlete_histories.begin(), athlete_histories.end(),
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

  for (const auto& athlete_history : athlete_histories) {
    rapidjson::Value races_json(rapidjson::kArrayType);
    for (const auto& race : athlete_history.races) {
      // std::cout << race.date << " " << race.change << std::endl;
      rapidjson::Value race_json(rapidjson::kObjectType);
      AddStringMember(race_json, "date", race.race_info.date);
      AddStringMember(race_json, "race", race.race_info.name);
      std::string type_str = ToString(race.race_info.type);
      AddStringMember(race_json, "type", type_str);

      const auto& contestant = race.contestant;

      rapidjson::Value timing_json(rapidjson::kObjectType);
      AddMember(timing_json, "swim", contestant.timing.swim);
      AddMember(timing_json, "t1", contestant.timing.t1);
      AddMember(timing_json, "bike", contestant.timing.bike);
      AddMember(timing_json, "t2", contestant.timing.t2);
      AddMember(timing_json, "run", contestant.timing.run);
      AddMember(timing_json, "finish", contestant.timing.finish);

      AddStringMember(race_json, "division", contestant.division);
      AddMember(race_json, "timing", timing_json);
      AddMember(race_json, "rank", contestant.rank);
      AddMember(race_json, "seed", contestant.seed);
      AddMember(race_json, "size", contestant.group_size);
      AddMember(race_json, "rating", contestant.rating);
      AddMember(race_json, "delta", contestant.delta);

      races_json.PushBack(race_json, allocator);
      last_date = std::max(last_date, race.race_info.date);
    }

    rapidjson::Value user_json(rapidjson::kObjectType);
    AddStringMember(user_json, "profile", athlete_history.athlete.profile);
    AddStringMember(user_json, "name", athlete_history.athlete.name);
    AddStringMember(user_json, "country", athlete_history.athlete.country);
    AddStringMember(user_json, "sex", athlete_history.athlete.sex);
    AddMember(user_json, "rating", athlete_history.rating);
    AddMember(user_json, "races", races_json);
    users_json.PushBack(user_json, allocator);
  }

  rating_json.AddMember("athletes", users_json, allocator);
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
  athlete.profile = value["profile"].GetString();
  athlete.name = value["name"].GetString();
  athlete.division = value["division"].GetString();
  athlete.country = value["country"].GetString();
  athlete.sex = value["sex"].GetString();
  return athlete;
}

elo::RatingChange ParseRace(const rapidjson::Value& race_json) {
  auto type_opt = tristats::FromString(race_json["type"].GetString());
  assert(type_opt.has_value());

  tristats::RaceInfo race_info{race_json["race"].GetString(), race_json["date"].GetString(),
                               /*url =*/"", *type_opt};
  std::string profile;

  elo::Contestant contestant{
      /*profile =*/"",
      race_json["division"].GetString(),
      race_json["rating"].GetInt(),
      tristats::Timing{race_json["timing"]["swim"].GetInt(), race_json["timing"]["t1"].GetInt(),
                       race_json["timing"]["bike"].GetInt(), race_json["timing"]["t2"].GetInt(),
                       race_json["timing"]["run"].GetInt(), race_json["timing"]["finish"].GetInt()},
      race_json["size"].GetInt(),
      race_json["rank"].GetDouble(),
      race_json["seed"].GetDouble(),
      race_json["delta"].GetInt()};
  return elo::RatingChange{race_info, contestant};
}

std::vector<elo::RatingChange> ParseRaces(const rapidjson::Value& races_json) {
  std::vector<elo::RatingChange> races;
  for (const auto& race_json : races_json.GetArray()) {
    races.push_back(ParseRace(race_json));
  }
  return races;
}

std::vector<elo::AthleteHistory> LoadFile(const fs::path& file) {
  std::vector<elo::AthleteHistory> athlete_histories;
  if (!fs::exists(file)) {
    return athlete_histories;
  }

  std::cerr << "read athlete cache file: " << file << std::endl;
  auto data = ReadFile(file.string());
  rapidjson::Document json;
  std::cerr << "parse athlete cache json" << std::endl;
  json.Parse(data.data(), data.length());

  for (const auto& athlete_history_json : json["athletes"].GetArray()) {
    elo::AthleteHistory athlete_history;
    athlete_history.rating = athlete_history_json["rating"].GetInt();
    athlete_history.athlete = ParseAthlete(athlete_history_json["athlete"]);
    athlete_history.races = ParseRaces(athlete_history_json["races"]);
    athlete_histories.push_back(athlete_history);
  }
  return athlete_histories;
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

  auto start_athlete_histories = LoadFile(rating_start_file);
  elo::RaceProcessor race_processor(start_athlete_histories);

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

    std::cerr << std::setw(4) << i + 1 << "/" << end_index << ": " << race_info.date << " "
              << race_info.name << " type: " << race_info.type << " url: " << race_info.url
              << " file: " << race_file << "\n";

    auto race_json = JsonFromFile(race_file);
    auto race_results = tristats::ParseRaceResults(race_json);

    tristats::Race race{std::move(race_info), std::move(race_results)};
    race_processor.Process(race);

    // if ((i + 1) % 1000 == 0) {
    // fs::path tmp_rating_file{"rating_" + std::to_string(i + 1) + ".json"};
    // std::cerr << "dump " << tmp_rating_file << std::endl;
    // DumpUserHistoriesDescByRating(tmp_rating_file, race_processor.GetUserHistories());
    // }

    // std::cin.ignore();
  }

  // fs::path rating_file{"rating.json"};
  // std::cerr << "dumping " << rating_file << std::endl;
  // DumpUserHistoriesDescByRating(rating_file, race_processor.GetUserHistories(), false);

  fs::path rating_file{"styled_rating.json"};
  std::cerr << "dumping " << rating_file << std::endl;
  DumpUserHistoriesDescByRating(rating_file, race_processor.GetUserHistories(), true);

  return 0;
}
