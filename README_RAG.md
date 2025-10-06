# 🤖 Sistema RAG + GPT-4o-mini + Phoenix Evals

Generador inteligente de preguntas de examen AWS CLF-C02 usando:
- **RAG (Retrieval-Augmented Generation)** con documentación oficial AWS
- **GPT-4o-mini** para generación de preguntas de alta calidad
- **Arize Phoenix** para evaluación automática de calidad

---

## 🎯 ¿Qué hace este sistema?

Genera preguntas de examen AWS CLF-C02 que son:
- ✅ **Basadas en docs oficiales AWS** (no inventadas)
- ✅ **Evaluadas automáticamente** para evitar hallucinations
- ✅ **Con explicaciones pedagógicas** detalladas
- ✅ **Distribuidas según dominios oficiales** CLF-C02
- ✅ **Ultra económicas**: ~$0.30 USD por 300 preguntas

---

## 📊 Costos Estimados

| Preguntas | Generación | Evaluación | Total |
|-----------|------------|------------|-------|
| 100 | $0.05 | $0.03 | **~$0.10** |
| 200 | $0.10 | $0.06 | **~$0.20** |
| 300 | $0.15 | $0.09 | **~$0.30** |
| 500 | $0.25 | $0.15 | **~$0.50** |

*Precios con buffer de 30% incluido*

---

## 🚀 Setup Rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar API Key

```bash
# Copiar ejemplo
cp .env.example .env

# Editar .env y agregar tu OPENAI_API_KEY
nano .env
```

### 3. Ejecutar Pipeline Completo

```bash
# Paso 1: Descargar docs AWS (~2 min)
python scripts/1_fetch_aws_docs.py

# Paso 2: Construir RAG (~5 min, costo: ~$0.01)
python scripts/2_build_rag.py

# Paso 3: Calcular costos (interactivo)
python scripts/3_estimate_cost.py

# Paso 4: Generar preguntas (~10 min para 300 preguntas)
python scripts/4_generate_questions.py --count 300

# Paso 5: Evaluar con Phoenix (~15 min)
python scripts/5_evaluate_with_phoenix.py
```

---

## 📁 Estructura del Proyecto

```
aws-clf02/
├── scripts/
│   ├── 1_fetch_aws_docs.py       # Descarga docs AWS
│   ├── 2_build_rag.py             # Crea vector DB
│   ├── 3_estimate_cost.py         # Calculadora de costos
│   ├── 4_generate_questions.py    # Generador con RAG
│   └── 5_evaluate_with_phoenix.py # Phoenix evals
│
├── prompts/
│   ├── system.txt                 # System prompt
│   └── examples.json              # Few-shot examples
│
├── data/
│   ├── aws_docs/                  # Docs descargadas
│   ├── chroma_db/                 # Vector database
│   ├── questions_raw.json         # Pre-evaluación
│   ├── questions_evaluated.json   # ✅ Aprobadas
│   └── questions_rejected.json    # ❌ Rechazadas
│
└── .env                           # Tu OPENAI_API_KEY
```

---

## 🔧 Scripts Detallados

### Script 1: Fetch AWS Docs

Descarga documentación oficial:
- AWS CLF-C02 Exam Guide (PDF)
- Well-Architected Framework (PDF)
- Cloud Adoption Framework (HTML)
- 17 Service FAQs (EC2, S3, Lambda, RDS, etc.)

```bash
python scripts/1_fetch_aws_docs.py
```

**Output:**
- `data/aws_docs/` con ~20 documentos
- ~10 MB de documentación oficial

### Script 2: Build RAG

Procesa docs y crea vector database:
- Divide en chunks de ~500 tokens
- Genera embeddings con `text-embedding-3-small`
- Almacena en ChromaDB (local, gratuito)

```bash
python scripts/2_build_rag.py
```

**Output:**
- `data/chroma_db/` con vector database
- Costo: ~$0.01 USD (one-time)

### Script 3: Cost Estimator

Calculadora interactiva:
- Ingresa número de preguntas deseadas
- Ve distribución por dominio CLF-C02
- Obtén estimación detallada de costos
- Opción de ejecutar generador directamente

```bash
python scripts/3_estimate_cost.py
```

**Ejemplo de salida:**
```
¿Cuántas preguntas deseas generar? 300

DISTRIBUCIÓN POR DOMINIO CLF-C02
════════════════════════════════════════════════════════════════════
Cloud Concepts
   ████████████ 24%
   72 preguntas

Security and Compliance
   ███████████████ 30%
   90 preguntas

...

TOTAL ESTIMADO: $0.31 USD
```

### Script 4: Generate Questions

Genera preguntas usando RAG + GPT-4o-mini:
- Busca contexto relevante (top-3 chunks)
- Inyecta en prompt con few-shot examples
- Genera pregunta + 4 opciones + explicación
- Progress bar en tiempo real

```bash
python scripts/4_generate_questions.py --count 300 --output questions_raw.json
```

**Opciones:**
- `--count`: Número de preguntas (default: 50)
- `--output`: Archivo de salida (default: questions_raw.json)

**Output:**
```json
{
  "question": "Una empresa...",
  "options": {
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  },
  "correct_answer": "B",
  "explanation": "**Respuesta correcta: B) ...**\n\n...",
  "domain": "Domain 3: Cloud Technology and Services",
  "topic": "Amazon S3 características",
  "retrieved_context": "AWS docs...",
  "tokens_used": {"input": 1450, "output": 380}
}
```

### Script 5: Phoenix Evaluations

Evalúa calidad con 3 evaluators:

1. **Hallucination Detection** (score < 0.3 para aprobar)
   - Detecta si inventa información
   - Verifica contra docs AWS reales

2. **QA Correctness** (score > 0.7 para aprobar)
   - Valida que pregunta tenga sentido
   - Verifica que respuesta correcta sea correcta

3. **CLF-C02 Compliance** (score >= 0.9 para aprobar)
   - 4 opciones válidas
   - Formato correcto
   - Dominio oficial

```bash
python scripts/5_evaluate_with_phoenix.py --input questions_raw.json
```

**Output:**
- `data/questions_evaluated.json` - ✅ Aprobadas
- `data/questions_rejected.json` - ❌ Rechazadas
- Phoenix Dashboard: http://localhost:6006

**Ejemplo de reporte:**
```
REPORTE DE EVALUACIONES
════════════════════════════════════════════════════════════════════
Total evaluadas: 300
✅ Aprobadas: 267 (89.0%)
❌ Rechazadas: 33 (11.0%)

Scores Promedio:
   Hallucination: 0.154 (menor es mejor, límite: 0.3)
   QA Correctness: 0.863 (mayor es mejor, límite: 0.7)
   CLF Compliance: 0.967 (mayor es mejor, límite: 0.9)
```

---

## 🎨 Phoenix Dashboard

Al ejecutar el Script 5, Phoenix abre un dashboard en http://localhost:6006

**Features del dashboard:**
- 📊 Métricas de calidad en tiempo real
- 🔍 Explorar preguntas rechazadas
- 📈 Distribución de scores
- 🔬 Traces de cada llamada a GPT
- 💰 Uso de tokens y costos

---

## 💡 Uso Avanzado

### Generar solo para un dominio específico

Edita `scripts/4_generate_questions.py` y modifica `DOMAINS`:

```python
# Solo Security & Compliance
DOMAINS = {
    "Domain 2: Security and Compliance": 100
}
```

### Ajustar criterios de evaluación

Edita `scripts/5_evaluate_with_phoenix.py`:

```python
# Más estricto
passed = (
    hall_result["score"] < 0.2 and  # Era 0.3
    qa_result["score"] > 0.8 and    # Era 0.7
    compliance_result["score"] >= 0.95  # Era 0.9
)
```

### Cambiar modelo

En `.env`:
```bash
OPENAI_MODEL=gpt-4o  # Mejor calidad pero más caro
# o
OPENAI_MODEL=gpt-4o-mini  # Más económico (default)
```

---

## 🎓 Integrar con Simulador

Para usar las preguntas generadas en el simulador web:

```bash
# Copiar preguntas evaluadas al simulador
cp data/questions_evaluated.json data/questions.json

# O combinar con preguntas existentes
python -c "
import json
with open('data/questions.json') as f: old = json.load(f)
with open('data/questions_evaluated.json') as f: new = json.load(f)
old['questions'].extend(new)
with open('data/questions.json', 'w') as f: json.dump(old, f, indent=2)
"
```

---

## 🐛 Troubleshooting

### Error: OPENAI_API_KEY no encontrada
```bash
# Verificar que .env existe
ls -la .env

# Verificar contenido
cat .env

# Debe contener:
# OPENAI_API_KEY=sk-...
```

### Error: ChromaDB no encontrado
```bash
# Ejecutar primero el script 2
python scripts/2_build_rag.py
```

### Rate limit de OpenAI
El script 4 ya incluye rate limiting (1 seg cada 10 preguntas).
Si aún hay errores, aumenta el delay en `scripts/4_generate_questions.py`:

```python
# Línea ~260
if i % 10 == 0:
    time.sleep(2)  # Era 1 segundo
```

### Phoenix no abre dashboard
```bash
# Verificar puerto 6006 disponible
lsof -i :6006

# Cambiar puerto en .env
PHOENIX_PORT=6007
```

---

## 📚 Referencias

- [OpenAI API Pricing](https://openai.com/api/pricing/)
- [Arize Phoenix Docs](https://arize.com/docs/phoenix/)
- [AWS CLF-C02 Exam Guide](https://d1.awsstatic.com/training-and-certification/docs-cloud-practitioner/AWS-Certified-Cloud-Practitioner_Exam-Guide.pdf)
- [LangChain RAG](https://python.langchain.com/docs/use_cases/question_answering/)

---

## ✅ Checklist de Uso

- [ ] Instalé dependencias (`pip install -r requirements.txt`)
- [ ] Configuré `OPENAI_API_KEY` en `.env`
- [ ] Ejecuté `1_fetch_aws_docs.py`
- [ ] Ejecuté `2_build_rag.py`
- [ ] Calculé costos con `3_estimate_cost.py`
- [ ] Generé preguntas con `4_generate_questions.py`
- [ ] Evalué con Phoenix `5_evaluate_with_phoenix.py`
- [ ] Revisé dashboard de Phoenix
- [ ] Integré preguntas aprobadas al simulador

---

**¡Listo! Ahora tienes un sistema completo de generación de preguntas AWS CLF-C02 con calidad garantizada.** 🚀
