"""Testes estatísticos das hipóteses H1 a H5c (seção 5 do artigo).

Entradas: results/ideal.csv (simulador ideal, 1.024 shots) e results/ruido_1024.csv (FakeTorino).
Saídas: results/hipoteses_resumo.csv, results/hipoteses_shap.csv e results/fig_shap_importancia.png.

Critérios (iguais aos do texto):
- H1: em pelo menos 2 das 3 famílias, a fração visível em alguma condição supera a do trabalho-base
  (|0...0>, base Z) em pelo menos 20 p.p., com McNemar significativo (Holm, 5%).
- H2: só portas de fase (Z, T, RZ). Reversíveis: |+>^n revela mais que |0...0> (em alguma das duas bases).
  Oráculos e emaranhamento: |+>^n não revela mais; rejeitada se revelar mais com diferença significativa.
- H3: verificação analítica nos reversíveis (nenhuma detecção de fase fora de "superposição + base X").
- H4: posição + papel >= 10% da importância SHAP média e ao menos um com efeito significativo
  na regressão logística (GEE binomial agrupada por circuito).
- H5a: mais de 50% das variantes visíveis com k95 <= 10.
- H5b: mediana de k95 de RZ(pi/16) maior que a das outras portas, ou maioria invisível.
- H5c: fração visível com ruído menor que no ideal (McNemar), e perda concentrada onde o impacto
  ideal fica abaixo do piso com ruído.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shap  # noqa: E402
import statsmodels.api as sm  # noqa: E402
import statsmodels.formula.api as smf  # noqa: E402
from scipy.stats import mannwhitneyu  # noqa: E402
from sklearn.ensemble import GradientBoostingClassifier  # noqa: E402
from statsmodels.stats.contingency_tables import mcnemar  # noqa: E402
from statsmodels.stats.multitest import multipletests  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

RAIZ = Path(__file__).resolve().parents[1]
RES = RAIZ / "results"
CHAVE = ["familia", "circuito", "porta", "posicao", "papel"]
FAMILIAS = ["reversivel", "oraculo", "emaranhamento"]
FASE = ["z", "t", "rz_pi16"]
ALFA = 0.05
SEMENTE = 0


def k95(p: float) -> float:
    if p <= 0:
        return np.inf
    if p >= 1:
        return 1
    return int(np.ceil(np.log(0.05) / np.log(1 - p)))


def teste_mcnemar(a: pd.Series, b: pd.Series) -> dict:
    """McNemar exato pareado. a e b: visível (True/False) para as mesmas variantes."""
    a, b = a.astype(bool).values, b.astype(bool).values
    tabela = [[np.sum(a & b), np.sum(a & ~b)], [np.sum(~a & b), np.sum(~a & ~b)]]
    res = mcnemar(tabela, exact=True)
    return {"n": len(a), "frac_a": a.mean(), "frac_b": b.mean(), "so_a": tabela[0][1], "so_b": tabela[1][0], "p": res.pvalue}


def condicoes_ideal(ideal: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por variante x base x tipo de entrada, com 'visivel'."""
    linhas = []
    for col, entrada in [("revela_zeros", "zeros"), ("revela_mais", "mais")]:
        d = ideal[CHAVE + ["base"]].copy()
        d["entrada"], d["visivel"] = entrada, ideal[col].astype(bool)
        linhas.append(d)
    for col, entrada in [("p_revela_base", "base_z"), ("p_revela_base_x", "base_x")]:
        d = ideal[CHAVE + ["base"]].copy()
        d["entrada"], d["visivel"] = entrada, ideal[col] > 0
        linhas.append(d)
    return pd.concat(linhas, ignore_index=True)


def por_variante(ideal: pd.DataFrame, cond: pd.DataFrame) -> pd.DataFrame:
    z = ideal[ideal.base == "z"].set_index(CHAVE)
    x = ideal[ideal.base == "x"].set_index(CHAVE)
    v = pd.DataFrame(index=z.index)
    v["trabalho"] = z.revela_zeros.astype(bool)
    v["alguma"] = cond.groupby(CHAVE).visivel.any()
    v["zeros_any"] = z.revela_zeros.astype(bool) | x.revela_zeros.astype(bool)
    v["mais_any"] = z.revela_mais.astype(bool) | x.revela_mais.astype(bool)
    v["p_melhor"] = np.maximum.reduce([z.p_revela_base, x.p_revela_base, z.p_revela_base_x, x.p_revela_base_x])
    v["k95"] = v.p_melhor.map(k95)
    # H3: detecções de fase fora da condição "entrada em superposição + medição em X"
    v["fora_sup_x"] = (
        z.revela_zeros.astype(bool) | x.revela_zeros.astype(bool) | z.revela_mais.astype(bool)
        | (z.p_revela_base > 0) | (x.p_revela_base > 0) | (z.p_revela_base_x > 0)
    )
    v["sup_x"] = (x.p_revela_base_x > 0) | x.revela_mais.astype(bool)
    return v.reset_index()


def h1(v: pd.DataFrame) -> pd.DataFrame:
    linhas = [{"familia": f, **teste_mcnemar(v[v.familia == f].alguma, v[v.familia == f].trabalho)} for f in FAMILIAS]
    t = pd.DataFrame(linhas)
    t["p_holm"] = multipletests(t.p, method="holm")[1]
    t["ganho_pp"] = 100 * (t.frac_a - t.frac_b)
    t["atende"] = (t.ganho_pp >= 20) & (t.p_holm < ALFA)
    return t


def h2(v: pd.DataFrame) -> pd.DataFrame:
    f = v[v.porta.isin(FASE)]
    linhas = [{"familia": fam, **teste_mcnemar(f[f.familia == fam].mais_any, f[f.familia == fam].zeros_any)} for fam in FAMILIAS]
    t = pd.DataFrame(linhas)
    t["p_holm"] = multipletests(t.p, method="holm")[1]
    sig = t.p_holm < ALFA
    mais_maior = t.frac_a > t.frac_b
    t["esperado"] = np.where(t.familia == "reversivel", "|+> revela mais", "|+> não revela mais")
    t["atende"] = np.where(t.familia == "reversivel", mais_maior & sig, ~(mais_maior & sig))
    return t


def h3(v: pd.DataFrame) -> dict:
    r = v[(v.familia == "reversivel") & v.porta.isin(FASE)]
    return {
        "variantes": len(r),
        "deteccoes_fora_de_sup_x": int(r.fora_sup_x.sum()),
        "frac_visivel_sup_x": r.sup_x.mean(),
        "atende": int(r.fora_sup_x.sum()) == 0,
    }


def h4(cond: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    fatores = ["porta", "posicao", "papel", "entrada", "base", "familia"]

    def importancia(dados: pd.DataFrame, cols: list[str]) -> pd.Series:
        X = pd.get_dummies(dados[cols].astype(str), prefix_sep="=")
        modelo = GradientBoostingClassifier(random_state=SEMENTE).fit(X, dados.visivel)
        valores = shap.TreeExplainer(modelo).shap_values(X)
        media = pd.Series(np.abs(valores).mean(axis=0), index=X.columns)
        por_fator = media.groupby(lambda c: c.split("=")[0]).sum()
        return por_fator / por_fator.sum(), modelo.score(X, dados.visivel)

    # Cenário A: só a condição do trabalho-base. Cenário B: todas as condições.
    a = cond[(cond.entrada == "zeros") & (cond.base == "z")]
    imp_a, acc_a = importancia(a, ["porta", "posicao", "papel", "familia"])
    imp_b, acc_b = importancia(cond, fatores)
    shap_tab = pd.DataFrame({"so_trabalho_base": imp_a, "todas_as_condicoes": imp_b}).fillna(0)

    # Regressão logística marginal (GEE) com o circuito como grupo.
    gee = smf.gee(
        "visivel ~ C(porta) + C(posicao) + C(papel) + C(entrada) + C(base) + C(familia)",
        groups="circuito",
        data=cond.assign(visivel=cond.visivel.astype(int)),
        family=sm.families.Binomial(),
        cov_struct=sm.cov_struct.Exchangeable(),
    ).fit()
    testes = gee.wald_test_terms(scalar=True)
    tabela = testes.table
    p_pos = float(tabela.loc["C(posicao)", "pvalue"])
    p_pap = float(tabela.loc["C(papel)", "pvalue"])
    p_holm = multipletests([p_pos, p_pap], method="holm")[1]
    share = imp_b.get("posicao", 0) + imp_b.get("papel", 0)
    resumo = {
        "share_pos_papel_todas": share,
        "share_pos_papel_trabalho_base": imp_a.get("posicao", 0) + imp_a.get("papel", 0),
        "p_posicao_holm": p_holm[0],
        "p_papel_holm": p_holm[1],
        "acuracia_modelo_A": acc_a,
        "acuracia_modelo_B": acc_b,
        "atende": (share >= 0.10) and (min(p_holm) < ALFA),
    }
    return resumo, shap_tab


def h5ab(v: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    vis = v[v.alguma]
    h5a = {"variantes_visiveis": len(vis), "frac_k95_ate_10": (vis.k95 <= 10).mean()}
    h5a["atende"] = h5a["frac_k95_ate_10"] > 0.5

    linhas = []
    for fam in FAMILIAS + ["todas"]:
        d = v if fam == "todas" else v[v.familia == fam]
        rz, outras = d[d.porta == "rz_pi16"], d[d.porta != "rz_pi16"]
        k_rz, k_out = rz.k95.replace(np.inf, 1e6), outras.k95.replace(np.inf, 1e6)
        p = mannwhitneyu(k_rz, k_out, alternative="greater").pvalue
        linhas.append({
            "familia": fam,
            "mediana_k95_rz": np.median(rz.k95),
            "mediana_k95_outras": np.median(outras.k95),
            "frac_rz_invisivel": (~rz.alguma).mean(),
            "p_mannwhitney": p,
            "atende": (np.median(rz.k95) > np.median(outras.k95)) or ((~rz.alguma).mean() > 0.5),
        })
    return h5a, pd.DataFrame(linhas)


def h5c(ruido: pd.DataFrame) -> dict:
    v = ruido.groupby(CHAVE)[["revela_ideal", "revela_ruido"]].any()
    t = teste_mcnemar(v.revela_ruido, v.revela_ideal)
    perdidas = ruido[ruido.revela_ideal & ~ruido.revela_ruido]
    t["combinacoes_perdidas"] = len(perdidas)
    t["frac_perdidas_abaixo_piso"] = (perdidas.tvd_ideal < perdidas.piso_ruido).mean()
    t["atende"] = (t["frac_a"] < t["frac_b"]) and (t["p"] < ALFA) and t["frac_perdidas_abaixo_piso"] > 0.5
    return t


def figura_shap(shap_tab: pd.DataFrame) -> None:
    nomes = {"porta": "Porta", "posicao": "Posição", "papel": "Papel do qubit", "entrada": "Entrada",
             "base": "Base de medição", "familia": "Família"}
    t = shap_tab.rename(index=nomes).sort_values("todas_as_condicoes")
    y = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.barh(y + 0.2, 100 * t.so_trabalho_base, height=0.38, color="#9aa5b1", label="Só |0…0⟩, base Z (trabalho-base)")
    ax.barh(y - 0.2, 100 * t.todas_as_condicoes, height=0.38, color="#2a6fdb", label="Todas as entradas e bases")
    ax.set_yticks(y, t.index)
    ax.set_xlabel("Importância SHAP média (% do total)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(RES / "fig_shap_importancia.png", dpi=200)


def main() -> None:
    ideal = pd.read_csv(RES / "ideal.csv")
    ruido = pd.read_csv(RES / "ruido_1024.csv")
    cond = condicoes_ideal(ideal)
    v = por_variante(ideal, cond)

    t1, t2, r3 = h1(v), h2(v), h3(v)
    r4, shap_tab = h4(cond)
    r5a, t5b = h5ab(v)
    r5c = h5c(ruido)

    fmt = lambda t: t.round(4).to_string(index=False)  # noqa: E731
    print("H1: alguma condição (a) x trabalho-base (b), por família\n" + fmt(t1))
    print("  -> H1 atende em", int(t1.atende.sum()), "de 3 famílias:", "CONFIRMADA" if t1.atende.sum() >= 2 else "REJEITADA", "\n")
    print("H2: portas de fase, |+>^n (a) x |0...0> (b), alguma base\n" + fmt(t2), "\n")
    print("H3:", {k: round(v_, 4) if isinstance(v_, float) else v_ for k, v_ in r3.items()}, "\n")
    print("H4:", {k: round(v_, 4) if isinstance(v_, float) else v_ for k, v_ in r4.items()})
    print("  importância SHAP (fração do total)\n" + shap_tab.round(3).to_string(), "\n")
    print("H5a:", {k: round(v_, 4) if isinstance(v_, float) else v_ for k, v_ in r5a.items()})
    print("H5b\n" + fmt(t5b))
    print("H5c: ruído (a) x ideal (b), 4 condições\n", {k: round(v_, 4) if isinstance(v_, float) else v_ for k, v_ in r5c.items()})

    resumo = pd.DataFrame([
        {"hipotese": "H1", "atende": bool(t1.atende.sum() >= 2), "detalhe": f"{int(t1.atende.sum())}/3 famílias"},
        *[{"hipotese": f"H2 ({r.familia})", "atende": bool(r.atende), "detalhe": f"|+>={r.frac_a:.2f} |0>={r.frac_b:.2f} p_holm={r.p_holm:.3g}"} for r in t2.itertuples()],
        {"hipotese": "H3", "atende": bool(r3["atende"]), "detalhe": f"{r3['deteccoes_fora_de_sup_x']} detecções fora de sup+X"},
        {"hipotese": "H4", "atende": bool(r4["atende"]), "detalhe": f"posição+papel={r4['share_pos_papel_todas']:.1%}"},
        {"hipotese": "H5a", "atende": bool(r5a["atende"]), "detalhe": f"{r5a['frac_k95_ate_10']:.1%} com k95<=10"},
        {"hipotese": "H5b", "atende": bool(t5b[t5b.familia == 'todas'].atende.iloc[0]), "detalhe": "ver hipoteses_h5b"},
        {"hipotese": "H5c", "atende": bool(r5c["atende"]), "detalhe": f"ideal={r5c['frac_b']:.2f} ruído={r5c['frac_a']:.2f} p={r5c['p']:.3g}"},
    ])
    resumo.to_csv(RES / "hipoteses_resumo.csv", index=False)
    t1.to_csv(RES / "hipoteses_h1.csv", index=False)
    t2.to_csv(RES / "hipoteses_h2.csv", index=False)
    t5b.to_csv(RES / "hipoteses_h5b.csv", index=False)
    shap_tab.to_csv(RES / "hipoteses_shap.csv")
    figura_shap(shap_tab)
    print("\nResumo\n" + resumo.to_string(index=False))


if __name__ == "__main__":
    main()
