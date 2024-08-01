

import pygame
import numpy as np

class display():
    def __init__(self) -> None:
        pygame.init()
        display_width, display_height = 1200, 600

        self.screen = pygame.display.set_mode((display_width, display_height))
        pygame.display.set_caption('Dynamic LED Display')

    def __delete__(self):
        pygame.quit()

    def draw(self, grid, layout, stripoffset):
        self.draw_led_grid(self.screen, grid, layout,stripoffset)
    # Function to draw the LED grid
    def draw_led_grid(self,screen, grid, layout, stripoffset, margin = 20, led_size = 20):
      #  grid = np.asarray(grid)
      #  print(grid.shape)
      screen.fill((50, 10, 0))
   #   print(grid.shape)
    #  print(stripoffset)
      for x,row in enumerate(grid):
                for y,entry in enumerate(row):
                #  print(x,y+stripoffset[i][x])
                    entry = grid[x,y]
                    color = (int(entry*255), int(entry*255), int(entry*255))
            #       print(color)
                    # print("rect", [(margin + led_size) * x + margin,
                    #     (margin + led_size) * y + margin,
                    #     led_size, led_size])
                    pygame.draw.rect(
                        screen,
                        color,
                        [(margin + led_size) * x + margin,
                        (margin + led_size) * (y) + margin,
                        led_size, led_size]
                    )

      for i,block in enumerate(layout):
        for x,row in enumerate(block):
            for y in range(row):
              #  print(x,y+stripoffset[i][x])
                entry = grid[x,y+stripoffset[i][x]]
                color = (int(entry*255), int(entry*255), int(entry*255))
         #       print(color)
                # print("rect", [(margin + led_size) * x + margin,
                #     (margin + led_size) * y + margin,
                #     led_size, led_size])
                pygame.draw.rect(
                    screen,
                    color,
                    [(margin + led_size) * x + margin +(i+1)*300,
                    (margin + led_size) * (y+stripoffset[i][x]) + margin,
                    led_size, led_size]
                )

    #  print(pygame.display.get_driver())
      pygame.display.flip()

if __name__ == "__main__":
    displays = display()
    while True:
        displays.draw([[[0.5,1,0]]])