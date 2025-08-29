@echo off
echo ========================================
echo LaCentrale Simple Scheduler
echo ========================================
echo Method: Direct function call
echo Schedule: Every 60 minutes
echo Press Ctrl+C to stop
echo ========================================
echo.

cd /d "%~dp0"
python simple_scheduler.py

echo.
echo Scheduler stopped.
pause
