#include <string>
#include <sys/stat.h>
#include <sys/types.h>
#include <iostream>
#include <pwd.h>
#include <grp.h>
#include <unistd.h>
#include <cstdlib>
#include <cerrno>
#include <cstring>

int main() {
  struct stat buf;
  std::string line;
  uid_t uid;
  gid_t gid;
  mode_t mode;
  size_t pos1, pos2, pos3, start;
  while(std::cin) {
      getline(std::cin, line);
      if(line.empty()) {
          break;
      }

      pos1 = line.find(' ');
      mode = static_cast<mode_t>(std::stoul(line.substr(0, pos1),
                                            nullptr, 8));

      start = pos1 + 1;
      pos2 = line.find(' ', start);
      uid = stoi(line.substr(start, pos2 - start));

      // Find the position of the third space starting from the character after pos2
      start = pos2 + 1;
      pos3 = line.find(' ', start);
      gid = std::stoi(line.substr(start, pos3 - start));

      // Extract everything after the third space
      std::string file = line.substr(pos3 + 1);
      if(lchown(file.c_str(), uid, gid) == -1) {
          std::cerr << "Error changing owner/group on " << file << std::endl;
      }
      if(lstat(file.c_str(), &buf) == -1) {
          std::cerr << "Error getting file status on " << file << ": "
                    << strerror(errno) << std::endl;
      } else {
        if(S_ISLNK(buf.st_mode)) {
          continue;
        }
      }
      if(chmod(file.c_str(), mode) == -1) {
          std::cerr << "Error changing file permissions on "
                    << file << ": " << strerror(errno) << std::endl;
      }
  };
}
//  chmod("./usr/bin/sudo", 0004755);
