# Execucao do CEP

```bash
export KAFKA_BOOTSTRAP_SERVERS=127.0.0.1:29092
docker compose up -d
python src/kafka/criar_topico.py
python -m src.cep.consumidor
```

O consumidor pertence ao grupo `cep` e lê `tatame.eventos`.
Complexos são publicados em `tatame.alertas`.
Os limites são hipótese, validação pendente.
