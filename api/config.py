"""
Configuração central da API TokenWise.

Todas as constantes ajustáveis ficam aqui para serem modificadas em um único lugar,
sem precisar procurar pelo código dos endpoints.
"""

# Número máximo de caracteres permitidos em um único prompt.
# Requisições que excedem esse limite são rejeitadas com HTTP 422 antes de
# qualquer processamento, prevenindo uso excessivo das APIs de LLM.
MAX_PROMPT_CHARS = 10_000

# Segundos de espera por uma resposta do LLM upstream (POST /chat).
# Requisições que excedem esse limite são canceladas com HTTP 504.
LLM_TIMEOUT_SECONDS = 30
