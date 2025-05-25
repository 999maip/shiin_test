#ifndef TITLESCREENBACKGROUND_H
#define TITLESCREENBACKGROUND_H

#include <QLabel>
#include <vector>

class QTitleScreenBackground : public QLabel
{
    Q_OBJECT
public:
    QTitleScreenBackground(QWidget* widget) : QLabel(widget)
    {
        Init();
    }
public slots:
    void OnUpdate();
public:
    void Init();
private:
    enum SPIRIT_IDX
    {
        BRIDE3 = 0,
        LIGHT2 = 1,
        BRIDE1 = 2,
        BRIDE2 = 3,
        LIGHT1 = 4,
        SHIMIO = 5,
    };
    int spirit_opacity = 100;
    QImage image;
    QImage img_bg;
    QImage img_tree;
    QImage img_logo;
    std::vector<QImage> spirits;
};

#endif // TITLESCREENBACKGROUND_H
