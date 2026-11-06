# orca-slicer — https://github.com/OrcaSlicer/OrcaSlicer

[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL--3.0--only-blue.svg)](https://github.com/OrcaSlicer/OrcaSlicer/blob/master/LICENSE.txt)

Advanced 3D printing slicer: it turns the models of a printer into the
G-code that the printer runs.

A fork of PrusaSlicer with improved supports, better compatibility with
the printers of other brands (Bambu Lab, Creality, Elegoo, …) and a few
extra features, like the calibration and the print time estimation of
the filament.

## Setup

Nothing to do — the application is installed with its desktop entry,
its icon and its data:

```sh
sudo dnf install orca-slicer
```

Then launch it from the menu of the desktop, or with:

```sh
orca-slicer
```

It also opens the models of the printer directly, and the command line
can slice them without the graphical interface:

```sh
orca-slicer --slice 0 --outputdir ~/gcode model.stl
```

## Files

| File | Purpose |
|---|---|
| `orca-slicer` | The launcher of the application |
| `/usr/libexec/orca-slicer/bin/orca-slicer` | The binary — the graphical interface and the command line interface |
| `/usr/libexec/orca-slicer/resources` | The data of the application: the profiles of the printers and of the filaments, the shaders, the icons and the help |
| `com.orcaslicer.OrcaSlicer.desktop` | The desktop entry |
| `com.orcaslicer.OrcaSlicer.metainfo.xml` | The AppStream metadata |
| `com.orcaslicer.OrcaSlicer.xml` | The file types of the models that the application opens (OBJ and AMF) |

## Notes

The application is built from the AppImage published by upstream: the
binary and the data are the very same ones the AppImage ships. It is
installed under `/usr/libexec` because the application looks for its
data in the `resources` directory next to the `bin` directory that holds
the binary — the layout of the AppImage is kept, so the application
finds its data wherever it is installed.

The libraries that the AppImage bundles (libexpat, liblzma, libmspack
and zlib) are not shipped: the ones of the system are used instead.
