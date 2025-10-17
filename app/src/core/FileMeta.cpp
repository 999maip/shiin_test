#include "FileMeta.h"

#include <QFile>
#include <QDir>
#include <QTextStream>

FileMeta::FileMeta() {}

const QString FileMeta::DEFAULT_FILEPATH = "file_metas.txt";
const QString FileMeta::PATCH_ROOT_DIR = "diff_folder_5A7A59794464";

ErrorCode FileMeta::LoadFileMetas(const QString& filepath, FileMetas& file_metas)
{
    ErrorCode ret = ErrorCode::OK;

    QFile file(QDir(PATCH_ROOT_DIR).filePath(filepath));
    if (!file.open(QIODeviceBase::ReadOnly | QIODeviceBase::Text))
    {
        return ErrorCode::FILE_META_OPEN_ERROR;
    }

    file_metas.clear();

    QTextStream in(&file);
    // ignore the header part
    in.readLine();
    in.readLine();
    in.readLine();

    while(!in.atEnd())
    {
        QString line = in.readLine();
        QStringList fields = line.split("|");
        if (fields.length() != 6)
        {
            ret = ErrorCode::FILE_META_FORMAT_ERROR;
            break;
        }
        FileMeta file_meta;
        file_meta.filename_short_ = fields[0];
        file_meta.filename_ = fields[1];
        file_meta.md5_[0] = fields[2];
        file_meta.md5_[1] = fields[3];

        bool convert_ok = false;
        file_meta.size_[0] = fields[4].toLongLong(&convert_ok, 16);
        if (!convert_ok)
        {
            ret = ErrorCode::FILE_META_DATA_ERROR;
            break;
        }
        file_meta.size_[1] = fields[5].toLongLong(&convert_ok, 16);
        if (!convert_ok)
        {
            ret = ErrorCode::FILE_META_DATA_ERROR;
            break;
        }

        file_metas.push_back(file_meta);
    }

    return ret;
}


PatchInfo FileMeta::LoadPatchInfo(QString filepath)
{
    QFile meta_file(QDir(PATCH_ROOT_DIR).filePath(filepath));
    PatchInfo patch_info;
    if (!meta_file.open(QIODeviceBase::ReadOnly | QIODeviceBase::Text))
    {
        return patch_info;
    }

    QTextStream in(&meta_file);
    patch_info.version_number_ = in.readLine();
    patch_info.description_ = in.readLine();

    return patch_info;
}
