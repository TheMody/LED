

import pygame
import numpy as np

class display():
    def __init__(self) -> None:
        pygame.init()
        display_width, display_height = 800, 600

        self.screen = pygame.display.set_mode((display_width, display_height))
        pygame.display.set_caption('Dynamic LED Display')

    def __delete__(self):
        pygame.quit()

    def draw(self, grid):
        self.draw_led_grid(self.screen, grid)
    # Function to draw the LED grid
    def draw_led_grid(self,screen, grid, margin = 20, led_size = 20):
      #  grid = np.asarray(grid)
      #  print(grid.shape)
      screen.fill((50, 10, 0))
      for i,block in enumerate(grid):
        for x,row in enumerate(block):
            for y,entry in enumerate(row):
                color = (int(entry*255), int(entry*255), int(entry*255))
         #       print(color)
                # print("rect", [(margin + led_size) * x + margin,
                #     (margin + led_size) * y + margin,
                #     led_size, led_size])
                pygame.draw.rect(
                    screen,
                    color,
                    [(margin + led_size) * x + margin +i*300,
                    (margin + led_size) * y + margin,
                    led_size, led_size]
                )

    #  print(pygame.display.get_driver())
      pygame.display.flip()

if __name__ == "__main__":
    displays = display()
    while True:
        displays.draw([[[0.5,1,0]]])