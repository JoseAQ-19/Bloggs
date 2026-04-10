---
title: "Microsoft Elimina Copilot y Los Usuarios Se Preguntan Si Es El Fin del Notepad"
date: 2026-04-10T13:31:13
draft: false
description: "Microsoft ha eliminado Copilot y los usuarios se cuestionan si esto marca el fin de Notepad. Descubre las implicaciones y el futuro de estas herramientas."
featured_image: "/images/microsoft-elimina-el-nombre-copilot-el-fin-de-una-era-en-notepad-y-snipping-tool.jpg"
slug: "microsoft-elimina-el-nombre-copilot-el-fin-de-una-era-en-notepad-y-snipping-tool"
canonical: "https://novumworld.com/es/tools/microsoft-elimina-el-nombre-copilot-el-fin-de-una-era-en-notepad-y-snipping-tool/"
tags: ["Tools & Productivity"]
categories: ["tools"]
type: "tools"
language: "es"
translationKey: "6b9dffe5-038a-0f53-a198-ad0c471c27e3"
---

![Microsoft Elimina Copilot y Los Usuarios Se Preguntan Si Es El Fin del Notepad](/images/microsoft-elimina-el-nombre-copilot-el-fin-de-una-era-en-notepad-y-snipping-tool.jpg)

La retirada de Copilot del Bloc de Notas no es una mera optimización de la interfaz, sino una autopsia pública de la sobreingeniería impulsada por el pánico de Microsoft a quedarse atrás en la carrera de la inteligencia artificial. Esta decisión confirma que la integración forzada de modelos de lenguaje masivo (LLM) en herramientas heredadas de Win32 creó una experiencia de usuario fragmentada y técnicamente insostenible.

* Microsoft ha procedido a eliminar la integración de Copilot del Bloc de Notas y la Herramienta de Recorte en Windows 11, reconociendo implícitamente que la inyección de IA generativa en aplicaciones de texto plano no generaba el valor funcional prometido.
* Pavan Davuluri, vicepresidente ejecutivo de Windows y Dispositivos, justificó la medida argumentando la necesidad de simplificar la oferta, aunque el movimiento coincide con informes que indican que el 95% de las empresas no han obtenido un retorno de inversión medible en sus proyectos de inteligencia artificial.
* La eliminación de estos asistentes no exime a Microsoft de las críticas sobre privacidad, especialmente tras la vulnerabilidad CW1226324 descubierta en enero de 2026, que permitió al sistema leer correos electrónicos confidenciales de las carpetas de elementos enviados y borradores.

{{< adsterra_native >}}

## Arquitectura de la Integración y Latencia en Win32

La integración de Copilot en el Bloc de Notas representaba un desafío arquitectónico significativo debido a la naturaleza heredada de la aplicación. El Bloc de Notas es una aplicación Win32 ligera que utiliza el control de edición estándar de Windows, diseñada para la velocidad y el consumo mínimo de recursos. La adición de funcionalidades de IA requería la inyección de componentes WebView2 o llamadas directas a la API REST de Azure OpenAI, lo que incrementaba la superficie de ataque y el consumo de memoria de una aplicación que históricamente se ejecutaba con una huella de menos de 5 MB.

La latencia introducida por las llamadas a la red para funciones como "Reescribir" o "Resumir" rompía el paradigma de respuesta inmediata esperado de un editor de texto. Cada solicitud de procesamiento de texto requería serializar el contenido del buffer, enviarlo a los servidores de Microsoft, procesarlo mediante un modelo de lenguaje grande y devolver el resultado. Este flujo asíncrono, aunque técnicamente viable, creaba una fricción perceptible en flujos de trabajo de edición rápida, donde la inmediatez es prioritaria sobre la generación asistida de contenido.

La arquitectura de "Copilot en todas partes" (Copilot everywhere) demostró ser un mito técnico en el contexto de aplicaciones de consumo masivo. La infraestructura necesaria para mantener una sesión contextualmente aware en cada instancia del Bloc de Notas abierta generaba una sobrecarga en los servicios backend de Microsoft. La incapacidad para mantener un contexto persistente y de bajo costo en sesiones efímeras de edición de texto llevó a una degradación de la experiencia del usuario, forzando a la empresa a reconsiderar la viabilidad de desplegar agentes de IA en procesos con baja densidad de información.

## La Falacia del Valor Añadido y la Simplificación Forzada

La narrativa corporativa alrededor de la "productividad mejorada por IA" se estrelló contra la realidad del uso cotidiano del Bloc de Notas. Pavan Davuluri, vicepresidente ejecutivo de Windows y Dispositivos, admitió que la decisión se basó en la falta de un valor claro para los usuarios en estas integraciones específicas. Esta admisión es un reconocimiento de que la automatización de tareas triviales, como cambiar el tono de un archivo de texto sin formato, no resuelve un problema real para la mayoría de los usuarios, sino que añade una capa de complejidad innecesaria.

La eliminación de estas funciones es un síntoma de la corrección del mercado tras la burbuja de expectativas inflada en 2023 y 2024. Los usuarios no buscaban un asistente conversacional dentro de su herramienta de toma de notas rápida, sino una herramienta fiable y sin distracciones. La inclusión de botones de IA en la barra de herramientas del Bloc de Notas era un ejercicio de marketing de características (feature creep) que ignoraba los principios de diseño de usabilidad centrados en la tarea. Al eliminar Copilot, Microsoft no está "simplificando" por benevolencia, sino retractándose de una estrategia de producto que sobrevaloró la capacidad de los LLMs para integrarse de manera transparente en flujos de trabajo analógicos.

El modelo de créditos implementado para el uso de estas funciones, limitado a 60 créditos mensuales para suscriptores de Microsoft 365 Personal y Family, y acceso ilimitado para usuarios de Copilot Pro, creaba una barrera artificial en una herramienta que históricamente ha sido gratuita y universal. La monetización de funciones básicas de edición de texto a través de un modelo de suscripción basado en consumo resultó ser poco atractiva para una base de usuarios acostumbrada a la utilidad sin fricciones del Bloc de Notas tradicional.

## Riesgos de Seguridad, Privacidad y el Escudo Legal

Más allá de la inutilidad funcional, la retirada de Copilot no aborda los problemas estructurales de privacidad y seguridad que la integración de IA conlleva. Microsoft ha enfrentado escrutinio por sus prácticas de telemetría y la inserción de publicidad dentro de la interfaz de Copilot, lo que sugiere que los datos del usuario podrían ser utilizados para fines de perfilado publicitario en lugar de limitarse estrictamente al procesamiento de la solicitud. La transformación de una herramienta de productividad en un canal de publicidad invasiva socava la confianza del usuario en la plataforma.

Un incidente crítico, documentado bajo el código de error CW1226324 en enero de 2026, expuso la fragilidad de los permisos de acceso de Copilot. Una vulnerabilidad en el servicio permitió que la IA leyera y resumiera correos electrónicos de las carpetas de "Enviados" y "Borradores" que estaban marcados con etiquetas de confidencialidad. Este fallo de lógica en los permisos de la API de Graph demostró que los mecanismos de aislamiento de datos entre el agente de IA y los datos sensibles del usuario eran insuficientes, permitiendo una fuga de información que permaneció activa durante varias semanas antes de ser detectada y corregida.

La respuesta legal de Microsoft a estos riesgos ha sido la inclusión de descargos de responsabilidad en sus términos de uso, indicando que Copilot es "solo para fines de entretenimiento" y que los deben usar bajo su propio riesgo. Esta postura es contradictoria con el posicionamiento de la herramienta como una solución para tareas profesionales y empresariales. La advertencia de "no confíes en Copilot", emitida por la propia empresa, revela una falta de confianza interna en la fiabilidad de las salidas de sus modelos, sugiriendo que la tecnología se lanzó al mercado antes de alcanzar un estándar de robustez adecuado para entornos de producción críticos.

## Impacto Empresarial y la Ilusión del Retorno de Inversión

La desconexión entre el marketing de IA y la realidad operativa es evidente en el sector empresarial. Un informe del MIT advirtió que el 95% de las empresas que han invertido en inteligencia artificial no han visto un retorno medible en sus ingresos. Esta estadística desmiente la narrativa de que la IA es una necesidad inmediata para la supervivencia empresarial y sugiere que muchas implementaciones, incluidas las de Microsoft en sus productos de consumo, son experimentos costosos con beneficios tangibles limitados.

A pesar de la falta de ROI claro para muchas organizaciones, el gobierno de los Estados Unidos ha firmado acuerdos masivos con Microsoft, como el [contrato Multi-Billion Dollar GSA OneGov](https://origin-www.gsa.gov/about-us/newsroom/news-releases/multibillion-dollar-gsa-onegov-agreement-with-microsoft-brings-steep-discounts-09022025), que ofrece descuentos significativos en Microsoft 365, Copilot y servicios en la nube. Este tipo de acuerdos institucionales crean una lock-in financiero que obliga a las agencias a adoptar tecnologías como Copilot independientemente de su utilidad práctica real, perpetuando el ciclo de inversión en herramientas que, como se ha visto con el Bloc de Notas, pueden ser retiradas o modificadas arbitrariamente por el proveedor.

Los documentos financieros presentados ante la [SEC](https://www.sec.gov/Archives/edgar/data/789019/000119312524242888/d815777dars.pdf) y [SEC](https://www.sec.gov/Archives/edgar/data/0000789019/000119312525245177/d61995dars.pdf) revelan una presión constante por parte de Microsoft para monetizar sus servicios de IA a través de suscripciones recurrentes. La eliminación de funciones gratuitas o integradas en el sistema operativo para reemplazarlas por suscripciones de pago (como Copilot Pro) es una estrategia clara para aumentar el ingreso promedio por usuario (ARPU). Esta táctica, sin embargo, aliena a los usuarios que ven cómo las capacidades de su software se degradan o se encierran detrás de muros de pago sin una mejora proporcional en la utilidad.

## El Futuro de la IA en Herramientas de Productividad

Kevin Scott, CTO de Microsoft, ha señalado que la "memoria" es uno de los problemas cruciales a resolver para mejorar la experiencia del usuario con Copilot. La incapacidad actual del sistema para recordar el contexto de las interacciones anteriores de manera eficiente limita su utilidad en tareas complejas. En el caso específico del Bloc de Notas, la falta de una memoria persistente que entendiera el proyecto o el contexto del archivo que se estaba editando convertía cada interacción en una transacción aislada y estúpida, obligando al usuario a proporcionar contexto repetidamente, lo cual es ineficiente.

La integración de IA en herramientas como el Bloc de Notas o la Herramienta de Recorte, según **informes recientes**, ha demostrado ser un fracaso en términos de adopción orgánica. Los usuarios no han incorporado estos flujos de trabajo en su rutina diaria, prefiriendo herramientas especializadas o la edición manual directa. Esto sugiere que el futuro de la IA en productividad no reside en la omnipresencia, sino en la integración contextual específica y profunda en aplicaciones donde el manejo de datos y la complejidad de la tarea justifiquen la sobrecarga cognitiva y técnica de la IA.

Bea Costa-Gomes, Research Program Manager de Microsoft AI, ha enfatizado la necesidad de entender cómo las personas utilizan las herramientas de IA en su vida diaria. Sin embargo, la retirada de Copilot de estas aplicaciones indica que los datos recopilados mostraron un patrón de uso bajo o nulo. La conclusión técnica es que la integración de LLMs en interfaces de usuario tradicionales sin una reinvención radical de la interacción humano-computador está destinada al fracaso. La "inteligencia" no puede ser simplemente una capa adicional pegada sobre una arquitectura obsoleta; debe ser fundamental para el diseño del sistema.

## Alternativas y el Ecosistema Competitivo

Ante la retirada de Microsoft de este espacio, los usuarios y empresas están buscando alternativas que ofrezcan capacidades similares sin los inconvenientes de la estrategia de "walled garden" de Microsoft. Plataformas como Enterprise Bot y soluciones listadas por Appvizer están ganando terreno al ofrecer flexibilidad y, a menudo, mejores modelos de privacidad de datos. Estas alternativas permiten a los usuarios implementar capacidades de IA en sus flujos de trabajo sin depender de los caprichos de las actualizaciones de Windows 11 o de las decisiones unilaterales de Redmond sobre qué características merecen sobrevivir.

La competencia en el espacio de la IA de productividad se está moviendo hacia modelos más abiertos y personalizables. La eliminación de Copilot del Bloc de Notas abre la puerta a editores de texto de terceros que pueden integrar modelos de código abierto (como Llama o Mistral) localmente, ofreciendo privacidad total y sin costos de suscripción por token. Este cambio hacia la inferencia local y la propiedad de los modelos representa una amenaza existencial para el modelo de negocio de Microsoft basado en la nube, ya que desintermedia al proveedor del servicio y devuelve el control al usuario final.

El mercado está empezando a valorar la especialización sobre la generalización. Mientras Microsoft intentaba poner un mismo asistente genérico en todas partes, los usuarios preferían herramientas optimizadas para tareas específicas. La existencia de alternativas viables indica que el monopolio de Microsoft en el escritorio ya no garantiza la adopción de sus servicios auxiliares, especialmente cuando estos servicios degradan la experiencia del usuario principal o comprometen su seguridad.

## Nuestra lectura

La eliminación de Copilot del Bloc de Notas es una admisión de derrota técnica y una señal de alerta para los arquitectos de sistemas que consideran la IA como una solución universal para problemas de usabilidad. Microsoft ha demostrado que la priorización de la narrativa de mercado sobre la solidez arquitectónica resulta en productos inestables, invasivos y finalmente rechazados por los usuarios. La estrategia de forzar la adopción de IA mediante la integración en el sistema operativo ha fallado, revelando una desconexión profunda entre las capacidades reales de los modelos actuales y las necesidades prácticas de los usuarios de software de productividad.

La vulnerabilidad CW1226324 y los descargos de responsabilidad de "entretenimiento" son pruebas irrefutables de que la tecnología se lanzó antes de estar lista. Los ingenieros y responsables de toma de decisiones deben ser escépticos ante las promesas de "productividad mágica" y evaluar críticamente la latencia, la privacidad y el valor real de cualquier integración de LLM. El futuro pertenece a herramientas que respeten la soberanía del usuario y la integridad de los datos, no a asistentes omnipresentes que leen tu correo privado mientras intentas editar un archivo de texto.

Microsoft ha sacrificado la integridad de sus herramientas más básicas en el altar de la hipérbole de IA, y ahora está pagando el precio con la desconfianza del usuario y un escritorio fragmentado.

## Metodología y Fuentes
- [sec.gov](https://www.sec.gov/Archives/edgar/data/789019/000119312524242888/d815777dars.pdf)
- [sec.gov](https://www.sec.gov/Archives/edgar/data/0000789019/000119312525245177/d61995dars.pdf)
- [origin-gsa.gov](https://origin-www.gsa.gov/about-us/newsroom/news-releases/multibillion-dollar-gsa-onegov-agreement-with-microsoft-brings-steep-discounts-09022025)
- [news.google.com](https://news.google.com/rss/articles/CBMi7AFBVV95cUxQUDlnWURpbGZzUzF5VXV3RmtwakEyZTFQWTdPTV9nZ3hURm5SbW1WTk1HMHRNcDVEQWlfYUI3QWNwcUd0aHkwUno3UXhzeXJtcUxvZDhHZFAyV3dfUnFSeWFSUzFfV19idGRiY0haQlBPbkVUS2Y4ZG1YblFfZnNRTkNybEdHd0trcEJGVXRWVWN4VzdJejVxNWMtUWY5S3laX1JMcTVuMWdUZ3FrcjFjZXdVSlFjQjM1Zm9BeDh3YmpfOG9uZzctTjFUX2g4Tlp3S29rRllmemVLbnI1emNLUmp4M250Wlphb2Vkaw?oc=5)


## Artículos relacionados
- [Halliburton y Schlu](/es/tools/analisis-tecnico-herramientas-perforacion-direccional-fusiones-2026/)
- [Alarma Google Workspace: Tu Automatizació](/es/tools/google-workspace-cli-automatizacion-ia/)
- [Datos Energéticos En Peli](/es/tools/analisis-tecnico-alianza-ace-mercado-datos-energeticos-espanol/)





<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "headline": "Microsoft Elimina Copilot y Los Usuarios Se Preguntan Si Es El Fin del Notepad",
  "description": "Microsoft ha eliminado Copilot y los usuarios se cuestionan si esto marca el fin de Notepad. Descubre las implicaciones y el futuro de estas herramientas.",
  "image": "https://novumworld.com/images/microsoft-elimina-el-nombre-copilot-el-fin-de-una-era-en-notepad-y-snipping-tool.jpg",
  "datePublished": "2026-04-10T13:31:13",
  "author": {
    "@type": "Organization",
    "name": "NovumWorld Editorial Team"
  },
  "publisher": {
    "@type": "Organization",
    "name": "NovumWorld",
    "logo": {
      "@type": "ImageObject",
      "url": "https://novumworld.com/images/logo.png"
    }
  }
}
</script>
