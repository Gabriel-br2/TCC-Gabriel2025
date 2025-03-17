import pygame

pygame.init()
screen = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()

# Criando uma Surface com transparência
polygon_surface = pygame.Surface((500, 500), pygame.SRCALPHA)

# Cor RGBA (verde com 50% de transparência)
green_transparent = (0, 255, 0, 5)

# Posição dos vértices do polígono
points = [(100, 300), (250, 100), (400, 300), (300, 400), (200, 400)]

# Desenhando o polígono na Surface transparente
pygame.draw.polygon(polygon_surface, green_transparent, points)

running = True
while running:
    screen.fill((30, 30, 30))  # Cor de fundo

    # Blita a superfície com o polígono transparente
    screen.blit(polygon_surface, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
