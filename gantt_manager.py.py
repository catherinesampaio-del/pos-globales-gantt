#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║           GANTT MANAGER — POS Globales                          ║
║   Script para agente de IA criar e atualizar o Gantt           ║
║                                                                  ║
║  FUNÇÕES DISPONÍVEIS PARA O AGENTE:                             ║
║   • add_task(...)       → adiciona nova fase/atividade          ║
║   • update_task(...)    → atualiza uma fase existente           ║
║   • remove_task(id)     → remove uma fase pelo ID              ║
║   • list_tasks()        → lista todas as atividades             ║
║   • generate_gantt()    → gera/atualiza o HTML do Gantt        ║
║   • get_task_by_id(id)  → retorna uma fase específica          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json
import os
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CONFIGURAÇÃO — altere se necessário
# ─────────────────────────────────────────────
DATA_FILE   = "gantt_data.json"
OUTPUT_FILE = "gantt_pos_globales.html"

TIPOS_VALIDOS   = ["Banner", "Campanha", "Webinar", "Arte", "Email", "Outro"]
STATUS_VALIDOS  = ["Concluído", "Ativo", "Aguardando", "Em Produção", "Agendado", "Cancelado"]

STATUS_CORES = {
    "Concluído":    "#2ecc71",
    "Ativo":        "#3498db",
    "Aguardando":   "#e67e22",
    "Em Produção":  "#9b59b6",
    "Agendado":     "#1abc9c",
    "Cancelado":    "#95a5a6",
}

TIPO_ICONES = {
    "Banner":   "🖼️",
    "Campanha": "📣",
    "Webinar":  "🎥",
    "Arte":     "🎨",
    "Email":    "📧",
    "Outro":    "📌",
}


# ══════════════════════════════════════════════
#  PERSISTÊNCIA DE DADOS
# ══════════════════════════════════════════════

def _load_data() -> dict:
    """Carrega o arquivo de dados. Cria se não existir."""
    if not os.path.exists(DATA_FILE):
        initial = {"tasks": [], "next_id": 1, "updated_at": _now()}
        _save_data(initial)
        return initial
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_data(data: dict):
    """Salva o arquivo de dados."""
    data["updated_at"] = _now()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ══════════════════════════════════════════════
#  FUNÇÕES PRINCIPAIS (CHAMADAS PELO AGENTE)
# ══════════════════════════════════════════════

def add_task(
    atividade: str,
    fase: str,
    tipo: str,
    inicio: str,
    fim: str,
    status: str,
    detalhe: str = ""
) -> dict:
    """
    Adiciona uma nova fase/atividade ao Gantt.

    Parâmetros:
        atividade : str  → Nome do agrupamento (ex: "Banner Juniper")
        fase      : str  → Descrição da fase (ex: "📤 Envio inicial")
        tipo      : str  → Tipo: Banner | Campanha | Webinar | Arte | Email | Outro
        inicio    : str  → Data início no formato YYYY-MM-DD
        fim       : str  → Data fim    no formato YYYY-MM-DD (pode ser igual ao início)
        status    : str  → Concluído | Ativo | Aguardando | Em Produção | Agendado | Cancelado
        detalhe   : str  → Texto explicativo para o tooltip (opcional)

    Retorna: dict com a tarefa criada e confirmação.

    Exemplo de chamada:
        add_task(
            atividade = "Arte Iberostar",
            fase      = "🎨 Produção da arte",
            tipo      = "Arte",
            inicio    = "2026-06-25",
            fim       = "2026-06-27",
            status    = "Em Produção",
            detalhe   = "Arte para newsletter de julho"
        )
    """
    # Validações
    erros = []
    if tipo not in TIPOS_VALIDOS:
        erros.append(f"Tipo inválido: '{tipo}'. Use: {TIPOS_VALIDOS}")
    if status not in STATUS_VALIDOS:
        erros.append(f"Status inválido: '{status}'. Use: {STATUS_VALIDOS}")
    try:
        datetime.strptime(inicio, "%Y-%m-%d")
        datetime.strptime(fim, "%Y-%m-%d")
    except ValueError:
        erros.append("Datas devem estar no formato YYYY-MM-DD (ex: 2026-06-17)")
    if inicio > fim:
        erros.append(f"Data de início ({inicio}) não pode ser maior que o fim ({fim})")

    if erros:
        return {"sucesso": False, "erros": erros}

    data = _load_data()
    task = {
        "id":        data["next_id"],
        "atividade": atividade.strip(),
        "fase":      fase.strip(),
        "tipo":      tipo,
        "inicio":    inicio,
        "fim":       fim,
        "status":    status,
        "detalhe":   detalhe.strip(),
        "criado_em": _now(),
    }
    data["tasks"].append(task)
    data["next_id"] += 1
    _save_data(data)

    return {
        "sucesso": True,
        "mensagem": f"✅ Fase '{fase}' adicionada à atividade '{atividade}' (ID: {task['id']})",
        "task": task,
    }


def update_task(task_id: int, **campos) -> dict:
    """
    Atualiza campos de uma fase existente pelo ID.

    Campos atualizáveis: atividade, fase, tipo, inicio, fim, status, detalhe

    Exemplo de chamada:
        update_task(3, status="Concluído", detalhe="Confirmado em 25/06")
        update_task(5, fim="2026-06-28")
    """
    data = _load_data()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)

    if not task:
        return {"sucesso": False, "erro": f"Tarefa ID {task_id} não encontrada."}

    campos_validos = {"atividade", "fase", "tipo", "inicio", "fim", "status", "detalhe"}
    invalidos = set(campos.keys()) - campos_validos
    if invalidos:
        return {"sucesso": False, "erro": f"Campos inválidos: {invalidos}. Válidos: {campos_validos}"}

    if "tipo" in campos and campos["tipo"] not in TIPOS_VALIDOS:
        return {"sucesso": False, "erro": f"Tipo inválido. Use: {TIPOS_VALIDOS}"}
    if "status" in campos and campos["status"] not in STATUS_VALIDOS:
        return {"sucesso": False, "erro": f"Status inválido. Use: {STATUS_VALIDOS}"}

    task.update(campos)
    task["atualizado_em"] = _now()
    _save_data(data)

    return {
        "sucesso": True,
        "mensagem": f"✅ Tarefa ID {task_id} atualizada com: {list(campos.keys())}",
        "task": task,
    }


def remove_task(task_id: int) -> dict:
    """
    Remove uma fase pelo ID.

    Exemplo: remove_task(4)
    """
    data = _load_data()
    original = len(data["tasks"])
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]

    if len(data["tasks"]) == original:
        return {"sucesso": False, "erro": f"Tarefa ID {task_id} não encontrada."}

    _save_data(data)
    return {"sucesso": True, "mensagem": f"✅ Tarefa ID {task_id} removida com sucesso."}


def list_tasks(atividade: str = None, status: str = None) -> dict:
    """
    Lista todas as tarefas, com filtros opcionais.

    Parâmetros:
        atividade : str (opcional) → filtra pelo nome da atividade
        status    : str (opcional) → filtra pelo status

    Exemplos:
        list_tasks()
        list_tasks(atividade="Banner Juniper")
        list_tasks(status="Aguardando")
    """
    data = _load_data()
    tasks = data["tasks"]

    if atividade:
        tasks = [t for t in tasks if atividade.lower() in t["atividade"].lower()]
    if status:
        tasks = [t for t in tasks if t["status"] == status]

    return {
        "sucesso": True,
        "total": len(tasks),
        "tasks": tasks,
        "atualizado_em": data.get("updated_at"),
    }


def get_task_by_id(task_id: int) -> dict:
    """
    Retorna uma tarefa específica pelo ID.

    Exemplo: get_task_by_id(2)
    """
    data = _load_data()
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if not task:
        return {"sucesso": False, "erro": f"Tarefa ID {task_id} não encontrada."}
    return {"sucesso": True, "task": task}


def generate_gantt(titulo: str = "📊 Gantt POS Globales", meses: list = None) -> dict:
    """
    Gera o arquivo HTML do Gantt com todos os dados atuais.

    Parâmetros:
        titulo : str        → Título do gráfico
        meses  : list[str]  → Lista de meses para o eixo X (ex: ["2026-06", "2026-07"])
                              Se None, calcula automaticamente a partir dos dados.

    Exemplo:
        generate_gantt()
        generate_gantt(titulo="POS Globales — Julho 2026", meses=["2026-07"])
    """
    data = _load_data()

    if not data["tasks"]:
        return {"sucesso": False, "erro": "Nenhuma tarefa cadastrada. Adicione atividades primeiro."}

    # ── Prepara DataFrame ──────────────────────────────────
    df = pd.DataFrame(data["tasks"])
    df["Inicio"] = pd.to_datetime(df["inicio"])
    df["Fim"]    = pd.to_datetime(df["fim"]) + pd.Timedelta(hours=23, minutes=59)

    # ── Define range do eixo X ────────────────────────────
    if meses:
        dates = [datetime.strptime(m, "%Y-%m") for m in meses]
        x_start = min(dates) - timedelta(days=2)
        x_end   = max(dates) + timedelta(days=33)
    else:
        x_start = df["Inicio"].min() - timedelta(days=3)
        x_end   = df["Fim"].max()    + timedelta(days=4)

    # ── Mapeamento de ícones para tipo ───────────────────
    df["label"] = df.apply(
        lambda r: f"{TIPO_ICONES.get(r['tipo'], '📌')} {r['fase']}", axis=1
    )

    # ── Ordem das atividades ─────────────────────────────
    ordem = df.drop_duplicates("atividade")["atividade"].tolist()

    # ── Figura Plotly ────────────────────────────────────
    fig = px.timeline(
        df,
        x_start="Inicio",
        x_end="Fim",
        y="atividade",
        color="status",
        color_discrete_map=STATUS_CORES,
        hover_name="fase",
        hover_data={
            "detalhe":   True,
            "tipo":      True,
            "Inicio":    "|%d/%m/%Y",
            "Fim":       False,
            "status":    True,
            "atividade": False,
            "label":     False,
        },
        text="label",
        title=titulo,
        category_orders={"atividade": ordem},
    )

    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        textfont=dict(size=11, color="white"),
        marker_line_color="rgba(0,0,0,0.2)",
        marker_line_width=1,
    )

    # ── Linha de HOJE ─────────────────────────────────────
    hoje = datetime.now()
    if x_start <= hoje <= x_end:
        fig.add_vline(
            x=hoje.timestamp() * 1000,
            line_width=2, line_dash="dash", line_color="#e74c3c",
            annotation_text="<b>HOJE</b>",
            annotation_position="top",
            annotation_font_color="#e74c3c",
            annotation_font_size=12,
        )

    # ── Layout ────────────────────────────────────────────
    n_atividades = df["atividade"].nunique()
    altura = max(350, n_atividades * 90 + 160)

    fig.update_layout(
        title=dict(
            text=titulo,
            font=dict(size=20, color="#2c3e50", family="Arial"),
            x=0.5, xanchor="center",
        ),
        paper_bgcolor="#f8f9fa",
        plot_bgcolor="#ffffff",
        font=dict(family="Arial", size=12, color="#2c3e50"),
        xaxis=dict(
            title="",
            tickformat="%d/%m",
            dtick=86400000,
            gridcolor="#ecf0f1",
            showgrid=True,
            zeroline=False,
            range=[x_start, x_end],
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
            showgrid=False,
        ),
        legend=dict(
            title="<b>Status</b>",
            orientation="h",
            yanchor="bottom", y=1.04,
            xanchor="right",  x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#bdc3c7", borderwidth=1,
            font=dict(size=11),
        ),
        margin=dict(l=200, r=40, t=100, b=70),
        height=altura,
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial", bordercolor="#bdc3c7"),
    )

    fig.add_annotation(
        text=(
            f"💡 <i>Última atualização: {data.get('updated_at', '—')} | "
            "Compartilhe este arquivo HTML com a equipe</i>"
        ),
        xref="paper", yref="paper",
        x=0.5, y=-0.18,
        showarrow=False,
        font=dict(size=10, color="#7f8c8d"),
        xanchor="center",
    )

    # ── Cabeçalho HTML ───────────────────────────────────
    ativos = sum(1 for t in data["tasks"] if t["status"] in ("Ativo", "Em Produção"))
    aguardando = sum(1 for t in data["tasks"] if t["status"] == "Aguardando")

    header = f"""
<div style="background:linear-gradient(135deg,#2c3e50 0%,#3498db 100%);
            padding:18px 40px;font-family:Arial,sans-serif;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
    <div>
      <h1 style="color:white;margin:0;font-size:19px;">📊 POS Globales — Tracking de Atividades</h1>
      <p style="color:#bde3ff;margin:4px 0 0;font-size:12px;">
        Atualizado em: {data.get("updated_at", "—")}
      </p>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <span style="background:rgba(255,255,255,.15);color:white;
                   padding:5px 13px;border-radius:20px;font-size:12px;">
        📋 {len(data["tasks"])} fases cadastradas
      </span>
      <span style="background:rgba(52,152,219,.4);color:white;
                   padding:5px 13px;border-radius:20px;font-size:12px;">
        🔵 {ativos} em andamento
      </span>
      <span style="background:rgba(230,126,34,.4);color:white;
                   padding:5px 13px;border-radius:20px;font-size:12px;">
        🟠 {aguardando} aguardando
      </span>
    </div>
  </div>
</div>"""

    html = fig.to_html(
        full_html=True,
        include_plotlyjs=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
            "toImageButtonOptions": {
                "format": "png",
                "filename": "gantt_pos_globales",
                "height": altura + 100,
                "width": 1400,
                "scale": 2,
            },
        },
    )
    html = html.replace("<body>", f"<body>{header}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    return {
        "sucesso": True,
        "mensagem": f"✅ Gantt gerado: {OUTPUT_FILE}",
        "arquivo":  OUTPUT_FILE,
        "total_fases": len(data["tasks"]),
        "atividades": list(df["atividade"].unique()),
    }


# ══════════════════════════════════════════════
#  DEMO — carrega dados iniciais + gera Gantt
# ══════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    # Se já existe arquivo de dados, só gera o Gantt
    if os.path.exists(DATA_FILE):
        print("📂 Arquivo de dados encontrado — gerando Gantt atualizado...")
        resultado = generate_gantt()
        print(resultado["mensagem"])
        sys.exit(0)

    print("🚀 Primeira execução — carregando dados iniciais do POS Globales...\n")

    tarefas_iniciais = [
        # Banner Juniper
        dict(atividade="Banner Juniper", fase="📤 Envio p/ conhecimento",
             tipo="Banner", inicio="2026-06-17", fim="2026-06-17",
             status="Concluído", detalhe="Banner enviado para conhecimento (17/06)"),
        dict(atividade="Banner Juniper", fase="✏️ Melhoria de banner + link",
             tipo="Banner", inicio="2026-06-19", fim="2026-06-19",
             status="Concluído", detalhe="Opção de melhoria enviada (19/06) — horário Espanha"),
        dict(atividade="Banner Juniper", fase="⏳ Aguardando ajuste / reenvio",
             tipo="Banner", inicio="2026-06-22", fim="2026-06-30",
             status="Aguardando", detalhe="Juniper respondeu (22/06): não saiu. Avaliando ajuste no banner deles."),
        # Campanha Princess
        dict(atividade="Campanha Princess", fase="📋 Briefing + Produção",
             tipo="Campanha", inicio="2026-06-17", fim="2026-06-21",
             status="Concluído", detalhe="Briefing enviado com ajustes para Globales (17/06)"),
        dict(atividade="Campanha Princess", fase="🚀 Campanha ATIVA — PY + USA",
             tipo="Campanha", inicio="2026-06-22", fim="2026-06-30",
             status="Ativo", detalhe="Campanha no ar nas plataformas PY e USA desde 22/06 ✅"),
        # Webinar Palmaia
        dict(atividade="Webinar Palmaia", fase="✅ Confirmação do sorteio",
             tipo="Webinar", inicio="2026-06-22", fim="2026-06-22",
             status="Concluído", detalhe="Betina confirmou: sorteio de 1 noite no hotel (22/06)"),
        dict(atividade="Webinar Palmaia", fase="🎨 Produção do novo convite",
             tipo="Webinar", inicio="2026-06-22", fim="2026-06-27",
             status="Em Produção", detalhe="Refazer convite com sorteio incluído"),
        dict(atividade="Webinar Palmaia", fase="📅 Webinar — Evento",
             tipo="Webinar", inicio="2026-06-30", fim="2026-06-30",
             status="Agendado", detalhe="Novo Webinar Palmaia — data confirmada: 30/06"),
    ]

    for t in tarefas_iniciais:
        resultado = add_task(**t)
        status_icon = "✅" if resultado["sucesso"] else "❌"
        print(f"  {status_icon} ID {resultado.get('task', {}).get('id', '?'):>2} — {t['atividade']} | {t['fase']}")

    print("\n🎨 Gerando Gantt HTML...\n")
    resultado = generate_gantt()
    print(resultado["mensagem"])
    print(f"   → {resultado['total_fases']} fases | Atividades: {resultado['atividades']}")
