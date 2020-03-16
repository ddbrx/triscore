#pragma once
#include <rapidjson/document.h>
#include <rapidjson/prettywriter.h>
#include <rapidjson/stringbuffer.h>
#include <rapidjson/writer.h>

#include <algorithm>
#include <iostream>
#include <string>
#include <unordered_map>
#include <vector>

namespace tristats {

std::string GetString(const rapidjson::Value& value) { return value.GetString(); }

std::string GetStringOrDefault(const rapidjson::Value& value, std::string default_value = "") {
  return value.IsString() ? value.GetString() : default_value;
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

std::string ToLower(std::string str) {
  std::transform(str.begin(), str.end(), str.begin(), ::tolower);
  return str;
}

bool EndsWith(std::string str, std::string end) { return str.find(end) != std::string::npos; }

std::vector<tristats::RaceResult> ParseRaceResults(const rapidjson::Document& race_json) {
  std::vector<tristats::RaceResult> race_results;
  std::unordered_map<std::string, std::string> profile_to_division;
  for (const auto& result_json : race_json.GetArray()) {
    tristats::RaceResult race_result;

    auto racer_url = GetStringOrDefault(result_json["RacerUrl"]);
    if (racer_url.empty()) {
      std::cerr << "skip racer with empty RacerUrl" << std::endl;
      continue;
    }

    auto profile_url = GetStringOrDefault(result_json["ProfileUrl"]);
    auto division = GetString(result_json["Division"]);
    auto sex = GetString(result_json["Sex"]);
    auto racer = GetStringOrDefault(result_json["Racer"]);
    auto country = ToLower(GetStringOrDefault(result_json["Country"], "nocountry"));

    auto racer_profile_url = "/" + country + "/" + "profile" + racer_url;
    auto profile =
        !profile_url.empty() && EndsWith(profile_url, racer_url) ? profile_url : racer_profile_url;

    if (profile_to_division.count(profile) > 0) {
      auto existing_division = profile_to_division[profile];
      if (existing_division != division) {
        auto modified_profile = profile + "-" + ToLower(division);
        std::cerr << "modify profile: " << profile << " to " << modified_profile << std::endl;
        profile = modified_profile;
        assert(profile_to_division.emplace(profile, division).second);
      } else {
        std::cerr << "skip duplicated profile: " << profile << " division: " << division
                  << std::endl;
        continue;
      }
    } else {
      assert(profile_to_division.emplace(profile, division).second);
    }

    race_result.athlete = {profile, racer, division, country, sex};
    race_result.timing = {
      StringDurationToSeconds(result_json["Swim"].GetString()),
      StringDurationToSeconds(result_json["T1"].GetString()),
      StringDurationToSeconds(result_json["Bike"].GetString()),
      StringDurationToSeconds(result_json["T2"].GetString()),
      StringDurationToSeconds(result_json["Run"].GetString()),
      StringDurationToSeconds(result_json["Finish"].GetString())
    };
    race_results.push_back(race_result);
  }
  return race_results;
}

}  // namespace tristats
