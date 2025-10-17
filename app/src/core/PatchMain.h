#pragma once

#include <QString>

#include "FileMeta.h"
#include "ErrorCode.h"

class PatchMain
{
public:
    enum LANG
    {
        EN_JP = 0,
        CN    = 1,
    };
    PatchMain();

    FILE* md5_fp_ = nullptr;

    ErrorCode CheckMD5(int lang, const FileMetas& file_metas);
    // @param[out] md5_str
    ErrorCode CalculateMD5(const QString &filename, QString& md5_str, qint64& actual_file_size);
    // @param[in] dest_lang destination language
    ErrorCode Patch(int dest_lang, bool check_md5 = true, const QString& file_meta_path = FileMeta::DEFAULT_FILEPATH);
    ErrorCode Convert(int dest_lang, const FileMetas& file_metas);
    static int ToSourceLang(int dest_lang);

    QString extra_error_message_;
};
