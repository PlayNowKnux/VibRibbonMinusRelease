import pygame, vibscore, math
from globals import *

width = SCREEN_WIDTH


def rot_center(image, rect, angle):
    #https://stackoverflow.com/questions/21080790/pygame-and-rotation-of-a-sprite
    """rotate an image while keeping its center"""
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = rot_image.get_rect(center=rect.center)
    return rot_image,rot_rect


def load_coupon_images(dir: str):
    imgs = []
    for t in range(0, 21):
        imgs.append(pygame.image.load(f"{dir}/{t}.png").convert_alpha())
    return imgs


class Flake:
    # One score coupon
    def __init__(self, t: int, imgs):
        self.imgs = imgs
        self.t = t
        self.rootImage = imgs[t]
        self.rootBox = self.rootImage.get_rect()
        self.rootX = (width // 2)  # - (self.rootBox.size[0]//2)
        self.rootY = 50

    def get_x(self, c):
        return int((math.cos(c / 400) * 80) + self.rootX)

    def get_size(self, c):
        return ((math.sin(c / 400)) + 2) / 16

    def blit(self, c, scrn):
        x = self.get_x(c)
        size = self.get_size(c)
        image = pygame.transform.scale(self.rootImage,
                                       (int(self.rootBox.size[0] * size), int(self.rootBox.size[1] * size)))
        box = image.get_rect()
        rot_image, rot_box = rot_center(image, box, c / 4)
        rot_box.centerx = int(x)
        rot_box.centery = self.rootY
        scrn.blit(rot_image, rot_box)

    def change(self, t):
        self.t = t
        self.rootImage = self.imgs[t]
        self.rootBox = self.rootImage.get_rect()


class FlakeList:
    # 7 score coupons
    def __init__(self, imgs, **kwargs):
        self.flakes = []
        self.imgs = imgs
        for i in range(0, 7):
            self.flakes.append(Flake(0, imgs))
            self.flakes[-1].rootY = kwargs.get("y", 50)

    def change_y(self, y: int):
        for i in self.flakes:
            i.rootY = y

    def change(self, value):
        # Change value
        p = vibscore.calculate(value).split(" ")
        p = [int(i) for i in p[:-1]]
        for i in range(0, 7):
            self.flakes[i].change(p[i])

    def blit(self, c, scrn):
        # c is an offset (for spinning)
        ctr = 0
        """
        flakes = self.flakes
        flakes.sort(key=lambda x: x.rootBox.size[0] * x.get_size(c + (ctr * -200)))
        print([x.get_size(c + (ctr * -200)) for x in flakes])
        """
        for i in self.flakes:
            i.blit(c + (ctr * -200), scrn)
            ctr += 1
