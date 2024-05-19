#pragma once

#include <QMessageBox>
#include <QString>

struct ErrorMessage
{
    QMessageBox::Icon icon;
    QString title;
    QString message;
};
