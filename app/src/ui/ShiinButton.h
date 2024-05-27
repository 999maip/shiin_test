#pragma once

#include <QPushButton>

class QShiinButton : public QPushButton
{
    Q_OBJECT
public:
    QShiinButton(QWidget* widget) : QPushButton(widget)
    {
    }
protected:
    virtual void enterEvent(QEnterEvent *event) override;
    virtual void leaveEvent(QEvent *event) override;
public:
    // 0:Default 1:White 2:Red 3:Blue
    QImage imgs[4];
private:
    bool on_hover_ = false;
public slots:
    void OnUpdate();
};
