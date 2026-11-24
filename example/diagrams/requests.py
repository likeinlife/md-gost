"""Условное распределение запросов к базе знаний по направлениям."""

sns.set_theme(style="whitegrid", font="DejaVu Sans", font_scale=1.0)
fig, ax = plt.subplots(figsize=(7, 3.2))
categories = ["Поиск", "Просмотр", "Добавление", "Обновление"]
requests = [128, 96, 57, 41]
sns.barplot(x=requests, y=categories, hue=categories, palette="crest", legend=False, ax=ax)
ax.set(xlabel="Число запросов за месяц", ylabel="", xlim=(0, 145))
ax.grid(axis="y", visible=False)
for bar in ax.containers:
    ax.bar_label(bar, padding=4)
sns.despine(ax=ax, left=True)
fig.tight_layout()
