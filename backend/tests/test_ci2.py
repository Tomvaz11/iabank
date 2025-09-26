# No mesmo arquivo
def test_ci_deve_falhar_propositalmente():
    print(">>> EXECUTANDO TESTE DE FALHA INTENCIONAL DO CI <<<") # Para fácil visualização nos logs
    assert "sucesso" == "falha"