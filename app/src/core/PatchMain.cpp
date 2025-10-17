#include "PatchMain.h"

#include <QCryptographicHash>
#include <QDir>
#include <QDirIterator>
#include <io.h>

PatchMain::PatchMain() {}

ErrorCode PatchMain::CalculateMD5(const QString &filename, QString& md5_str, qint64& actual_file_size)
{
    QCryptographicHash md5(QCryptographicHash::Md5);
    static char data[65536];
    actual_file_size = 0;

    QFile file(filename);
    if (!file.open(QIODeviceBase::ReadOnly))
    {
        return ErrorCode::GAME_FILE_OPEN_ERROR;
    }

    while (!file.atEnd())
    {
        qint64 bytes_read = file.read(data, 65536);
        md5.addData(QByteArray(data, bytes_read));
        actual_file_size += bytes_read;
    }

    QByteArray md5sum = md5.result();
    md5_str = md5sum.toHex();
    return ErrorCode::OK;
}

ErrorCode PatchMain::CheckMD5(int lang, const FileMetas& file_metas)
{
    ErrorCode ret = ErrorCode::OK;
    static char line_buff[2048];

    bool md5_file_creation_tried = false;
    md5_fp_ = nullptr;
    for (size_t i = 0; i < file_metas.size(); ++i)
    {
        const FileMeta& file_meta = file_metas[i];
        QString md5sum;
        qint64 actual_file_size = 0;
        ret = CalculateMD5(file_meta.filename_, md5sum, actual_file_size);
        if (ret != ErrorCode::OK)
        {
            break;
        }
        if (md5sum != file_meta.md5_[lang])
        {
            if (!md5_file_creation_tried)
            {
                if (fopen_s(&md5_fp_, "md5_check.txt", "w") != 0)
                {
                    md5_fp_ = nullptr;
                }
                md5_file_creation_tried = true;
            }
            if (md5_fp_ != nullptr)
            {
                snprintf(line_buff, 2048, "%s|%s|%lu|%lu|%s|%s\n",
                    file_meta.filename_short_.toUtf8().constData(),
                    file_meta.filename_.toUtf8().constData(),
                    file_meta.size_[lang],
                    actual_file_size,
                    file_meta.md5_[lang].toUtf8().constData(),
                    md5sum.toUtf8().constData()
                );
                fwrite(line_buff, 1, strlen(line_buff), md5_fp_);
            }

            extra_error_message_ = QString("file[") + file_meta.filename_short_ + "] should be "
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

        QFile target_file(file_meta.filename_);
        if (!target_file.open(QIODeviceBase::ReadWrite))
        {
            return ErrorCode::GAME_FILE_OPEN_ERROR;
        }

        QString patch_dir = QDir(FileMeta::PATCH_ROOT_DIR).filePath(file_meta.filename_short_ + ((dest_lang == CN) ? "_n" : "_o"));
        target_file.resize(file_meta.size_[dest_lang]);

        QDirIterator iter(patch_dir, {"*.patch"}, QDir::Files);

        if (!iter.hasNext())
        {
            target_file.close();
            return ErrorCode::PATCH_FILE_OPEN_ERROR;
        }
        while (iter.hasNext())
        {
            QString filepath = iter.next();
            QFile fpatch(filepath);
            QFileInfo fileinfo(fpatch);

            if (!fpatch.open(QIODeviceBase::ReadOnly))
            {
                target_file.close();
                return ErrorCode::PATCH_FILE_OPEN_ERROR;
            }

            long long offset = fileinfo.baseName().toLongLong();
            size_t read_bytes = fpatch.read(buf, 8192 * 16);

            fpatch.close();

            if (read_bytes == 0 || offset >= file_meta.size_[dest_lang])
            {
                continue;
            }
            target_file.seek(offset);
            target_file.write(buf, read_bytes);
        }
        target_file.close();
    }
    return ErrorCode::OK;
}

int PatchMain::ToSourceLang(int dest_lang)
{
    return !dest_lang;
}

ErrorCode PatchMain::Patch(int dest_lang, bool check_md5, const QString& file_metas_path)
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

    // 3. do the actual patch
    ret = Convert(dest_lang, file_metas);

    return ret;
}
