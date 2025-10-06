# 🎓 Simulador AWS Certified Cloud Practitioner (CLF-C02)

Simulador de examen interactivo para el **AWS Certified Cloud Practitioner (CLF-C02)** completamente en español, basado en los dominios oficiales de AWS.

## 🚀 Demo en Vivo

[Ver Simulador](https://hesusg.github.io/aws-clf02/) 🔗

## ✨ Características

- ✅ **208 preguntas** organizadas según dominios oficiales AWS CLF-C02
- ✅ **4 Dominios oficiales**: Cloud Concepts, Security & Compliance, Technology & Services, Billing & Support
- ✅ **Dos modos de estudio**:
  - **Modo Estudio**: Ve las respuestas y explicaciones inmediatamente
  - **Modo Simulación**: Réplica exacta del examen real (65 preguntas, 90 minutos)
- ✅ **Temporizador** con alertas
- ✅ **Resultados detallados** con desglose por dominio
- ✅ **Puntaje escalado** (100-1000, mínimo 700 para aprobar)
- ✅ **Interfaz responsive** (funciona en móvil, tablet y desktop)
- ✅ **100% offline** después de la carga inicial
- ✅ **Sin registro** ni cuentas necesarias

## 📊 Distribución de Preguntas

Según el análisis de las preguntas disponibles:

| Dominio | Preguntas Disponibles | % Oficial |
|---------|----------------------|-----------|
| Domain 1: Cloud Concepts | 24 preguntas | 24% |
| Domain 2: Security and Compliance | 30 preguntas | 30% |
| Domain 3: Cloud Technology and Services | 135 preguntas | 34% |
| Domain 4: Billing, Pricing, and Support | 19 preguntas | 12% |

## 🎯 Información del Examen CLF-C02

- **Preguntas**: 65 (50 scored + 15 unscored)
- **Duración**: 90 minutos
- **Formato**: Opción múltiple y respuesta múltiple
- **Puntaje**: 100-1000 (mínimo 700 para aprobar)
- **Idiomas**: Disponible en múltiples idiomas (este simulador está en español)
- **Precio**: $100 USD
- **Validez**: 3 años

## 🛠️ Tecnologías Utilizadas

- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Almacenamiento**: LocalStorage (sin backend)
- **Hosting**: GitHub Pages
- **Diseño**: Mobile-first, colores oficiales AWS

## 📦 Instalación Local

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/aws-clf02.git

# Navegar al directorio
cd aws-clf02

# Abrir en el navegador
# Opción 1: Abrir index.html directamente
# Opción 2: Usar un servidor local
python3 -m http.server 8000
# Luego visitar http://localhost:8000
```

## 🔧 Estructura del Proyecto

```
aws-clf02/
├── index.html              # Página principal y configuración
├── simulator.html          # Simulador de examen
├── review.html             # Resultados y revisión
├── css/
│   └── main.css            # Estilos globales
├── js/
│   ├── config.js           # Lógica de configuración
│   ├── simulator.js        # Lógica del examen
│   └── results.js          # Lógica de resultados
├── data/
│   ├── questions.json      # Base de datos de preguntas
│   └── reflection_report.json  # Reporte de calidad
├── parser.py               # Script para procesar preguntas
└── README.md
```

## 📝 Uso

1. **Configurar examen**: Selecciona dominios, número de preguntas, tiempo y modo
2. **Realizar examen**: Responde las preguntas navegando con los botones
3. **Revisar resultados**: Analiza tu rendimiento por dominio y revisa cada pregunta

## 🎨 Personalización

### Agregar más preguntas

1. Edita el archivo fuente de texto con el formato:
```
1. ¿Pregunta aquí?
A) Opción A
B) Opción B
C) Opción C ✅
D) Opción D

✔ Correcta: C) Explicación aquí.
```

2. Ejecuta el parser:
```bash
python3 parser.py
```

### Modificar colores

Edita las variables CSS en `css/main.css`:
```css
:root {
    --aws-orange: #FF9900;
    --aws-dark: #232F3E;
    /* ... */
}
```

## 🔍 Sistema de Reflexión y Validación

El parser incluye validaciones automáticas:

- ✅ Verifica que cada pregunta tenga 4 opciones (A-D)
- ✅ Valida que haya una respuesta correcta marcada
- ✅ Clasifica preguntas por dominio oficial AWS
- ✅ Extrae servicios AWS mencionados
- ✅ Genera reporte de distribución por dominio

Ver `data/reflection_report.json` para detalles.

## 📚 Recursos Oficiales AWS

- [AWS Certified Cloud Practitioner](https://aws.amazon.com/certification/certified-cloud-practitioner/)
- [Exam Guide (PDF)](https://d1.awsstatic.com/training-and-certification/docs-cloud-practitioner/AWS-Certified-Cloud-Practitioner_Exam-Guide.pdf)
- [AWS Skill Builder](https://skillbuilder.aws/)

## ⚠️ Disclaimer

Este simulador es una herramienta de estudio independiente y **NO está afiliada con Amazon Web Services (AWS)**. Las preguntas han sido creadas con fines educativos basándose en los dominios oficiales del examen CLF-C02.

## 📄 Licencia

MIT License - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📧 Contacto

Si encuentras errores o tienes sugerencias, por favor abre un issue en GitHub.

---

**¡Buena suerte en tu certificación AWS! 🚀**
