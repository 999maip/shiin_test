#include "mainwindow.h"
#include "./ui_mainwindow.h"

#include <QMessageBox>
#include <QImageReader>
#include <stdlib.h>
#include <QVideoWidget>
#include <QFileInfo>
#include <QDirIterator>
#include <io.h>
#include <QGraphicsOpacityEffect>
#include <QPropertyAnimation>
#include <QPainter>
#include <QTimer>
#include "core/ErrorCode.h"
#include "ui/ShiinButton.h"

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
    setWindowFlags(Qt::MSWindowsFixedSizeDialogHint);
    ui->setupUi(this);

    // initialize the buttons
    QShiinButton* btn_to_cn = findChild<QShiinButton*>("pushButton");
    if (btn_to_cn)
    {
        btn_to_cn->imgs[0] = QImage("image/shiin_btn_to_cn_d.png");
        btn_to_cn->imgs[1] = QImage("image/shiin_btn_to_cn_w.png");
        btn_to_cn->imgs[2] = QImage("image/shiin_btn_to_cn_r.png");
        btn_to_cn->imgs[3] = QImage("image/shiin_btn_to_cn_b.png");
    }

    QShiinButton* btn_to_jp = findChild<QShiinButton*>("pushButton_2");
    if (btn_to_jp)
    {
        btn_to_jp->imgs[0] = QImage("image/shiin_btn_to_jp_d.png");
        btn_to_jp->imgs[1] = QImage("image/shiin_btn_to_jp_w.png");
        btn_to_jp->imgs[2] = QImage("image/shiin_btn_to_jp_r.png");
        btn_to_jp->imgs[3] = QImage("image/shiin_btn_to_jp_b.png");
    }

    QShiinButton* btn_desc = findChild<QShiinButton*>("pushButton_3");
    if (btn_desc)
    {
        btn_desc->imgs[0] = QImage("image/shiin_btn_desc_d.png");
        btn_desc->imgs[1] = QImage("image/shiin_btn_desc_w.png");
        btn_desc->imgs[2] = QImage("image/shiin_btn_desc_r.png");
        btn_desc->imgs[3] = QImage("image/shiin_btn_desc_b.png");
    }

    QShiinButton* btn_exit = findChild<QShiinButton*>("pushButton_4");
    if (btn_exit)
    {
        btn_exit->imgs[0] = QImage("image/shiin_btn_exit_d.png");
        btn_exit->imgs[1] = QImage("image/shiin_btn_exit_w.png");
        btn_exit->imgs[2] = QImage("image/shiin_btn_exit_r.png");
        btn_exit->imgs[3] = QImage("image/shiin_btn_exit_b.png");
    }

    QTitleScreenBackground* bg_label = findChild<QTitleScreenBackground*>("label_2");

    static QTimer timer(this);
    connect(&timer, &QTimer::timeout, bg_label,  &QTitleScreenBackground::OnUpdate);
    connect(&timer, &QTimer::timeout, btn_to_cn, &QShiinButton::OnUpdate);
    connect(&timer, &QTimer::timeout, btn_to_jp, &QShiinButton::OnUpdate);
    connect(&timer, &QTimer::timeout, btn_desc,  &QShiinButton::OnUpdate);
    connect(&timer, &QTimer::timeout, btn_exit,  &QShiinButton::OnUpdate);
    timer.start(100);
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
    QMessageBox msgBox(error_msg.icon, error_msg.title,
                       error_msg.message + QString(patch_main_.extra_error_message_.c_str()));
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
