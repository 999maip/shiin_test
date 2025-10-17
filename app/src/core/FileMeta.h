#pragma once

#include <vector>
#include "ErrorCode.h"
#include "PatchInfo.h"

class FileMeta;
typedef std::vector<FileMeta> FileMetas;

class FileMeta
{
public:
    FileMeta();

    // @param[out] file_meta
    static ErrorCode LoadFileMetas(const QString& filepath, FileMetas& file_meta);
    static PatchInfo LoadPatchInfo(QString filepath = DEFAULT_FILEPATH);
    static const QString DEFAULT_FILEPATH;
    static const QString PATCH_ROOT_DIR;


    QString filename_; // the real file path (relative to game's root path)
    QString filename_short_; // script generated path (indexed based)

    // 0: origin 1: cn-lized
    QString md5_[2];
    qint64 size_[2];
};
