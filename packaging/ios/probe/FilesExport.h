// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <QString>
#include <functional>
class QWidget;
void exportToFiles(QWidget *parent, const QString &localPath,
                   std::function<void(bool, QString)> completion);
