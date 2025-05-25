#include "TitleScreenBackground.h"

#include <QImageReader>
#include <QGraphicsOpacityEffect>
#include <QPropertyAnimation>
#include <QPainter>

void QTitleScreenBackground::Init()
{
    QImageReader reader("image/graphic_title.exg.png");
    reader.setAutoTransform(true);
    image = reader.read();

    img_tree = image.copy(0, 2176, 900, 450);
    img_bg = image.copy(1920, 1088, 1920, 1100);
    img_logo = image.copy(3690, 2176, 310, 520);

    spirits.push_back(image.copy(3400, 2190, 300, 800));
    spirits.push_back(image.copy(1800, 2200, 700, 800));
    spirits.push_back(image.copy(2580, 2190, 110, 300));
    spirits.push_back(image.copy(2800, 2190, 200, 500));
    spirits.push_back(image.copy(997, 2200, 700, 600));
    spirits.push_back(image.copy(3068, 2200, 300, 800));
}

void QTitleScreenBackground::OnUpdate()
{
    static std::vector<int> tree_opacities =
    {
        0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
        55, 60, 65, 70, 75, 80, 85, 90, 95, 100,
        95, 90, 85, 80, 75, 70, 65, 60, 55, 50,
        45, 40, 35, 30, 25, 20, 15, 10
    };
    static std::vector<int> spirit_opacities =
    {
        0, 20, 40, 60, 80, 100, 100, 100, 100, 100, 100,
        100, 100, 100, 100, 100, 100, 100, 100,
        100, 100, 100, 100, 100,
        100, 100, 100, 100, 100, 80, 60, 40, 20
    };
    static std::vector<std::pair<int, int>> spirit_pos = {
        {1050, 240}, {1105, 125}, {1015, 357}, {740, 288},
        {383, 262}, {1600, 275}
    };

    static int idx_tree_opacities = 0;
    static int idx_spirit_opacities = 0;
    static int idx_spirit = 0;

    QPixmap pixmap;
    QImage result_img = QImage(1920, 1100, QImage::Format_ARGB32_Premultiplied);
    QPainter painter(&result_img);

    painter.setCompositionMode(QPainter::CompositionMode_DestinationOver);
    painter.setOpacity(1);
    painter.drawImage(0, 0, img_bg);

    painter.setOpacity(tree_opacities[idx_tree_opacities] / 100.0f);
    idx_tree_opacities++;
    if (idx_tree_opacities >= tree_opacities.size())
    {
        idx_tree_opacities = 0;
    }
    painter.setCompositionMode(QPainter::CompositionMode_SourceOver);
    painter.drawImage(473, 0, img_tree);

    idx_spirit_opacities++;
    if (idx_spirit_opacities >= spirit_opacities.size())
    {
        idx_spirit_opacities = 0;
        idx_spirit++;
        if (idx_spirit >= spirits.size())
        {
            idx_spirit = 0;
        }
    }
    painter.setCompositionMode(QPainter::CompositionMode_SourceOver);
    painter.setOpacity(spirit_opacities[idx_spirit_opacities] / 100.0f);
    painter.drawImage(spirit_pos[idx_spirit].first, spirit_pos[idx_spirit].second, spirits[idx_spirit]);

    painter.setCompositionMode(QPainter::CompositionMode_SourceOver);
    painter.setOpacity(1.0f);
    painter.drawImage(810, 120, img_logo);

    painter.end();

    double scale_factor = 2.84;
    result_img = result_img.scaled(static_cast<int>(result_img.width() / scale_factor),
                    static_cast<int>(result_img.height() / scale_factor), Qt::KeepAspectRatio);


    pixmap.convertFromImage(result_img);
    this->setScaledContents(true);
    this->setPixmap(pixmap);
    this->resize(pixmap.size());
}
