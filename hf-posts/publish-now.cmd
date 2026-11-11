@echo off
chcp 65001 >nul
title Publish LLM test reports to Hugging Face
echo.
echo  Публикация тестов в обсуждения Hugging Face.
echo  Токен вводится здесь и нигде не сохраняется на диск.
echo.
echo  Нужен токен с правом Write: https://huggingface.co/settings/tokens
echo  Рекомендуется fine-grained на 1 день, только Discussions.
echo.
set /p HF_TOKEN=Вставь токен и нажми Enter: 
if "%HF_TOKEN%"=="" (
  echo Токен не введён, выходим.
  pause
  exit /b 1
)
cd /d "%~dp0"
python publish.py --confirm
echo.
echo  Готово. После проверки отзови токен: https://huggingface.co/settings/tokens
set HF_TOKEN=
pause
