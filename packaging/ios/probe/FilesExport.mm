// SPDX-License-Identifier: GPL-3.0-or-later
#include "FilesExport.h"
#include <QWidget>
#import <UIKit/UIKit.h>
#import <objc/runtime.h>

@interface ProbeExportDelegate : NSObject <UIDocumentPickerDelegate, UIAdaptivePresentationControllerDelegate> {
@public
    std::function<void(bool, QString)> completion;
}
- (void)finish:(BOOL)success message:(QString)message;
@end

@implementation ProbeExportDelegate
- (void)finish:(BOOL)success message:(QString)message
{
    // Both picker cancellation and interactive dismissal may be reported.
    if (completion) {
        auto callback = std::move(completion);
        completion = {};
        callback(success, message);
    }
}
- (void)documentPicker:(UIDocumentPickerViewController *)controller didPickDocumentsAtURLs:(NSArray<NSURL *> *)urls
{
    Q_UNUSED(controller);
    [self finish:urls.count > 0 message:QStringLiteral("Files export completed")];
}
- (void)documentPickerWasCancelled:(UIDocumentPickerViewController *)controller
{
    Q_UNUSED(controller);
    [self finish:NO message:QStringLiteral("Files export cancelled")];
}
- (void)presentationControllerDidDismiss:(UIPresentationController *)controller
{
    Q_UNUSED(controller);
    [self finish:NO message:QStringLiteral("Files export dismissed")];
}
@end

void exportToFiles(QWidget *parent, const QString &localPath,
                   std::function<void(bool, QString)> completion)
{
    UIView *view = (__bridge UIView *)(reinterpret_cast<void *>(parent->window()->winId()));
    UIViewController *presenter = view.window.rootViewController;
    while (presenter.presentedViewController) presenter = presenter.presentedViewController;
    if (!presenter || presenter.isBeingDismissed) {
        completion(false, QStringLiteral("No available iOS window for Files export"));
        return;
    }
    NSURL *url = [NSURL fileURLWithPath:localPath.toNSString()];
    auto *picker = [[UIDocumentPickerViewController alloc] initForExportingURLs:@[url] asCopy:YES];
    auto *delegate = [ProbeExportDelegate new];
    delegate->completion = std::move(completion);
    picker.delegate = delegate;
    picker.modalPresentationStyle = UIModalPresentationFormSheet;
    picker.presentationController.delegate = delegate;
    // UIKit's delegate property is weak. Keep it alive for the picker's lifetime.
    static char delegateKey;
    objc_setAssociatedObject(picker, &delegateKey, delegate, OBJC_ASSOCIATION_RETAIN_NONATOMIC);
    [presenter presentViewController:picker animated:YES completion:nil];
}
