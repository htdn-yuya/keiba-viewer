@echo off
chcp 65001 >nul
setlocal

echo ===================================================
echo  keiba-viewer 自動更新 & GitHub プッシュ処理
echo ===================================================

set "SRC_JSON=C:\keiba\keiba_pipeline\reports\latest_prediction.json"
set "APP_DIR=C:\Streamlit_app"

:: 1. コピー元ファイルの存在確認
if not exist "%SRC_JSON%" (
    echo [ERROR] 予測JSONファイルが見つかりません:
    echo "%SRC_JSON%"
    goto FAILED
)

:: 2. 作業ディレクトリへ移動
cd /d "%APP_DIR%"
if errorlevel 1 (
    echo [ERROR] ディレクトリの移動に失敗しました: %APP_DIR%
    goto FAILED
)

:: 3. 最新の JSON ファイルをコピー
echo.
echo [1/4] 最新予測JSONをコピー中...
copy /y "%SRC_JSON%" ".\latest_prediction.json" >nul
if errorlevel 1 (
    echo [ERROR] JSONファイルのコピーに失敗しました。
    goto FAILED
)
echo コピー完了: latest_prediction.json

:: 4. build_html.py を実行して index.html を再生成
echo.
echo [2/4] index.html をビルド中...
python build_html.py
if errorlevel 1 (
    echo [ERROR] build_html.py の実行中にエラーが発生しました。
    goto FAILED
)

:: 5. Git ステージング & 差分確認
echo.
echo [3/4] 差分の確認およびコミット処理中...
git add index.html build_html.py

git diff --cached --quiet
if not errorlevel 1 (
    echo [INFO] 前回のファイルから変更がありませんでした。プッシュをスキップします。
    goto SUCCESS
)

:: 日時を取得してコミット
set "TIMESTAMP=%DATE% %TIME:~0,8%"
git commit -m "Update prediction viewer: %TIMESTAMP%"
if errorlevel 1 (
    echo [ERROR] git commit に失敗しました。
    goto FAILED
)

:: 6. GitHub へプッシュ
echo.
echo [4/4] GitHub (mainブランチ) へプッシュ中...
git push origin main
if errorlevel 1 (
    echo [ERROR] git push に失敗しました。ネットワークや認証を確認してください。
    goto FAILED
)

:SUCCESS
echo.
echo ===================================================
echo  すべての処理が正常に完了しました！
echo  公開URL (1〜2分で自動反映):
echo  https://htdn-yuya.github.io/keiba-viewer/
echo ===================================================
goto END

:FAILED
echo.
echo ===================================================
echo  処理が中断されました。上記のエラーを確認してください。
echo ===================================================

:END
pause