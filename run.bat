@echo off

if /i "%~1"=="setup" (
    echo Creating virtual environment and installing dependencies...

    if not exist .uvenv\Scripts\python.exe (
        python -m venv .uvenv
    )
    if not exist .uvenv\Scripts\python.exe (
        echo Error: bootstrap virtual environment was not created successfully.
        exit /b 1
    )

    .uvenv\Scripts\python.exe -m pip install  --upgrade pip uv
    .uvenv\Scripts\uv.exe sync --python 3.13 --index-strategy first-index
    goto :eof
)

if /i "%~1"=="run" (
    if /i "%~2"=="--no-cache" (
        .venv\Scripts\python.exe -m itm_weeding.main input\books_1950-1990_book_infile.txt --students input\Uitleen_collega's.csv --staff input\Uitleen_2019-2026.csv --no-cache
    ) else (
        .venv\Scripts\python.exe -m itm_weeding.main input\books_1950-1990_book_infile.txt --students input\Uitleen_collega's.csv --staff input\Uitleen_2019-2026.csv
    )
    goto :eof
)

if /i "%~1"=="run-concurrent" (
    .venv\Scripts\python.exe -m itm_weeding.main input\books_1950-1990_book_infile.txt --students input\Uitleen_collega's.csv --staff input\Uitleen_2019-2026.csv --concurrent %2 %3 %4 %5 %6 %7 %8 %9
    goto :eof
)

echo Usage: run.bat setup ^| run ^| run-concurrent
exit /b 1
