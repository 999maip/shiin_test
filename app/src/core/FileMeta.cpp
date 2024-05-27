#include "FileMeta.h"

#include <QFile>
#include <QTextStream>

FileMeta::FileMeta() {}

ErrorCode FileMeta::LoadFileMetas(const char* filepath, FileMetas& file_metas)
{
    ErrorCode ret = ErrorCode::OK;

    QFile file(filepath);
    if (!file.open(QIODeviceBase::ReadOnly | QIODeviceBase::Text))
    {
        return ErrorCode::FILE_META_OPEN_ERROR;
    }

    file_metas.clear();

    QTextStream in(&file);
    // ignore the header
    in.readLine();

    while(!in.atEnd())
    {
        QString line = in.readLine();
        QStringList fields = line.split(" ");
        if (fields.length() != 6)
        {
            ret = ErrorCode::FILE_META_FORMAT_ERROR;
            break;
        }
        FileMeta file_meta;
        file_meta.filename_ = fields[0].toStdString();
        file_meta.filename_short_ = fields[1].toStdString();
        file_meta.md5_[0] = fields[2].toStdString();
        file_meta.md5_[1] = fields[3].toStdString();

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
