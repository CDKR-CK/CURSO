import json
 
with open("registros_latencia_costo.jsonl", encoding="utf-8") as f:
    for linea in f:
        r = json.loads(linea)
        tokens_entrada = r["tokens"]["input_tokens"] if r["tokens"] else None
        print(f"k={r['k']}  input_tokens={tokens_entrada}  total={r['tiempo_total_ms']} ms  {r['pregunta']}")

        