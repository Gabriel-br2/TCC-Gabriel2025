import pygame
import pymunk
import pymunk.pygame_util

import sys

class screen:
    def __init__(self, config, color, clickCallback, debug=False):
        pygame.init()

        self.running       = True
        self.debug         = debug
        self.color         = color
        self.clickCallback = clickCallback

        self.screen_Height = config['screen']['height']
        self.screen_Width  = config['screen']['width']

        self.clock = pygame.time.Clock()
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)

        self.FPS = 60

        self.screen = pygame.display.set_mode((self.screen_Width, self.screen_Height))
        pygame.display.set_caption(config['screen']['caption'])

        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)

    def screen_Loop(self, objects):
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                self.running = False
            if event.type == pygame.KEYDOWN:
                self.clickCallback(event.key)

        pos_mouse = pygame.mouse.get_pos()
        objects[0].body.position = pos_mouse

        self.space.step(1/self.FPS)
        self.screen.fill(self.color["background"])
       
        objects[0].draw()
        objects[1].draw()
        
        #self.space.debug_draw(self.draw_options)

        pygame.display.flip()

        self.clock.tick(self.FPS)

    def close(self):
        pygame.quit()
        sys.exit()