# Climpt - Clipboard Prompt Manager

Легковесное кроссплатформенное приложение для хранения и быстрой вставки текстовых промптов через буфер обмена.

## Структура проекта
```bash
climpt/
├── .github/
│   └── workflows/
│       └── ci.yml
climpt/
├── main.py
├── storage.py
├── gui/
│   ├── main_frame.py
│   ├── edit_dialog.py
│   ├── prompt_card.py
│   ├── settings_dialog.py
│   └── tag_panel.py
├── config.py
├── app.py
├── hotkeys.py
├── utils.py
├── prompts.json
├── pixi.toml
├── README.md
├── .pylintrc
└── .gitignore
```

## 🚀 Быстрый старт

### Установка Pixi

Если у вас еще не установлен Pixi:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

### Установка зависимостей

```bash
pixi install
```

### Запуск приложения

```bash
pixi run start
```

### Сборка исполняемого файла

```bash
pixi run build
```

## 🎯 Горячие клавиши

- `Ctrl + Shift + P` — открыть окно Climpt
- `Ctrl + 1` — вставить первый промпт
- `Ctrl + 2` — вставить второй промпт

## 📁 Структура данных

Промпты хранятся в файле `prompts.json` в формате:

```json
{
  "prompts": [
    {
      "id": 1,
      "name": "Запрос на анализ",
      "content": "Проанализируй данные: ...",
      "tags": ["анализ", "LLM"]
    }
  ]
}
```

## 📝 О Climpt

**Climpt** (Clipboard Prompt Manager) — это инструмент для разработчиков, копирайтеров и всех, кто часто работает с шаблонами текста. Быстро вставляйте готовые промпты одним нажатием!