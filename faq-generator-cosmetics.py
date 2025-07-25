import pandas as pd
from openai import OpenAI
from typing import Dict, List, Tuple
import json
import time
from datetime import datetime
import re
import random
import os


from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

if __name__ == "__main__":
    # CONFIGURACIÓN - Usar variable de entorno
    API_KEY = os.getenv('OPENAI_API_KEY')
    
    if not API_KEY:
        print("❌ Error: No se encontró la API key de OpenAI")
        print("Asegúrate de tener un archivo .env con OPENAI_API_KEY")
        exit(1)

class PremiumCosmeticsFAQGenerator:
    """
    Generador PREMIUM de FAQs para productos cosméticos - Máxima calidad
    Actualizado para OpenAI v1.0+ con sistema anti-patrones
    """
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
        # Sistema de validación de calidad
        self.criterios_calidad = {
            "longitud_minima_respuesta": 150,  # Aumentado de 80
            "longitud_maxima_respuesta": 350,  # Mantenemos el máximo
            "palabras_prohibidas": ["cosa", "algo", "etc", "etcétera"],
            "debe_incluir": ["específicamente", "recomendamos", "óptimo", "importante"]
        }
        
        # Sistema anti-patrones: banco de variaciones de preguntas
        self.banco_preguntas = {
            "aplicacion": [
                "¿Cuál es la técnica correcta para aplicar {producto}?",
                "¿Cómo maximizo la efectividad de {producto}?",
                "¿Qué cantidad de {producto} debo usar en cada aplicación?",
                "¿Existe algún truco profesional para aplicar {producto}?",
                "¿En qué orden debo incluir {producto} en mi rutina?",
                "¿Necesito alguna preparación especial antes de usar {producto}?"
            ],
            "compatibilidad": [
                "¿Puedo usar {producto} si tengo tendencia al acné?",
                "¿Es {producto} seguro durante el embarazo o lactancia?",
                "Mi piel es {tipo}, ¿me beneficiará {producto}?",
                "¿Hay alguna contraindicación para usar {producto}?",
                "¿Desde qué edad es recomendable usar {producto}?",
                "¿Funciona {producto} en climas húmedos/secos?"
            ],
            "resultados": [
                "¿En cuántos días notaré cambios visibles con {producto}?",
                "¿Los beneficios de {producto} son acumulativos?",
                "¿Qué puedo esperar después de un mes usando {producto}?",
                "¿Hay un período de adaptación al usar {producto}?",
                "Si dejo de usar {producto}, ¿se revierten los resultados?",
                "¿Cómo sé si {producto} está funcionando correctamente?"
            ],
            "ingredientes": [
                "¿Qué principios activos hacen efectivo a {producto}?",
                "¿Contiene {producto} ingredientes de origen natural?",
                "¿Es {producto} libre de parabenos y sulfatos?",
                "¿La fórmula de {producto} es vegana?",
                "¿Qué concentración de activos tiene {producto}?",
                "¿Los ingredientes de {producto} son fotosensibles?"
            ],
            "diferenciacion": [
                "¿Por qué {producto} justifica su precio premium?",
                "¿Qué tecnología exclusiva usa {producto}?",
                "¿En qué se diferencia {producto} de alternativas más económicas?",
                "¿Qué hace único a {producto} en el mercado?",
                "¿Por qué los dermatólogos recomiendan {producto}?",
                "¿Qué premios o certificaciones tiene {producto}?"
            ],
            "combinaciones": [
                "¿Puedo mezclar {producto} con retinol/vitamina C?",
                "¿{producto} potencia el efecto de otros tratamientos?",
                "¿Debo esperar entre aplicar {producto} y maquillaje?",
                "¿Hay productos que no debo usar junto con {producto}?",
                "¿Cómo integro {producto} si ya uso ácidos?",
                "¿{producto} interfiere con tratamientos médicos?"
            ],
            "conservacion": [
                "¿Cómo sé si {producto} se ha oxidado o deteriorado?",
                "¿Necesita {producto} refrigeración?",
                "¿Cuánto dura {producto} después de abierto?",
                "¿El color/textura de {producto} puede cambiar?",
                "¿Afecta la luz solar a {producto}?",
                "¿Puedo llevar {producto} en el avión?"
            ],
            "precauciones": [
                "¿Es normal sentir hormigueo al usar {producto}?",
                "¿Debo usar SPF adicional con {producto}?",
                "¿Puede {producto} manchar la ropa o almohada?",
                "¿Qué hago si {producto} me irrita?",
                "¿{producto} puede causar purging inicial?",
                "¿Hay zonas donde no debo aplicar {producto}?"
            ]
        }
        
        # Historial para evitar repeticiones
        self.preguntas_usadas = []
    
    def limpiar_html(self, texto_html: str) -> str:
        """
        Limpia el HTML para obtener texto plano
        """
        if pd.isna(texto_html):
            return ""
        # Eliminar etiquetas HTML
        texto = re.sub('<.*?>', ' ', str(texto_html))
        # Limpiar espacios múltiples
        texto = ' '.join(texto.split())
        return texto
    
    def analizar_producto_profundo(self, producto: Dict) -> Dict:
        """
        Análisis profundo del producto para generar mejores FAQs
        """
        # Intentar obtener la descripción con diferentes nombres de columna
        descripcion = ""
        for columna in ['Body HTML', 'Body (HTML)', 'body_html', 'description']:
            if columna in producto and producto[columna]:
                descripcion = self.limpiar_html(producto.get(columna, ''))
                break
        
        # Extraer información clave
        analisis = {
            "tiene_ingredientes": any(word in descripcion.lower() for word in 
                                    ['ácido', 'retinol', 'vitamina', 'colágeno', 'hialurónico']),
            "es_tratamiento": any(word in descripcion.lower() for word in 
                                ['tratamiento', 'serum', 'intensivo', 'concentrado']),
            "menciona_edad": any(word in descripcion.lower() for word in 
                               ['antiedad', 'arrugas', 'firmeza', 'madur']),
            "tipo_producto": self.detectar_tipo_producto(producto.get('Title', ''), descripcion),
            "precio_alto": float(producto.get('Variant Price', 0)) > 50 if producto.get('Variant Price') else False,
            "marca_premium": producto.get('Vendor', '') in ['Natura Bissé', 'La Mer', 'Sisley', 'La Prairie']
        }
        
        return analisis
    
    def detectar_tipo_producto(self, titulo: str, descripcion: str) -> str:
        """
        Detecta el tipo de producto para personalizar las FAQs
        """
        texto_completo = f"{titulo} {descripcion}".lower()
        
        tipos = {
            "serum": ["serum", "sérum", "suero"],
            "crema": ["crema", "cream", "moisturizer"],
            "limpiador": ["limpiador", "cleanser", "jabón", "gel limpiador"],
            "mascarilla": ["mascarilla", "mask", "máscara"],
            "contorno_ojos": ["ojos", "eye", "contorno", "ojeras"],
            "tratamiento": ["tratamiento", "treatment", "ampolla"],
            "protector": ["spf", "protector", "solar", "sunscreen"]
        }
        
        for tipo, palabras in tipos.items():
            if any(palabra in texto_completo for palabra in palabras):
                return tipo
        
        return "cosmético"
    
    def seleccionar_categorias_aleatorias(self, producto: Dict, analisis: Dict) -> List[str]:
        """
        Selecciona 5 categorías de preguntas de forma inteligente pero aleatoria
        """
        todas_categorias = list(self.banco_preguntas.keys())
        
        # Categorías prioritarias según el tipo de producto
        prioridades = []
        
        if analisis['tiene_ingredientes']:
            prioridades.append('ingredientes')
        if analisis['es_tratamiento']:
            prioridades.extend(['resultados', 'combinaciones'])
        if analisis['precio_alto']:
            prioridades.append('diferenciacion')
        if 'retinol' in str(producto).lower() or 'ácido' in str(producto).lower():
            prioridades.append('precauciones')
        
        # Asegurar variedad: máximo 2 categorías prioritarias
        categorias_seleccionadas = random.sample(prioridades, min(2, len(prioridades)))
        
        # Completar con categorías aleatorias
        categorias_restantes = [cat for cat in todas_categorias if cat not in categorias_seleccionadas]
        categorias_adicionales = random.sample(categorias_restantes, 5 - len(categorias_seleccionadas))
        
        categorias_finales = categorias_seleccionadas + categorias_adicionales
        random.shuffle(categorias_finales)  # Mezclar el orden
        
        return categorias_finales[:5]
    
    def crear_prompt_premium(self, producto: Dict, analisis: Dict) -> str:
        """
        Prompt ultra-optimizado para máxima calidad con variabilidad
        """
        # Obtener descripción con diferentes nombres de columna
        descripcion_limpia = ""
        for columna in ['Body HTML', 'Body (HTML)', 'body_html', 'description']:
            if columna in producto and producto[columna]:
                descripcion_limpia = self.limpiar_html(producto.get(columna, ''))
                break
        
        # Seleccionar categorías aleatorias para este producto
        categorias = self.seleccionar_categorias_aleatorias(producto, analisis)
        
        # Crear ejemplos de preguntas específicas
        ejemplos_preguntas = []
        for cat in categorias:
            pregunta_base = random.choice(self.banco_preguntas[cat])
            pregunta = pregunta_base.replace("{producto}", producto.get('Title', 'este producto'))
            pregunta = pregunta.replace("{tipo}", "mixta")  # Placeholder
            ejemplos_preguntas.append(f"- {pregunta}")
        
        # Personalizar según el análisis
        contexto_extra = ""
        if analisis['tiene_ingredientes']:
            contexto_extra += "\nIMPORTANTE: Incluye preguntas sobre los ingredientes activos mencionados."
        if analisis['es_tratamiento']:
            contexto_extra += "\nIMPORTANTE: Incluye preguntas sobre protocolo de uso y combinación con otros productos."
        if analisis['precio_alto']:
            contexto_extra += "\nIMPORTANTE: Justifica el valor del producto con beneficios específicos."
        
        return f"""
        Eres un dermatólogo experto y consultor de belleza de lujo con 20 años de experiencia.
        Genera 5 FAQs EXCEPCIONALES para este producto cosmético.

        PRODUCTO ANALIZADO:
        - Nombre: {producto.get('Title', '')}
        - Marca: {producto.get('Vendor', '')}
        - Descripción: {descripcion_limpia[:600]}
        - Tipo detectado: {analisis['tipo_producto']}
        - Precio: {producto.get('Variant Price', '')}€
        - Tags: {producto.get('Tags', '')}
        {contexto_extra}

        CRITERIOS DE MÁXIMA CALIDAD:
        
        1. PREGUNTAS (Características obligatorias):
           - Deben ser las que REALMENTE haría un cliente exigente
           - Específicas para ESTE producto, no genéricas
           - Reflejar preocupaciones reales de compra online de cosmética premium
           - Entre 10-20 palabras cada pregunta
           - Usar "¿" al inicio y "?" al final SIEMPRE
        
        2. RESPUESTAS (Características obligatorias):
           - Entre 150-350 caracteres (3-5 frases completas y detalladas)
           - CADA respuesta debe incluir AL MENOS 2 de estos elementos:
             * Datos específicos (tiempos, cantidades, porcentajes)
             * Modo de uso detallado
             * Beneficio concreto
             * Consejo profesional
             * Ingrediente clave con su función
           - Tono experto pero accesible
           - NUNCA usar palabras vagas como "etc", "cosa", "algo"
           - Dar información práctica y accionable
           - Evitar respuestas genéricas que podrían aplicar a cualquier producto
        
        3. IMPORTANTE - VARIABILIDAD:
        
        Para este producto específico, crea preguntas inspiradas en estos temas (pero NO copies literalmente):
        {chr(10).join(ejemplos_preguntas)}
        
        MEZCLA el orden y tipo de preguntas. NO sigas un patrón predecible.
        
        4. EJEMPLOS DE ESTILO (úsalos como guía, no copies):
        
        PREGUNTA ESPECÍFICA: "¿El retinol de [producto] es apto para principiantes?"
        RESPUESTA DETALLADA: "Contiene retinol encapsulado al 0.3%, perfecto para iniciarse. Aplica 2 noches por semana las primeras 3 semanas, luego aumenta gradualmente. Los resultados en textura se notan desde la semana 4. Siempre complementa con SPF50+ por las mañanas."
        
        PREGUNTA TÉCNICA: "¿Cómo maximizo la absorción de [producto]?"
        RESPUESTA PROFESIONAL: "Aplica sobre piel ligeramente húmeda para potenciar la penetración de activos. Usa la técnica de presión-liberación: presiona suavemente por 3 segundos en cada zona. Espera 90 segundos antes del siguiente producto. La absorción mejora un 40% con esta técnica."

        RESPONDE ÚNICAMENTE con este JSON:
        {{
            "faq1": {{"pregunta": "...", "respuesta": "..."}},
            "faq2": {{"pregunta": "...", "respuesta": "..."}},
            "faq3": {{"pregunta": "...", "respuesta": "..."}},
            "faq4": {{"pregunta": "...", "respuesta": "..."}},
            "faq5": {{"pregunta": "...", "respuesta": "..."}}
        }}
        """
    
    def validar_calidad_faqs(self, faqs: Dict) -> Tuple[bool, List[str]]:
        """
        Valida que las FAQs cumplan con los estándares de calidad
        """
        errores = []
        
        for i in range(1, 6):
            faq = faqs.get(f'faq{i}', {})
            pregunta = faq.get('pregunta', '')
            respuesta = faq.get('respuesta', '')
            
            # Validar pregunta
            if not pregunta.startswith('¿') or not pregunta.endswith('?'):
                errores.append(f"FAQ{i}: Pregunta mal formateada")
            
            if len(pregunta.split()) < 5:
                errores.append(f"FAQ{i}: Pregunta demasiado corta")
            
            # Validar respuesta
            if len(respuesta) < self.criterios_calidad['longitud_minima_respuesta']:
                errores.append(f"FAQ{i}: Respuesta muy corta ({len(respuesta)} chars)")
            
            if len(respuesta) > self.criterios_calidad['longitud_maxima_respuesta']:
                errores.append(f"FAQ{i}: Respuesta muy larga ({len(respuesta)} chars)")
            
            # Verificar palabras prohibidas
            for palabra in self.criterios_calidad['palabras_prohibidas']:
                if palabra.lower() in respuesta.lower():
                    errores.append(f"FAQ{i}: Contiene palabra vaga '{palabra}'")
        
        return len(errores) == 0, errores
    
    def generar_faqs_con_reintentos(self, producto: Dict, max_intentos: int = 3) -> Dict:
        """
        Genera FAQs con reintentos si no cumplen la calidad
        """
        analisis = self.analizar_producto_profundo(producto)
        
        # Verificar si el producto tiene información suficiente
        descripcion = ""
        for columna in ['Body HTML', 'Body (HTML)', 'body_html', 'description']:
            if columna in producto and producto[columna]:
                descripcion = self.limpiar_html(producto.get(columna, ''))
                break
                
        if len(descripcion) < 50:
            print(f"   ⚠️  Descripción muy corta ({len(descripcion)} chars), usando información básica...")
            # Enriquecer con información genérica basada en el título
            titulo = producto.get('Title', '')
            if 'tónico' in titulo.lower():
                descripcion += " Tónico facial para equilibrar y preparar la piel. Uso diario recomendado."
            elif 'serum' in titulo.lower() or 'sérum' in titulo.lower():
                descripcion += " Tratamiento concentrado para el cuidado facial. Aplicar antes de la crema hidratante."
            elif 'contour' in titulo.lower() or 'contorno' in titulo.lower():
                descripcion += " Tratamiento específico para el contorno de ojos. Reduce arrugas y ojeras."
            elif 'cream' in titulo.lower() or 'crema' in titulo.lower():
                descripcion += " Crema facial nutritiva e hidratante. Aplicar mañana y/o noche."
            
            # Actualizar en el producto
            if 'Body HTML' in producto:
                producto['Body HTML'] = descripcion
            else:
                producto['Body (HTML)'] = descripcion
        
        for intento in range(max_intentos):
            try:
                # Usar GPT-3.5-turbo con configuración optimizada para mejor calidad
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Mantenemos 3.5 por costo
                    messages=[
                        {
                            "role": "system", 
                            "content": """Eres un dermatólogo experto con 20 años de experiencia en cosmética de lujo. 
                            CRITICAL: Genera FAQs de MÁXIMA CALIDAD con respuestas DETALLADAS de 150-350 caracteres.
                            Cada respuesta debe ser específica, práctica y profesional.
                            VARÍA el tipo y orden de preguntas para cada producto.
                            Responde SOLO con JSON válido."""
                        },
                        {
                            "role": "user", 
                            "content": self.crear_prompt_premium(producto, analisis)
                        }
                    ],
                    temperature=0.8,  # Aumentado ligeramente para más creatividad
                    max_tokens=1200,  # Aumentado para respuestas más largas
                    presence_penalty=0.4,  # Aumentado para evitar repeticiones
                    frequency_penalty=0.4,
                    top_p=0.95  # Añadido para mejor calidad
                )
                
                # Parsear respuesta
                respuesta = response.choices[0].message.content
                # Limpiar posibles problemas de formato
                respuesta = respuesta.strip()
                if respuesta.startswith('```json'):
                    respuesta = respuesta[7:]
                if respuesta.endswith('```'):
                    respuesta = respuesta[:-3]
                
                faqs = json.loads(respuesta)
                
                # Validar calidad
                es_valido, errores = self.validar_calidad_faqs(faqs)
                
                if es_valido:
                    # Preparar resultado final
                    resultado = {
                        "Handle": producto.get('Handle', ''),
                        "faq1question (product.metafields.custom.faq1question)": faqs['faq1']['pregunta'],
                        "faq1answer (product.metafields.custom.faq1answer)": faqs['faq1']['respuesta'],
                        "faq2question (product.metafields.custom.faq2question)": faqs['faq2']['pregunta'],
                        "faq2answer (product.metafields.custom.faq2answer)": faqs['faq2']['respuesta'],
                        "faq3question (product.metafields.custom.faq3question)": faqs['faq3']['pregunta'],
                        "faq3answer (product.metafields.custom.faq3answer)": faqs['faq3']['respuesta'],
                        "faq4question (product.metafields.custom.faq4question)": faqs['faq4']['pregunta'],
                        "faq4answer (product.metafields.custom.faq4answer)": faqs['faq4']['respuesta'],
                        "faq5question (product.metafields.custom.faq5question)": faqs['faq5']['pregunta'],
                        "faq5answer (product.metafields.custom.faq5answer)": faqs['faq5']['respuesta'],
                        "_calidad": "PREMIUM",
                        "_intentos": intento + 1
                    }
                    
                    return resultado
                else:
                    print(f"   ⚠️  Intento {intento + 1} - Errores de calidad: {', '.join(errores[:3])}")
                    if intento < max_intentos - 1:
                        print(f"   🔄 Reintentando para mejorar calidad...")
                        time.sleep(1)
                    
            except Exception as e:
                print(f"   ❌ Error en intento {intento + 1}: {str(e)}")
                if intento < max_intentos - 1:
                    time.sleep(2)
        
        return None
    
    def procesar_productos_premium(self, archivo_csv: str, limite: int = 10):
        """
        Procesamiento premium con control de calidad
        """
        print(f"🌟 GENERADOR PREMIUM DE FAQs - MÁXIMA CALIDAD")
        print(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🤖 Modelo: GPT-3.5-turbo (Optimizado)")
        print("="*60)
        
        # Leer CSV
        df = pd.read_csv(archivo_csv)
        total_productos = min(limite, len(df))
        
        print(f"📊 Productos a procesar: {total_productos}")
        print(f"💰 Costo estimado: ${total_productos * 0.006:.2f} USD (GPT-3.5-turbo)")
        print(f"⚡ Tiempo estimado: {total_productos * 3 // 60} minutos")
        print("="*60)
        
        # Confirmar
        confirmar = input("\n¿Proceder con la generación PREMIUM? (s/n): ")
        if confirmar.lower() != 's':
            print("Cancelado.")
            return
        
        resultados = []
        errores = []
        
        # Procesar cada producto
        for idx in range(total_productos):
            producto = df.iloc[idx].to_dict()
            
            print(f"\n[{idx+1}/{total_productos}] {producto.get('Title', 'Unknown')[:50]}")
            print(f"   Marca: {producto.get('Vendor', 'Unknown')}")
            print(f"   Precio: {producto.get('Variant Price', 'N/A')}€")
            
            # Generar FAQs premium
            faqs = self.generar_faqs_con_reintentos(producto)
            
            if faqs:
                resultados.append(faqs)
                print(f"   ✅ FAQs PREMIUM generadas (intentos: {faqs['_intentos']})")
                
                # Mostrar preview
                print(f"\n   📝 Preview FAQ 1:")
                print(f"   P: {faqs['faq1question (product.metafields.custom.faq1question)']}")
                print(f"   R: {faqs['faq1answer (product.metafields.custom.faq1answer)']}")
            else:
                errores.append({
                    'Handle': producto.get('Handle', ''),
                    'Title': producto.get('Title', ''),
                    'Error': 'No se pudo generar con calidad suficiente'
                })
                print(f"   ❌ No se pudo alcanzar la calidad requerida")
            
            # Pausa entre productos (importante para GPT-4)
            if idx < total_productos - 1:
                print(f"\n   ⏳ Esperando antes del siguiente producto...")
                time.sleep(2)
        
        # Guardar resultados
        self.guardar_resultados_premium(resultados, errores)
        
        return resultados, errores
    
    def guardar_resultados_premium(self, resultados: List[Dict], errores: List[Dict]):
        """
        Guardado especial para resultados premium con reporte de calidad
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if resultados:
            # Quitar campos internos antes de guardar
            for r in resultados:
                r.pop('_calidad', None)
                r.pop('_intentos', None)
            
            # Guardar CSV para Matrixify
            df_faqs = pd.DataFrame(resultados)
            archivo_faqs = f'faqs_PREMIUM_{timestamp}.csv'
            df_faqs.to_csv(archivo_faqs, index=False, encoding='utf-8-sig')  # utf-8-sig para Excel
            
            # Crear reporte de calidad detallado
            with open(f'reporte_calidad_{timestamp}.txt', 'w', encoding='utf-8') as f:
                f.write("📊 REPORTE DE CALIDAD - FAQs PREMIUM\n")
                f.write("="*60 + "\n\n")
                f.write(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"🤖 Modelo: GPT-3.5-turbo (Optimizado)\n")
                f.write(f"📦 Archivo procesado: {archivo_faqs}\n\n")
                
                f.write("RESUMEN GENERAL\n")
                f.write("-"*30 + "\n")
                f.write(f"✅ Productos procesados exitosamente: {len(resultados)}\n")
                f.write(f"❌ Productos con error: {len(errores)}\n")
                f.write(f"📈 Tasa de éxito: {len(resultados)/(len(resultados)+len(errores))*100:.1f}%\n")
                f.write(f"💰 Costo estimado: ${len(resultados) * 0.006:.2f} USD\n\n")
                
                f.write("ANÁLISIS DE CALIDAD\n")
                f.write("-"*30 + "\n")
                
                # Estadísticas detalladas
                longitudes_respuestas = []
                longitudes_preguntas = []
                productos_por_marca = {}
                
                for r in resultados:
                    # Analizar longitudes
                    for i in range(1, 6):
                        preg = r.get(f'faq{i}question (product.metafields.custom.faq{i}question)', '')
                        resp = r.get(f'faq{i}answer (product.metafields.custom.faq{i}answer)', '')
                        if preg:
                            longitudes_preguntas.append(len(preg))
                        if resp:
                            longitudes_respuestas.append(len(resp))
                
                f.write("📏 Longitudes:\n")
                f.write(f"  Preguntas:\n")
                f.write(f"    - Promedio: {sum(longitudes_preguntas)/len(longitudes_preguntas):.0f} caracteres\n")
                f.write(f"    - Mínimo: {min(longitudes_preguntas)} caracteres\n")
                f.write(f"    - Máximo: {max(longitudes_preguntas)} caracteres\n")
                f.write(f"  Respuestas:\n")
                f.write(f"    - Promedio: {sum(longitudes_respuestas)/len(longitudes_respuestas):.0f} caracteres\n")
                f.write(f"    - Mínimo: {min(longitudes_respuestas)} caracteres\n")
                f.write(f"    - Máximo: {max(longitudes_respuestas)} caracteres\n\n")
                
                f.write("\n📝 Ejemplos de FAQs generadas:\n")
                f.write("-"*30 + "\n")
                # Mostrar 2 ejemplos
                for idx, r in enumerate(resultados[:2]):
                    f.write(f"\nProducto: {r.get('Handle', 'N/A')}\n")
                    f.write(f"FAQ 1:\n")
                    f.write(f"  P: {r.get('faq1question (product.metafields.custom.faq1question)', '')}\n")
                    f.write(f"  R: {r.get('faq1answer (product.metafields.custom.faq1answer)', '')}\n")
            
            print(f"\n✅ Archivos generados:")
            print(f"   - FAQs Premium: {archivo_faqs}")
            print(f"   - Reporte calidad: reporte_calidad_{timestamp}.txt")
        
        # Guardar errores detallados si los hay
        if errores:
            df_errores = pd.DataFrame(errores)
            archivo_errores = f'errores_premium_{timestamp}.csv'
            df_errores.to_csv(archivo_errores, index=False)
            
            # Crear reporte detallado de errores
            with open(f'errores_detallado_{timestamp}.txt', 'w', encoding='utf-8') as f:
                f.write("🚨 REPORTE DETALLADO DE ERRORES\n")
                f.write("="*60 + "\n\n")
                f.write(f"Total de errores: {len(errores)}\n\n")
                
                for idx, error in enumerate(errores):
                    f.write(f"Error #{idx+1}\n")
                    f.write("-"*30 + "\n")
                    f.write(f"Handle: {error.get('Handle', 'N/A')}\n")
                    f.write(f"Título: {error.get('Title', 'N/A')}\n")
                    f.write(f"Motivo: {error.get('Error', 'N/A')}\n")
                    f.write(f"Sugerencia: Revisar manualmente o reintentarlo con un prompt más específico\n\n")
                
                f.write("\nPOSIBLES CAUSAS COMUNES:\n")
                f.write("-"*30 + "\n")
                f.write("1. Descripción del producto muy corta o vacía\n")
                f.write("2. Caracteres especiales que causan problemas en el JSON\n")
                f.write("3. Límite de reintentos alcanzado sin cumplir criterios de calidad\n")
                f.write("4. Timeout o error de conexión con la API\n")
                
            print(f"   - Errores CSV: {archivo_errores}")
            print(f"   - Errores detallado: errores_detallado_{timestamp}.txt")
        
        print(f"\n📊 RESUMEN FINAL:")
        print(f"   - FAQs generadas: {len(resultados)}")
        print(f"   - Calidad: PREMIUM ⭐⭐⭐⭐⭐")
        print(f"   - Listo para importar en Shopify")


# EJEMPLO DE USO PREMIUM
if __name__ == "__main__":
    # CONFIGURACIÓN - MODIFICAR AQUÍ
    API_KEY = os.getenv('OPENAI_API_KEY', 'tu_api_key_aqui')
    ARCHIVO_CSV = "V4/Products.csv"
    
    # Crear generador premium
    generador = PremiumCosmeticsFAQGenerator(API_KEY)
    
    # Ejemplo de FAQs de máxima calidad esperadas
    print("🌟 EJEMPLO DE FAQs PREMIUM ESPERADAS:\n")
    
    ejemplo_premium = {
        "Producto": "Essential Shock Intense Duo - Natura Bissé",
        "FAQ1": {
            "P": "¿Cuál es la forma correcta de aplicar este dúo reafirmante?",
            "R": "Aplica 2-3 gotas del sérum nocturno con retinol sobre piel limpia, espera 60 segundos y sella con la crema Essential Shock en movimientos ascendentes desde cuello hasta frente."
        },
        "FAQ2": {
            "P": "¿Es compatible con pieles sensibles o reactivas al retinol?",
            "R": "Recomendamos empezar aplicando el sérum con retinol solo 2 noches por semana durante 15 días. Si no hay irritación, aumenta gradualmente hasta uso diario nocturno."
        },
        "FAQ3": {
            "P": "¿En cuánto tiempo notaré mejoras en firmeza y arrugas?",
            "R": "La hidratación profunda es inmediata gracias a los proteoglicanos. Las mejoras visibles en firmeza aparecen a los 15 días y la reducción de arrugas profundas a las 4-6 semanas de uso constante."
        }
    }
    
    for key, value in ejemplo_premium.items():
        if key == "Producto":
            print(f"📦 {value}\n")
        else:
            print(f"{key}:")
            print(f"   {value['P']}")
            print(f"   → {value['R']}\n")
    
    print("="*60)
    
    # Test rápido de conexión
    print("\n🔍 Verificando conexión con OpenAI...")
    try:
        test_client = OpenAI(api_key=API_KEY)
        test_response = test_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Di 'OK'"}],
            max_tokens=10
        )
        print("✅ Conexión exitosa con OpenAI")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("Verifica tu API key y que tengas créditos disponibles")
        exit(1)
    
    # Procesar productos
    resultados, errores = generador.procesar_productos_premium(
        archivo_csv=ARCHIVO_CSV,
        limite=10  # Empezar con 10 productos
    )
    
    print("\n🎉 ¡Proceso PREMIUM completado!")


# NOTAS IMPORTANTES
"""
ACTUALIZADO PARA OpenAI v1.0+ con SISTEMA ANTI-PATRONES

CARACTERÍSTICAS PRINCIPALES:
- Sistema anti-patrones con 50+ variaciones de preguntas
- Selección inteligente y aleatoria de categorías
- Usa GPT-3.5-turbo para reducir costos (10x más barato)
- Validación de calidad automática
- Reportes detallados de calidad y errores

COSTOS ESTIMADOS CON GPT-3.5-turbo:
- 10 productos: ~$0.06 USD (0.05€)
- 100 productos: ~$0.60 USD (0.55€)
- 1400 productos: ~$8.40 USD (7.70€)

Para usar GPT-4 (10x más caro pero mayor calidad):
Cambia model="gpt-3.5-turbo" por model="gpt-4"

SISTEMA ANTI-PATRONES:
- Selección aleatoria de categorías de preguntas
- Mezcla inteligente basada en el tipo de producto
- Variación automática del orden
- Banco de 50+ variaciones de preguntas

REQUERIMIENTOS:
- Python 3.7+
- openai>=1.0.0
- pandas

INSTALACIÓN:
pip install openai pandas

TIEMPO ESTIMADO:
- 10 productos: ~30 segundos
- 100 productos: ~5 minutos
- 1400 productos: ~70 minutos
"""