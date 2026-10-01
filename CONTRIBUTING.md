# Участие в разработке

1. Установите Python 3.12.
2. Создайте ветку от `main`.
3. Запустите `run-dev.ps1`.
4. Перед pull request выполните:

```powershell
.\.venv\Scripts\ruff.exe check src tests main.py
.\.venv\Scripts\pytest.exe
```

Не добавляйте Discord Client Secret, Bot Token, токены Яндекса или личные журналы.