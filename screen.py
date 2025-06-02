import pygame

from players.human import humanInteraction

class Screen:
    def __init__(self, config, color, client_id):
        pygame.init()

        self.fps = 60
        self.menu_running = True
        self.game_running = True

        self.color = color      
        self.config = config    
        self.client_id = client_id

        self.screen_height = config['screen']['height'] 
        self.screen_width  = config['screen']['width']  

        self.clock = pygame.time.Clock()                         
        self.font = pygame.font.SysFont("Arial", 18, bold=True)  
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(f"{config['screen']['caption']} - player: {client_id}")

    def game_loop(self, objects, iou):
        my_objects = objects[-self.config['game']['objectsNum']:]

        for event in pygame.event.get():       
            if event.type == pygame.QUIT:      
                self.game_running = False      
                break
            
            humanInteraction(event, objects, my_objects)

        self.screen.fill(self.color["background"])
        
        for obj in objects:
            obj.draw()

        iou_text = self.font.render(f"Objetivo Concluído: {iou * 100:.2f} %", True, (0, 0, 0))
        text_rect = iou_text.get_rect(center=(self.config["screen"]["width"] // 2, 25))
        self.screen.blit(iou_text, text_rect)

        pygame.display.flip()  
        self.clock.tick(self.fps)

        return [[*my_obj.position, my_obj.type] for my_obj in my_objects]
    
    def close(self):
        pygame.quit()  