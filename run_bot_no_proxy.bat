@echo off
echo 🤖 Starting Bot Without Proxy...
echo.

set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=

echo 🧹 Cleared all proxy settings
echo.

python direct_polling.py

pause