#include "patchmain.h"

#include <QCryptographicHash>
#include <QDir>
#include <QDirIterator>
#include <fstream>
#include <io.h>

PatchMain::PatchMain() {}


ErrorCode PatchMain::CalculateMD5(const std::string &filename, std::string &md5_str)
{
    QCryptographicHash md5(QCryptographicHash::Md5);
    static char data[65536];
    int filesize = 0;
    {
        std::ifstream in(filename, std::ifstream::ate | std::ifstream::binary);

        if (!in)
        {
            return ErrorCode::GAME_FILE_OPEN_ERROR;
        }

        filesize = in.tellg();

        if (md5_fp_ != nullptr)
        {
            std::string str_size = std::to_string(filesize);
            fwrite(str_size.c_str(), 1, str_size.size(), md5_fp_);
            fwrite(" ", 1, 1, md5_fp_);
        }

        in.seekg(in.beg);

        while (in)
        {
            in.read(data, 65536);
            md5.addData(QByteArray(data, in.gcount()));
        }
    }

    QByteArray md5sum = md5.result();
    md5_str = md5sum.toHex().toStdString();
    return ErrorCode::OK;
}

ErrorCode PatchMain::CheckMD5(int lang, const FileMetas& file_metas)
{
    ErrorCode ret = ErrorCode::OK;

    std::wstring lmd5sum;
    md5_fp_ = nullptr;
    if (fopen_s(&md5_fp_, "md5_check.txt", "w") != 0)
    {
        md5_fp_ = nullptr;
    }

    for (size_t i = 0; i < file_metas.size(); ++i)
    {
        const FileMeta& file_meta = file_metas[i];
        std::string md5sum;
        ret = CalculateMD5(file_meta.filename_, md5sum);
        if (ret != ErrorCode::OK)
        {
            break;
        }
        if (md5_fp_ != nullptr)
        {
            fwrite(" ", 1, 1, md5_fp_);
            fwrite(md5sum.c_str(), 1, md5sum.size(), md5_fp_);
            fwrite("\n", 1, 1, md5_fp_);
        }

        if (md5sum != file_meta.md5_[lang])
        {

            extra_error_message_ = file_meta.filename_short_ + " should be "
                                   + file_meta.md5_[lang] + " but is " + md5sum;
            ret = ErrorCode::MD5_CHECK_ERROR;
            break;
        }
    }

    if (md5_fp_ != nullptr) fclose(md5_fp_);

    return ret;
}

ErrorCode PatchMain::Convert(int dest_lang, const FileMetas& file_metas)
{
    static char buf[8192 * 16];

    for (size_t i = 0; i < file_metas.size(); ++i)
    {
        const FileMeta& file_meta = file_metas[i];
        FILE* fout = nullptr;
        fopen_s(&fout, file_meta.filename_.c_str(), "r+b");

        if (!fout)
        {
            return ErrorCode::GAME_FILE_OPEN_ERROR;
        }
        std::string patch_dir = file_meta.filename_short_;
        if (dest_lang == CN)
        {
            patch_dir += "_n";
        }
        else {
            patch_dir += "_o";
        }
        _chsize_s(_fileno(fout), file_meta.size_[dest_lang]);
        _fseeki64(fout, 0, SEEK_SET);

        QDirIterator iter(patch_dir.c_str(), {"*.patch"}, QDir::Files);

        if (!iter.hasNext())
        {
            fclose(fout);
            return ErrorCode::PATCH_FILE_OPEN_ERROR;
        }
        while (iter.hasNext())
        {
            QString filepath = iter.next();
            QFile fpatch(filepath);
            QFileInfo fileinfo(fpatch);

            if (!fpatch.open(QIODeviceBase::ReadOnly))
            {
                fclose(fout);
                return ErrorCode::PATCH_FILE_OPEN_ERROR;
            }

            long long offset = fileinfo.baseName().toLongLong();
            size_t cnt =  fpatch.read(buf, 8192 * 16);

            fpatch.close();

            if (cnt == 0 || offset >= file_meta.size_[dest_lang])
            {
                continue;
            }
            _fseeki64(fout, offset, SEEK_SET);
            fwrite(buf, 1, cnt, fout);
        }
        fclose(fout);
    }
    return ErrorCode::OK;
}

int PatchMain::ToSourceLang(int dest_lang)
{
    return !dest_lang;
}

ErrorCode PatchMain::Patch(int dest_lang, bool check_md5, const char* file_metas_path)
{
    ErrorCode ret = ErrorCode::OK;
    extra_error_message_ = "";

    // 1. load file metas
    FileMetas file_metas;
    ret = FileMeta::LoadFileMetas(file_metas_path, file_metas);
    if (ret != ErrorCode::OK)
    {
        return ret;
    }

    // 2. check md5 (optional, the checking process may take a lot of time)
    if (check_md5)
    {
        // check source language's md5
        ret = CheckMD5(ToSourceLang(dest_lang), file_metas);
        if (ret != ErrorCode::OK)
        {
            return ret;
        }
    }

    // 3. do the real patch
    ret = Convert(dest_lang, file_metas);

    return ret;
}
