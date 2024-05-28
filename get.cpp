#include <filesystem>
#include <iostream>
#include <regex>
#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <utility>
#include <fstream>


std::vector<std::regex> ignorePatterns;
std::vector<std::regex> includePatterns;

std::string regexEscape(const std::string& input) {
    std::ostringstream escaped;
    for (char c : input) {
        switch (c) {
            // Add more cases if other characters need to be escaped
            case '^':
            case '$':
            case '\\':
            case '.':
            case '|':
            case '?':
            case '*':
            case '+':
            case '(':
            case ')':
            case '[':
            case ']':
            case '{':
            case '}':
                escaped << '\\' << c;
                break;
            default:
                escaped << c;
                break;
        }
    }
    return escaped.str();
}


//Converts gitignore to close enough regex.
//(the file will be reincluded eaven though
//used for a three structure where this is a performace
//optimization for us that do string processing it is
//cheaper to just do pattern matching)
std::regex parsePattern(const std::string& pattern) {
  std::string regexPattern;
  bool isDirectoryPattern = (pattern.back() == '/');
  for(char c : pattern) {
    switch (c) {
      case '*':
        regexPattern += ".*";
        break;
      case '?':
        regexPattern += ".";
        break;
      case '/':
        regexPattern += "\\/";
        break;
      default:
        regexPattern += regexEscape(std::string(1,c));
        break;
    }
  }
  if(isDirectoryPattern) {
    regexPattern.pop_back();
    regexPattern.pop_back();
    regexPattern += ".*";
  }
  return std::regex(regexPattern);
}

void parseGitIgnoreFile(const std::string& filename) {
  std::ifstream file(filename);
  std::string line;
  while(std::getline(file, line)) {
    while(!line.empty() && line.back() == ' ') {
      if(line.size() > 1 && line[line.size() - 2] == '\\') {
        break;
      }
      line.pop_back();
    }

    if(line.empty() || line[0] == '#') {
      continue;
    }

    if(line[0] == '!') {
      includePatterns.push_back(parsePattern(line.substr(1)));
    } else {
      ignorePatterns.push_back(parsePattern(line));
    }
  }
}

bool shouldIgnore(const std::string& path) {
  for(const std::regex& pattern : includePatterns) {
    if(std::regex_match(path, pattern)) {
      return false;
    }
  }

  for(const std::regex& pattern : ignorePatterns) {
    if(std::regex_match(path, pattern)) {
      return true;
    }
  }
  return false;
}

int main() {
  parseGitIgnoreFile(".gitignore");
  parseGitIgnoreFile(".permignore");

  struct stat st;
  std::string path;
  for (std::filesystem::recursive_directory_iterator
          i("."), end;
       i != end; ++i) {
    path = i->path().string().substr(2);
    if(shouldIgnore(path)){
      continue;
    }
    //lstat to have symlinks not be transparrent
    if (lstat(i->path().c_str(), &st) == 0) {
      std::cout << std::oct << (st.st_mode & 04777) << std::dec << " "
                << st.st_uid << " " << st.st_gid << " " << path << std::endl;
    }
  }
}
