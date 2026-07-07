@echo off

if /i "%~1"=="setup" (
    echo Creating virtual environment and installing dependencies...

    if not exist .uvenv\Scripts\python.exe (
        py -3.13 -m venv .uvenv
    )
    if not exist .uvenv\Scripts\python.exe (
        py -3 -m venv .uvenv
    )
    if not exist .uvenv\Scripts\python.exe (
        python -m venv .uvenv
    )
    if not exist .uvenv\Scripts\python.exe (
        echo Error: bootstrap virtual environment was not created successfully.
        exit /b 1
    )

    set "INDEX_URL=https://pypi.org/simple/"
    set "PIP_CONFIG_FILE=nul"
    .uvenv\Scripts\python.exe -m pip install --index-url "%INDEX_URL%" --upgrade pip uv
    .uvenv\Scripts\uv.exe sync --python 3.13 --index-url "%INDEX_URL%" --index-strategy first-index
    goto :eof
)

if /i "%~1"=="run" (
    set "NO_CACHE_FLAG="
    if /i "%~2"=="--no-cache" set "NO_CACHE_FLAG=--no-cache"
    .venv\Scripts\python.exe -m itm_weeding.main input\books_1950-1990_book_infile.txt --students input\Uitleen_collega's.csv --staff input\Uitleen_2019-2026.csv %NO_CACHE_FLAG%
    goto :eof
)

if /i "%~1"=="run-concurrent" (
    .venv\Scripts\python.exe -m itm_weeding.main input\books_1950-1990_book_infile.txt --students input\Uitleen_collega's.csv --staff input\Uitleen_2019-2026.csv --concurrent
    goto :eof
)

echo Usage: run.bat setup ^| run ^| run-concurrent
exit /b 1
