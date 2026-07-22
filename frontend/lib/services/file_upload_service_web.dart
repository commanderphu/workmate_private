import 'dart:async';
import 'dart:js_interop';

import 'package:web/web.dart' as web;

import 'file_upload_service_stub.dart';

/// Web implementation of FileUploadService using package:web (replaces dart:html)
class FileUploadService {
  Future<FileUploadResult?> pickFromCamera() async {
    return _pickFile(useCamera: true);
  }

  Future<FileUploadResult?> pickFromGallery() async {
    return _pickFile(useCamera: false);
  }

  Future<FileUploadResult?> pickFile() async {
    return _pickFile(useCamera: false, accept: 'image/*,.pdf');
  }

  Future<FileUploadResult?> _pickFile({
    bool useCamera = false,
    String accept = 'image/*,.pdf',
  }) async {
    final completer = Completer<FileUploadResult?>();

    final input = web.HTMLInputElement();
    input.type = 'file';
    input.accept = accept;
    if (useCamera) {
      input.setAttribute('capture', 'environment');
    }

    input.addEventListener(
      'change',
      (web.Event _) {
        final files = input.files;
        if (files == null || files.length == 0) {
          completer.complete(null);
          return;
        }

        final file = files.item(0)!;
        final reader = web.FileReader();

        reader.addEventListener(
          'loadend',
          (web.Event _) {
            final result = reader.result;
            if (result == null) {
              completer.complete(null);
              return;
            }
            final bytes = (result as JSArrayBuffer).toDart.asUint8List();
            completer.complete(
              FileUploadResult(bytes: bytes, filename: file.name),
            );
          }.toJS,
        );

        reader.addEventListener(
          'error',
          ((web.Event _) => completer.complete(null)).toJS,
        );

        reader.readAsArrayBuffer(file);
      }.toJS,
    );

    input.click();
    return completer.future;
  }
}
