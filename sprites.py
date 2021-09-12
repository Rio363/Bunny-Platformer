from settings import *
import random

vec = pg.math.Vector2


class Bunny(pg.sprite.Sprite):
	def __init__(self, game_obj):
		self._layer = PLAYER_LAYER
		super().__init__(game_obj.all_sprites)
		self.game_obj = game_obj
		self.lives = 3
		self.gold_coins = 0
		self.silver_coins = 0
		self.bronze_coins = 0
		self.carrots = 0

		self.walking = False
		self.jumping = False
		self.pow_jumping = False
		self.hurt = False
		self.hit_time = self.first_hurt = 0
		self.on_screen = True
		self.hurt_period = 3000
		self.frame = 0
		self.last_frame_update = 0

		self.load_images()

		self.image = self.standing_frames[0]
		self.rect = self.image.get_rect()
		self.rect.centerx = 50
		self.rect.bottom = HEIGHT - 40

		self.acc = vec(0, 0)
		self.vel = vec(0, 0)
		self.pos = vec(50, HEIGHT - 40)

	def load_images(self):
		self.standing_frames = [
			self.game_obj.sprite_sheet.get_sprite(614, 1063, 120, 191),
			self.game_obj.sprite_sheet.get_sprite(690, 406, 120, 201)
		]
		self.right_walking_frames = [
			self.game_obj.sprite_sheet.get_sprite(678, 860, 120, 201),
			self.game_obj.sprite_sheet.get_sprite(692, 1458, 120, 207),
		]
		self.left_walking_frames = [
			pg.transform.flip(img, True, False) for img in self.right_walking_frames
		]
		self.jumping_frame = self.game_obj.sprite_sheet.get_sprite(382, 763, 150, 181)

	def jump(self):
		if not self.hurt:
			self.rect.y += 5
			hits = pg.sprite.spritecollide(self, self.game_obj.platforms, False)
			self.rect.y -= 5
			if hits and not self.jumping:
				self.jumping = True
				self.vel.y = JUMP_HEIGHT
				self.game_obj.jump_sound.play()

	def jump_cut(self):
		if self.jumping and not self.pow_jumping:
			if self.vel.y < -3:
				self.vel.y /= 2

	def update(self):
		if self.hurt:
			now = pg.time.get_ticks()
			if now - self.hit_time > 200:
				self.hit_time = now
				if self.on_screen:
					self.on_screen = False
					self.rect.center = self.last_pos
				elif not self.on_screen:
					self.rect.center = (1000, 1000)
					self.on_screen = True
			if now - self.first_hurt > self.hurt_period:
				self.hurt = False
		else:
			self.movement()
			self.animate()	


	def movement(self):
		self.acc = vec(0, GRAVITY)
		keys = pg.key.get_pressed()

		if keys[pg.K_LEFT]:
			self.acc.x = -PLAYER_ACC
		if keys[pg.K_RIGHT]:
			self.acc.x = PLAYER_ACC

		self.acc.x += self.vel.x * FRICTION
		self.vel += self.acc
		self.pos += self.vel + 0.5 * self.acc

		if self.pos.x - self.rect.width / 2 > WIDTH:
			self.pos.x = 0
		if self.pos.x + self.rect.width / 2 < 0:
			self.pos.x = WIDTH

		self.rect.midbottom = self.pos

	def hurt_bunny(self):
		self.last_pos = self.rect.center
		self.hurt = True
		self.hit_time = self.first_hurt = pg.time.get_ticks()
		self.image = self.game_obj.bunny_hurt
		self.rect.center = self.last_pos

	def animate(self):
		if self.vel.x <= -1 or self.vel.x >= 1:
			self.walking = True
		else:
			self.walking = False

		now = pg.time.get_ticks()
		if not self.walking and not self.jumping:
			if now - self.last_frame_update > 350:
				self.last_frame_update = now
				self.frame = (self.frame + 1) % len(self.standing_frames)
				old_center = self.rect.center
				self.image = self.standing_frames[self.frame]
				self.rect = self.image.get_rect(center=old_center)
		
		if self.walking and not self.jumping:
			if now - self.last_frame_update > 100:
				self.last_frame_update = now
				self.frame = (self.frame + 1) % len(self.right_walking_frames)
				old_center = self.rect.center

				if self.vel.x > 0:
					self.image = self.right_walking_frames[self.frame]
				elif self.vel.x < 0:
					self.image = self.left_walking_frames[self.frame]

				self.rect = self.image.get_rect(center=old_center)

		if self.jumping:
			old_center = self.rect.center
			self.image = self.jumping_frame
			self.rect.center = old_center

		self.mask = pg.mask.from_surface(self.image)


class Platform(pg.sprite.Sprite):
	def __init__(self, game_obj, x, y):
		self._layer = PLATFORM_LAYER
		super().__init__(game_obj.all_sprites, game_obj.platforms)
		self.platform_images = [
			game_obj.sprite_sheet.get_sprite(0, 288, 380, 94),
			game_obj.sprite_sheet.get_sprite(213, 1662, 201, 100)
		]
		self.image = random.choice(self.platform_images)
		self.rect = self.image.get_rect(topleft=[x, y])

		# Spawn a Mob/Pow only when not pow_jumping
		if not game_obj.bunny.pow_jumping:
			if random.random() > POWERUP_PCT and len(game_obj.powerups) == 0 and game_obj.score > 100:
				Pow(game_obj, self)
			if random.random() > POWERUP_PCT_LIFE and len(game_obj.powerups) <= 2 and game_obj.bunny.lives < 5:
				Pow(game_obj, self, "life")

			if random.random() > MOB_SPAWN_PCT and len(game_obj.mobs) == 0 and game_obj.score > 400:
				Mob(game_obj, self)

			# Spawn Pow(life) separately....

		if random.random() > EXTRAS_SPAWN_PCT:
			ExtraObjects(game_obj, self)

		if random.random() > COLLECTABLES_SPAWN_PCT and len(game_obj.platforms) > 1: # len > 1 to Spawn only after the first platform
			Collectables(game_obj, self)


class SpriteSheet():
	def __init__(self, filename):
		self.sprite_sheet = pg.image.load(filename).convert()

	def get_sprite(self, x, y, w, h):
		sprite = pg.Surface([w, h])
		sprite.set_colorkey((BLACK))
		sprite.blit(self.sprite_sheet, (0, 0), (x, y, w, h))
		return pg.transform.scale(sprite, (w // 2, h // 2))


class Pow(pg.sprite.Sprite):
	def __init__(self, game_obj, plat, powerup_type=None):
		self._layer = POW_LAYER
		super().__init__(game_obj.all_sprites, game_obj.powerups)
		self.game_obj = game_obj
		self.plat = plat

		self.pow_type = powerup_type
		if self.pow_type is None:
			self.pow_type = random.choice(["boost"])

		if self.pow_type == "boost":
			self.image = game_obj.sprite_sheet.get_sprite(820, 1805, 71, 70)
		elif self.pow_type == "life":
			self.image = game_obj.sprite_sheet.get_sprite(826, 1220, 71, 70)

		self.rect = self.image.get_rect()
		self.rect.centerx = self.plat.rect.centerx
		self.rect.bottom = self.plat.rect.top - 8

	def update(self):
		self.rect.bottom = self.plat.rect.top - 8

		if not self.game_obj.platforms.has(self.plat):
			self.kill()


class Mob(pg.sprite.Sprite):
	def __init__(self, game_obj, plat):
		self._layer = MOB_LAYER
		super().__init__(game_obj.all_sprites, game_obj.mobs)
		self.game_obj = game_obj
		# self.plat = plat
		self.plat_rect = plat.rect

		self.mob_type = random.choice(["flyman", "spikeman", "wingman"])

		self.frame = 0
		self.last_frame_update = 0
		self.frame_speed = 1
		self.anim_wait_time = 150
		if self.mob_type == "flyman":
			self.anim_wait_time = 200
		self.load_mob_images()

		if self.mob_type == "flyman":
			self.anim_lst = self.flyman
		elif self.mob_type == "spikeman":
			self.anim_lst = self.spikeman_r
		elif self.mob_type == "wingman":
			self.anim_lst = self.wingman
			self.anim_wait_time = 100

		self.image = self.anim_lst[self.frame]
		self.rect = self.image.get_rect()
		self.rect.x = random.randint(self.plat_rect.left, self.plat_rect.right - self.rect.width)
		if self.mob_type == "spikeman":
			self.rect.bottom = self.plat_rect.top
		else:
			self.rect.bottom = self.plat_rect.top - 25

		self.spike_speedx = random.choice([1, 2])
		self.speedx = random.choice([2, 4])
		if random.random() > 0.5:
			self.spike_speedx *= -1
			self.speedx *= -1
		self.flyman_vy = 0
		self.flyman_dy = 0.5

	def load_mob_images(self):
		self.flyman = [
			self.game_obj.sprite_sheet.get_sprite(566, 510, 122, 139),
			self.game_obj.sprite_sheet.get_sprite(692, 1667, 120, 132),
		]

		self.spikeman_r = [
			self.game_obj.sprite_sheet.get_sprite(704, 1256, 120, 159),
			self.game_obj.sprite_sheet.get_sprite(812, 296, 90, 155),
		]
		self.spikeman_l = [pg.transform.flip(img, True, False) for img in self.spikeman_r]

		self.wingman = [
			self.game_obj.sprite_sheet.get_sprite(382, 635, 174, 126),
			self.game_obj.sprite_sheet.get_sprite(0, 1879, 206, 107),			
			self.game_obj.sprite_sheet.get_sprite(0, 1559, 216, 101),			
			self.game_obj.sprite_sheet.get_sprite(0, 1456, 216, 101),
			self.game_obj.sprite_sheet.get_sprite(382, 510, 182, 123),			
		]

	def update(self):
		self.movement()
		self.animate()
		if random.random() > SHOOTING_PCT and len(self.game_obj.mobs_bullets) < 2:
			self.shoot()

	def movement(self):
		if self.mob_type == "flyman":
			self.flyman_vy += self.flyman_dy
			if self.flyman_vy > 3 or self.flyman_vy < -3:
				self.flyman_dy *= -1
			self.rect.y += self.flyman_vy

		if self.mob_type == "flyman" or self.mob_type == "wingman":
			self.rect.x += self.speedx

			if self.rect.left > WIDTH:
				self.rect.right = 0
				if self.mob_type == "flyman":
					self.game_obj.heli_sound.play()
			elif self.rect.right < 0:
				self.rect.left = WIDTH
				if self.mob_type == "flyman":
					self.game_obj.heli_sound.play()

		elif self.mob_type == "spikeman":
			self.rect.x += self.spike_speedx
			# Bounce off edges...
			if self.rect.left <= self.plat_rect.left:
				self.spike_speedx *= -1
			elif self.rect.right >= self.plat_rect.right:
				self.spike_speedx *= -1

			if self.spike_speedx > 0:
				self.anim_lst = self.spikeman_r
			else:
				self.anim_lst = self.spikeman_l

	def animate(self):
		now = pg.time.get_ticks()
		if now - self.last_frame_update > self.anim_wait_time:
			self.last_frame_update = now
			if self.mob_type in ["spikeman", "flyman"]:
				self.frame = (self.frame + 1) % len(self.anim_lst)
			else:
				self.frame += self.frame_speed

				if self.frame == 0 or self.frame + self.frame_speed >= len(self.anim_lst):
					self.frame_speed *= -1

			old_center = self.rect.center
			self.image = self.anim_lst[self.frame]
			self.rect = self.image.get_rect(center=old_center)
			self.mask = pg.mask.from_surface(self.image)


	def shoot(self):
		MobBullet(self.game_obj, self)


# Grass/Cactus...
class ExtraObjects(pg.sprite.Sprite):
	def __init__(self, game_obj, plat):
		self._layer = EXTRAS_LAYER
		super().__init__(game_obj.all_sprites)
		self.game_obj = game_obj
		self.plat = plat
		self.load_images()
		self.image = random.choice(self.extras)
		self.rect = self.image.get_rect()
		self.rect.bottom = plat.rect.top
		self.rect.x = random.randint(plat.rect.left, plat.rect.right - self.rect.width)

	def load_images(self):
		self.extras = [
			self.game_obj.sprite_sheet.get_sprite(707, 134, 117, 160),
			self.game_obj.sprite_sheet.get_sprite(534, 1063, 58, 57),
			self.game_obj.sprite_sheet.get_sprite(801, 752, 82, 70),
			self.game_obj.sprite_sheet.get_sprite(868, 1877, 58, 57),
			self.game_obj.sprite_sheet.get_sprite(784, 1931, 82, 70),
			self.game_obj.sprite_sheet.get_sprite(814, 1574, 81, 85),
			self.game_obj.sprite_sheet.get_sprite(812, 453, 81, 99),
		]
		# Add the same images but flipped...
		[self.extras.append(pg.transform.flip(img, True, False)) for img in self.extras[:]] # [:] as a copy

	def update(self):
		self.rect.bottom = self.plat.rect.top

		if not self.game_obj.platforms.has(self.plat):
			self.kill()


# Carrot/Money...
class Collectables(pg.sprite.Sprite):
	def __init__(self, game_obj, plat):
		self._layer = COLLECTABLES_LAYER
		super().__init__(game_obj.all_sprites, game_obj.collectables)
		self.game_obj = game_obj
		self.plat = plat
		self.load_images()


		self.frame = 0
		self.frame_speed = 1
		self.last_frame_update = 0
		self.anim_wait_time = 75

		self.collectable_type = random.choice(["gold_coin", "carrot", "silver_coin", "bronze_coin", "bronze_coin"])
		if self.collectable_type == "gold_coin":
			self.anim_lst = self.gold_coins
		elif self.collectable_type == "silver_coin":
			self.anim_lst = self.silver_coins
		elif self.collectable_type == "bronze_coin":
			self.anim_lst = self.bronze_coins
		elif self.collectable_type == "carrot":
			self.anim_lst = self.carrot

		if self.collectable_type == "carrot":
			self.image = self.carrot
		else:
			self.image = self.anim_lst[self.frame]

		self.rect = self.image.get_rect()
		self.rect.bottom = plat.rect.top
		self.rect.x = random.randint(plat.rect.left, plat.rect.right - self.rect.width)


	def load_images(self):
		self.carrot = self.game_obj.sprite_sheet.get_sprite(820, 1733, 78, 70) # Carrot

		self.gold_coins = [
			self.game_obj.sprite_sheet.get_sprite(698, 1931, 84, 84),
			self.game_obj.sprite_sheet.get_sprite(829, 0, 66, 84),
			self.game_obj.sprite_sheet.get_sprite(897, 1574, 50, 84),
			self.game_obj.sprite_sheet.get_sprite(645, 651, 15, 84),
		]

		self.silver_coins = [
			self.game_obj.sprite_sheet.get_sprite(584, 406, 84, 84),
			self.game_obj.sprite_sheet.get_sprite(852, 1003, 66, 84),
			self.game_obj.sprite_sheet.get_sprite(899, 1219, 50, 84),
			self.game_obj.sprite_sheet.get_sprite(662, 651, 14, 84),
		]
		self.bronze_coins = [
			self.game_obj.sprite_sheet.get_sprite(707, 296, 84, 84),
			self.game_obj.sprite_sheet.get_sprite(826, 206, 66, 84),
			self.game_obj.sprite_sheet.get_sprite(899, 116, 50, 84),
			self.game_obj.sprite_sheet.get_sprite(670, 406, 14, 84),
		]

	def update(self):
		self.rect.bottom = self.plat.rect.top - 10

		if not self.game_obj.platforms.has(self.plat):
			self.kill()

		if self.collectable_type != "carrot":
			self.animate()

	def animate(self):
		now = pg.time.get_ticks()

		if now - self.last_frame_update > self.anim_wait_time:
			self.last_frame_update = now
			old_center = self.rect.center

			self.frame += self.frame_speed
			if self.frame == 0 or self.frame + self.frame_speed >= len(self.anim_lst):
				self.frame_speed *= -1

			self.image = self.anim_lst[self.frame]
			self.rect = self.image.get_rect(center=old_center)


class MobBullet(pg.sprite.Sprite):
	def __init__(self, game_obj, mob):
		self._layer = MOB_BULLET_LAYER
		super().__init__(game_obj.all_sprites, game_obj.mobs_bullets)
		self.game_obj = game_obj
		# self.mob_type = mob.mob_type # for bullet collision -- to know what was the bullet/mob shape/type
		self.load_images()
		self.speedy = random.randint(2, 5)
		self.speedx = 0

		if mob.mob_type == "spikeman":
			game_obj.spike_bullet_sound.play()
			self.image = self.spike_bullet
			self.speedy = 0
			self.speedx = random.randint(2, 5)
			if random.random() > 0.5:
				self.speedx *= -1
		elif mob.mob_type == "flyman":
			game_obj.lightning_sound.play()
			self.image = self.yellow_lightning
		elif mob.mob_type == "wingman":
			game_obj.lightning_sound.play()
			self.image = self.blue_lightning


		self.rect = self.image.get_rect()
		self.rect.top = mob.rect.bottom
		if mob.mob_type == "spikeman":
			self.rect.centery = mob.rect.centery
		self.rect.centerx = mob.rect.centerx

	def load_images(self):
		self.yellow_lightning = pg.transform.scale(self.game_obj.sprite_sheet.get_sprite(897, 0, 55, 114), (int(27 // 1.3), int(57 // 1.3)))

		self.blue_lightning = pg.transform.scale(self.game_obj.sprite_sheet.get_sprite(895, 453, 55, 114), (int(27 // 1.3), int(57 // 1.3)))

		self.spike_bullet = pg.transform.scale(self.game_obj.sprite_sheet.get_sprite(284, 1254, 20, 20), (20, 20))

	def update(self):
		self.rect.y += self.speedy
		self.rect.x += self.speedx

		if self.rect.top > HEIGHT or self.rect.left > WIDTH or self.rect.right < 0:
			self.kill()


class Cloud(pg.sprite.Sprite):
	def __init__(self, game_obj, pos_x=None, pos_y=None):
		super().__init__(game_obj.all_sprites, game_obj.clouds)
		self.image = random.choice(game_obj.cloud_images)
		self.rect = self.image.get_rect()
		if pos_x is None:
			pos_x = random.randint(-100, WIDTH - self.rect.width // 1.5)
		if pos_y is None:
			pos_y = random.randint(-1000, -50)
		scale = 1
		if random.random() > 0.5:
			scale = random.randint(50, 100) / 100
		self.image = pg.transform.scale(self.image, (int(self.rect.width * scale), int(self.rect.height * scale)))
		self.rect.topleft = [pos_x, pos_y]

	def update(self):
		if self.rect.top > HEIGHT + HEIGHT / 4:
			self.kill()
