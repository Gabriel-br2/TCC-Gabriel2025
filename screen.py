import os
import threading
import webbrowser

import pygame
from dotenv import load_dotenv

from players.human import humanInteraction

load_dotenv()
URL = os.getenv("FORM_URL")


class Screen:
    def __init__(self, config, color, player_type):
        pygame.init()

        self.config = config
        self.color = color
        self.player_type = player_type

        self.fps = 60
        self.iou = 0.0
        self.lock = True
        self.menu_running = True
        self.game_running = True

        self.width = config["screen"]["width"]
        self.height = config["screen"]["height"]

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 32, bold=True)

        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(config["screen"]["caption"])

        self.nameId = None
        if self.player_type == "human":
            self.nameId = self.initial_screen()

    def initial_screen(self):
        nome = ""
        sobrenome = ""

        box_width = 300
        box_height = 40

        input_box_nome = pygame.Rect(
            self.width / 2 - box_width / 2, self.height / 2 - 100, box_width, box_height
        )
        input_box_sobrenome = pygame.Rect(
            self.width / 2 - box_width / 2, self.height / 2, box_width, box_height
        )
        continue_button = pygame.Rect(
            self.width / 2 - 100, self.height / 2 + 100, 200, 50
        )

        color_inactive = pygame.Color("gray")
        color_active = pygame.Color("black")
        color_button_inactive = pygame.Color("darkgray")
        color_button_active = pygame.Color(0, 150, 0)  #

        active_nome = False
        active_sobrenome = False

        running = True
        while running:
            fields_filled = bool(nome and sobrenome)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False  # Sinaliza para o app principal fechar
                    running = False
                    return None, None  # Retorna None se o usuário fechar a janela

                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Checa cliques nos campos de input
                    if input_box_nome.collidepoint(event.pos):
                        active_nome = True
                        active_sobrenome = False
                    elif input_box_sobrenome.collidepoint(event.pos):
                        active_nome = False
                        active_sobrenome = True
                    # Checa clique no botão "Continuar"
                    elif continue_button.collidepoint(event.pos) and fields_filled:
                        running = False  # Sai do loop e retorna os nomes
                    else:
                        # Desativa ambos se clicar fora
                        active_nome = False
                        active_sobrenome = False

                if event.type == pygame.KEYDOWN:
                    # Lógica para o campo "Nome"
                    if active_nome:
                        if event.key == pygame.K_BACKSPACE:
                            nome = nome[:-1]
                        elif event.key == pygame.K_TAB:
                            # Pula para o próximo campo
                            active_nome = False
                            active_sobrenome = True
                        else:
                            nome += event.unicode
                    # Lógica para o campo "Sobrenome"
                    elif active_sobrenome:
                        if event.key == pygame.K_BACKSPACE:
                            sobrenome = sobrenome[:-1]
                        elif event.key == pygame.K_TAB:
                            # Pula para o campo anterior
                            active_nome = True
                            active_sobrenome = False
                        elif (
                            event.key in (pygame.K_RETURN, pygame.K_KP_ENTER)
                            and fields_filled
                        ):
                            running = False  # Permite submeter com Enter se os campos estiverem preenchidos
                        else:
                            sobrenome += event.unicode

            # --- Seção de Desenho (Renderização) ---

            self.screen.fill(self.color["background"])

            # Título da tela
            title_surf = self.large_font.render(
                "Identificação do Jogador", True, (0, 0, 0)
            )
            title_rect = title_surf.get_rect(center=(self.width / 2, self.height / 4))
            self.screen.blit(title_surf, title_rect)

            # --- Campo "Nome" ---
            # Label (Rótulo)
            label_nome_surf = self.font.render("Nome:", True, (0, 0, 0))
            self.screen.blit(label_nome_surf, (input_box_nome.x, input_box_nome.y - 25))
            # Caixa de input
            color_nome = color_active if active_nome else color_inactive
            pygame.draw.rect(self.screen, color_nome, input_box_nome, 2)
            # Texto dentro da caixa
            txt_surface_nome = self.font.render(nome, True, (0, 0, 0))
            self.screen.blit(
                txt_surface_nome, (input_box_nome.x + 5, input_box_nome.y + 5)
            )

            # --- Campo "Sobrenome" ---
            # Label (Rótulo)
            label_sobrenome_surf = self.font.render("Sobrenome:", True, (0, 0, 0))
            self.screen.blit(
                label_sobrenome_surf,
                (input_box_sobrenome.x, input_box_sobrenome.y - 25),
            )
            # Caixa de input
            color_sobrenome = color_active if active_sobrenome else color_inactive
            pygame.draw.rect(self.screen, color_sobrenome, input_box_sobrenome, 2)
            # Texto dentro da caixa
            txt_surface_sobrenome = self.font.render(sobrenome, True, (0, 0, 0))
            self.screen.blit(
                txt_surface_sobrenome,
                (input_box_sobrenome.x + 5, input_box_sobrenome.y + 5),
            )

            button_color = (
                color_button_active if fields_filled else color_button_inactive
            )
            pygame.draw.rect(self.screen, button_color, continue_button)

            btn_text_surf = self.font.render("Continuar", True, (255, 255, 255))
            btn_text_rect = btn_text_surf.get_rect(center=continue_button.center)
            self.screen.blit(btn_text_surf, btn_text_rect)

            pygame.display.flip()
            self.clock.tick(self.fps)

        return f"{nome} {sobrenome}"

    def setup_player_specifics(self, client_id, timestamp, LLM_source="local"):
        self.client_id = client_id
        pygame.display.set_caption(
            f"{self.config['screen']['caption']} - player: {self.client_id}"
        )

    def show_waiting_screen(self, attempt_count):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_running = False
                return False

        self.screen.fill(self.color["background"])

        dots = "." * (attempt_count % 4)

        text_surface = self.large_font.render(
            f"Rodada já completada aguarde sua vez {dots}", True, (0, 0, 0)
        )
        text_rect = text_surface.get_rect(center=(self.width / 2, self.height / 2))

        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()

        self.clock.tick(10)
        return True

    # --- Loop principal ---
    def game_loop(self, objects, iou):
        local_player_objects = [obj for obj in objects if obj.id == self.client_id]

        self._render(objects, iou)
        self._handle_events(objects, local_player_objects)

        self.clock.tick(self.fps)

        return [[*obj.position, obj.type] for obj in local_player_objects]

    def change_screen(self):
        large_font = pygame.font.SysFont("Arial", self.width // 35, bold=True)
        text_surface = large_font.render(
            "Objetivo concluído, iniciando próximo ciclo", True, (0, 0, 0)
        )
        text_rect = text_surface.get_rect(center=(self.width / 2, self.height / 2))
        self.screen.fill(self.color["background"])

        self.screen.blit(text_surface, text_rect)
        pygame.display.flip()
        pygame.time.wait(3000)

    def end_screen(self):
        return

        end_font = pygame.font.SysFont("Arial", self.width // 35, bold=True)
        end_text = end_font.render(
            "Experimento concluído! Por favor responda o Questinário:", True, (0, 0, 0)
        )
        end_rect = end_text.get_rect(center=(self.width / 2, self.height / 2))

        end_font.set_underline(True)
        link_text = end_font.render("Questionário via Google Forms", True, (0, 0, 255))
        link_rect = link_text.get_rect(center=(self.width / 2, self.height / 2 + 150))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    return

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if link_rect.collidepoint(event.pos):
                        webbrowser.open(URL)

            self.screen.fill(self.color["background"])
            self.screen.blit(end_text, end_rect)
            self.screen.blit(link_text, link_rect)

            pygame.display.flip()
            self.clock.tick(self.fps)

    # --- Input ---
    def _handle_events(self, objects, local_objects):
        def human_events():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                    return
                humanInteraction(event, objects, local_objects)

        def LLM_events():
            if not os.path.exists("screendata"):
                os.makedirs("screendata")

            for obj in local_objects + objects:
                obj.draw_label(obj.id)
            pygame.image.save(self.screen, "screendata/last.jpg")
            for obj in local_objects + objects:
                obj.clear_label()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                    return
            self.LLM.LLMInteraction(objects, local_objects, self.iou)
            self.lock = True

        if self.player_type == "human":
            human_events()

        if self.player_type == "LLM":
            if self.lock:
                self.lock = False
                thread1 = threading.Thread(target=LLM_events)
                thread1.start()

    # --- Renderização ---
    def _render(self, objects, iou):
        self.screen.fill(self.color["background"])
        self._draw_objects(objects)
        self._draw_iou(iou)
        pygame.display.flip()

    def _draw_objects(self, objects):
        for obj in objects:
            obj.draw()

    def _draw_iou(self, iou):
        self.iou = iou
        text = self.font.render(
            f"Objetivo Concluído: {iou * 100:.2f} %", True, (0, 0, 0)
        )
        rect = text.get_rect(center=(self.width // 2, 25))
        self.screen.blit(text, rect)

    # --- Encerramento ---
    def close(self):
        pygame.quit()
