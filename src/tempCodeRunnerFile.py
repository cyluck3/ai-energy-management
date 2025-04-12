# --- Dentro de main.py ---
from utils.agent import flowtask
from utils.gen_cons import gen_data
import asyncio
import json
import pygame
import sys
import traceback
import threading
import queue
import math
import time
import random # <-- Añadido para posible jitter (opcional)

# --- Clases ConsumptionModifier y Energy_manager (sin cambios lógicos internos) ---
# ... (Código de las clases como en la versión anterior) ...
class ConsumptionModifier:
    def __init__(self, agent_name, ai_model):
        self.name = agent_name
        self.ai_model = ai_model

    async def modify_consumption(self, current_data_dict, modification_rules):
        # ... (código existente sin cambios, asegurándose que devuelve None en error) ...
        if not isinstance(current_data_dict, dict):
            print(f"Error en modify_consumption: Se esperaba un diccionario, se recibió {type(current_data_dict)}")
            return None
        current_json_string = json.dumps(current_data_dict, indent=4)
        prompt = f"""
        You are an AI assistant specialized in energy data manipulation.
        Your task is to modify the energy consumption values in the provided JSON data based on the following rules: '{modification_rules}'.

        Here is the current energy consumption data:
        ```json
        {current_json_string}
        ```

        Apply the modification rules to the consumption values for each house.
        Ensure the final consumption values remain between 0.0 and 1.0 (inclusive).
        Maintain the exact same JSON structure (sectors and house names).

        Respond ONLY with the modified JSON data, without any introductory text, explanations, or markdown formatting like ```json ... ```.
        """
        print(f"\n--- [Modifier] Enviando datos a {self.name} para modificación ---")
        agent = flowtask(self.name, self.ai_model)
        modified_data_string = await agent.add_instruction(prompt)
        # Aumentar log en caso de sospecha de respuesta incompleta
        print(f"\n--- [Modifier] Respuesta cruda de {self.name} (len: {len(modified_data_string)}):\n{modified_data_string[:500]}...")
        try:
            modified_data_string = modified_data_string.strip()
            if modified_data_string.startswith("```json"): modified_data_string = modified_data_string[7:]
            if modified_data_string.endswith("```"): modified_data_string = modified_data_string[:-3]
            modified_data_string = modified_data_string.strip()
            if not modified_data_string.startswith("{") or not modified_data_string.endswith("}"):
                 print(f"--- [Modifier] Error: Respuesta no parece ser un JSON válido (falta {{ o }}): {modified_data_string[:50]}...")
                 return None
            modified_data_dict = json.loads(modified_data_string)
            print(f"\n--- [Modifier] Datos modificados por {self.name} (Parseados) ---")
            return modified_data_dict
        except json.JSONDecodeError as e:
            print(f"\n--- [Modifier] Error al decodificar JSON modificado por {self.name}: {e}")
            print("--- [Modifier] Respuesta recibida que causó el error ---")
            print(modified_data_string) # Imprimir toda la respuesta en caso de error JSON
            print("---------------------------------------------")
            print("--- [Modifier] Devolviendo None debido a error en modificación.")
            return None
        except Exception as e:
            print(f"\n--- [Modifier] Ocurrió un error inesperado durante la modificación: {e}")
            traceback.print_exc()
            print("--- [Modifier] Devolviendo None debido a error inesperado.")
            return None


# --- Clase Energy_manager (Modificada para devolver ambos data sets) ---
class Energy_manager:
    def __init__(self, global_name):
        self.name = global_name
        self.modifier = ConsumptionModifier("Consumption Modifier Agent", "gemini-2.0-flash")
        self.modification_rules = """Simulate a slight decrease (around - 0.1 and 0.6) system in consumption for all houses due to weather changes. Use this as the reference:
            < 0.3 its normal consumption, don't do anything
            >= 0.3 & <= 0.5 is starting to consume more than what it should, don't do anything
            >= 0.5 is not normal, subtract 0.1 - 0.6
            Ensure final values are between 0.0 and 1.0.
            """

    async def generate_and_modify_data(self):
        """
        Genera datos iniciales, los modifica y devuelve AMBOS: (initial_data, modified_data).
        Devuelve None si ocurre un error en cualquier paso crítico.
        """
        print("\n--- [Manager] Iniciando generación de nuevo escenario ---")
        initial_json_data = None
        modified_json_data = None
        data_str = "N/A"

        try:
            # 1. Generar datos iniciales
            data_str = await gen_data()
            if not data_str or not isinstance(data_str, str):
                 print("--- [Manager] Error: gen_data() no devolvió una cadena válida.")
                 return None
            print(f"--- [Manager] Raw data received (len: {len(data_str)}): {data_str[:100]}...")

            # 2. Limpiar y parsear datos iniciales
            data_str = data_str.strip()
            if data_str.startswith("```json"): data_str = data_str[7:]
            if data_str.endswith("```"): data_str = data_str[:-3]
            data_str = data_str.strip()
            if not data_str.startswith("{") or not data_str.endswith("}"):
                 print(f"--- [Manager] Error: Datos iniciales no parecen JSON válido: {data_str[:50]}...")
                 return None
            initial_json_data = json.loads(data_str)
            print("--- [Manager] Datos iniciales parseados ---")

            # 3. Modificar los datos
            if isinstance(initial_json_data, dict):
                 modified_json_data = await self.modifier.modify_consumption(
                     initial_json_data, self.modification_rules
                 )
                 if modified_json_data:
                     print("--- [Manager] Datos modificados exitosamente ---")
                 else:
                     # Si la modificación falla, no podemos devolver el par
                     print("--- [Manager] Falló la modificación de datos.")
                     return None
            else:
                print("--- [Manager] Error: Datos iniciales parseados no son un diccionario.")
                return None

            # 4. Devolver AMBOS datasets si todo fue bien
            return initial_json_data, modified_json_data

        except json.JSONDecodeError as e:
            print(f"\n--- [Manager] Error al decodificar JSON INICIAL: {e}")
            print(f"--- [Manager] Datos recibidos (len: {len(data_str)}):")
            print(data_str[:500] + ('...' if len(data_str) > 500 else ''))
            print("---------------------------------------------")
            return None
        except Exception as e:
            print(f"\n--- [Manager] Ocurrió un error inesperado en generate_and_modify_data: {e}")
            traceback.print_exc()
            return None


# --- FUNCIÓN TARGET PARA EL HILO DE REGENERACIÓN (sin cambios) ---
def _run_regeneration_async(manager, result_queue):
    # ... (código existente sin cambios) ...
    print("--- [Thread] Iniciando tarea asíncrona de regeneración... ---")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # generate_and_modify_data ahora devuelve una tupla (initial, modified) o None
        result_tuple = loop.run_until_complete(manager.generate_and_modify_data())
        loop.close()
        print(f"--- [Thread] Tarea asíncrona completada. Resultado: {'Tupla de Datos' if result_tuple else 'None'} ---")
        result_queue.put(result_tuple)
    except Exception as e:
        print(f"--- [Thread] Error en el hilo de regeneración: {e}")
        traceback.print_exc()
        result_queue.put(None)


# --- FUNCIÓN DE INTERPOLACIÓN LINEAL (Lerp) ---
def lerp(a, b, t):
    """Interpola linealmente entre a y b usando t (0.0 a 1.0)."""
    # Manejar casos donde a o b puedan ser None o no numéricos
    if not isinstance(a, (int, float)): a = 0.0 # O algún valor por defecto
    if not isinstance(b, (int, float)): b = a # Si b es inválido, no interpolar
    t = max(0.0, min(1.0, t)) # Clamp t
    return a + (b - a) * t

# --- FUNCIÓN DE VISUALIZACIÓN PYGAME MODIFICADA ---
def visualize_data_pygame(initial_data_tuple, manager):
    pygame.init()

    # --- Constantes ---
    INITIAL_SCREEN_WIDTH = 1200
    INITIAL_SCREEN_HEIGHT = 500
    # ... (colores) ...
    BACKGROUND_COLOR = (30, 30, 30)
    TEXT_COLOR = (230, 230, 230)
    SECTOR_COLOR = (100, 100, 200)
    COLOR_LOW = (0, 255, 0)
    COLOR_MEDIUM = (255, 255, 0)
    COLOR_HIGH = (255, 0, 0)
    COLOR_INVALID = (128, 128, 128)
    BUTTON_COLOR = (0, 100, 200)
    BUTTON_HOVER_COLOR = (0, 150, 255)
    BUTTON_DISABLED_COLOR = (70, 70, 70)
    BUTTON_TEXT_COLOR = (255, 255, 255)


    # Layout y Animación
    BASE_HOUSE_RADIUS = 12 # Radio base
    H_SPACING = 8
    V_SPACING = 8
    PAIR_SPACING = 5
    TEXT_H_OFFSET = BASE_HOUSE_RADIUS + 4
    SECTOR_V_SPACING = 25
    MARGIN = 30
    BUTTON_HEIGHT = 40
    BUTTON_WIDTH = 150
    BUTTON_MARGIN = 10
    PULSE_FREQUENCY = 0.0035 # Ligeramente más rápido
    BRIGHTNESS_PULSE_AMPLITUDE = 0.35 # Un poco más pronunciado
    SIZE_PULSE_AMPLITUDE = 0.15 # Amplitud del pulso de tamaño (15%)
    ANIMATION_DURATION = 750 # Duración de la animación de transición (ms)

    # --- Estado ---
    initial_display_data = None
    modified_display_data = None # Estado *objetivo* actual
    previous_modified_data = None # Estado *anterior* para la animación lerp
    if isinstance(initial_data_tuple, tuple) and len(initial_data_tuple) == 2:
        initial_display_data, modified_display_data = initial_data_tuple
        # Al inicio, el estado anterior es igual al actual (sin animación inicial)
        previous_modified_data = modified_display_data
    else:
        print("--- [Pygame] Error: Datos iniciales no son una tupla válida. ---")

    is_loading = False
    regeneration_thread = None
    result_queue = queue.Queue()
    last_error_message = None
    last_error_time = 0
    animation_start_time = None # Timestamp de cuándo empezó la última animación lerp

    # --- Pantalla y Fuentes (SIN RESIZABLE explícito) ---
    screen_width, screen_height = INITIAL_SCREEN_WIDTH, INITIAL_SCREEN_HEIGHT
    try:
        # Crear ventana SIN el flag RESIZABLE
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Visualización de Consumo Energético (Animado)")
        # ... (fuentes como antes) ...
        font_house = pygame.font.SysFont("Consolas", 10)
        font_sector = pygame.font.SysFont("Arial", 16, bold=True)
        font_button = pygame.font.SysFont("Arial", 16)
        font_status = pygame.font.SysFont("Arial", 18, bold=True)
        font_legend = pygame.font.SysFont("Arial", 12)
    except Exception as e:
        print(f"Error cargando fuentes: {e}. Usando fuentes por defecto.")
        screen = pygame.display.set_mode((screen_width, screen_height)) # Sin RESIZABLE
        # ... (fuentes fallback como antes) ...
        font_house = pygame.font.Font(None, 16)
        font_sector = pygame.font.Font(None, 24)
        font_button = pygame.font.Font(None, 22)
        font_status = pygame.font.Font(None, 28)
        font_legend = pygame.font.Font(None, 18)


    # --- Botón (posición dinámica) ---
    def get_button_rect(w, h):
         return pygame.Rect(
            w - BUTTON_WIDTH - BUTTON_MARGIN,
            h - BUTTON_HEIGHT - BUTTON_MARGIN,
            BUTTON_WIDTH,
            BUTTON_HEIGHT
        )
    button_rect = get_button_rect(screen_width, screen_height)

    # --- Funciones de Color y Pulso (Modificada para devolver radio) ---
    def get_color_for_consumption(value):
        # ... (código existente sin cambios) ...
        if not isinstance(value, (int, float)): return COLOR_INVALID
        value = max(0.0, min(1.0, value))
        if value <= 0.5:
            ratio = value / 0.5
            r = int(COLOR_LOW[0] * (1 - ratio) + COLOR_MEDIUM[0] * ratio)
            g = int(COLOR_LOW[1] * (1 - ratio) + COLOR_MEDIUM[1] * ratio)
            b = int(COLOR_LOW[2] * (1 - ratio) + COLOR_MEDIUM[2] * ratio)
        else:
            ratio = (value - 0.5) / 0.5
            r = int(COLOR_MEDIUM[0] * (1 - ratio) + COLOR_HIGH[0] * ratio)
            g = int(COLOR_MEDIUM[1] * (1 - ratio) + COLOR_HIGH[1] * ratio)
            b = int(COLOR_MEDIUM[2] * (1 - ratio) + COLOR_HIGH[2] * ratio)
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


    def get_pulsing_color_and_radius(base_color, time_ms, phase_offset=0):
        """Calcula el color y radio pulsantes."""
        if base_color == COLOR_INVALID:
            return base_color, BASE_HOUSE_RADIUS # No pulsar colores/tamaños inválidos

        # Factor de brillo (como antes, pero con constante)
        brightness_factor = 1.0 + BRIGHTNESS_PULSE_AMPLITUDE * math.sin(time_ms * PULSE_FREQUENCY + phase_offset)
        pulsed_color = tuple(max(0, min(255, int(c * brightness_factor))) for c in base_color)

        # Factor de tamaño (nueva animación)
        # Usar una frecuencia o fase ligeramente diferente para desincronizar
        size_factor = 1.0 + SIZE_PULSE_AMPLITUDE * math.sin(time_ms * PULSE_FREQUENCY * 1.1 + phase_offset + math.pi / 3)
        pulsed_radius = max(1, int(BASE_HOUSE_RADIUS * size_factor)) # Asegurar radio mínimo de 1

        return pulsed_color, pulsed_radius

    # --- Bucle Principal ---
    running = True
    clock = pygame.time.Clock()

    while running:
        time_ms = pygame.time.get_ticks()
        mouse_pos = pygame.mouse.get_pos()
        delta_time = clock.tick(60) # Limita FPS y obtiene tiempo delta (no usado aquí, pero útil)

        # --- Calcular Progreso de Animación Lerp ---
        animation_progress = 1.0 # Por defecto, animación completada
        if animation_start_time is not None:
            elapsed = time_ms - animation_start_time
            if elapsed < ANIMATION_DURATION:
                animation_progress = elapsed / ANIMATION_DURATION
            else:
                # Animación completada
                animation_start_time = None
                # Asegurarse que el estado 'previous' se actualice al final
                previous_modified_data = modified_display_data


        # --- Comprobar resultado del hilo ---
        if regeneration_thread and not regeneration_thread.is_alive():
             is_loading = False
             regeneration_thread = None

        try:
            new_data_tuple = result_queue.get_nowait()
            if isinstance(new_data_tuple, tuple) and len(new_data_tuple) == 2:
                new_initial, new_modified = new_data_tuple
                # Iniciar animación: el estado actual se convierte en el 'previous'
                previous_modified_data = modified_display_data
                initial_display_data = new_initial
                modified_display_data = new_modified # Este es el nuevo *objetivo*
                animation_start_time = time_ms # Iniciar temporizador de animación
                print("--- [Pygame] Nuevos datos recibidos. Iniciando animación de transición. ---")
                last_error_message = None
            elif new_data_tuple is None:
                # ... (manejo de error como antes) ...
                print("--- [Pygame] Fallo al regenerar datos (recibido None). La visualización no se actualizó. ---")
                last_error_message = "Error al regenerar datos"
                last_error_time = time_ms

            else:
                 # ... (manejo de error como antes) ...
                 print(f"--- [Pygame] Error: Se recibió un tipo inesperado de la cola: {type(new_data_tuple)} ---")
                 last_error_message = "Error interno procesando datos"
                 last_error_time = time_ms

            result_queue.task_done()
        except queue.Empty:
            pass
        except Exception as e:
             # ... (manejo de error como antes) ...
             print(f"--- [Pygame] Error procesando cola: {e}")
             last_error_message = "Error interno procesando datos"
             last_error_time = time_ms


        # --- Manejo de Eventos ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Manejo de Redimensionamiento (útil aunque no usemos RESIZABLE explícito)
            elif event.type == pygame.VIDEORESIZE:
                screen_width, screen_height = event.w, event.h
                # Recrear screen SÓLO si es necesario (puede causar parpadeo)
                # screen = pygame.display.set_mode((screen_width, screen_height)) # Podría ser necesario si el contenido no se redibuja bien
                button_rect = get_button_rect(screen_width, screen_height)
                print(f"--- [Pygame] Evento VIDEORESIZE detectado: {screen_width}x{screen_height} ---")
            # ... (Manejo de Clic como antes) ...
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(mouse_pos) and not is_loading:
                    print("--- [Pygame] Botón 'Regenerar' presionado! ---")
                    is_loading = True
                    last_error_message = None
                    # Asegurarse que la animación actual se detenga si se regenera rápido
                    animation_start_time = None
                    regeneration_thread = threading.Thread(
                        target=_run_regeneration_async,
                        args=(manager, result_queue),
                        daemon=True
                    )
                    regeneration_thread.start()


        # --- Dibujo ---
        screen.fill(BACKGROUND_COLOR)

        # Dibujar contenido solo si tenemos datos válidos
        # Necesitamos initial, modified (target), y previous_modified
        if isinstance(initial_display_data, dict) and \
           isinstance(modified_display_data, dict) and \
           isinstance(previous_modified_data, dict):

            current_y = MARGIN
            house_index = 0

            # --- Leyenda (como antes) ---
            legend_y = MARGIN // 2
            legend_initial_text = font_legend.render("Consumo Inicial /", True, TEXT_COLOR)
            legend_modified_text = font_legend.render("Modificado", True, TEXT_COLOR)
            legend_x_start = screen_width - max(legend_initial_text.get_width(), legend_modified_text.get_width()) - MARGIN
            screen.blit(legend_initial_text, (legend_x_start, legend_y))
            screen.blit(legend_modified_text, (legend_x_start, legend_y + legend_initial_text.get_height() + 2))


            for sector_name, initial_houses_dict in initial_display_data.items():
                # ... (dibujar nombre de sector como antes) ...
                sector_text_surface = font_sector.render(sector_name, True, SECTOR_COLOR)
                screen.blit(sector_text_surface, (MARGIN, current_y))
                current_y += sector_text_surface.get_height() + V_SPACING * 1.5


                # Obtener diccionarios correspondientes del estado target y previous
                target_modified_houses = modified_display_data.get(sector_name, {})
                prev_modified_houses = previous_modified_data.get(sector_name, {})

                if isinstance(initial_houses_dict, dict):
                    current_x = MARGIN + BASE_HOUSE_RADIUS # Centro del primer círculo
                    items_in_row = 0

                    # Calcular ancho item usando BASE_HOUSE_RADIUS para layout estable
                    example_text_width = font_house.render("house-XX: 0.00 / 0.00", True, TEXT_COLOR).get_width()
                    item_pair_width = (BASE_HOUSE_RADIUS * 2) + PAIR_SPACING + (BASE_HOUSE_RADIUS * 2)
                    item_total_width = item_pair_width + TEXT_H_OFFSET + example_text_width + H_SPACING * 2
                    max_items_per_row = (screen_width - 2 * MARGIN) // item_total_width
                    if max_items_per_row < 1: max_items_per_row = 1

                    for house_name, initial_consumption in initial_houses_dict.items():
                        # Obtener valores target y previous para la animación
                        target_modified_consumption = target_modified_houses.get(house_name, None)
                        prev_modified_consumption = prev_modified_houses.get(house_name, target_modified_consumption) # Fallback al target si no hay previous

                        # --- Calcular valor interpolado para el segundo círculo ---
                        interpolated_modified_consumption = lerp(
                            prev_modified_consumption,
                            target_modified_consumption,
                            animation_progress
                        )

                        # Calcular posiciones (basadas en BASE_HOUSE_RADIUS para estabilidad)
                        initial_circle_center_x = current_x
                        modified_circle_center_x = current_x + BASE_HOUSE_RADIUS + PAIR_SPACING + BASE_HOUSE_RADIUS
                        circle_center_y = current_y + BASE_HOUSE_RADIUS

                        # Obtener colores base (inicial y el *interpolado* modificado)
                        initial_base_color = get_color_for_consumption(initial_consumption)
                        interpolated_modified_base_color = get_color_for_consumption(interpolated_modified_consumption)

                        # Obtener colores y radios pulsantes
                        initial_pulsed_color, initial_pulsed_radius = get_pulsing_color_and_radius(
                            initial_base_color, time_ms, house_index * 0.5
                        )
                        modified_pulsed_color, modified_pulsed_radius = get_pulsing_color_and_radius(
                            interpolated_modified_base_color, time_ms, house_index * 0.5 + math.pi / 4
                        )

                        # Dibujar círculos con radios pulsantes
                        pygame.draw.circle(screen, initial_pulsed_color, (initial_circle_center_x, circle_center_y), initial_pulsed_radius)
                        pygame.draw.circle(screen, modified_pulsed_color, (modified_circle_center_x, circle_center_y), modified_pulsed_radius)

                        # Preparar y dibujar texto (mostrar valor inicial y *target* modificado)
                        cons_text_initial = f"{initial_consumption:.2f}" if isinstance(initial_consumption, (int, float)) else "N/A"
                        cons_text_modified_target = f"{target_modified_consumption:.2f}" if isinstance(target_modified_consumption, (int, float)) else "N/A"
                        house_info = f"{house_name}: {cons_text_initial} / {cons_text_modified_target}"
                        text_surface = font_house.render(house_info, True, TEXT_COLOR)
                        # Posicionar texto a la derecha del par (usando BASE_HOUSE_RADIUS para pos fija)
                        text_rect = text_surface.get_rect(midleft=(current_x + BASE_HOUSE_RADIUS + PAIR_SPACING + BASE_HOUSE_RADIUS + TEXT_H_OFFSET, circle_center_y))
                        screen.blit(text_surface, text_rect)

                        # ... (actualizar current_x, items_in_row, house_index como antes) ...
                        current_x += item_total_width
                        items_in_row += 1
                        house_index += 1

                        # Nueva fila
                        if items_in_row >= max_items_per_row:
                            current_x = MARGIN + BASE_HOUSE_RADIUS
                            current_y += (BASE_HOUSE_RADIUS * 2) + V_SPACING * 2
                            items_in_row = 0


                    # ... (mover current_y si la fila no estaba llena, como antes) ...
                    if items_in_row > 0:
                        current_y += (BASE_HOUSE_RADIUS * 2) + V_SPACING * 2

                else:
                    # ... (manejo de error si initial_houses_dict no es dict) ...
                    error_text = font_house.render(f"Error: Datos iniciales inválidos para {sector_name}", True, COLOR_HIGH)
                    screen.blit(error_text, (MARGIN + 10, current_y))
                    current_y += error_text.get_height() + V_SPACING


                current_y += SECTOR_V_SPACING
        else:
            # ... (mensaje si los datos iniciales no son válidos, como antes) ...
            status_msg = "Error inicial al cargar datos." if not initial_display_data else "Esperando datos..."
            status_surface = font_status.render(status_msg, True, COLOR_HIGH if not initial_display_data else TEXT_COLOR)
            status_rect = status_surface.get_rect(center=(screen_width // 2, screen_height // 2))
            screen.blit(status_surface, status_rect)


        # --- Dibujar Botón y Mensaje de Estado/Error (como antes) ---
        # ... (código existente para dibujar botón y mensajes de loading/error) ...
        button_active = not is_loading
        btn_color = BUTTON_DISABLED_COLOR
        if button_active:
            btn_color = BUTTON_HOVER_COLOR if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
        pygame.draw.rect(screen, btn_color, button_rect, border_radius=5)
        button_text = "Regenerar" if button_active else "Cargando..."
        button_text_surface = font_button.render(button_text, True, BUTTON_TEXT_COLOR)
        button_text_rect = button_text_surface.get_rect(center=button_rect.center)
        screen.blit(button_text_surface, button_text_rect)

        # --- Dibujar Mensaje de Estado/Error Temporal ---
        status_rect_center_x = screen_width // 2 # Centrar mensajes de estado
        if is_loading:
             status_surface = font_status.render("Cargando nuevo escenario...", True, TEXT_COLOR)
             status_rect = status_surface.get_rect(center=(status_rect_center_x, screen_height // 2))
             overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
             overlay.fill((0, 0, 0, 128))
             screen.blit(overlay, (0, 0))
             screen.blit(status_surface, status_rect)
        elif last_error_message and time_ms - last_error_time < 5000:
             status_surface = font_status.render(last_error_message, True, COLOR_HIGH)
             # Posicionar error cerca del botón pero centrado horizontalmente
             status_rect = status_surface.get_rect(midbottom=(status_rect_center_x, screen_height - BUTTON_MARGIN * 2 - BUTTON_HEIGHT))
             screen.blit(status_surface, status_rect)


        # --- Actualizar Pantalla ---
        pygame.display.flip()

    # --- Salir ---
    pygame.quit()
    print("--- Visualización Pygame cerrada ---")


# --- CÓDIGO PRINCIPAL DE EJECUCIÓN (sin cambios) ---
if __name__ == "__main__":
    # ... (código existente para iniciar, cargar datos iniciales y llamar a visualize_data_pygame) ...
    print("--- Iniciando Simulador de Energía ---")
    ema = Energy_manager("Energy Manager Principal")

    print("--- Generando escenario inicial (puede tardar)... ---")
    initial_data_queue = queue.Queue()
    initial_load_thread = threading.Thread(
        target=_run_regeneration_async,
        args=(ema, initial_data_queue),
        daemon=True
    )
    initial_load_thread.start()
    initial_load_thread.join(timeout=90) # Aumentar timeout por si acaso

    initial_data_result_tuple = None
    try:
        initial_data_result_tuple = initial_data_queue.get_nowait()
    except queue.Empty:
        print("--- ERROR FATAL: Timeout o fallo al generar escenario inicial. ---")
    except Exception as e:
        print(f"--- ERROR FATAL: Excepción al obtener datos iniciales: {e} ---")

    # Validar que obtuvimos una tupla válida
    if isinstance(initial_data_result_tuple, tuple) and len(initial_data_result_tuple) == 2:
        print("--- Escenario inicial generado (Inicial y Modificado). Iniciando visualización Pygame ---")
        visualize_data_pygame(initial_data_result_tuple, ema)
    else:
        print("--- ERROR FATAL: No se pudo generar la tupla de datos inicial. Abortando visualización. ---")
        # Opcional: Iniciar Pygame con mensaje de error permanente
        # visualize_data_pygame(None, ema)

    print("--- Simulador de Energía Finalizado ---")
