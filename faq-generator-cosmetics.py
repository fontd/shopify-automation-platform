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
    Generador PREMIUM de FAQs para productos cosméticos - Máxima calidad v2.0
    Actualizado con sistema de reportes unificado y validación avanzada
    """
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
        # Sistema de validación de calidad mejorado
        self.criterios_calidad = {
            "longitud_minima_respuesta": 150,
            "longitud_maxima_respuesta": 350,
            "longitud_optima_min": 200,
            "longitud_optima_max": 300,
            "palabras_prohibidas": ["cosa", "algo", "etc", "etcétera"],
            "palabras_tecnicas": ["dermatólog", "activos", "concentr", "fórmula", "ingredientes", "aplicación", "absorción", "penetración"],
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
        """Limpia el HTML para obtener texto plano"""
        if pd.isna(texto_html):
            return ""
        # Eliminar etiquetas HTML
        texto = re.sub('<.*?>', ' ', str(texto_html))
        # Limpiar espacios múltiples
        texto = ' '.join(texto.split())
        return texto
    
    def obtener_descripcion_producto(self, producto: Dict) -> str:
        """Obtiene descripción del producto desde diferentes columnas posibles"""
        for columna in ['Body HTML', 'Body (HTML)', 'body_html', 'description', 'Description']:
            if columna in producto and producto[columna]:
                return self.limpiar_html(producto[columna])
        return ""
    
    def analizar_producto_profundo(self, producto: Dict) -> Dict:
        """Análisis profundo del producto para generar mejores FAQs"""
        descripcion = self.obtener_descripcion_producto(producto)
        
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
        """Detecta el tipo de producto para personalizar las FAQs"""
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
    
    def enriquecer_descripcion_basica(self, producto: Dict, descripcion: str) -> str:
        """Enriquece descripciones básicas con información inferida del título y otros campos"""
        titulo = producto.get('Title', '').lower()
        precio = producto.get('Variant Price', 0)
        vendor = producto.get('Vendor', '')
        tags = producto.get('Tags', '').lower()
        
        # Información básica inferida
        info_adicional = []
        
        # Por tipo de producto
        if any(word in titulo for word in ['serum', 'sérum', 'suero']):
            info_adicional.append("Tratamiento concentrado en formato sérum de rápida absorción.")
            info_adicional.append("Aplicar sobre piel limpia antes de la crema hidratante.")
        elif any(word in titulo for word in ['crema', 'cream', 'moisturizer']):
            info_adicional.append("Crema facial de textura rica que proporciona hidratación profunda.")
            info_adicional.append("Aplicar mañana y/o noche con movimientos circulares.")
        elif any(word in titulo for word in ['contorno', 'eye', 'ojos']):
            info_adicional.append("Tratamiento específico para el delicado contorno de ojos.")
            info_adicional.append("Aplicar con pequeños toques desde el lagrimal hacia la sien.")
        elif any(word in titulo for word in ['limpiador', 'cleanser', 'gel']):
            info_adicional.append("Producto de limpieza facial que elimina impurezas y maquillaje.")
            info_adicional.append("Aplicar sobre piel húmeda, masajear suavemente y aclarar.")
        elif any(word in titulo for word in ['mascarilla', 'mask']):
            info_adicional.append("Mascarilla facial de tratamiento intensivo.")
            info_adicional.append("Aplicar en capa gruesa, dejar actuar y retirar según instrucciones.")
        
        # Por ingredientes mencionados en título o tags
        if any(word in titulo + ' ' + tags for word in ['retinol', 'retinal']):
            info_adicional.append("Contiene retinol, ingrediente antiedad de eficacia comprobada.")
            info_adicional.append("Usar preferentemente por la noche y complementar con SPF durante el día.")
        elif any(word in titulo + ' ' + tags for word in ['vitamina c', 'vitamin c']):
            info_adicional.append("Rico en vitamina C, potente antioxidante que ilumina la piel.")
            info_adicional.append("Ideal para uso matutino seguido de protector solar.")
        elif any(word in titulo + ' ' + tags for word in ['acido', 'acid', 'ácido']):
            info_adicional.append("Formulado con ácidos que renuevan y mejoran la textura de la piel.")
            info_adicional.append("Introducir gradualmente en la rutina para evitar irritaciones.")
        elif any(word in titulo + ' ' + tags for word in ['hialuronico', 'hyaluronic']):
            info_adicional.append("Contiene ácido hialurónico para hidratación profunda y duradera.")
        
        # Por precio (inferir calidad)
        try:
            precio_float = float(precio) if precio else 0
            if precio_float > 80:
                info_adicional.append("Producto premium de alta gama con ingredientes selectos.")
            elif precio_float > 40:
                info_adicional.append("Producto de gama media-alta con fórmula avanzada.")
            elif precio_float > 15:
                info_adicional.append("Producto de calidad con excelente relación calidad-precio.")
        except:
            pass
        
        # Por marca
        marcas_premium = ['natura bissé', 'la mer', 'sisley', 'la prairie', 'skinceuticals']
        if vendor.lower() in marcas_premium:
            info_adicional.append(f"Desarrollado por {vendor}, marca de prestigio en cosmética de lujo.")
        
        # Combinar descripción original con información adicional
        descripcion_final = descripcion
        if info_adicional:
            descripcion_final += " " + " ".join(info_adicional[:3])  # Máximo 3 líneas adicionales
        
        return descripcion_final
    
    def seleccionar_categorias_aleatorias(self, producto: Dict, analisis: Dict) -> List[str]:
        """Selecciona 5 categorías de preguntas de forma inteligente pero aleatoria"""
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
    
    def generar_contexto_producto(self, analisis: Dict, intento: int) -> str:
        """Genera contexto específico según el análisis del producto y el intento"""
        contexto = []
        
        if analisis['tiene_ingredientes']:
            if intento >= 1:
                contexto.append("\nIMPORTANTE INTENTO {}: Detalla ESPECÍFICAMENTE cada ingrediente activo y su concentración.".format(intento + 1))
            else:
                contexto.append("\nIMPORTANTE: Incluye preguntas sobre ingredientes activos con detalles técnicos.")
        
        if analisis['es_tratamiento']:
            if intento >= 1:
                contexto.append("\nIMPORTANTE INTENTO {}: Incluye protocolo PASO A PASO de aplicación y tiempos exactos.".format(intento + 1))
            else:
                contexto.append("\nIMPORTANTE: Incluye protocolo detallado de uso y combinaciones.")
        
        if analisis['precio_alto']:
            if intento >= 1:
                contexto.append("\nIMPORTANTE INTENTO {}: JUSTIFICA el precio premium con datos CONCRETOS y comparaciones.".format(intento + 1))
            else:
                contexto.append("\nIMPORTANTE: Justifica el valor premium con beneficios específicos.")
        
        if analisis['menciona_edad']:
            contexto.append("\nIMPORTANTE: Incluye información sobre resultados antiedad con plazos específicos.")
        
        return "".join(contexto)
    
    def crear_prompt_premium_adaptativo(self, producto: Dict, analisis: Dict, intento: int) -> str:
        """Prompt que se adapta según el número de intento para mejorar progresivamente"""
        descripcion_limpia = self.obtener_descripcion_producto(producto)
        
        # Seleccionar categorías (cambiar en cada intento para variedad)
        categorias = self.seleccionar_categorias_aleatorias(producto, analisis)
        
        # Crear ejemplos específicos
        ejemplos_preguntas = []
        for cat in categorias:
            pregunta_base = random.choice(self.banco_preguntas[cat])
            pregunta = pregunta_base.replace("{producto}", producto.get('Title', 'este producto'))
            pregunta = pregunta.replace("{tipo}", "mixta")
            ejemplos_preguntas.append(f"- {pregunta}")
        
        # Personalizar según análisis del producto
        contexto_extra = self.generar_contexto_producto(analisis, intento)
        
        # Ajustar instrucciones según el intento
        instrucciones_intento = {
            0: "PRIMERA OPORTUNIDAD: Genera FAQs de máxima calidad desde el primer intento.",
            1: "SEGUNDO INTENTO: El intento anterior no alcanzó la calidad requerida. Sé MÁS ESPECÍFICO y técnico.",
            2: "ÚLTIMO INTENTO: Este es el último intento. Genera respuestas con el MÁXIMO NIVEL DE DETALLE y profesionalidad."
        }
        
        # Criterios de calidad progresivamente más estrictos
        criterios_longitud = {
            0: "Entre 200-350 caracteres",
            1: "Entre 220-350 caracteres (más detalladas)",
            2: "Entre 250-350 caracteres (máximo detalle)"
        }
        
        return f"""
        Eres un dermatólogo experto y consultor de belleza de lujo con 20 años de experiencia.
        
        {instrucciones_intento.get(intento, '')}
        
        PRODUCTO ANALIZADO:
        - Nombre: {producto.get('Title', '')}
        - Marca: {producto.get('Vendor', '')}
        - Descripción: {descripcion_limpia[:600]}
        - Tipo detectado: {analisis['tipo_producto']}
        - Precio: {producto.get('Variant Price', '')}€
        - Tags: {producto.get('Tags', '')}
        {contexto_extra}

        CRITERIOS DE MÁXIMA CALIDAD PARA ESTE INTENTO:
        
        1. PREGUNTAS (Obligatorio):
           - Específicas para ESTE producto exacto, no genéricas
           - Entre 8-15 palabras cada pregunta
           - Usar "¿" al inicio y "?" al final SIEMPRE
           - Reflejar preocupaciones reales de compra online
        
        2. RESPUESTAS (Obligatorio - {criterios_longitud.get(intento, '')}):
           - {criterios_longitud.get(intento, '')} (4-6 frases completas)
           - OBLIGATORIO incluir en CADA respuesta AL MENOS 3 de estos elementos:
             * Datos específicos (cantidades exactas, tiempos, porcentajes)
             * Modo de uso detallado paso a paso
             * Beneficio concreto y medible
             * Consejo profesional basado en experiencia
             * Ingrediente clave con su función específica
             * Recomendación de combinación o precaución
           - Tono experto pero accesible
           - PROHIBIDO usar: "etc", "cosa", "algo", respuestas vagas
           - Dar información práctica y accionable
           - Incluir jerga técnica apropiada (dermatológicamente, concentración, etc.)
        
        3. VARIABILIDAD - Categorías sugeridas para este producto:
        {chr(10).join(ejemplos_preguntas)}
        
        4. EJEMPLOS DE CALIDAD PREMIUM (para inspirarte, NO copies):
        
        PREGUNTA TÉCNICA: "¿La concentración de retinol es adecuada para piel madura?"
        RESPUESTA PREMIUM: "Contiene retinol microencapsulado al 0.5%, concentración óptima para pieles maduras con experiencia previa. Aplicar 3 noches por semana durante las primeras 2 semanas, después aumentar a noches alternas. Los resultados en firmeza y reducción de arrugas son visibles desde la semana 6. Siempre usar SPF50+ al día siguiente."
        
        PREGUNTA APLICACIÓN: "¿Cuál es el protocolo exacto de aplicación nocturna?"
        RESPUESTA DETALLADA: "Limpiar rostro, esperar 15 minutos hasta sequedad completa. Aplicar 2-3 gotas en palma, calentar y presionar suavemente desde centro hacia exterior del rostro. Evitar contorno de ojos. Esperar 20 minutos antes de aplicar crema hidratante. El orden correcto potencia la absorción un 60% según estudios clínicos."

        RESPONDE ÚNICAMENTE con este JSON válido:
        {{
            "faq1": {{"pregunta": "...", "respuesta": "..."}},
            "faq2": {{"pregunta": "...", "respuesta": "..."}},
            "faq3": {{"pregunta": "...", "respuesta": "..."}},
            "faq4": {{"pregunta": "...", "respuesta": "..."}},
            "faq5": {{"pregunta": "...", "respuesta": "..."}}
        }}
        """
    
    def validar_calidad_faqs_mejorada(self, faqs: Dict) -> Tuple[bool, List[str], Dict]:
        """Validación de calidad mejorada con puntuación detallada"""
        errores = []
        puntuaciones = {}
        puntuacion_total = 0
        
        for i in range(1, 6):
            faq = faqs.get(f'faq{i}', {})
            pregunta = faq.get('pregunta', '')
            respuesta = faq.get('respuesta', '')
            puntuacion_faq = 0
            
            # === VALIDACIÓN DE PREGUNTA ===
            if not pregunta.startswith('¿') or not pregunta.endswith('?'):
                errores.append(f"FAQ{i}: Pregunta mal formateada (debe empezar con ¿ y terminar con ?)")
            else:
                puntuacion_faq += 1
            
            palabras_pregunta = len(pregunta.split())
            if palabras_pregunta < 5:
                errores.append(f"FAQ{i}: Pregunta demasiado corta ({palabras_pregunta} palabras)")
            elif 8 <= palabras_pregunta <= 15:
                puntuacion_faq += 2  # Longitud óptima
            else:
                puntuacion_faq += 1
            
            # Verificar especificidad de la pregunta
            palabras_genericas = ['producto', 'esto', 'eso', 'cosa']
            if not any(palabra in pregunta.lower() for palabra in palabras_genericas):
                puntuacion_faq += 1  # Pregunta específica
            
            # === VALIDACIÓN DE RESPUESTA ===
            longitud_respuesta = len(respuesta)
            
            if longitud_respuesta < self.criterios_calidad['longitud_minima_respuesta']:
                errores.append(f"FAQ{i}: Respuesta muy corta ({longitud_respuesta} chars, mínimo {self.criterios_calidad['longitud_minima_respuesta']})")
            elif 200 <= longitud_respuesta <= 300:
                puntuacion_faq += 3  # Longitud óptima
            elif self.criterios_calidad['longitud_minima_respuesta'] <= longitud_respuesta < 200:
                puntuacion_faq += 2  # Longitud aceptable
            else:
                puntuacion_faq += 1
            
            if longitud_respuesta > self.criterios_calidad['longitud_maxima_respuesta']:
                errores.append(f"FAQ{i}: Respuesta muy larga ({longitud_respuesta} chars, máximo {self.criterios_calidad['longitud_maxima_respuesta']})")
            
            # Verificar palabras prohibidas
            for palabra in self.criterios_calidad['palabras_prohibidas']:
                if palabra.lower() in respuesta.lower():
                    errores.append(f"FAQ{i}: Contiene palabra vaga '{palabra}'")
                    puntuacion_faq -= 1
            
            # === CRITERIOS DE CALIDAD PREMIUM ===
            
            # 1. Datos específicos (números, porcentajes, tiempos)
            tiene_datos_especificos = bool(re.search(r'\d+\s*(mg|ml|%|días?|semanas?|meses?|años?|veces?|minutos?|horas?)', respuesta.lower()))
            if tiene_datos_especificos:
                puntuacion_faq += 2
            
            # 2. Palabras técnicas/profesionales
            palabras_tecnicas = ['dermatólog', 'activos', 'concentr', 'fórmula', 'ingredientes', 'aplicación', 'absorción', 'penetración']
            tiene_palabras_tecnicas = any(palabra in respuesta.lower() for palabra in palabras_tecnicas)
            if tiene_palabras_tecnicas:
                puntuacion_faq += 1
            
            # 3. Instrucciones específicas de uso
            instrucciones = ['aplica', 'usa', 'espera', 'combina', 'evita', 'recomendamos']
            tiene_instrucciones = any(palabra in respuesta.lower() for palabra in instrucciones)
            if tiene_instrucciones:
                puntuacion_faq += 1
            
            # 4. Menciona beneficios concretos
            beneficios = ['reduce', 'mejora', 'aumenta', 'estimula', 'protege', 'hidrata', 'nutre']
            tiene_beneficios = any(palabra in respuesta.lower() for palabra in beneficios)
            if tiene_beneficios:
                puntuacion_faq += 1
            
            # 5. Estructura de respuesta (oraciones completas)
            num_oraciones = respuesta.count('.') + respuesta.count('!') + respuesta.count('?')
            if num_oraciones >= 3:
                puntuacion_faq += 1
            
            puntuaciones[f'faq{i}'] = {
                'puntuacion': puntuacion_faq,
                'longitud_pregunta': palabras_pregunta,
                'longitud_respuesta': longitud_respuesta,
                'tiene_datos': tiene_datos_especificos,
                'tiene_tecnicas': tiene_palabras_tecnicas,
                'tiene_instrucciones': tiene_instrucciones,
                'tiene_beneficios': tiene_beneficios
            }
            
            puntuacion_total += puntuacion_faq
        
        # Puntuación promedio (máximo teórico: ~12 puntos por FAQ)
        puntuacion_promedio = puntuacion_total / 5
        calidad_general = "EXCELENTE" if puntuacion_promedio >= 8 else "BUENA" if puntuacion_promedio >= 6 else "ACEPTABLE" if puntuacion_promedio >= 4 else "INSUFICIENTE"
        
        # Criterios de aprobación más estrictos
        es_valido = len(errores) == 0 and puntuacion_promedio >= 5
        
        return es_valido, errores, {
            'puntuacion_total': puntuacion_total,
            'puntuacion_promedio': puntuacion_promedio,
            'calidad_general': calidad_general,
            'detalle_faqs': puntuaciones
        }
    
    def generar_faqs_con_reintentos_mejorado(self, producto: Dict, max_intentos: int = 3) -> Dict:
        """Generación con reintentos mejorada que incluye métricas de calidad"""
        analisis = self.analizar_producto_profundo(producto)
        mejor_resultado = None
        mejor_puntuacion = 0
        historial_intentos = []
        
        # Verificar descripción del producto
        descripcion = self.obtener_descripcion_producto(producto)
        if len(descripcion) < 50:
            descripcion = self.enriquecer_descripcion_basica(producto, descripcion)
            # Actualizar en el producto
            if 'Body HTML' in producto:
                producto['Body HTML'] = descripcion
            else:
                producto['Body (HTML)'] = descripcion
        
        for intento in range(max_intentos):
            try:
                # Ajustar parámetros según el intento
                temperature = 0.7 + (intento * 0.1)  # Aumentar creatividad en reintentos
                
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": f"""Eres un dermatólogo experto con 20 años de experiencia en cosmética de lujo. 
                            INTENTO {intento + 1}/{max_intentos}: {'PRIMERA OPORTUNIDAD - Genera la mejor calidad posible' if intento == 0 else 'MEJORA LA CALIDAD - Sé más específico y técnico' if intento == 1 else 'ÚLTIMO INTENTO - Máximo nivel de detalle y profesionalidad'}
                            
                            CRITICAL: Genera FAQs de MÁXIMA CALIDAD con respuestas DETALLADAS de 200-350 caracteres.
                            Incluye SIEMPRE datos específicos (cantidades, tiempos, porcentajes).
                            VARÍA el tipo y orden de preguntas para cada producto.
                            Responde SOLO con JSON válido."""
                        },
                        {
                            "role": "user", 
                            "content": self.crear_prompt_premium_adaptativo(producto, analisis, intento)
                        }
                    ],
                    temperature=temperature,
                    max_tokens=1500,  # Aumentado para más detalle
                    presence_penalty=0.3 + (intento * 0.1),
                    frequency_penalty=0.3 + (intento * 0.1),
                    top_p=0.95
                )
                
                # Parsear respuesta
                respuesta = response.choices[0].message.content.strip()
                if respuesta.startswith('```json'):
                    respuesta = respuesta[7:]
                if respuesta.endswith('```'):
                    respuesta = respuesta[:-3]
                
                faqs = json.loads(respuesta)
                
                # Validar con el sistema mejorado
                es_valido, errores, metricas = self.validar_calidad_faqs_mejorada(faqs)
                
                historial_intentos.append({
                    'intento': intento + 1,
                    'puntuacion': metricas['puntuacion_promedio'],
                    'calidad': metricas['calidad_general'],
                    'errores': len(errores)
                })
                
                # Guardar mejor resultado hasta ahora
                if metricas['puntuacion_promedio'] > mejor_puntuacion:
                    mejor_puntuacion = metricas['puntuacion_promedio']
                    mejor_resultado = {
                        'faqs': faqs,
                        'metricas': metricas,
                        'intento': intento + 1
                    }
                
                if es_valido and metricas['calidad_general'] in ['EXCELENTE', 'BUENA']:
                    print(f"   ✅ Calidad {metricas['calidad_general']} alcanzada en intento {intento + 1}")
                    break
                else:
                    print(f"   ⚠️  Intento {intento + 1}: {metricas['calidad_general']} (puntuación: {metricas['puntuacion_promedio']:.1f})")
                    if intento < max_intentos - 1:
                        print(f"      Errores: {', '.join(errores[:2])}...")
                        time.sleep(1)
                        
            except Exception as e:
                print(f"   ❌ Error en intento {intento + 1}: {str(e)}")
                historial_intentos.append({
                    'intento': intento + 1,
                    'error': str(e)
                })
                if intento < max_intentos - 1:
                    time.sleep(2)
        
        # Usar el mejor resultado obtenido
        if mejor_resultado:
            faqs = mejor_resultado['faqs']
            metricas = mejor_resultado['metricas']
            
            # Preparar resultado final con métricas detalladas
            resultado = {
                "Handle": producto.get('Handle', ''),
                "Metafield: custom.faq1question [single_line_text_field]": faqs['faq1']['pregunta'],
                "Metafield: custom.faq1answer [multi_line_text_field]": faqs['faq1']['respuesta'],
                "Metafield: custom.faq2question [single_line_text_field]": faqs['faq2']['pregunta'],
                "Metafield: custom.faq2answer [multi_line_text_field]": faqs['faq2']['respuesta'],
                "Metafield: custom.faq3question [single_line_text_field]": faqs['faq3']['pregunta'],
                "Metafield: custom.faq3answer [multi_line_text_field]": faqs['faq3']['respuesta'],
                "Metafield: custom.faq4question [single_line_text_field]": faqs['faq4']['pregunta'],
                "Metafield: custom.faq4answer [multi_line_text_field]": faqs['faq4']['respuesta'],
                "Metafield: custom.faq5question [single_line_text_field]": faqs['faq5']['pregunta'],
                "Metafield: custom.faq5answer [multi_line_text_field]": faqs['faq5']['respuesta'],
                "_calidad": metricas['calidad_general'],
                "_intentos": mejor_resultado['intento'],
                "_puntuacion": metricas['puntuacion_promedio'],
                "_historial": historial_intentos
            }
            
            return resultado
        
        return None
    
    def extraer_titulo_desde_handle(self, handle: str) -> str:
        """Convierte el handle en un título legible"""
        if not handle:
            return "Producto sin identificar"
        
        # Convertir handle a título
        titulo = handle.replace('-', ' ').replace('_', ' ')
        titulo = ' '.join(word.capitalize() for word in titulo.split())
        
        return titulo
    
    def evaluar_calidad_respuesta(self, respuesta: str) -> str:
        """Evalúa la calidad de una respuesta individual"""
        longitud = len(respuesta)
        
        # Criterios de calidad
        tiene_datos_especificos = any(char.isdigit() for char in respuesta)
        tiene_palabras_tecnicas = any(word in respuesta.lower() for word in 
                                     ['activos', 'ingredientes', 'dermatólog', 'concentr', 'fórmula'])
        evita_palabras_vagas = not any(word in respuesta.lower() for word in 
                                      ['cosa', 'algo', 'etc', 'etcétera'])
        
        puntuacion = 0
        if 150 <= longitud <= 350:
            puntuacion += 2
        elif longitud >= 150:
            puntuacion += 1
        
        if tiene_datos_especificos:
            puntuacion += 1
        if tiene_palabras_tecnicas:
            puntuacion += 1
        if evita_palabras_vagas:
            puntuacion += 1
        
        if puntuacion >= 4:
            return "EXCELENTE ⭐⭐⭐⭐⭐"
        elif puntuacion >= 3:
            return "BUENA ⭐⭐⭐⭐"
        elif puntuacion >= 2:
            return "ACEPTABLE ⭐⭐⭐"
        else:
            return "MEJORABLE ⭐⭐"
    
    def escribir_estadisticas_calidad(self, f, resultados):
        """Escribe estadísticas detalladas de calidad"""
        if not resultados:
            return
        
        f.write("📈 ESTADÍSTICAS DE CALIDAD\n")
        f.write("-" * 50 + "\n")
        
        # Calcular estadísticas
        longitudes_respuestas = []
        longitudes_preguntas = []
        intentos = []
        
        for r in resultados:
            intentos.append(r.get('_intentos', 1))
            
            for i in range(1, 6):
                preg_key = f'Metafield: custom.faq{i}question [single_line_text_field]'
                resp_key = f'Metafield: custom.faq{i}answer [multi_line_text_field]'
                
                pregunta = r.get(preg_key, '')
                respuesta = r.get(resp_key, '')
                
                if pregunta:
                    longitudes_preguntas.append(len(pregunta))
                if respuesta:
                    longitudes_respuestas.append(len(respuesta))
        
        # Escribir estadísticas
        f.write(f"📝 Total de FAQs generadas: {len(longitudes_respuestas)}\n")
        f.write(f"📏 Longitud promedio de respuestas: {sum(longitudes_respuestas)/len(longitudes_respuestas):.0f} caracteres\n")
        f.write(f"📏 Longitud promedio de preguntas: {sum(longitudes_preguntas)/len(longitudes_preguntas):.0f} caracteres\n")
        f.write(f"🎯 Intentos promedio por producto: {sum(intentos)/len(intentos):.1f}\n")
        f.write(f"✅ Respuestas que cumplen longitud mínima: {sum(1 for l in longitudes_respuestas if l >= 150)}/{len(longitudes_respuestas)} ({sum(1 for l in longitudes_respuestas if l >= 150)/len(longitudes_respuestas)*100:.1f}%)\n")
        f.write(f"⚡ Respuestas óptimas (200-300 chars): {sum(1 for l in longitudes_respuestas if 200 <= l <= 300)}/{len(longitudes_respuestas)} ({sum(1 for l in longitudes_respuestas if 200 <= l <= 300)/len(longitudes_respuestas)*100:.1f}%)\n\n")
    
    def escribir_analisis_detallado(self, f, resultados):
        """Escribe análisis detallado de patrones y calidad"""
        f.write("🔍 ANÁLISIS DETALLADO\n")
        f.write("-" * 50 + "\n")
        
        # Análisis de palabras clave en preguntas
        categorias_detectadas = {
            'aplicación': ['aplicar', 'usar', 'utilizar', 'modo de uso'],
            'compatibilidad': ['piel', 'tipo', 'sensible', 'apto'],
            'resultados': ['cuánto', 'tiempo', 'resultados', 'efectos'],
            'ingredientes': ['contiene', 'ingredientes', 'activos', 'fórmula'],
            'diferenciación': ['diferencia', 'único', 'especial', 'ventaja'],
            'precauciones': ['seguro', 'contraindicación', 'cuidado', 'evitar']
        }
        
        conteo_categorias = {cat: 0 for cat in categorias_detectadas.keys()}
        
        for resultado in resultados:
            for i in range(1, 6):
                preg_key = f'Metafield: custom.faq{i}question [single_line_text_field]'
                pregunta = resultado.get(preg_key, '').lower()
                
                for categoria, palabras in categorias_detectadas.items():
                    if any(palabra in pregunta for palabra in palabras):
                        conteo_categorias[categoria] += 1
                        break
        
        f.write("📊 Distribución de tipos de preguntas:\n")
        total_preguntas = len(resultados) * 5
        for categoria, count in conteo_categorias.items():
            porcentaje = (count / total_preguntas) * 100
            f.write(f"   {categoria.capitalize()}: {count}/{total_preguntas} ({porcentaje:.1f}%)\n")
        
        f.write(f"\n✅ Variedad de preguntas: {'EXCELENTE' if len([c for c in conteo_categorias.values() if c > 0]) >= 4 else 'BUENA' if len([c for c in conteo_categorias.values() if c > 0]) >= 3 else 'MEJORABLE'}\n\n")
    
    def escribir_seccion_errores(self, f, errores):
        """Escribe sección detallada de errores"""
        f.write("❌ PRODUCTOS CON ERRORES\n")
        f.write("-" * 50 + "\n")
        f.write(f"Total de errores: {len(errores)}\n\n")
        
        for idx, error in enumerate(errores, 1):
            f.write(f"Error #{idx}\n")
            f.write(f"   Handle: {error.get('Handle', 'N/A')}\n")
            f.write(f"   Título: {error.get('Title', 'N/A')}\n")
            f.write(f"   Motivo: {error.get('Error', 'N/A')}\n")
            f.write(f"   Recomendación: Revisar descripción del producto\n\n")
    
    def escribir_recomendaciones(self, f, resultados, errores):
        """Escribe recomendaciones basadas en el análisis"""
        f.write("💡 RECOMENDACIONES Y PRÓXIMOS PASOS\n")
        f.write("-" * 50 + "\n")
        
        tasa_exito = len(resultados) / (len(resultados) + len(errores)) * 100
        
        if tasa_exito >= 95:
            f.write("🎉 EXCELENTE: Tasa de éxito superior al 95%\n")
        elif tasa_exito >= 80:
            f.write("👍 BUENO: Tasa de éxito superior al 80%\n")
        else:
            f.write("⚠️  MEJORABLE: Tasa de éxito por debajo del 80%\n")
        
        f.write("\n📋 Acciones recomendadas:\n")
        f.write("1. ✅ Revisar el archivo CSV generado para importar en Shopify\n")
        f.write("2. 🔍 Verificar manualmente 2-3 FAQs para confirmar calidad\n")
        f.write("3. 📊 Si la calidad es buena, procesar el resto de productos\n")
        
        if errores:
            f.write("4. ❌ Revisar productos con errores y mejorar sus descripciones\n")
        
        f.write("5. 🚀 Considerar ejecutar con límite mayor para procesar más productos\n\n")
        
        f.write("🔧 Parámetros sugeridos para la próxima ejecución:\n")
        if tasa_exito >= 90:
            f.write("   - Límite recomendado: 50-100 productos\n")
        elif tasa_exito >= 80:
            f.write("   - Límite recomendado: 20-50 productos\n")
        else:
            f.write("   - Límite recomendado: 10-20 productos\n")
            f.write("   - Revisar y mejorar descripciones de productos primero\n")
    
    def crear_reporte_unificado(self, resultados: List[Dict], errores: List[Dict], archivo: str, timestamp: str):
        """Crea un reporte unificado completo con todas las FAQs en formato legible"""
        with open(archivo, 'w', encoding='utf-8') as f:
            # CABECERA DEL REPORTE
            f.write("🌟" + "="*80 + "🌟\n")
            f.write("   REPORTE COMPLETO - GENERADOR DE FAQs PREMIUM v2.0\n")
            f.write("🌟" + "="*80 + "🌟\n\n")
            
            # INFORMACIÓN GENERAL
            f.write("📊 INFORMACIÓN GENERAL\n")
            f.write("-" * 50 + "\n")
            f.write(f"📅 Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"🤖 Modelo utilizado: GPT-3.5-turbo (Optimizado con validación avanzada)\n")
            f.write(f"✅ Productos procesados exitosamente: {len(resultados)}\n")
            f.write(f"❌ Productos con errores: {len(errores)}\n")
            f.write(f"📈 Tasa de éxito: {len(resultados)/(len(resultados)+len(errores))*100:.1f}%\n")
            f.write(f"💰 Costo estimado: ${len(resultados) * 0.008:.3f} USD\n")
            f.write(f"⏱️  Tiempo de procesamiento: {len(resultados) * 4} segundos aprox.\n\n")
            
            # ESTADÍSTICAS DE CALIDAD
            self.escribir_estadisticas_calidad(f, resultados)
            
            # FAQS GENERADAS - SECCIÓN PRINCIPAL
            f.write("\n🎯 FAQs GENERADAS POR PRODUCTO\n")
            f.write("=" * 80 + "\n\n")
            
            for idx, resultado in enumerate(resultados, 1):
                handle = resultado.get('Handle', 'unknown')
                
                # Extraer información del producto del handle o título
                titulo_producto = self.extraer_titulo_desde_handle(handle)
                
                f.write(f"[{idx:02d}] {titulo_producto}\n")
                f.write("─" * 80 + "\n")
                f.write(f"🔗 Handle: {handle}\n")
                f.write(f"🎯 Calidad: {resultado.get('_calidad', 'PREMIUM')} ⭐⭐⭐⭐⭐\n")
                f.write(f"🔄 Intentos necesarios: {resultado.get('_intentos', 1)}\n")
                f.write(f"📊 Puntuación: {resultado.get('_puntuacion', 0):.1f}/10\n\n")
                
                # Mostrar las 5 FAQs de forma clara y organizada
                for faq_num in range(1, 6):
                    pregunta_key = f'Metafield: custom.faq{faq_num}question [single_line_text_field]'
                    respuesta_key = f'Metafield: custom.faq{faq_num}answer [multi_line_text_field]' 
                    
                    pregunta = resultado.get(pregunta_key, '')
                    respuesta = resultado.get(respuesta_key, '')
                    
                    if pregunta and respuesta:
                        f.write(f"❓ FAQ {faq_num}\n")
                        f.write(f"P: {pregunta}\n")
                        f.write(f"R: {respuesta}\n")
                        f.write(f"   📏 Longitud: {len(respuesta)} caracteres\n")
                        f.write(f"   📊 Calidad: {self.evaluar_calidad_respuesta(respuesta)}\n\n")
                
                f.write("\n" + "="*80 + "\n\n")
            
            # SECCIÓN DE ANÁLISIS DETALLADO
            self.escribir_analisis_detallado(f, resultados)
            
            # ERRORES SI LOS HAY
            if errores:
                self.escribir_seccion_errores(f, errores)
            
            # RECOMENDACIONES Y PRÓXIMOS PASOS
            self.escribir_recomendaciones(f, resultados, errores)
            
            # PIE DEL REPORTE
            f.write("\n🌟" + "="*80 + "🌟\n")
            f.write("   FIN DEL REPORTE - Shopify Automation Platform\n")
            f.write("🌟" + "="*80 + "🌟\n")
    
    def guardar_resultados_premium_mejorados(self, resultados: List[Dict], errores: List[Dict]):
        """Sistema de guardado mejorado con reporte unificado completo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if resultados:
            # 1. GUARDAR CSV PARA SHOPIFY (sin cambios)
            df_faqs_clean = []
            for r in resultados:
                clean_result = {k: v for k, v in r.items() if not k.startswith('_')}
                df_faqs_clean.append(clean_result)
            
            df_faqs = pd.DataFrame(df_faqs_clean)
            archivo_faqs = f'faqs_PREMIUM_{timestamp}.csv'
            df_faqs.to_csv(archivo_faqs, index=False, encoding='utf-8-sig')
            
            # 2. REPORTE UNIFICADO COMPLETO EN TXT
            archivo_reporte = f'REPORTE_COMPLETO_{timestamp}.txt'
            self.crear_reporte_unificado(resultados, errores, archivo_reporte, timestamp)
            
            print(f"\n✅ Archivos generados:")
            print(f"   📊 Reporte completo: {archivo_reporte}")
            print(f"   📄 FAQs para Shopify: {archivo_faqs}")
            
            if errores:
                archivo_errores = f'errores_{timestamp}.csv'
                pd.DataFrame(errores).to_csv(archivo_errores, index=False)
                print(f"   ❌ Errores: {archivo_errores}")
        
        return archivo_reporte if resultados else None
    
    def mostrar_resumen_final(self, resultados, errores, metricas, tiempo_total):
        """Muestra un resumen final detallado del procesamiento"""
        print(f"\n🎉 PROCESAMIENTO COMPLETADO")
        print("="*70)
        
        total_procesados = len(resultados) + len(errores)
        tasa_exito = len(resultados) / total_procesados * 100 if total_procesados > 0 else 0
        
        print(f"📊 RESULTADOS FINALES:")
        print(f"   ✅ Productos exitosos: {len(resultados)}")
        print(f"   ❌ Productos con error: {len(errores)}")
        print(f"   📈 Tasa de éxito: {tasa_exito:.1f}%")
        print(f"   ⏱️  Tiempo total: {tiempo_total/60:.1f} minutos")
        
        if resultados:
            # Métricas de calidad
            puntuacion_promedio = sum(metricas['puntuaciones']) / len(metricas['puntuaciones'])
            intentos_promedio = sum(metricas['intentos_promedio']) / len(metricas['intentos_promedio'])
            tiempo_promedio = sum(metricas['tiempo_por_producto']) / len(metricas['tiempo_por_producto'])
            
            print(f"\n📈 MÉTRICAS DE CALIDAD:")
            print(f"   ⭐ Puntuación promedio: {puntuacion_promedio:.1f}/10")
            print(f"   🔄 Intentos promedio: {intentos_promedio:.1f}")
            print(f"   ⏱️  Tiempo promedio por producto: {tiempo_promedio:.1f}s")
            
            print(f"\n🏆 DISTRIBUCIÓN DE CALIDAD:")
            for calidad, count in metricas['calidades'].items():
                if count > 0:
                    porcentaje = count / len(resultados) * 100
                    estrellas = "⭐" * (5 if calidad == 'EXCELENTE' else 4 if calidad == 'BUENA' else 3 if calidad == 'ACEPTABLE' else 2)
                    print(f"   {calidad}: {count} productos ({porcentaje:.1f}%) {estrellas}")
            
            # Recomendaciones basadas en resultados
            print(f"\n💡 RECOMENDACIONES:")
            if puntuacion_promedio >= 8:
                print(f"   🚀 Excelente calidad! Puedes procesar más productos con confianza.")
            elif puntuacion_promedio >= 6:
                print(f"   👍 Buena calidad. Considera revisar productos con puntuación baja.")
            else:
                print(f"   ⚠️  Calidad mejorable. Revisa las descripciones de productos.")
            
            if intentos_promedio > 2:
                print(f"   🔧 Muchos reintentos necesarios. Considera mejorar las descripciones base.")
            
            # Costo real
            costo_real = len(resultados) * intentos_promedio * 0.003  # Ajustado por reintentos
            print(f"\n💰 COSTO REAL: ${costo_real:.3f} USD")
        
        print(f"\n📁 Archivos generados listos para usar!")
        print("="*70)
    
    def procesar_productos_premium_mejorado(self, archivo_csv: str, limite: int = 10):
        """Procesamiento premium con métricas detalladas y progreso visual"""
        print(f"🌟 GENERADOR PREMIUM DE FAQs - MÁXIMA CALIDAD v2.0")
        print(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🤖 Modelo: GPT-3.5-turbo (Optimizado con validación avanzada)")
        print("="*70)
        
        # Leer y analizar CSV
        df = pd.read_csv(archivo_csv)
        total_productos = min(limite, len(df))
        
        # Análisis previo del dataset
        productos_con_descripcion = sum(1 for _, row in df.head(total_productos).iterrows() 
                                       if len(self.obtener_descripcion_producto(row.to_dict())) > 50)
        
        print(f"📊 ANÁLISIS DEL DATASET:")
        print(f"   Total productos en CSV: {len(df)}")
        print(f"   Productos a procesar: {total_productos}")
        print(f"   Productos con descripción rica: {productos_con_descripcion}/{total_productos} ({productos_con_descripcion/total_productos*100:.1f}%)")
        print(f"💰 Costo estimado: ${total_productos * 0.008:.3f} USD")  # Ligeramente mayor por reintentos
        print(f"⚡ Tiempo estimado: {total_productos * 4 // 60} min {total_productos * 4 % 60} seg")
        print("="*70)
        
        # Confirmar
        confirmar = input(f"\n¿Proceder con la generación PREMIUM mejorada? (s/n): ")
        if confirmar.lower() != 's':
            print("Cancelado.")
            return
        
        # Inicializar métricas
        inicio_proceso = time.time()
        resultados = []
        errores = []
        metricas_globales = {
            'puntuaciones': [],
            'calidades': {'EXCELENTE': 0, 'BUENA': 0, 'ACEPTABLE': 0, 'INSUFICIENTE': 0},
            'intentos_promedio': [],
            'tiempo_por_producto': []
        }
        
        print(f"\n🚀 INICIANDO PROCESAMIENTO...")
        print("="*70)
        
        # Procesar cada producto
        for idx in range(total_productos):
            inicio_producto = time.time()
            producto = df.iloc[idx].to_dict()
            
            # Header del producto
            print(f"\n[{idx+1:02d}/{total_productos}] {producto.get('Title', 'Unknown')[:55]}")
            print(f"{'─' * 70}")
            print(f"   🏷️  Marca: {producto.get('Vendor', 'Unknown')}")
            print(f"   💰 Precio: {producto.get('Variant Price', 'N/A')}€")
            
            # Análisis previo del producto
            descripcion = self.obtener_descripcion_producto(producto)
            print(f"   📝 Descripción: {len(descripcion)} caracteres {'✅' if len(descripcion) > 100 else '⚠️' if len(descripcion) > 50 else '❌'}")
            
            # Generar FAQs
            print(f"   🤖 Generando FAQs...")
            faqs = self.generar_faqs_con_reintentos_mejorado(producto)
            
            tiempo_producto = time.time() - inicio_producto
            metricas_globales['tiempo_por_producto'].append(tiempo_producto)
            
            if faqs:
                resultados.append(faqs)
                
                # Actualizar métricas
                puntuacion = faqs['_puntuacion']
                calidad = faqs['_calidad']
                intentos = faqs['_intentos']
                
                metricas_globales['puntuaciones'].append(puntuacion)
                metricas_globales['calidades'][calidad] += 1
                metricas_globales['intentos_promedio'].append(intentos)
                
                # Mostrar resultado
                print(f"   ✅ FAQs generadas: {calidad} (⭐ {puntuacion:.1f}/10)")
                print(f"   🔄 Intentos: {intentos} | ⏱️ Tiempo: {tiempo_producto:.1f}s")
                
                # Preview de la mejor FAQ
                mejor_faq_idx = max(range(1, 6), key=lambda i: 
                    len(faqs.get(f'faq{i}answer (product.metafields.custom.faq{i}answer)', '')))
                
                pregunta_key = f'Metafield: custom.faq{mejor_faq_idx}question [single_line_text_field]'
                respuesta_key = f'Metafield: custom.faq{mejor_faq_idx}answer [multi_line_text_field]'
                
                print(f"\n   📋 Preview mejor FAQ:")
                print(f"   P: {faqs.get(pregunta_key, '')}")
                print(f"   R: {faqs.get(respuesta_key, '')[:120]}{'...' if len(faqs.get(respuesta_key, '')) > 120 else ''}")
                
            else:
                errores.append({
                    'Handle': producto.get('Handle', ''),
                    'Title': producto.get('Title', ''),
                    'Error': 'No se pudo generar con calidad suficiente tras múltiples intentos',
                    'Descripcion_chars': len(descripcion)
                })
                print(f"   ❌ Error: No se alcanzó la calidad mínima")
                print(f"   💡 Sugerencia: Revisar descripción del producto")
            
            # Mostrar progreso general
            if idx < total_productos - 1:
                progreso = (idx + 1) / total_productos * 100
                tiempo_transcurrido = time.time() - inicio_proceso
                tiempo_estimado_restante = (tiempo_transcurrido / (idx + 1)) * (total_productos - idx - 1)
                
                print(f"\n   📊 Progreso: {progreso:.1f}% | ⏱️ Tiempo restante: {tiempo_estimado_restante/60:.1f} min")
                
                # Métricas intermedias
                if resultados:
                    puntuacion_promedio = sum(metricas_globales['puntuaciones']) / len(metricas_globales['puntuaciones'])
                    print(f"   📈 Calidad promedio hasta ahora: ⭐ {puntuacion_promedio:.1f}/10")
                
                print(f"   ⏳ Pausa antes del siguiente producto...")
                time.sleep(2)
        
        # Finalizar procesamiento
        tiempo_total = time.time() - inicio_proceso
        
        # Guardar resultados con el nuevo sistema
        if resultados:
            archivo_reporte = self.guardar_resultados_premium_mejorados(resultados, errores)
            
            # Mostrar resumen final detallado
            self.mostrar_resumen_final(resultados, errores, metricas_globales, tiempo_total)
            
            return resultados, errores, archivo_reporte
        else:
            print(f"\n❌ No se generaron FAQs válidas.")
            return [], errores, None


# EJEMPLO DE USO PREMIUM v2.0
if __name__ == "__main__":
    # CONFIGURACIÓN - MODIFICAR AQUÍ
    API_KEY = os.getenv('OPENAI_API_KEY', 'tu_api_key_aqui')
    ARCHIVO_CSV = "Products.csv"
    
    # Crear generador premium
    generador = PremiumCosmeticsFAQGenerator(API_KEY)
    
    # Ejemplo de FAQs de máxima calidad esperadas v2.0
    print("🌟 EJEMPLO DE FAQs PREMIUM ESPERADAS v2.0:\n")
    
    ejemplo_premium = {
        "Producto": "Essential Shock Intense Duo - Natura Bissé",
        "FAQ1": {
            "P": "¿Cuál es el protocolo exacto de aplicación para este tratamiento reafirmante?",
            "R": "Aplicar 2-3 gotas del sérum con retinol encapsulado al 0.3% sobre piel completamente limpia y seca, esperar 90 segundos para absorción completa, después sellar con la crema Essential Shock mediante movimientos ascendentes desde cuello hasta frente. La secuencia correcta potencia la penetración de activos un 65% según estudios clínicos."
        },
        "FAQ2": {
            "P": "¿Es seguro para pieles sensibles o con primera experiencia en retinol?",
            "R": "El retinol microencapsulado permite introducción gradual: comenzar aplicando solo 2 noches por semana durante las primeras 3 semanas. Si no aparece irritación, aumentar a noches alternas durante 2 semanas más, después uso diario nocturno. La encapsulación reduce irritación un 40% comparado con retinol convencional."
        },
        "FAQ3": {
            "P": "¿En qué tiempo específico notaré mejoras visibles en firmeza y arrugas?",
            "R": "La hidratación profunda es inmediata gracias a los proteoglicanos de alto peso molecular. Mejoras en textura aparecen desde la semana 2, incremento visible de firmeza a los 21 días, y reducción significativa de arrugas profundas entre las semanas 6-8 de uso constante según evaluaciones dermatológicas."
        }
    }
    
    for key, value in ejemplo_premium.items():
        if key == "Producto":
            print(f"📦 {value}\n")
        else:
            print(f"{key}:")
            print(f"   {value['P']}")
            print(f"   → {value['R']}\n")
    
    print("="*70)
    
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
    
    # Procesar productos con el sistema mejorado
    resultados, errores, archivo_reporte = generador.procesar_productos_premium_mejorado(
        archivo_csv=ARCHIVO_CSV,
        limite=10  # Empezar con 10 productos
    )
    
    if archivo_reporte:
        print(f"\n🎉 ¡Proceso PREMIUM v2.0 completado!")
        print(f"📊 Consulta el reporte completo en: {archivo_reporte}")
        print(f"📁 Archivo CSV para Shopify listo para importar")
    else:
        print(f"\n❌ No se pudieron generar FAQs. Revisar configuración y archivo CSV.")


# NOTAS IMPORTANTES v2.0
"""
ACTUALIZADO PARA OpenAI v1.0+ con SISTEMA DE REPORTES UNIFICADO v2.0

NUEVAS CARACTERÍSTICAS v2.0:
- ✨ Reporte unificado completo en formato TXT legible
- 📊 Sistema de puntuación avanzado (0-10 por FAQ)
- 🔄 Reintentos inteligentes con prompts adaptativos
- 📈 Métricas de calidad en tiempo real
- 🎯 Validación de calidad mejorada con múltiples criterios
- ⏱️ Progreso visual detallado con tiempo estimado
- 🏆 Análisis de distribución de calidad por producto

CARACTERÍSTICAS PRINCIPALES HEREDADAS:
- Sistema anti-patrones con 50+ variaciones de preguntas
- Selección inteligente y aleatoria de categorías
- Usa GPT-3.5-turbo para reducir costos (10x más barato que GPT-4)
- Validación de calidad automática
- Reportes detallados de calidad y errores

ARCHIVOS GENERADOS:
1. 📊 REPORTE_COMPLETO_[timestamp].txt - Reporte unificado con todas las FAQs
2. 📄 faqs_PREMIUM_[timestamp].csv - Archivo CSV para importar en Shopify
3. ❌ errores_[timestamp].csv - Lista de productos con errores (si los hay)

COSTOS ESTIMADOS CON GPT-3.5-turbo v2.0:
- 10 productos: ~$0.08 USD (0.07€) - Incluye reintentos
- 100 productos: ~$0.80 USD (0.73€)
- 1400 productos: ~$11.20 USD (10.22€)

Para usar GPT-4 (10x más caro pero mayor calidad):
Cambia model="gpt-3.5-turbo" por model="gpt-4"

SISTEMA ANTI-PATRONES v2.0:
- Selección aleatoria de categorías de preguntas
- Mezcla inteligente basada en el tipo de producto
- Variación automática del orden
- Banco de 50+ variaciones de preguntas
- Prompts adaptativos según número de intento

SISTEMA DE PUNTUACIÓN v2.0:
- Longitud óptima de preguntas y respuestas
- Presencia de datos específicos (números, tiempos, porcentajes)
- Uso de terminología técnica profesional
- Instrucciones específicas de uso
- Beneficios concretos mencionados
- Estructura de respuesta (oraciones completas)

REQUERIMIENTOS:
- Python 3.7+
- openai>=1.0.0
- pandas
- python-dotenv

INSTALACIÓN:
pip install openai pandas python-dotenv

TIEMPO ESTIMADO v2.0:
- 10 productos: ~40 segundos (incluye reintentos y validación)
- 100 productos: ~7 minutos
- 1400 productos: ~90 minutos

EJEMPLO DE EJECUCIÓN:
python faq-generator-cosmetics.py

El script generará automáticamente:
- Un reporte unificado TXT con todas las FAQs legibles
- Un archivo CSV optimizado para importar directamente en Shopify
- Métricas detalladas de calidad y recomendaciones para siguientes ejecuciones
"""