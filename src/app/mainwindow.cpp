#include "mainwindow.h"
#include "./ui_mainwindow.h"

#include <QMessageBox>
#include <stdlib.h>
#include <QVideoWidget>
#include <QFileInfo>
#include <QDirIterator>
#include <io.h>
#include "ErrorCode.h"

std::map<ErrorCode, ErrorMessage> MainWindow::error_message_map_ =
{
    {ErrorCode::OK, {QMessageBox::Icon::Information, "OK啦", "转化成功！"}},
    {ErrorCode::GAME_FILE_OPEN_ERROR, {QMessageBox::Icon::Critical, "出错啦",
                                       "无法打开相关游戏文件，请确认游戏文件存在且拥有访问权限。"}},
    {ErrorCode::PATCH_FILE_OPEN_ERROR, {QMessageBox::Icon::Critical, "出错啦",
                                        "补丁文件缺失!"}},
    {ErrorCode::FILE_META_OPEN_ERROR, {QMessageBox::Icon::Critical, "出错啦",
                                       "元数据信息缺失!"}},
    {ErrorCode::FILE_META_FORMAT_ERROR, {QMessageBox::Icon::Critical, "出错啦",
                                         "元数据格式错误!"}},
    {ErrorCode::FILE_META_DATA_ERROR, {QMessageBox::Icon::Critical, "出错啦",
                                       "元数据数值错误!"}},
    {ErrorCode::MD5_CHECK_ERROR, {QMessageBox::Icon::Critical, "出错啦",
                                  "补丁版本和游戏文件版本不一致，请尝试将游戏和补丁更新到最新版再试："}},
};

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)

{
    setWindowFlags(Qt::MSWindowsFixedSizeDialogHint | Qt::FramelessWindowHint);
    ui->setupUi(this);
}

MainWindow::~MainWindow()
{
    delete ui;
}


void MainWindow::on_pushButton_3_clicked()
{
    QMessageBox msgBox;
    msgBox.setIcon(QMessageBox::Icon::Information);
    msgBox.setWindowTitle("补丁说明");
    msgBox.setText("内部测试用。");
    msgBox.exec();
}

void MainWindow::on_pushButton_4_clicked()
{
    exit(0);
}

// to cn
void MainWindow::on_pushButton_clicked()
{
    findChild<QPushButton*>("pushButton")->setEnabled(false);
    findChild<QPushButton*>("pushButton_2")->setEnabled(false);
    findChild<QPushButton*>("pushButton_3")->setEnabled(false);
    findChild<QPushButton*>("pushButton_4")->setEnabled(false);

    ErrorCode ret = patch_main_.Patch(PatchMain::CN);

    findChild<QPushButton*>("pushButton")->setEnabled(true);
    findChild<QPushButton*>("pushButton_2")->setEnabled(true);
    findChild<QPushButton*>("pushButton_3")->setEnabled(true);
    findChild<QPushButton*>("pushButton_4")->setEnabled(true);

    ErrorMessage error_msg = error_message_map_[ret];
    QMessageBox msgBox(error_msg.icon, error_msg.title, error_msg.message);
    msgBox.exec();
    exit(0);
}


void MainWindow::on_pushButton_2_clicked()
{
    // to en/jp
    findChild<QPushButton*>("pushButton")->setEnabled(false);
    findChild<QPushButton*>("pushButton_2")->setEnabled(false);
    findChild<QPushButton*>("pushButton_3")->setEnabled(false);
    findChild<QPushButton*>("pushButton_4")->setEnabled(false);

    ErrorCode ret = patch_main_.Patch(PatchMain::EN_JP);

    findChild<QPushButton*>("pushButton")->setEnabled(true);
    findChild<QPushButton*>("pushButton_2")->setEnabled(true);
    findChild<QPushButton*>("pushButton_3")->setEnabled(true);
    findChild<QPushButton*>("pushButton_4")->setEnabled(true);

    ErrorMessage error_msg = error_message_map_[ret];
    QMessageBox msgBox(error_msg.icon, error_msg.title,
                       error_msg.message + QString(patch_main_.extra_error_message_.c_str()));
    msgBox.exec();
}
