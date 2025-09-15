from tdd_core.domain.entities.user_story import UserStory


def test_user_story_creation_and_validation():
    us = UserStory(
        epic_id=1,
        key="US-001",
        title="Como usuário, quero me autenticar",
        narrative="Como usuário, quero fazer login para acessar minha conta",
        acceptance_criteria=["Deve aceitar email e senha", "Mensagem de erro em caso de falha"],
    )
    print("[CREATE] UserStory criada:", us.key, us.title)
    assert us.is_valid()

    bad = UserStory(
        epic_id=0, key=" ", title=" ", narrative=" ", acceptance_criteria=[]
    )
    errors = bad.validate()
    print("[VALIDATE] Erros esperados:")
    for e in errors:
        print("  -", e)
    assert "epic_id is required" in errors
    assert "key is required and cannot be empty" in errors
    assert "title is required and cannot be empty" in errors
    assert "narrative is required and cannot be empty" in errors
    assert "acceptance_criteria is required and cannot be empty" in errors

