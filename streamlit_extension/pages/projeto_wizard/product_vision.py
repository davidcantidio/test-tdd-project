import streamlit as st
from typing import List, Dict
from src.ia.services.vision_refine_service import VisionRefineService

# ---------- helpers de estado ----------
def _init_state():
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "vision" not in st.session_state:
        st.session_state.vision = {
            "product_name": "",
            "target_user": "",
            "problem": "",
            "outcome": "",
            "constraints": [],  # lista de strings
        }
    if "ia_busy" not in st.session_state:
        st.session_state.ia_busy = False

def _all_fields_filled(d: Dict) -> bool:
    required = ["product_name", "target_user", "problem", "outcome", "constraints"]
    for k in required:
        v = d.get(k)
        if isinstance(v, str) and not v.strip():
            return False
        if isinstance(v, list) and len([x for x in v if x and x.strip()]) == 0:
            return False
    return True

def _constraints_as_text(lst: List[str]) -> str:
    return "\n".join(lst)

def _constraints_from_text(txt: str) -> List[str]:
    items = [line.strip() for line in txt.splitlines()]
    return [x for x in items if x]

# ---------- UI ----------
def step_header():
    st.title("Novo Projeto · Visão do Produto (Wizard)")
    st.caption("Preencha os campos, refine com IA se desejar e salve.")

def step_1():
    with st.form("step1"):
        st.subheader("Passo 1 — Identidade do Produto")
        st.session_state.vision["product_name"] = st.text_input(
            "Nome do produto",
            st.session_state.vision.get("product_name", "")
        )
        st.session_state.vision["target_user"] = st.text_input(
            "Usuário-alvo (persona/segmento)",
            st.session_state.vision.get("target_user", "")
        )
        col1, col2 = st.columns(2)
        next_clicked = col2.form_submit_button("Avançar ➡")
        if next_clicked:
            # validação mínima
            if st.session_state.vision["product_name"].strip() and st.session_state.vision["target_user"].strip():
                st.session_state.step = 2
            else:
                st.warning("Preencha os campos obrigatórios.")

def step_2():
    with st.form("step2"):
        st.subheader("Passo 2 — Problema & Resultado")
        st.session_state.vision["problem"] = st.text_area(
            "Problema a resolver",
            st.session_state.vision.get("problem", ""),
            height=120
        )
        st.session_state.vision["outcome"] = st.text_area(
            "Resultado desejado (outcome de negócio/usuário)",
            st.session_state.vision.get("outcome", ""),
            height=120
        )
        col1, col2 = st.columns(2)
        back = col1.form_submit_button("⬅ Voltar")
        next_clicked = col2.form_submit_button("Avançar ➡")
        if back:
            st.session_state.step = 1
        if next_clicked:
            if st.session_state.vision["problem"].strip() and st.session_state.vision["outcome"].strip():
                st.session_state.step = 3
            else:
                st.warning("Preencha os campos obrigatórios.")

def step_3():
    st.subheader("Passo 3 — Restrições & Revisão")
    with st.form("step3"):
        constraints_text = st.text_area(
            "Restrições (uma por linha)",
            _constraints_as_text(st.session_state.vision.get("constraints", [])),
            height=120,
            placeholder="Ex.: orçamento limitado\natender LGPD\nlançar em 90 dias"
        )
        # atualiza lista a partir do textarea quando submeter
        col = st.columns([1,1,1,2])
        back = col[0].form_submit_button("⬅ Voltar")
        refine = col[1].form_submit_button("Refinar com IA ✨", disabled=st.session_state.ia_busy)
        save = col[2].form_submit_button("Salvar ✅", disabled=st.session_state.ia_busy)

        if back:
            st.session_state.step = 2
            return

        # aplica constraints do form no estado antes de qualquer ação
        st.session_state.vision["constraints"] = _constraints_from_text(constraints_text)

        # preview dos dados
        st.write("### Pré-visualização")
        st.json(st.session_state.vision)

        # ações
        if refine:
            _handle_refine()

        if save:
            _handle_save()

def _handle_refine():
    vision = st.session_state.vision
    if not _all_fields_filled(vision):
        st.warning("Para refinar com IA, preencha todos os campos dos passos 1–3.")
        return
    st.session_state.ia_busy = True
    with st.spinner("Refinando com IA..."):
        try:
            service = VisionRefineService()
            result = service.refine(vision)  # dict com as mesmas chaves
            # aplica resultado nos campos (permitindo edição posterior)
            for k in ["product_name", "target_user", "problem", "outcome"]:
                if isinstance(result.get(k), str) and result[k].strip():
                    st.session_state.vision[k] = result[k].strip()
            if isinstance(result.get("constraints"), list) and result["constraints"]:
                st.session_state.vision["constraints"] = result["constraints"]
            st.success("Campos atualizados com a sugestão da IA. Revise/edite antes de salvar.")
        except Exception as e:
            st.error(f"Falha ao refinar com IA: {e}")
        finally:
            st.session_state.ia_busy = False

def _handle_save():
    vision = st.session_state.vision
    if not _all_fields_filled(vision):
        st.warning("Preencha todos os campos antes de salvar.")
        return
    try:
        # TODO: injete seu serviço real de persistência aqui
        # ex.: ServiceContainer().project_service.create_product_vision(vision)
        st.success("Visão do produto salva com sucesso! ✅")
        # opcional: reset do wizard
        # st.session_state.step = 1
        # st.session_state.vision = { ... }
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

def main():
    _init_state()
    step_header()
    if st.session_state.step == 1:
        step_1()
    elif st.session_state.step == 2:
        step_2()
    else:
        step_3()

if __name__ == "__main__":
    main()
