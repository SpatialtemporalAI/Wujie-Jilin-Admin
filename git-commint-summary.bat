@echo off
chcp 65001 >nul
:: 获取今天日期 yyyy-MM-dd
for /f "delims=" %%t in ('powershell -Command "(Get-Date).AddDays(-1).ToString('yyyy-MM-dd')"') do set YESTERDAY=%%t

for /f "delims=" %%t in ('powershell -Command "(Get-Date).ToString('yyyy-MM-dd')"') do set TODAY=%%t
:: 获取明天日期
for /f "delims=" %%n in ('powershell -Command "(Get-Date).AddDays(1).ToString('yyyy-MM-dd')"') do set TOMORROW=%%n

set OUT_FILE=git_commit_summary.txt
echo ==============================================
echo 正在导出 %TODAY% 当日Git提交记录
echo 输出文件：%OUT_FILE%
echo ==============================================
echo.

echo ====================== %TODAY%===================== >> %OUT_FILE%

:: 执行git log，过滤合并提交，输出到文件
git log --since="%YESTERDAY%" --until="%TOMORROW%" --pretty="%%s" --date=short --no-merges >> %OUT_FILE%

echo. >> %OUT_FILE%
echo. >> %OUT_FILE%

echo.
echo 导出完成！
echo 路径：%cd%\%OUT_FILE%
pause