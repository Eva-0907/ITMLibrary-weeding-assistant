@echo off

if /i "%~1"=="setup" (
    if exist .venv\Scripts\python.exe goto :install

    echo Creating virtual environment...
    py -3.13 -m venv .venv
    if not exist .venv\Scripts\python.exe (
        py -3 -m venv .venv
    )
    if not exist .venv\Scripts\python.exe (
        python -m venv .venv
    )

    if not exist .venv\Scripts\python.exe (
        echo Error: virtual environment Python was not created successfully.
        exit /b 1
    )

    :install
    echo Syncing dependencies...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install uv
    .venv\Scripts\python.exe -m uv sync --python 3.13
    goto :eof
)

if /i "%~1"=="run" (
    .venv\Scripts\python.exe -m itm_weeding.main input\books_1950-1990_book_infile.txt --students input\Uitleen_collega's.csv --staff input\Uitleen_2019-2026.csv
    goto :eof
)

if /i "%~1"=="run-concurrent" (
    .venv\Scripts\python.exe -m itm_weeding.main input\books_1950-1990_book_infile.txt --students input\Uitleen_collega's.csv --staff input\Uitleen_2019-2026.csv --concurrent
    goto :eof
)

echo Usage: run.bat setup ^| run ^| run-concurrent
exit /b 1
