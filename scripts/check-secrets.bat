@echo off
REM Security check script for Windows
REM Run this before pushing to GitHub

echo 🔍 SECURITY CHECK: Scanning for sensitive files and data...

set ERRORS=0

echo 1. Checking for tracked sensitive files...
git ls-files | findstr /R "\.db$ \.sqlite$ \.sqlite3$ \.env$ \.pem$ \.key$ \.crt$ \.cert$" | findstr /V "\.example" | findstr /V "\.production$" > temp_sensitive.txt 2>NUL
if exist temp_sensitive.txt (
    for /f %%i in ('type temp_sensitive.txt ^| find /v /c ""') do set FILE_COUNT=%%i
    if not !FILE_COUNT!==0 (
        echo ❌ DANGER: Sensitive files found in Git:
        type temp_sensitive.txt
        set /a ERRORS=!ERRORS!+1
    )
    del temp_sensitive.txt
)

echo 2. Checking for .env files are ignored...
git ls-files | findstr "\.env$" > temp_env.txt 2>NUL
if exist temp_env.txt (
    for /f %%i in ('type temp_env.txt ^| find /v /c ""') do set ENV_COUNT=%%i
    if not !ENV_COUNT!==0 (
        echo ❌ .env files are tracked (they should be ignored):
        type temp_env.txt
        set /a ERRORS=!ERRORS!+1
    )
    del temp_env.txt
)

echo 3. Checking for database files...
dir /s /b *.db *.sqlite *.sqlite3 2>NUL | findstr /V "node_modules" | findstr /V ".git" > temp_db.txt 2>NUL
if exist temp_db.txt (
    for /f %%i in ('type temp_db.txt ^| find /v /c ""') do set DB_COUNT=%%i
    if not !DB_COUNT!==0 (
        echo ❌ Database files found (should not be committed):
        type temp_db.txt
        set /a ERRORS=!ERRORS!+1
    )
    del temp_db.txt
)

echo 4. Checking .gitignore exists and covers common patterns...
if not exist .gitignore (
    echo ❌ No .gitignore file found!
    set /a ERRORS=!ERRORS!+1
) else (
    findstr "\.env" .gitignore >NUL || (
        echo ⚠️ WARNING: .gitignore doesn't include .env files
    )
    findstr "\.db" .gitignore >NUL || (
        echo ⚠️ WARNING: .gitignore doesn't include database files
    )
)

echo.
echo ==========================================
if %ERRORS%==0 (
    echo ✅ SECURITY CHECK PASSED
    echo ✅ No sensitive data found
    echo ✅ Repository is safe to push to GitHub
) else (
    echo ❌ SECURITY CHECK FAILED
    echo ❌ Found %ERRORS% critical issues
    echo 🚨 DO NOT PUSH until issues are resolved!
    echo.
    echo To fix:
    echo 1. Remove sensitive files: git rm --cached ^<file^>
    echo 2. Add to .gitignore and commit
    echo 3. Rotate any exposed secrets
    echo 4. Re-run this check
    pause
    exit /b 1
)
echo ==========================================
pause