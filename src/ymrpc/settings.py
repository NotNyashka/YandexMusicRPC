from __future__ import annotations

from tkinter import BooleanVar, IntVar, StringVar, Tk, messagebox, ttk

from .config import Config, save_config

SOURCE_LABELS = {
    "Автоматически": "auto",
    "Только приложение Яндекс Музыки": "yandex",
    "Только браузер": "browser",
}
STYLE_LABELS = {
    "Подробный": "detailed",
    "Минималистичный": "minimal",
    "Приватный": "private",
}


def show_settings(config: Config) -> bool:
    root = Tk()
    root.title("Настройки YandexMusicRPC")
    root.geometry("520x420")
    root.resizable(False, False)

    frame = ttk.Frame(root, padding=22)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="YandexMusicRPC", font=("Segoe UI", 17, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Настройте источник музыки и карточку Discord.").pack(
        anchor="w", pady=(2, 18)
    )

    source_label = next(
        (label for label, value in SOURCE_LABELS.items() if value == config.source_mode),
        "Автоматически",
    )
    source = StringVar(value=source_label)
    ttk.Label(frame, text="Источник музыки").pack(anchor="w")
    ttk.Combobox(
        frame,
        textvariable=source,
        values=list(SOURCE_LABELS),
        state="readonly",
    ).pack(fill="x", pady=(4, 14))

    style_label = next(
        (label for label, value in STYLE_LABELS.items() if value == config.presence_style),
        "Подробный",
    )
    style = StringVar(value=style_label)
    ttk.Label(frame, text="Оформление Discord").pack(anchor="w")
    ttk.Combobox(
        frame,
        textvariable=style,
        values=list(STYLE_LABELS),
        state="readonly",
    ).pack(fill="x", pady=(4, 14))

    pause_minutes = IntVar(value=max(1, config.paused_timeout_seconds // 60))
    ttk.Label(frame, text="Скрывать статус после паузы, минут").pack(anchor="w")
    ttk.Spinbox(frame, from_=1, to=60, textvariable=pause_minutes).pack(fill="x", pady=(4, 12))

    autostart = BooleanVar(value=config.autostart)
    show_button = BooleanVar(value=config.show_button)
    show_album = BooleanVar(value=config.show_album)
    ttk.Checkbutton(frame, text="Запускать вместе с Windows", variable=autostart).pack(anchor="w")
    ttk.Checkbutton(frame, text="Показывать кнопку «Открыть трек»", variable=show_button).pack(
        anchor="w"
    )
    ttk.Checkbutton(frame, text="Показывать альбом рядом с исполнителем", variable=show_album).pack(
        anchor="w"
    )

    result = {"saved": False}

    def save() -> None:
        try:
            minutes = min(60, max(1, int(pause_minutes.get())))
        except (ValueError, TypeError):
            messagebox.showerror("Ошибка", "Введите время паузы от 1 до 60 минут.")
            return
        config.source_mode = SOURCE_LABELS[source.get()]
        config.presence_style = STYLE_LABELS[style.get()]
        config.paused_timeout_seconds = minutes * 60
        config.autostart = autostart.get()
        config.show_button = show_button.get()
        config.show_album = show_album.get()
        save_config(config)
        result["saved"] = True
        root.destroy()

    buttons = ttk.Frame(frame)
    buttons.pack(fill="x", side="bottom", pady=(18, 0))
    ttk.Button(buttons, text="Отмена", command=root.destroy).pack(side="right")
    ttk.Button(buttons, text="Сохранить", command=save).pack(side="right", padx=(0, 8))
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()
    return result["saved"]
