# Prime Informática — Sistema de Caixa

## Usuários

| Usuário | Senha | Acesso |
|---|---|---|
| loja57 | prime57 | Prime Informática 5/7 |
| loja42 | prime42 | Prime Informática 4/2 |
| admin | primeadm | Painel administrativo |

## Como rodar localmente

```bash
uv sync
uv run streamlit run app.py
```

## Como fazer deploy no Streamlit Cloud

1. Suba o projeto para um repositório no GitHub
2. Acesse https://share.streamlit.io
3. Clique em "New app"
4. Selecione o repositório e o arquivo `app.py`
5. Clique em "Deploy"

⚠️ **Importante:** No Streamlit Cloud os dados ficam em memória temporária.
Para persistência real use o st.secrets com um banco externo (ex: Supabase gratuito).
Por enquanto funciona perfeitamente para uso local.

## Rodar local (recomendado para começar)

O sistema funciona 100% offline. Cada computador roda sua própria instância
e os dados ficam salvos em arquivos `.db` na pasta `data/`.
