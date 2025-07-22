# Install tesseract

This role installs tesseract OCR with the default configurations

## Usage

```yaml
- ansible.builtin.import_role:
    name: dataiku.dss.install_tesseract
  become: true
  become_user: dataiku
  vars:
    force_install: true
```

If using the role from Fleet Manager:

```yaml
- ansible.builtin.import_role:
    name: dataiku.dss.install_tesseract
  become: true
  become_user: dataiku
  vars:
    force_install: "{{ dataiku_dss_was_installed or dataiku_dss_was_upgraded }}"
```

## Expected behavior

This role installs tesseract OCR, along with leptonica and tessdata.
They are compiled from source and then installed:
- `/data/dataiku/opt/lib` -> The default directory where tesseract lives
- `/data/dataiku/opt/lib` -> The default directory where leptonica lives
- `/data/dataiku/opt/share/tessdata` -> The default directory where tessdata lives

All these configurations can be overridden by providing `tesseract_output_dir`, `leptonica_output_dir` and `tessdata_output_dir`

## Available inputs

This role accepts the following inputs

| Input                       | Required | Type    | Default                                                                                                                                                     | Comment                                                              |
|-----------------------------|----------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| force_install               | false    | bool    | false                                                                                                                                                       | Whether to force reinstallation of tesseract, leptonica and tessdata |
| keep_tmp_directory          | false    | bool    | false                                                                                                                                                       | Whether to keep the tmp directory after installation                 |
| archive_output              | false    | str     | "/data/dataiku/tmp"                                                                                                                                         | Path where the temporary files are stored                            |
| compilation_output          | false    | str     | "/data/dataiku/opt"                                                                                                                                         | Path where the installed software lives                              |
| leptonica_version           | false    | number  | 1.83.1                                                                                                                                                      | Leptonica version to install                                         |
| leptonica_archive_source    | false    | str     | "https://github.com/DanBloomberg/leptonica/releases/download/{{ leptonica_version }}/leptonica-{{ leptonica_version }}.tar.gz"                              | Leptonica archive source                                             |
| leptonica_unarchive_options | false    | list    | []                                                                                                                                                          | Options used while unarchiving leptonica                             |
| leptonica_unarchive_prefix  | false    | str     | "{{ archive_output }}"                                                                                                                                      | Path to unarchive Leptonica                                          |
| leptonica_compile_env_vars  | false    | object  | {"LANG": "en_US.utf-8", "LC_ALL": "en_US.utf-8"}                                                                                                            | Environment variables used when compiling Leptonica                  |
| leptonica_compile_options   | false    | str     | "--with-zlib --with-jpeg --with-libwebp --with-libtiff --with-libpng"                                                                                       | Options used when compiling Leptonica                                |
| leptonica_output_dir        | false    | str     | "{{ compilation_output }}"                                                                                                                                  | Path to store Leptonica after compilation                            |
| leptonica_state_file        | false    | str     | "{{ leptonica_output_dir }}/leptonica-install.txt"                                                                                                          | Path to store the state of the Leptonica installation                |
| tessdata_version            | false    | number  | 4.1.0                                                                                                                                                       | Tessdata version to install                                          |
| tessdata_archive_source     | false    | str     | "https://github.com/tesseract-ocr/tessdata/archive/refs/tags/{{ tessdata_version }}.tar.gz"                                                                 | Tessdata archive source                                              |
| tessdata_unarchive_options  | false    | list    | ["--strip-components=1", "--exclude=configs", "--exclude=pdf.ttf"]                                                                                          | Options used while unarchiving Tessdata                              |
| tessdata_output_dir         | false    | str     | "{{ compilation_output }}/share/tessdata"                                                                                                                   | Path to unarchive Tessdata                                           |
| tesseract_version           | false    | number  | 5.3.3                                                                                                                                                       | Tesseract version to install                                         |
| tesseract_archive_source    | false    | str     | "https://github.com/tesseract-ocr/tesseract/archive/refs/tags/{{ tesseract_version }}.tar.gz"                                                               | Tesseract archive source                                             |
| tesseract_unarchive_options | false    | list    | []                                                                                                                                                          | Options used while unarchiving Tesseract                             |
| tesseract_unarchive_prefix  | false    | str     | "{{ archive_output }}"                                                                                                                                      | Path to unarchive Tesseract                                          |
| tesseract_compile_env_vars  | false    | object  | {"LANG": "en_US.utf-8", "LC_ALL": "en_US.utf-8", "LIBLEPT_HEADERSDIR": "{{ leptonica_output_dir }}", "PKG_CONFIG_PATH": "/data/dataiku/opt/lib/pkgconfig/"} | Environment variables used when compiling Tesseract                  |
| tesseract_compile_options   | false    | str     | null                                                                                                                                                        | Options used when compiling Tesseract                                |
| tesseract_output_dir        | false    | str     | "{{ compilation_output }}"                                                                                                                                  | Path to store Tesseract after compilation                            |