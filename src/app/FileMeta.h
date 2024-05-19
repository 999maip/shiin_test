#pragma once

#include <string>
#include <vector>
#include "ErrorCode.h"

class FileMeta;
typedef std::vector<FileMeta> FileMetas;

class FileMeta
{
public:
    FileMeta();

    // @param[out] file_meta
    static ErrorCode LoadFileMetas(const char* filepath, FileMetas& file_meta);

    std::string filename_;
    std::string filename_short_;

    // 0: origin 1: cn-lized
    std::string md5_[2];
    long long size_[2];
};
