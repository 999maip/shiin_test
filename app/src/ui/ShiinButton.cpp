#include "ShiinButton.h"

#include <QPainter>
#include <random>

void QShiinButton::enterEvent(QEnterEvent *event)
{
    on_hover_ = true;
    // force update
    OnUpdate();
}

void QShiinButton::leaveEvent(QEvent *event)
{

    on_hover_ = false;
    // force update
    OnUpdate();
}

void QShiinButton::OnUpdate()
{
    static std::random_device rd;  // a seed source for the random number engine
    static std::mt19937 gen(rd()); // mersenne_twister_engine seeded with rd()

    // static std::vector<std::vector<int>> patterns = {
    //     {0, 0, 0, 0},
    //     {1, 0, 2, 0},
    //     {2, 0, 1, 0},
    //     {}
    // };

    QImage result_img = QImage(100, 30, QImage::Format_ARGB32_Premultiplied);
    QPainter painter(&result_img);
    painter.setCompositionMode(QPainter::CompositionMode_Source);
    painter.fillRect(result_img.rect(), Qt::transparent);
    if (on_hover_)
    {
        std::uniform_int_distribution<> distribx_or_y(0, 1);
        std::uniform_int_distribution<> distribx(-1, 1);
        std::uniform_int_distribution<> distriby(-1, 1);
        for (int i = 2; i <= 3; ++i)
        {
            int x_or_y = distribx_or_y(gen);
            painter.setCompositionMode(QPainter::CompositionMode_SourceOver);
            painter.setOpacity(1);
            if (x_or_y == 0)
            {
                painter.drawImage(distribx(gen), 0, imgs[i]);
            }
            else
            {
                painter.drawImage(0, distriby(gen), imgs[i]);
            }
        }

        painter.setCompositionMode(QPainter::CompositionMode_SourceOver);
        painter.setOpacity(1);
        painter.drawImage(0, 0, imgs[1]);
    }
    else
    {
        painter.setCompositionMode(QPainter::CompositionMode_SourceOver);
        painter.setOpacity(1);
        painter.drawImage(0, 0, imgs[0]);
    }
    painter.end();
    QPixmap pixmap = QPixmap::fromImage(result_img);

    this->setIcon(QIcon(pixmap));
    this->setIconSize(pixmap.rect().size());
}
