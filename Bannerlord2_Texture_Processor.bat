@echo off
setlocal enabledelayedexpansion

:: Default width for Windows 7/8.1
set "width=80"
set "height=24"

:: Detect Windows 10/11 and set a wider console if applicable
ver | findstr /B /C:"[10." > nul
if %errorlevel% == 0 (
    set "width=120"
    set "height=30"
)

:: Set console size
mode con: cols=%width% lines=%height%

:: Main menu loop
:main_menu
    cls
    call :print_header "Bannerlord2 Texture Processor"
    echo.
    echo 1) Run Bannerlord2 Texture Processor
    echo 2) Install/Setup Requirements
    echo.

    set "selection="
    set /p "selection=Selection; Menu Options = 1-2, Exit Program = X: "

    if /i "%selection%"=="1" (
        call :run_main
        goto :main_menu
    )
    if /i "%selection%"=="2" (
        call :run_installer
        goto :main_menu
    )
    if /i "%selection%"=="x" (
        goto :eof
    )

    echo Invalid selection. Please try again.
    timeout /t 3 > nul
    goto :main_menu

:: Subroutine to run the main script
:run_main
    cls
    call :print_header "Running Main Script"
    echo.
    python mainScript.py
    echo.
    echo Press any key to return to the main menu.
    pause > nul
    exit /b

:: Subroutine to run the installer
:run_installer
    cls
    call :print_header "Running Installer/Setup"
    echo.
    python installer.py
    echo.
    echo Press any key to return to the main menu.
    pause > nul
    exit /b

:: Subroutine to print a separator line
:print_separator
    set "line="
    for /L %%i in (1, 1, %width%) do set "line=!line!#"
    set "line=!line:~0,%width%!"
    echo !line!
    exit /b

:: Subroutine to print a formatted header with a title
:print_header
    set "title=%~1"
    call :print_separator
    echo %title%
    call :print_separator
    exit /b
