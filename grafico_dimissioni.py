import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# ---- Dati campagna ----
is_obtained = 35.88
is_lost_rank = 46.86
is_lost_budget = 17.27

kpis = [
    ("Impressioni", "15.104"),
    ("Clic", "870"),
    ("CTR", "5,76%"),
    ("CPC medio", "€2,49"),
    ("Chiamate", "93,77"),
    ("Tasso conv.", "10,78%"),
    ("Costo/chiamata", "€23,10"),
    ("Costo", "€2.166"),
]

fig = plt.figure(figsize=(12, 6.6), dpi=160)
fig.patch.set_facecolor("white")
fig.suptitle("SEARCH | MILANO | DIMISSIONI | CHIAMATA",
             fontsize=16, fontweight="bold", y=0.975)
fig.text(0.5, 0.917, "Analisi campagna a chiamata  ·  1–21 giugno 2026",
         ha="center", fontsize=10.5, color="#666666")

# ---- Donut: quota impressioni ----
ax1 = fig.add_axes([0.03, 0.10, 0.43, 0.70])
sizes = [is_obtained, is_lost_rank, is_lost_budget]
labels = ["Intercettata", "Persa per ranking", "Persa per budget"]
colors = ["#2E9E5B", "#E4572E", "#BFC4CC"]
wedges, _ = ax1.pie(
    sizes, colors=colors, startangle=90, counterclock=False,
    wedgeprops=dict(width=0.40, edgecolor="white", linewidth=2.5),
)
ax1.text(0, 0.10, "35,88%", ha="center", va="center",
         fontsize=27, fontweight="bold", color="#2E9E5B")
ax1.text(0, -0.20, "quota impressioni\nintercettata", ha="center", va="center",
         fontsize=10, color="#555555")
ax1.set_title("Quota impressioni: usi solo ~1/3 della domanda",
              fontsize=12.5, fontweight="bold", pad=16)
ax1.legend(
    wedges,
    [f"{l}  —  {s:.2f}%".replace(".", ",") for l, s in zip(labels, sizes)],
    loc="upper center", bbox_to_anchor=(0.5, -0.02),
    frameon=False, fontsize=9.5, ncol=1, handlelength=1.1, labelspacing=0.5,
)

# ---- Riquadro "margine" ----
fig.text(0.245, 0.085,
         "≈ 64% di domanda ancora disponibile  →  margine di crescita",
         ha="center", fontsize=9.5, style="italic", color="#E4572E",
         bbox=dict(boxstyle="round,pad=0.4", fc="#FCEEEA", ec="#E4572E", lw=0.8))

# ---- KPI cards ----
ax2 = fig.add_axes([0.50, 0.06, 0.47, 0.74])
ax2.set_xlim(0, 4)
ax2.set_ylim(0, 2)
ax2.axis("off")
ax2.text(2, 2.18, "Metriche chiave (3 settimane)", ha="center",
         fontsize=12.5, fontweight="bold")

centers_x = [0.5, 1.5, 2.5, 3.5]
centers_y = [1.45, 0.5]
order = [(0, 0), (0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (1, 3)]
for (label, value), (r, c) in zip(kpis, order):
    cx, cy = centers_x[c], centers_y[r]
    card = FancyBboxPatch(
        (cx - 0.46, cy - 0.40), 0.92, 0.80,
        boxstyle="round,pad=0.02,rounding_size=0.08",
        fc="#F4F6F8", ec="#E2E6EA", lw=1.0, transform=ax2.transData,
    )
    ax2.add_patch(card)
    ax2.text(cx, cy + 0.10, value, ha="center", va="center",
             fontsize=15, fontweight="bold", color="#1F2A37")
    ax2.text(cx, cy - 0.22, label, ha="center", va="center",
             fontsize=9.2, color="#6B7280")

fig.savefig("/home/user/agents-platform/grafico_dimissioni_chiamata.png",
            bbox_inches="tight", facecolor="white")
print("OK")
