#pragma once

#include <QString>
#include <string>

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

    ErrorCode CheckMD5(int lang, const FileMetas& file_metas);
    // @param[out] md5_str
    ErrorCode CalculateMD5(const std::string &filename, std::string& md5_str);
    // @param[in] dest_lang destination language
    ErrorCode Patch(int dest_lang, bool check_md5 = true, const char* file_meta_path = "file_metas.txt");
    ErrorCode Convert(int dest_lang, const FileMetas& file_metas);
    static int ToSourceLang(int dest_lang);

    std::string extra_error_message_;
private:
    FILE* md5_fp_ = nullptr;
};
