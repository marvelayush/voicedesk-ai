from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue


def make_prop(name: str, value):
    prop = PropertyValue()
    prop.Name = name
    prop.Value = value
    return prop


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: lo_save_as_docx.py <input> <output>")
        return 2

    input_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()

    local_ctx = uno.getComponentContext()
    resolver = local_ctx.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local_ctx
    )

    ctx = None
    for _ in range(60):
        try:
            ctx = resolver.resolve("uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
            break
        except Exception:
            time.sleep(0.5)
    if ctx is None:
        print("could not connect to LibreOffice")
        return 1

    smgr = ctx.ServiceManager
    desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

    file_url = uno.systemPathToFileUrl(str(input_path))
    out_url = uno.systemPathToFileUrl(str(output_path))
    load_props = (
        make_prop("Hidden", True),
        make_prop("ReadOnly", False),
    )
    doc = desktop.loadComponentFromURL(file_url, "_blank", 0, load_props)
    if doc is None:
        print("could not open input")
        return 1

    save_props = (
        make_prop("FilterName", "MS Word 2007 XML"),
        make_prop("Overwrite", True),
    )
    doc.storeAsURL(out_url, save_props)
    doc.close(True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
